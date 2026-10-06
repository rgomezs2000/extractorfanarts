"""Adaptador de Misskey / CherryPick (misma API; endpoints públicos sin token).

La búsqueda de texto (notes/search) suele exigir token, así que el adaptador
usa timelines públicas y filtra por palabra clave / hashtag localmente.
"""
from __future__ import annotations

import re

from ...models.artwork import Artwork, SearchQuery
from ..http_client import BlockedError, PoliteClient
from .base import SearchAdapter

_HASHTAG_RE = re.compile(r"#([\w]+)")


class MisskeyAdapter(SearchAdapter):
    def __init__(self, instance: str):
        instance = instance.strip()
        if not instance.startswith(("http://", "https://")):
            instance = "https://" + instance
        self.base = instance.rstrip("/")
        self.name = f"Misskey · {self.base.split('://', 1)[-1]}"

    def _api(self, client: PoliteClient, endpoint: str, payload: dict):
        return client.post_json(f"{self.base}/api/{endpoint}", payload)

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        notes: list[dict] = []
        if query.usuario:
            notes = self._by_user(client, query)
        else:
            notes = self._by_timeline(client, query)

        out: list[Artwork] = []
        for note in notes:
            for f in note.get("files", []) or []:
                if not str(f.get("type", "")).startswith("image"):
                    continue
                art = self._normalize(note, f)
                if art is not None:
                    out.append(art)
                    if len(out) >= query.limit:
                        return out
        return out

    def _by_user(self, client: PoliteClient, query: SearchQuery) -> list[dict]:
        handle = query.usuario.strip().lstrip("@")
        if "@" in handle:
            username, host = handle.split("@", 1)
        else:
            username, host = handle, None
        try:
            users = self._api(client, "users/search-by-username-and-host", {
                "username": username, "host": host, "limit": 5,
            })
        except BlockedError:
            users = []
        if not users:
            shown = self._api(client, "users/show", {"username": username, "host": host})
            users = [shown] if shown else []
        if not users:
            raise BlockedError(f"no se encontró el usuario '{handle}' en {self.base}")
        return self._api(client, "users/notes", {
            "userId": users[0]["id"], "limit": min(query.limit, 100), "withFiles": True,
        })

    def _by_timeline(self, client: PoliteClient, query: SearchQuery) -> list[dict]:
        notes = self._api(client, "notes/local-timeline", {"limit": 100, "withFiles": True})
        needle = (query.hashtag or query.keyword or "").strip().lstrip("#").lower()
        if not needle:
            return notes
        return [
            n for n in notes
            if needle in (n.get("text") or "").lower()
            or needle in [t.lower() for t in (n.get("tags") or [])]
        ]

    # ------------------------------------------------------------------ normalización
    def _normalize(self, note: dict, f: dict) -> Artwork | None:
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
            site=self.name,
            site_id=str(note.get("id", "")),
            url=url,
            preview_url=f.get("thumbnailUrl") or url,
            page_url=f"{self.base}/notes/{note.get('id')}",
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
