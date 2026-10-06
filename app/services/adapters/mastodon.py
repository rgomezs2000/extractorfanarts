"""Adaptador de Mastodon (API nativa pública, sin login)."""
from __future__ import annotations

import re

from ...models.artwork import Artwork, SearchQuery
from ..http_client import BlockedError, PoliteClient
from .base import SearchAdapter

_HASHTAG_RE = re.compile(r"#([\w]+)")


class MastodonAdapter(SearchAdapter):
    def __init__(self, instance: str):
        instance = instance.strip()
        if not instance.startswith(("http://", "https://")):
            instance = "https://" + instance
        self.base = instance.rstrip("/")
        self.name = f"Mastodon · {self.base.split('://', 1)[-1]}"

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        statuses: list[dict] = []
        if query.usuario:
            statuses = self._by_user(client, query)
        elif query.hashtag:
            statuses = self._by_hashtag(client, query)
        else:
            statuses = self._by_keyword(client, query)

        out: list[Artwork] = []
        for st in statuses:
            for media in st.get("media_attachments", []):
                if media.get("type") not in ("image", "unknown"):
                    continue
                art = self._normalize(st, media)
                if art is not None:
                    out.append(art)
                    if len(out) >= query.limit:
                        return out
        return out

    def _by_user(self, client: PoliteClient, query: SearchQuery) -> list[dict]:
        acct = query.usuario.strip().lstrip("@")
        data = client.get_json(
            f"{self.base}/api/v2/search",
            params={"q": acct, "type": "accounts", "limit": "5", "resolve": "true"},
        )
        accounts = data.get("accounts", [])
        if not accounts:
            raise BlockedError(f"no se encontró el usuario '{acct}' en {self.base}")
        acc_id = accounts[0]["id"]
        return client.get_json(
            f"{self.base}/api/v1/accounts/{acc_id}/statuses",
            params={"limit": "40", "only_media": "true"},
        )

    def _by_hashtag(self, client: PoliteClient, query: SearchQuery) -> list[dict]:
        tag = query.hashtag.strip().lstrip("#")
        return client.get_json(
            f"{self.base}/api/v1/timelines/tag/{tag}",
            params={"limit": "40", "only_media": "true"},
        )

    def _by_keyword(self, client: PoliteClient, query: SearchQuery) -> list[dict]:
        data = client.get_json(
            f"{self.base}/api/v2/search",
            params={"q": query.keyword, "type": "statuses", "limit": "40", "resolve": "false"},
        )
        return data.get("statuses", [])

    # ------------------------------------------------------------------ normalización
    def _normalize(self, st: dict, media: dict) -> Artwork | None:
        url = media.get("url")
        if not url:
            return None
        text = st.get("content") or ""
        tags = [t.get("name", "") for t in st.get("tags", [])]
        tags += _HASHTAG_RE.findall(text)
        account = st.get("account", {})
        author = account.get("acct") or account.get("username")
        return Artwork(
            site=self.name,
            site_id=str(st.get("id", "")),
            url=url,
            preview_url=media.get("preview_url") or url,
            page_url=st.get("url") or st.get("uri"),
            tags=list(dict.fromkeys(t for t in tags if t)),
            rating="general",
            md5=None,
            author=author,
            license=None,
            created_at=st.get("created_at"),
            content_text=re.sub(r"<[^>]+>", " ", text)[:2000],
            source_field=None,
            raw=st,
        )
