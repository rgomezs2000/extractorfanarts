"""Adaptador de X / Twitter sobre la API pública de **FxTwitter** (proyecto FxEmbed).

FxTwitter (https://github.com/FxEmbed/FxEmbed, licencia MIT) publica una API con datos de
X **sin cuenta ni claves**: perfiles, posts, medios, hilos…  Este adaptador usa solo lo
justo para traer imágenes y va **espaciando las peticiones** a propósito (FxTwitter permite
1000 por minuto y por IP; aquí se va mucho más despacio, con un retardo explícito entre
consultas, para no comportarse como un bot ni saturar un servicio comunitario).

Qué permite y qué no — es una limitación de X, no del programa:

  · ✅ **Galería de un usuario**: `/2/profile/<usuario>/media` (con paginación).
  · ✅ **Un post concreto**: `/2/status/<id>` (pegando el enlace del tuit o su id en
       el campo «@usuario»).
  · ❌ **Buscar por palabra clave o hashtag**: X no sirve esa búsqueda sin sesión de
       usuario y FxTwitter responde 404. Para eso están las demás plataformas.
"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime

from ... import config
from ...models.artwork import Artwork, SearchQuery
from ..http_client import ConfigError, PoliteClient
from .base import SearchAdapter
from .social_filtros import Criterios

logger = logging.getLogger("imaginteca")

BASE = "https://api.fxtwitter.com"
# Un enlace de tuit, o un id suelto, en el campo «@usuario».
_POST_RE = re.compile(r"(?:status/|statuses/)(\d{5,})")
_ID_RE = re.compile(r"^\d{5,}$")
# Cortesía entre peticiones (segundos). Ajustable en config_local.py.
PAUSA = float(getattr(config, "FXTWITTER_PAUSA", 1.2) or 1.2)
MAX_PAGINAS = int(getattr(config, "FXTWITTER_MAX_PAGINAS", 4) or 4)


class XAdapter(SearchAdapter):
    name = "X (Twitter)"

    def __init__(self):
        self._ultima = 0.0

    # ------------------------------------------------------------------ cortesía
    def _esperar(self) -> None:
        """Deja pasar el retardo entre peticiones (para no comportarse como un bot)."""
        if PAUSA <= 0:
            return
        if self._ultima:
            desde = time.monotonic() - self._ultima
            if desde < PAUSA:
                time.sleep(PAUSA - desde)
        self._ultima = time.monotonic()

    def _pedir(self, client: PoliteClient, ruta: str, params: dict | None = None) -> dict:
        self._esperar()
        logger.info("FxTwitter: GET %s %s", ruta, params or "")
        return client.get_json(f"{BASE}{ruta}", params=params or {})

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        criterios = Criterios.desde_query(query)
        if criterios.vacio:
            return []

        usuario = (criterios.usuario or "").strip()
        if usuario:
            return self._de_un_usuario(client, query, usuario)

        raise ConfigError(
            "X (Twitter) por FxTwitter trae imágenes **por usuario** y **posts sueltos**\n"
            "(no hay búsqueda por palabra clave: X no la sirve sin sesión y FxTwitter\n"
            "responde 404).\n\n"
            "· Para la galería de alguien: escribe su @usuario (p. ej. @NASA).\n"
            "· Para un post concreto: pega su enlace (https://x.com/usuario/status/…)\n"
            "  o su número de id en el campo «@usuario».\n"
            "· Para buscar por tema o hashtag, usa otra plataforma (boorus, fediverso,\n"
            "  DeviantArt, Pixiv, Tumblr, Bluesky…).\n"
            "Sin claves y sin cuenta: no hay nada que configurar."
        )

    def _de_un_usuario(self, client: PoliteClient, query: SearchQuery,
                       usuario: str) -> list[Artwork]:
        """Un post concreto (si lo que hay es un enlace/id) o la galería del usuario."""
        enlace = _POST_RE.search(usuario)
        if enlace or _ID_RE.match(usuario):
            ident = enlace.group(1) if enlace else usuario
            datos = self._pedir(client, f"/2/status/{ident}")
            post = datos.get("status") or datos
            return self._arte_de_post(post)

        handle = usuario.lstrip("@").strip()
        if not handle:
            return []
        salida: list[Artwork] = []
        cursor = ""
        for pagina in range(MAX_PAGINAS):
            params: dict = {"count": "40"}
            if cursor:
                params["cursor"] = cursor
            datos = self._pedir(client, f"/2/profile/{handle}/media", params)
            for post in datos.get("results") or []:
                salida.extend(self._arte_de_post(post))
                if len(salida) >= query.limit:
                    return salida[: query.limit]
            cursor = str(((datos.get("cursor") or {}).get("bottom")) or "")
            if not cursor or not datos.get("results"):
                break
            logger.info("FxTwitter: página %d de %s (llevamos %d imágenes)",
                        pagina + 1, handle, len(salida))
        return salida[: query.limit]

    # ------------------------------------------------------------------ normalizar
    def _arte_de_post(self, post: dict) -> list[Artwork]:
        """Una imagen por foto del post (los vídeos y GIF se ignoran: esto es de fotos)."""
        if not isinstance(post, dict) or not post:
            return []
        media = post.get("media") or {}
        fotos = media.get("photos") or []
        if not fotos:
            return []
        autor = post.get("author") or {}
        usuario = str(autor.get("screen_name") or "").strip()
        texto = str(post.get("text") or post.get("raw_text") or "").strip()
        sensible = bool(post.get("possibly_sensitive"))
        ident = str(post.get("id") or "")
        enlace = (str(post.get("url") or "")
                  or (f"https://x.com/{usuario}/status/{ident}" if ident else ""))
        fecha = None
        marca = post.get("created_timestamp")
        if marca:
            try:
                fecha = datetime.fromtimestamp(int(marca))
            except (TypeError, ValueError, OSError):
                fecha = None

        salida: list[Artwork] = []
        for indice, foto in enumerate(fotos):
            if not isinstance(foto, dict):
                continue
            url = str(foto.get("url") or "").strip()
            if not url:
                continue
            sufijo = f"{ident}_{indice}" if len(fotos) > 1 else ident
            salida.append(Artwork(
                site="X (Twitter)",
                site_id=sufijo or url,
                url=url,
                preview_url=_miniatura(url),
                page_url=enlace or url,
                tags=[texto[:120]] if texto else [],
                rating="sensitive" if sensible else "general",
                md5=None,
                author=(f"@{usuario}" if usuario else None),
                license=None,
                created_at=fecha,
                content_text=texto or None,
                source_field="fxtwitter",
                raw=post,
            ))
        return salida


def _miniatura(url: str) -> str:
    """Miniatura de la CDN de X (más ligera) para la tira de ejemplos."""
    if not url:
        return url
    separador = "&" if "?" in url else "?"
    return f"{url}{separador}name=small"
