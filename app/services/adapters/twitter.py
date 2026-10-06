"""Adaptador de X / Twitter (API v2 oficial, autenticación app-only).

La API de X es DE PAGO por uso desde 2026: requiere una app de desarrollador
con facturación activa. Configura X_BEARER_TOKEN (o X_API_KEY + X_API_SECRET)
en app/config.py. Sin credenciales, este adaptador informa el motivo.
"""
from __future__ import annotations

import base64
import re

from ... import config
from ...models.artwork import Artwork, SearchQuery
from ..http_client import ConfigError, PoliteClient
from .base import SearchAdapter

_HASHTAG_RE = re.compile(r"#([\w]+)")
API_BASE = "https://api.twitter.com/2"


class XAdapter(SearchAdapter):
    name = "X (Twitter)"

    def __init__(self):
        self._token: str | None = None

    # ------------------------------------------------------------------ token
    def _bearer(self, client: PoliteClient) -> str:
        if self._token:
            return self._token
        if config.X_BEARER_TOKEN:
            self._token = config.X_BEARER_TOKEN
            return self._token
        if not (config.X_API_KEY and config.X_API_SECRET):
            raise ConfigError(
                "X (Twitter) requiere credenciales en app/config.py: "
                "X_BEARER_TOKEN, o X_API_KEY + X_API_SECRET. La API es de pago "
                "por uso desde 2026 (app de desarrollador con facturación)."
            )
        cred = base64.b64encode(
            f"{config.X_API_KEY}:{config.X_API_SECRET}".encode("utf-8")
        ).decode("ascii")
        data = client.post_form(
            "https://api.twitter.com/oauth2/token",
            {"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {cred}"},
        )
        self._token = data.get("access_token")
        if not self._token:
            raise ConfigError("no se pudo obtener el token de X (revisa las claves)")
        return self._token

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        token = self._bearer(client)
        headers = {"Authorization": f"Bearer {token}"}
        common = {
            "tweet.fields": "attachments,author_id,created_at",
            "expansions": "attachments.media_keys,author_id",
            "media.fields": "url,preview_image_url,type",
        }

        if query.usuario:
            handle = query.usuario.strip().lstrip("@")
            data = client.get_json(
                f"{API_BASE}/users/by/username/{handle}", headers=headers
            )
            uid = (data.get("data") or {}).get("id")
            if not uid:
                return []
            data = client.get_json(
                f"{API_BASE}/users/{uid}/tweets",
                params={
                    "exclude": "retweets,replies",
                    "max_results": str(min(query.limit, 10)),
                    **common,
                },
                headers=headers,
            )
        else:
            q = (query.hashtag or query.keyword or "").strip()
            if query.hashtag and not q.startswith("#"):
                q = f"#{q.lstrip('#')}"
            if not q:
                return []
            data = client.get_json(
                f"{API_BASE}/tweets/search/recent",
                params={"query": q, "max_results": str(min(query.limit, 10)), **common},
                headers=headers,
            )

        media = {
            m["media_key"]: m
            for m in data.get("includes", {}).get("media", [])
            if m.get("type") == "photo"
        }
        users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

        out: list[Artwork] = []
        for tw in data.get("data", []):
            for key in (tw.get("attachments") or {}).get("media_keys", []):
                m = media.get(key)
                if not m:
                    continue
                url = m.get("url") or m.get("preview_image_url")
                if not url:
                    continue
                user = users.get(tw.get("author_id"), {})
                username = user.get("username", "")
                text = tw.get("text") or ""
                out.append(Artwork(
                    site=self.name,
                    site_id=str(tw.get("id", "")),
                    url=url,
                    preview_url=m.get("preview_image_url") or url,
                    page_url=f"https://x.com/{username}/status/{tw.get('id')}",
                    tags=list(dict.fromkeys(_HASHTAG_RE.findall(text))),
                    rating="general",
                    md5=None,
                    author=username or None,
                    license=None,
                    created_at=tw.get("created_at"),
                    content_text=text[:2000],
                    source_field=None,
                    raw=tw,
                ))
                if len(out) >= query.limit:
                    return out
        return out
