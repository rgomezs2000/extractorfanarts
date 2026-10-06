"""Adaptador de Tumblr (consumer key, OAuth 1.0a; sin login de usuario).

Requiere TUMBLR_API_KEY en app/config.py.
"""
from __future__ import annotations

from ... import config
from ...models.artwork import Artwork, SearchQuery
from ..http_client import ConfigError, PoliteClient
from .base import SearchAdapter

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
        posts: list[dict] = []
        if query.usuario:
            blog = query.usuario.strip().lstrip("@").split(".")[0]
            data = client.get_json(
                f"{API_BASE}/blog/{blog}.tumblr.com/posts/photo",
                params={"api_key": config.TUMBLR_API_KEY, "limit": "20"},
            )
            posts = data.get("response", [])
        else:
            tag = (query.hashtag or query.keyword or "").strip().lstrip("#")
            if not tag:
                return []
            data = client.get_json(
                f"{API_BASE}/tagged",
                params={"tag": tag, "api_key": config.TUMBLR_API_KEY, "limit": "20"},
            )
            posts = data.get("response", [])

        out: list[Artwork] = []
        for post in posts:
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
