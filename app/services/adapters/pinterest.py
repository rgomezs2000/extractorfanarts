"""Adaptador de Pinterest (API v5 oficial, OAuth de usuario).

Requisitos en app/config.py:
  - PINTEREST_ACCESS_TOKEN: token OAuth 2.0 (app de Pinterest aprobada).
  - PINTEREST_COUNTRY_CODE (opcional): necesario para la búsqueda global
    (/v5/search/partner/pins, en beta para apps asociadas). Sin este código,
    se usa /v5/search/pins, que busca sobre los pins de la cuenta conectada.
"""
from __future__ import annotations

import re

from ... import config
from ...models.artwork import Artwork, SearchQuery
from ..http_client import ConfigError, PoliteClient
from .base import SearchAdapter
from .social_filtros import Criterios

_HASHTAG_RE = re.compile(r"#([\w]+)")
API_BASE = "https://api.pinterest.com/v5"


class PinterestAdapter(SearchAdapter):
    name = "Pinterest"

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        token = config.PINTEREST_ACCESS_TOKEN
        if not token:
            raise ConfigError(
                "Pinterest requiere PINTEREST_ACCESS_TOKEN en app/config.py "
                "(API v5: app aprobada + token OAuth del usuario). La búsqueda "
                "global usa /v5/search/partner/pins (beta) y además requiere "
                "PINTEREST_COUNTRY_CODE."
            )
        headers = {"Authorization": f"Bearer {token}"}
        criterios = Criterios.desde_query(query)
        if criterios.vacio:
            return []
        # N valores sin límite: se busca cada palabra clave o hashtag (y, si no hay
        # ninguno, el usuario) y se unen los resultados; después se filtran en local
        # con TODOS los valores indicados.
        terminos = list(criterios.hashtags) + list(criterios.palabras)
        if not terminos and criterios.usuario:
            terminos = [criterios.usuario.strip().lstrip("#@")]
        terminos = [t for t in terminos if t]
        if not terminos:
            return []
        solo_texto = Criterios(usuario="", palabras=criterios.palabras,
                               hashtags=criterios.hashtags)

        pines: list[dict] = []
        vistos: set[str] = set()
        for term in terminos:
            try:
                if config.PINTEREST_COUNTRY_CODE:
                    data = client.get_json(
                        f"{API_BASE}/search/partner/pins",
                        params={"term": term,
                                "country_code": config.PINTEREST_COUNTRY_CODE,
                                "limit": str(min(query.limit, 25))},
                        headers=headers,
                    )
                else:
                    data = client.get_json(
                        f"{API_BASE}/search/pins",
                        params={"query": term, "page_size": str(min(query.limit, 25))},
                        headers=headers,
                    )
            except Exception as exc:  # noqa: BLE001
                logger.info("Pinterest: «%s» no se pudo buscar (%s)", term, exc)
                continue
            for pin in data.get("items", []) or []:
                clave = str(pin.get("id"))
                if clave not in vistos:
                    vistos.add(clave)
                    pines.append(pin)

        out: list[Artwork] = []
        for pin in pines:
            texto = f"{pin.get('title') or ''} {pin.get('description') or ''}"
            if not solo_texto.cumple(texto=texto, etiquetas=[]):
                continue
            art = self._normalize(pin)
            if art is not None:
                out.append(art)
                if len(out) >= query.limit:
                    return out
        return out

    # ------------------------------------------------------------------ normalización
    @staticmethod
    def _pick_image(pin: dict) -> tuple[str | None, str | None]:
        media = pin.get("media") or {}
        images = media.get("images") or media.get("originals") or {}
        if not images:
            return None, None
        full = (
            images.get("original")
            or images.get("originals")
            or images.get("1200x")
            or images.get("600x")
        )
        preview = images.get("400x300") or images.get("150x150") or full
        return (full or {}).get("url"), (preview or {}).get("url")

    def _normalize(self, pin: dict) -> Artwork | None:
        url, preview = self._pick_image(pin)
        if not url:
            return None
        sid = str(pin.get("id", ""))
        title = pin.get("title") or ""
        desc = pin.get("description") or ""
        text = f"{title} {desc}".strip()
        tags = list(dict.fromkeys(_HASHTAG_RE.findall(text)))
        page = pin.get("link") or f"https://www.pinterest.com/pin/{sid}/"
        author = None
        for key in ("pinner", "owner"):
            owner = pin.get(key) or {}
            if owner.get("username"):
                author = owner["username"]
                break
        return Artwork(
            site=self.name,
            site_id=sid,
            url=url,
            preview_url=preview or url,
            page_url=page,
            tags=tags,
            rating="general",
            md5=None,
            author=author,
            license=None,
            created_at=pin.get("created_at"),
            content_text=text[:2000],
            source_field=None,
            raw=pin,
        )
