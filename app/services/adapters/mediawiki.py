"""Adaptador de wikis de fandom (MediaWiki: Fandom.com y otras wikis).

Busca el fandom (franquicia) y/o personaje/concepto en el repositorio de la
wiki usando la API pública api.php, sin login.
"""
from __future__ import annotations

import re
from urllib.parse import quote

from ...models.artwork import Artwork, SearchQuery
from ..http_client import ConfigError, PoliteClient
from .base import SearchAdapter


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


class MediaWikiAdapter(SearchAdapter):
    name = "Fandom (MediaWiki)"

    # ------------------------------------------------------------------ resolución de la wiki
    def _resolve_base(self, client: PoliteClient, query: SearchQuery) -> str:
        if query.wiki_url:
            base = query.wiki_url.rstrip("/")
        elif query.fandom:
            base = f"https://{_slug(query.fandom)}.fandom.com"
        else:
            base = None
        if not base:
            raise ConfigError(
                "Indica el nombre del fandom (ej. naruto) o la URL completa de la wiki"
            )
        try:
            client.get_json(f"{base}/api.php", params={
                "action": "query", "meta": "siteinfo", "format": "json",
            })
        except Exception as exc:
            raise ConfigError(
                f"No se pudo conectar con la wiki '{base}'. "
                "Escribe la URL completa de la wiki (ej. https://naruto.fandom.com). "
                f"({exc})"
            )
        return base

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        base = self._resolve_base(client, query)
        needle = (query.character or query.fandom or "").strip()

        files: list[str] = []

        # 1) búsqueda de páginas (franquicia/personaje/concepto)
        try:
            data = client.get_json(f"{base}/api.php", params={
                "action": "query", "list": "search", "srsearch": needle,
                "srlimit": "10", "format": "json",
            })
            titles = [hit.get("title", "") for hit in data.get("query", {}).get("search", [])]
            titles = [t for t in titles if t]
        except Exception:
            titles = []

        # 2) imágenes usadas en las páginas encontradas
        if titles:
            try:
                data = client.get_json(f"{base}/api.php", params={
                    "action": "query", "prop": "images", "imlimit": "100",
                    "titles": "|".join(titles[:10]), "format": "json",
                })
                for page in data.get("query", {}).get("pages", {}).values():
                    for img in page.get("images", []) or []:
                        name = img.get("title", "")
                        if name.startswith("File:"):
                            files.append(name[5:])
            except Exception:
                pass

        # 3) archivos cuyo nombre empieza por el concepto/personaje
        if needle:
            try:
                data = client.get_json(f"{base}/api.php", params={
                    "action": "query", "list": "allimages", "aiprefix": needle,
                    "ailimit": "100", "aiprop": "url", "format": "json",
                })
                for img in data.get("query", {}).get("allimages", []) or []:
                    files.append(img.get("name", ""))
            except Exception:
                pass

        # dedupe conservando orden
        seen: set[str] = set()
        files = [f for f in files if f and not (f in seen or seen.add(f))]

        out: list[Artwork] = []
        for name in files[: query.limit]:
            art = self._normalize(base, name, needle)
            if art is not None:
                out.append(art)
        return out

    # ------------------------------------------------------------------ normalización
    def _normalize(self, base: str, name: str, needle: str) -> Artwork | None:
        try:
            url = f"{base}/wiki/Special:FilePath/{quote(name)}"
            return Artwork(
                site=f"Wiki: {base.replace('https://', '')}",
                site_id=name,
                url=url,
                preview_url=f"{url}?width=640",
                page_url=f"{base}/wiki/File:{quote(name)}",
                tags=[needle] if needle else [],
                rating="general",
                md5=None,
                author=None,
                license=None,  # las wikis mezclan libre con fair use → confirmación manual
                created_at=None,
                content_text=None,
                source_field=None,
                raw={"wiki": base, "file": name},
            )
        except Exception:
            return None
