"""Adaptador de wikis de fandom (MediaWiki: Fandom.com y otras wikis).

Busca el fandom (franquicia) y/o personaje/concepto en el repositorio de la
wiki usando la API pública api.php, sin login.

Detalles:
  - Usa `prop=imageinfo` para obtener la **URL directa** del archivo, el
    **autor** (uploader) y la **licencia** (extmetadata), además de descartar
    videos/audio (solo imágenes).
  - La descarga usa esa URL directa; la miniatura de ejemplo usa
    Special:FilePath con ?width=640.
"""
from __future__ import annotations

import re
from urllib.parse import quote, urlparse

from ...models.artwork import Artwork, SearchQuery
from ..http_client import ConfigError, PoliteClient
from .base import SearchAdapter

_HTML_RE = re.compile(r"<[^>]+>")


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _norm_titulo(nombre: str) -> str:
    return nombre.replace("_", " ").strip()


def _texto_plano(valor: str | None) -> str | None:
    if not valor:
        return None
    limpio = _HTML_RE.sub("", str(valor)).strip()
    return limpio or None


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
        except Exception as exc:  # noqa: BLE001
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
        files = self._collect_files(client, base, needle)
        if not files:
            return []

        seleccion = files[: query.limit]
        infos = self._imageinfo(client, base, seleccion)

        out: list[Artwork] = []
        for nombre in seleccion:
            art = self._normalize(base, nombre, needle, infos.get(_norm_titulo(nombre)))
            if art is not None:
                out.append(art)
        return out

    def _collect_files(self, client: PoliteClient, base: str, needle: str) -> list[str]:
        files: list[str] = []

        # 1) búsqueda de páginas (franquicia/personaje/concepto)
        titles: list[str] = []
        if needle:
            try:
                data = client.get_json(f"{base}/api.php", params={
                    "action": "query", "list": "search", "srsearch": needle,
                    "srlimit": "10", "format": "json",
                })
                titles = [hit.get("title", "") for hit in data.get("query", {}).get("search", [])]
                titles = [t for t in titles if t]
            except Exception:  # noqa: BLE001
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
                        nombre = img.get("title", "")
                        if nombre.startswith("File:"):
                            files.append(nombre[5:])
            except Exception:  # noqa: BLE001
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
            except Exception:  # noqa: BLE001
                pass

        # dedupe conservando orden
        seen: set[str] = set()
        return [f for f in files if f and not (f in seen or seen.add(f))]

    # ------------------------------------------------------------------ imageinfo (por lotes)
    def _imageinfo(self, client: PoliteClient, base: str, nombres: list[str]) -> dict[str, dict]:
        """Devuelve {titulo_normalizado: imageinfo} en lotes de 50 títulos."""
        infos: dict[str, dict] = {}
        for i in range(0, len(nombres), 50):
            lote = nombres[i:i + 50]
            try:
                data = client.get_json(f"{base}/api.php", params={
                    "action": "query", "prop": "imageinfo",
                    "iiprop": "url|user|size|mime|extmetadata",
                    "titles": "|".join(f"File:{n}" for n in lote),
                    "format": "json",
                })
            except Exception:  # noqa: BLE001
                continue
            for page in data.get("query", {}).get("pages", {}).values():
                info = (page.get("imageinfo") or [{}])[0]
                titulo = str(page.get("title", "")).replace("File:", "", 1)
                if titulo:
                    infos[_norm_titulo(titulo)] = info
        return infos

    # ------------------------------------------------------------------ normalización
    def _normalize(self, base: str, nombre: str, needle: str,
                   info: dict | None) -> Artwork | None:
        info = info or {}
        mime = str(info.get("mime") or "")
        if mime and not mime.startswith("image/"):
            return None  # la app es un extractor de imágenes: se ignora video/audio/pdf

        host = urlparse(base).netloc
        url = info.get("url") or f"{base}/wiki/Special:FilePath/{quote(nombre)}"
        preview = f"{base}/wiki/Special:FilePath/{quote(nombre)}?width=640"
        meta = info.get("extmetadata") or {}
        licencia = _texto_plano((meta.get("LicenseShortName") or {}).get("value"))
        autor = info.get("user") or None
        tags = [t for t in ([needle] if needle else []) if t]

        return Artwork(
            site=f"Wiki: {host}",
            site_id=nombre,
            url=url,
            preview_url=preview,
            page_url=info.get("descriptionurl") or f"{base}/wiki/File:{quote(nombre)}",
            tags=tags,
            rating="general",
            md5=None,
            author=autor,
            license=licencia,  # las wikis mezclan libre con fair use → confirmación manual
            created_at=None,
            content_text=None,
            source_field=None,
            raw={"wiki": base, "file": nombre, "info": info},
        )
