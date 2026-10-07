"""Adaptador de boorus: familias Gelbooru (dapi), Danbooru y Moebooru.

Plantilla replicable: cada sitio es una entrada de configuración (BOORU_SITES
en app/config.py); el mismo código sirve para Gelbooru, Rule34.xxx, Safebooru,
Danbooru, Yande.re, Konachan y cualquier booru de esas familias.
"""
from __future__ import annotations

import re

from ... import config
from ...models.artwork import Artwork, SearchQuery
from ..http_client import ConfigError, PoliteClient
from .base import SearchAdapter, split_tags

_RATING_MAP = {
    "s": "general", "safe": "general", "g": "general",
    "sensitive": "sensitive", "q": "questionable", "questionable": "questionable",
    "e": "explicit", "explicit": "explicit",
}

# Extractor de imágenes: los posts de video/webm/zip se descartan en el adaptador.
_NON_IMAGE_EXTS = {".webm", ".mp4", ".zip", ".swf", ".mov", ".avi", ".mkv"}


def _is_video_name(name: str | None) -> bool:
    if not name:
        return False
    lowered = name.lower()
    return any(lowered.endswith(ext) for ext in _NON_IMAGE_EXTS)


def _auth_params(site_cfg: dict) -> dict:
    """Resuelve las credenciales del sitio desde config (por ahora en código)."""
    kind = site_cfg.get("auth")
    if not kind:
        return {}
    kind = kind[0]
    if kind == "GELBOORU":
        if not config.GELBOORU_API_KEY or not config.GELBOORU_USER_ID:
            raise ConfigError(
                "Gelbooru requiere API key y user ID: escríbelos en app/config_local.py "
                "(https://gelbooru.com/index.php?page=account&s=options)"
            )
        return {"api_key": config.GELBOORU_API_KEY, "user_id": config.GELBOORU_USER_ID}
    if kind == "RULE34":
        if not config.RULE34_API_KEY or not config.RULE34_USER_ID:
            raise ConfigError(
                "Rule34.xxx requiere API key y user ID: escríbelos en app/config_local.py "
                "(https://rule34.xxx/index.php?page=account&s=options)"
            )
        return {"api_key": config.RULE34_API_KEY, "user_id": config.RULE34_USER_ID}
    raise ConfigError(f"tipo de autenticación desconocido: {kind}")


