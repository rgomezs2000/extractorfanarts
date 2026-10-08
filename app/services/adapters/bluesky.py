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

logger = logging.getLogger("extractorfanarts")

_HASHTAG_RE = re.compile(r"#([\w]+)")
API_BASE = "https://public.api.bsky.app/xrpc"
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
            data = client.get_json(
                f"{API_BASE}/app.bsky.feed.searchPosts",
                params={"q": consulta, "limit": str(min(query.limit, 25))},
            )
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
        embed = record.get("embed") or {}
        images: list[dict] = []
        etype = embed.get("$type", "")
        if etype == "app.bsky.embed.images":
            images = embed.get("images", [])
        elif etype == "app.bsky.embed.recordWithMedia":
            media = embed.get("media") or {}
            if media.get("$type") == "app.bsky.embed.images":
                images = media.get("images", [])

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
