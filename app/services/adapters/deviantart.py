"""Adaptador de DeviantArt (OAuth2 client credentials; sin login de usuario).

Requiere DEVIANTART_CLIENT_ID/CLIENT_SECRET en app/config.py.
"""
from __future__ import annotations

from ... import config
from ...models.artwork import Artwork, SearchQuery
from ..http_client import ConfigError, PoliteClient
from .base import SearchAdapter

TOKEN_URL = "https://www.deviantart.com/oauth2/token"
API_BASE = "https://www.deviantart.com/api/v1/oauth2"


class DeviantArtAdapter(SearchAdapter):
    name = "DeviantArt"

    def __init__(self):
        self._token: str | None = None

    # ------------------------------------------------------------------ token
    def _ensure_token(self, client: PoliteClient) -> str:
        if self._token:
            return self._token
        if not config.DEVIANTART_CLIENT_ID or not config.DEVIANTART_CLIENT_SECRET:
            raise ConfigError(
                "DeviantArt requiere client credentials: completa "
                "DEVIANTART_CLIENT_ID y DEVIANTART_CLIENT_SECRET en app/config.py"
            )
        data = client.post_form(TOKEN_URL, {
            "grant_type": "client_credentials",
            "client_id": config.DEVIANTART_CLIENT_ID,
            "client_secret": config.DEVIANTART_CLIENT_SECRET,
        })
        self._token = data.get("access_token")
        if not self._token:
            raise ConfigError("no se pudo obtener el token de DeviantArt")
        return self._token

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        token = self._ensure_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        results: list[dict] = []
        if query.usuario:
            username = query.usuario.strip().lstrip("@")
            data = client.get_json(
                f"{API_BASE}/browse/user/{username}",
                params={"limit": "24", "mature_content": "true"},
            )
            results = data.get("results", [])
        else:
            tag = (query.hashtag or query.keyword or "").strip().lstrip("#")
            if not tag:
                return []
            data = client.get_json(
                f"{API_BASE}/browse/tags",
                params={"tag": tag, "limit": "24", "mature_content": "true"},
            )
            results = data.get("results", [])

        out: list[Artwork] = []
        for item in results:
            art = self._normalize(item)
            if art is not None:
                out.append(art)
                if len(out) >= query.limit:
                    return out
        return out

    # ------------------------------------------------------------------ normalización
    def _normalize(self, item: dict) -> Artwork | None:
        content = item.get("content") or {}
        preview = item.get("preview") or {}
        url = content.get("src")
        if not url:
            return None
        author = (item.get("author") or {}).get("username")
        return Artwork(
            site=self.name,
            site_id=str(item.get("deviationid", "")),
            url=url,
            preview_url=preview.get("src") or url,
            page_url=item.get("url"),
            tags=[t.get("tag_name", "") for t in item.get("tags", [])],
            rating="explicit" if item.get("is_mature") else "general",
            md5=None,
            author=author,
            license=None,  # la API browse no expone la licencia; queda a confirmación
            created_at=None,
            content_text=(item.get("title") or "")[:2000],
            source_field=None,
            raw=item,
        )
