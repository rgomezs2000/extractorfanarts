"""Adaptador de Misskey / CherryPick (misma API; endpoints públicos sin token).

Soporta cualquier instancia:
  - `@usuario`          → se busca en la instancia seleccionada (campo Instancia).
  - `@usuario@host.tld` → se consulta **la instancia de ese usuario** directamente.
  - `#hashtag` / palabra clave → búsqueda por etiqueta o timeline pública de la
    instancia, filtrada localmente.

**Filtros combinados:** los tres campos (usuario, palabras clave y hashtags) se aplican
a la vez, y se admiten **varios** valores en palabras clave y hashtags. La API de Misskey
no sabe combinarlos, así que se piden candidatos (con paginación) y se filtran en local
con `social_filtros.Criterios`.
"""
from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

from ... import config
from ...models.artwork import Artwork, SearchQuery
from ..http_client import BlockedError, PoliteClient, SinResultados
from .base import SearchAdapter
from .mastodon import host_de_handle, normalizar_instancia
from .social_filtros import Criterios, etiquetas_de

logger = logging.getLogger("imaginteca")

_HASHTAG_RE = re.compile(r"#([\w]+)")


class MisskeyAdapter(SearchAdapter):
    def __init__(self, instance: str = "misskey.io"):
        self.base_default = normalizar_instancia(instance) or "https://misskey.io"
        self.name = f"Misskey · {self._host(self.base_default)}"

    @staticmethod
    def _host(base: str) -> str:
        return urlparse(base).netloc or base

    def _base(self, query: SearchQuery) -> str:
        host = host_de_handle(query.usuario)
        if host:
            return normalizar_instancia(host)
        if query.instance:
            return normalizar_instancia(query.instance)
        return self.base_default

    def _api(self, client: PoliteClient, base: str, endpoint: str, payload: dict):
        return client.post_json(f"{base}/api/{endpoint}", payload)

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        base = self._base(query)
        criterios = Criterios.desde_query(query)
        if criterios.vacio:
            return []
        aviso = getattr(client, "aviso", None)
        if aviso is not None:
            aviso(f"filtros de búsqueda → {criterios.detalle()}")
        logger.info("Misskey %s: %s", self._host(base), criterios.descripcion())

        notas = self._candidatas(client, criterios, base, query.limit)
        descartadas = 0
        out: list[Artwork] = []
        for note in notas:
            texto = note.get("text") or ""
            etiquetas = etiquetas_de(note.get("tags") or [], _HASHTAG_RE.findall(texto))
            user = note.get("user") or {}
            username = user.get("username") or ""
            host = user.get("host") or ""
            autor = f"@{username}@{host}" if host else f"@{username}"
            if not criterios.cumple(texto=texto, etiquetas=etiquetas, autor=autor):
                descartadas += 1
                continue
            for f in note.get("files", []) or []:
                if not str(f.get("type", "")).startswith("image"):
                    continue
                art = self._normalize(note, f, base)
                if art is not None:
                    out.append(art)
                    if len(out) >= query.limit:
                        return out
        logger.info("Misskey %s: %d notas revisadas, %d descartadas, %d imágenes",
                    self._host(base), len(notas), descartadas, len(out))
        return out

    # ------------------------------------------------------------------ candidatas
    def _candidatas(self, client: PoliteClient, criterios: Criterios, base: str,
                    limite: int) -> list[dict]:
        if criterios.fuente == "usuario":
            return self._por_usuario(client, criterios, base, limite)
        if criterios.hashtags:
            listas = [self._por_etiqueta(client, base, tag) for tag in criterios.hashtags]
            listas = [lista for lista in listas if lista]
            if listas:
                if criterios.exigir_todos and len(listas) > 1:
                    comunes = {str(n.get("id")) for n in listas[0]}
                    for lista in listas[1:]:
                        comunes &= {str(n.get("id")) for n in lista}
                    return [n for n in listas[0] if str(n.get("id")) in comunes]
                union: dict[str, dict] = {}
                for lista in listas:
                    for nota in lista:
                        union.setdefault(str(nota.get("id")), nota)
                return list(union.values())
        return self._por_timeline(client, base)

    def _por_usuario(self, client: PoliteClient, criterios: Criterios, base: str,
                     limite: int) -> list[dict]:
        username = criterios.usuario.strip().lstrip("@").split("@", 1)[0]
        try:
            usuarios = self._api(client, base, "users/search-by-username-and-host", {
                "username": username, "host": None, "limit": 5,
            })
        except Exception:  # noqa: BLE001
            usuarios = []
        if not usuarios:
            mostrado = self._api(client, base, "users/show", {"username": username})
            usuarios = [mostrado] if mostrado else []
        if not usuarios:
            raise SinResultados(f"no se encontró el usuario '@{username}' en {self._host(base)}")

        notas: list[dict] = []
        until_id: str | None = None
        for _ in range(max(1, int(getattr(config, "SOCIAL_PAGINAS", 6)))):
            payload = {"userId": usuarios[0]["id"], "limit": min(config.SOCIAL_PAGINA, 100),
                       "withFiles": True}
            if until_id:
                payload["untilId"] = until_id
            pagina = self._api(client, base, "users/notes", payload)
            if not pagina:
                break
            notas.extend(pagina)
            encontradas = 0
            for note in notas:
                texto = note.get("text") or ""
                etiquetas = etiquetas_de(note.get("tags") or [], _HASHTAG_RE.findall(texto))
                if criterios.cumple(texto=texto, etiquetas=etiquetas):
                    encontradas += 1
            if encontradas >= limite or len(notas) >= config.SOCIAL_MAX_CANDIDATOS:
                break
            if not (criterios.palabras or criterios.hashtags):
                break                      # sin filtros extra, una página basta
            until_id = str(pagina[-1].get("id") or "")
            if not until_id:
                break
        return notas

    def _por_etiqueta(self, client: PoliteClient, base: str, tag: str) -> list[dict]:
        """Notas de una etiqueta (con respaldo a la timeline si la API lo exige)."""
        try:
            return self._api(client, base, "notes/search-by-tag", {
                "tag": tag, "limit": min(config.SOCIAL_MAX_CANDIDATOS, 100),
                "withFiles": True,
            })
        except Exception as exc:  # noqa: BLE001
            logger.info("búsqueda por etiqueta no disponible en %s (%s); se usa la timeline",
                        self._host(base), exc)
        return []

    def _por_timeline(self, client: PoliteClient, base: str) -> list[dict]:
        return self._api(client, base, "notes/local-timeline", {
            "limit": min(config.SOCIAL_MAX_CANDIDATOS, 100), "withFiles": True,
        })

    # ------------------------------------------------------------------ normalización
    def _normalize(self, note: dict, f: dict, base: str) -> Artwork | None:
        url = f.get("url")
        if not url:
            return None
        user = note.get("user", {})
        username = user.get("username", "")
        host = user.get("host") or ""
        author = f"@{username}@{host}" if host else f"@{username}"
        sensitive = bool(f.get("isSensitive"))
        text = note.get("text") or ""
        tags = list(note.get("tags") or [])
        tags += _HASHTAG_RE.findall(text)
        return Artwork(
            site=f"Misskey · {self._host(base)}",
            site_id=str(note.get("id", "")),
            url=url,
            preview_url=f.get("thumbnailUrl") or url,
            page_url=f"{base}/notes/{note.get('id')}",
            tags=list(dict.fromkeys(t for t in tags if t)),
            rating="sensitive" if sensitive else "general",
            md5=None,
            author=author,
            license=None,
            created_at=note.get("createdAt"),
            content_text=(text or "")[:2000],
            source_field=None,
            raw=note,
        )
