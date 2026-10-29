"""Adaptador de Bluesky (API pública atproto, sin autenticación).

**Filtros combinados:** usuario (`from:`), varias palabras clave y varios hashtags se
envían juntos a la API de búsqueda y, además, se comprueban en local con
`social_filtros.Criterios` (la API puede devolver coincidencias parciales; así el
resultado cumple TODOS los filtros, igual que en el fediverso).
"""
from __future__ import annotations

import logging
import re

from ...models.artwork import Artwork, SearchQuery
from ..http_client import PoliteClient
from .base import SearchAdapter
from .social_filtros import Criterios, repartir_en_lotes

logger = logging.getLogger("imaginteca")

_HASHTAG_RE = re.compile(r"#([\w]+)")
# Bases de la API pública, en orden de preferencia. public.api.bsky.app está
# detrás de un CDN que devuelve 403 (BunnyCDN) a las peticiones de programas;
# pi.bsky.app sirve el mismo contenido y responde bien.
API_BASES = (
    "https://api.bsky.app/xrpc",
    "https://public.api.bsky.app/xrpc",
)
API_BASE = API_BASES[0]
# Longitud máxima razonable de la consulta (la API de Bluesky la limita). No limita
# cuántos valores escribes: si no caben en una consulta, se hacen varias y se unen.
MAX_CONSULTA = 300


class BlueskyAdapter(SearchAdapter):
    name = "Bluesky"

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        criterios = Criterios.desde_query(query)
        if criterios.vacio:
            return []
        aviso = getattr(client, "aviso", None)
        if aviso is not None:
            aviso(f"filtros de búsqueda → {criterios.detalle()}")

        partes: list[str] = []
        if criterios.usuario:
            # En Bluesky los handles se escriben con puntos; si viene del fediverso
            # ('@usuario@host') se convierte a 'usuario.host'.
            partes.append(f"from:{criterios.usuario.strip().lstrip('@').replace('@', '.')}")
        for tag in criterios.hashtags:
            partes.append(f"#{tag}")
        for frase in criterios.palabras:
            partes.append(f'"{frase}"' if " " in frase else frase)

        # N valores sin límite: una consulta por lote y se unen las publicaciones
        publicaciones: list[dict] = []
        vistas: set[str] = set()
        for lote in repartir_en_lotes(partes, MAX_CONSULTA):
            consulta = " ".join(lote)
            logger.info("Bluesky: %s", consulta)
            # Las bases se prueban en orden: el CDN que sirve public.api.bsky.app devuelve
            # 403 Forbidden (BunnyCDN) aunque la petición sea legítima; api.bsky.app sí
            # responde con el mismo contenido.
            data = None
            ultimo_error: Exception | None = None
            for base in API_BASES:
                try:
                    data = client.get_json(
                        f"{base}/app.bsky.feed.searchPosts",
                        params={"q": consulta, "limit": str(min(query.limit, 25))},
                    )
                    break
                except Exception as exc:  # noqa: BLE001
                    ultimo_error = exc
                    logger.info("Bluesky: %s no respondió (%s); se prueba otra base", base, exc)
            if data is None:
                if ultimo_error is not None:
                    raise ultimo_error
                continue
            for post in data.get("posts", []) or []:
                clave = str(post.get("uri") or post.get("cid"))
                if clave not in vistas:
                    vistas.add(clave)
                    publicaciones.append(post)

        descartados = 0
        out: list[Artwork] = []
        for post in publicaciones:
            record = post.get("record") or {}
            texto = record.get("text") or ""
            etiquetas = _HASHTAG_RE.findall(texto)
            autor = (post.get("author") or {}).get("handle") or ""
            if not criterios.cumple(texto=texto, etiquetas=etiquetas, autor=autor):
                descartados += 1
                continue
            for art in self._post_images(post):
                out.append(art)
                if len(out) >= query.limit:
                    return out
        logger.info("Bluesky: %d publicaciones, %d descartadas por los filtros, %d imágenes",
                    len(publicaciones), descartados, len(out))
        return out

    # ------------------------------------------------------------------ extracción
    def _post_images(self, post: dict) -> list[Artwork]:
        record = post.get("record", {})
        # En `searchPosts` las imágenes NO vienen en `record.embed` (eso es el embebido
        # «de escritura», con tipos sin sufijo) sino en `post.embed`, ya resuelto por el
        # servidor con tipos `#view`: app.bsky.embed.images#view. Mirando solo
        # record.embed no se extraía ninguna imagen y la búsqueda daba cero resultados.
        images: list[dict] = []
        for origen in (post.get("embed"), record.get("embed")):
            if not isinstance(origen, dict) or not origen:
                continue
            etype = str(origen.get("$type") or "")
            if etype.startswith("app.bsky.embed.images"):
                images = origen.get("images") or []
            elif etype.startswith("app.bsky.embed.recordWithMedia"):
                media = origen.get("media") or {}
                if str(media.get("$type") or "").startswith("app.bsky.embed.images"):
                    images = media.get("images") or []
            if images:
                break

        author = post.get("author", {})
        did = author.get("did", "")
        rkey = (post.get("uri") or "").rsplit("/", 1)[-1]
        text = record.get("text") or ""
        tags = _HASHTAG_RE.findall(text)

        out: list[Artwork] = []
        for img in images:
            thumb = img.get("thumb")
            full = img.get("fullsize")
            if not (thumb or full):
                continue
            out.append(Artwork(
                site=self.name,
                site_id=f"{did}/{rkey}",
                url=full or thumb,
                preview_url=thumb or full,
                page_url=f"https://bsky.app/profile/{did}/post/{rkey}",
                tags=list(dict.fromkeys(tags)),
                rating="general",
                md5=None,
                author=author.get("handle") or author.get("displayName"),
                license=None,
                created_at=record.get("createdAt"),
                content_text=text[:2000],
                source_field=None,
                raw=post,
            ))
        return out
