"""Adaptador de Misskey / CherryPick (misma API; endpoints públicos sin token).

Soporta cualquier instancia:
  - `@usuario`          → se busca en la instancia seleccionada (campo Instancia).
  - `@usuario@host.tld` → se consulta **la instancia de ese usuario** directamente.
  - `#hashtag` / palabra clave → timeline pública de la instancia, filtrada localmente
    (la búsqueda de texto de Misskey suele exigir token, así que no se usa).
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

from ...models.artwork import Artwork, SearchQuery
from ..http_client import BlockedError, PoliteClient
from .base import SearchAdapter
from .mastodon import host_de_handle, normalizar_instancia

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
        if query.usuario:
            notes = self._by_user(client, query, base)
        else:
            notes = self._by_timeline(client, query, base)

        out: list[Artwork] = []
        for note in notes:
            for f in note.get("files", []) or []:
                if not str(f.get("type", "")).startswith("image"):
                    continue
                art = self._normalize(note, f, base)
                if art is not None:
                    out.append(art)
                    if len(out) >= query.limit:
                        return out
        return out

    def _by_user(self, client: PoliteClient, query: SearchQuery, base: str) -> list[dict]:
        handle = query.usuario.strip().lstrip("@")
        username = handle.split("@", 1)[0]
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
            raise BlockedError(f"no se encontró el usuario '@{username}' en {self._host(base)}")
        return self._api(client, base, "users/notes", {
            "userId": usuarios[0]["id"], "limit": min(query.limit, 100), "withFiles": True,
        })

    def _by_timeline(self, client: PoliteClient, query: SearchQuery, base: str) -> list[dict]:
        notes = self._api(client, base, "notes/local-timeline",
                          {"limit": 100, "withFiles": True})
        needle = (query.hashtag or query.keyword or "").strip().lstrip("#").lower()
        if not needle:
            return notes
        return [
            n for n in notes
            if needle in (n.get("text") or "").lower()
            or needle in [t.lower() for t in (n.get("tags") or [])]
        ]

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
