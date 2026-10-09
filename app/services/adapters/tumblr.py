"""Adaptador de Tumblr (consumer key, OAuth 1.0a; sin login de usuario).

Requiere TUMBLR_API_KEY en app/config.py.

**Filtros combinados:** usuario + palabras clave + hashtags se exigen todos (varios
valores admitidos). La API de Tumblr solo sabe buscar por blog o por una etiqueta, así
que se piden candidatos con el criterio más selectivo y se filtran en local.
"""
from __future__ import annotations

import logging

from ... import config
from ...models.artwork import Artwork, SearchQuery
from ..http_client import ConfigError, PoliteClient
from .base import SearchAdapter
from .social_filtros import Criterios

logger = logging.getLogger("imaginteca")

API_BASE = "https://api.tumblr.com/v2"


class TumblrAdapter(SearchAdapter):
    name = "Tumblr"

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        if not config.TUMBLR_API_KEY:
            raise ConfigError(
                "Tumblr requiere una consumer key: completa TUMBLR_API_KEY "
                "en app/config.py (https://www.tumblr.com/oauth/apps)"
            )
        criterios = Criterios.desde_query(query)
        if criterios.vacio:
            return []

        posts: list[dict] = []
        vistos: set[str] = set()
        if criterios.usuario:
            blog = criterios.usuario.strip().lstrip("@").split(".")[0]
            data = client.get_json(
                f"{API_BASE}/blog/{blog}.tumblr.com/posts/photo",
                params={"api_key": config.TUMBLR_API_KEY, "limit": "20"},
            )
            posts = data.get("response", [])
        else:
            # N valores sin límite: se consulta cada etiqueta o palabra clave y se unen
            terminos = list(criterios.hashtags) + list(criterios.palabras)
            if not terminos:
                return []
            for tag in terminos:
                try:
                    data = client.get_json(
                        f"{API_BASE}/tagged",
                        params={"tag": tag, "api_key": config.TUMBLR_API_KEY, "limit": "20"},
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.info("Tumblr: «%s» no se pudo consultar (%s)", tag, exc)
                    continue
                for post in data.get("response", []) or []:
                    clave = str(post.get("id"))
                    if clave not in vistos:
                        vistos.add(clave)
                        posts.append(post)

        out: list[Artwork] = []
        for post in posts:
            texto = f"{post.get('caption') or ''} {post.get('summary') or ''}"
            if not criterios.cumple(texto=texto, etiquetas=post.get("tags") or [],
                                    autor=post.get("blog_name") or ""):
                continue
            for art in self._normalize(post):
                out.append(art)
                if len(out) >= query.limit:
                    return out
        return out

    # ------------------------------------------------------------------ normalización
    def _normalize(self, post: dict) -> list[Artwork]:
        arts: list[Artwork] = []
        for photo in post.get("photos", []):
            original = photo.get("original_size") or {}
            url = original.get("url")
            if not url:
                continue
            alt_sizes = photo.get("alt_sizes") or []
            preview = alt_sizes[-1]["url"] if alt_sizes else url
            tags = list(post.get("tags") or [])
            arts.append(Artwork(
                site=self.name,
                site_id=str(post.get("id", "")),
                url=url,
                preview_url=preview,
                page_url=post.get("post_url"),
                tags=tags,
                rating="explicit" if post.get("is_nsfw") else "general",
                md5=None,
                author=post.get("blog_name"),
                license=None,
                created_at=post.get("date"),
                content_text=(post.get("caption") or "")[:2000],
                source_field=None,
                raw=post,
            ))
        return arts