class BooruAdapter(SearchAdapter):
    def __init__(self, site_cfg: dict):
        self.cfg = site_cfg
        self.name = site_cfg["name"]
        self.family = site_cfg["family"]
        self.base = site_cfg["base"].rstrip("/")
        self.view_tpl = site_cfg.get("view_tpl", "")

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        tags = split_tags(query.tags)
        if self.family == "danbooru" and len(tags) > 2 and not _auth_params(self.cfg):
            # límite documentado: sin API key, Danbooru permite máximo 2 tags
            raise ConfigError(
                "Danbooru anónimo permite máximo 2 tags por búsqueda "
                "(usa una API key en config.py para ampliarlo)"
            )

        out: list[Artwork] = []
        page = 0
        while len(out) < query.limit:
            raw = self._fetch_page(client, tags, page)
            if not raw:
                break
            for item in raw:
                art = self._normalize(item)
                if art is not None:
                    out.append(art)
                    if len(out) >= query.limit:
                        return out
            if len(raw) < self._page_size():
                break
            page += 1
        return out

    def _page_size(self) -> int:
        if self.family == "danbooru":
            return 200
        if self.family == "philomena":
            return 50
        return 100

    def _fetch_page(self, client: PoliteClient, tags: list[str], page: int) -> list[dict]:
        joined = " ".join(tags)
        auth = _auth_params(self.cfg)
        if self.family == "gelbooru":
            params = {
                "page": "dapi", "s": "post", "q": "index", "json": "1",
                "tags": joined, "limit": "100", "pid": str(page),
                **auth,
            }
            data = client.get_json(f"{self.base}/index.php", params=params)
            return data if isinstance(data, list) else []
        if self.family == "danbooru":
            params = {"tags": joined, "limit": "200", "page": str(page + 1)}
            params.update(auth)
            data = client.get_json(f"{self.base}/posts.json", params=params)
            return data if isinstance(data, list) else []
        if self.family == "moebooru":
            params = {"tags": joined, "limit": "100", "page": str(page + 1)}
            data = client.get_json(f"{self.base}/post.json", params=params)
            return data if isinstance(data, list) else []
        if self.family == "philomena":
            params = {"q": joined, "per_page": "50", "page": str(page + 1)}
            data = client.get_json(f"{self.base}/api/v1/json/search/images", params=params)
            return data.get("images", []) if isinstance(data, dict) else []
        raise ConfigError(f"familia de booru desconocida: {self.family}")

    # ------------------------------------------------------------------ normalización
    def _normalize(self, raw: dict) -> Artwork | None:
        try:
            if self.family == "gelbooru":
                return self._normalize_gelbooru(raw)
            if self.family == "danbooru":
                return self._normalize_danbooru(raw)
            if self.family == "moebooru":
                return self._normalize_moebooru(raw)
            if self.family == "philomena":
                return self._normalize_philomena(raw)
        except (KeyError, TypeError):
            return None
        return None

    def _normalize_gelbooru(self, raw: dict) -> Artwork | None:
        sid = str(raw.get("id", ""))
        tags = re.split(r"\s+", (raw.get("tags") or "").strip())
        directory = raw.get("directory") or ""
        image = raw.get("image") or ""
        if _is_video_name(image):
            return None
        # Algunos sitios de esta familia no incluyen file_url: se construye
        # desde directory+image (p. ej. The Big ImageBoard).
        url = raw.get("file_url")
        if not url and directory and image:
            url = f"{self.base}/images/{directory}/{image}"
        if not url:
            return None
        preview = raw.get("sample_url") or raw.get("preview_url")
        if not preview and directory and image:
            preview = f"{self.base}/thumbnails/{directory}/thumbnail_{image}"
        return Artwork(
            site=self.name,
            site_id=sid,
            url=url,
            preview_url=preview,
            page_url=self.view_tpl.format(id=sid),
            tags=[t for t in tags if t],
            rating=_RATING_MAP.get(str(raw.get("rating", "")).lower(), "general"),
            md5=raw.get("md5"),
            author=raw.get("owner"),
            license=None,
            created_at=raw.get("created_at"),
            content_text=None,
            source_field=raw.get("source") or "",
            raw=raw,
        )

    def _normalize_danbooru(self, raw: dict) -> Artwork:
        sid = str(raw.get("id", ""))
        if _is_video_name(raw.get("file_ext")):
            return None
        tags = re.split(r"\s+", (raw.get("tag_string") or "").strip())
        artist = (raw.get("tag_string_artist") or "").strip().split(" ")[0] or None
        return Artwork(
            site=self.name,
            site_id=sid,
            url=raw.get("file_url") or raw.get("large_file_url", ""),
            preview_url=raw.get("preview_file_url"),
            page_url=self.view_tpl.format(id=sid),
            tags=[t for t in tags if t],
            rating=_RATING_MAP.get(str(raw.get("rating", "")).lower(), "general"),
            md5=raw.get("md5"),
            author=artist,
            license=None,
            created_at=raw.get("created_at"),
            content_text=None,
            source_field=raw.get("source") or "",
            raw=raw,
        )

    def _normalize_moebooru(self, raw: dict) -> Artwork:
        sid = str(raw.get("id", ""))
        if _is_video_name(raw.get("file_url")):
            return None
        tags = re.split(r"\s+", (raw.get("tags") or "").strip())
        return Artwork(
            site=self.name,
            site_id=sid,
            url=raw["file_url"],
            preview_url=raw.get("sample_url") or raw.get("preview_url"),
            page_url=self.view_tpl.format(id=sid),
            tags=[t for t in tags if t],
            rating=_RATING_MAP.get(str(raw.get("rating", "")).lower(), "general"),
            md5=raw.get("md5"),
            author=raw.get("author") or None,
            license=None,
            created_at=str(raw.get("created_at", "")) or None,
            content_text=None,
            source_field=raw.get("source") or "",
            raw=raw,
        )

    def _normalize_philomena(self, raw: dict) -> Artwork | None:
        """Familia Philomena (p. ej. Derpibooru)."""
        sid = str(raw.get("id", ""))
        if _is_video_name(raw.get("format")):
            return None
        rep = raw.get("representations") or {}
        url = rep.get("full")
        if not url:
            return None
        preview = rep.get("medium") or rep.get("large") or rep.get("small") or url
        tags = raw.get("tags") or []
        low = [t.lower() for t in tags]
        if any("explicit" in t or "grimdark" in t for t in low):
            rating = "explicit"
        elif any("questionable" in t for t in low):
            rating = "questionable"
        elif any("suggestive" in t for t in low):
            rating = "sensitive"
        else:
            rating = "general"
        return Artwork(
            site=self.name,
            site_id=sid,
            url=url,
            preview_url=preview,
            page_url=self.view_tpl.format(id=sid),
            tags=tags,
            rating=rating,
            md5=None,
            author=raw.get("uploader") or None,
            license=None,
            created_at=raw.get("created_at"),
            content_text=(raw.get("description") or "")[:2000],
            source_field=raw.get("source_url") or "",
            raw=raw,
        )
