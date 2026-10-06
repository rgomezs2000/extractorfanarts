"""Adaptador de Bluesky (API pública atproto, sin autenticación)."""
from __future__ import annotations

import re

from ...models.artwork import Artwork, SearchQuery
from ..http_client import PoliteClient
from .base import SearchAdapter

_HASHTAG_RE = re.compile(r"#([\w]+)")
API_BASE = "https://public.api.bsky.app/xrpc"


class BlueskyAdapter(SearchAdapter):
    name = "Bluesky"

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        parts = []
        if query.usuario:
            parts.append(f"from:{query.usuario.strip().lstrip('@')}")
        if query.hashtag:
            parts.append(f"#{query.hashtag.strip().lstrip('#')}")
        if query.keyword:
            parts.append(query.keyword.strip())
        if not parts:
            return []
        q = " ".join(parts)

        data = client.get_json(
            f"{API_BASE}/app.bsky.feed.searchPosts",
            params={"q": q, "limit": str(min(query.limit, 25))},
        )
        out: list[Artwork] = []
        for post in data.get("posts", []):
            for art in self._post_images(post):
                out.append(art)
                if len(out) >= query.limit:
                    return out
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
