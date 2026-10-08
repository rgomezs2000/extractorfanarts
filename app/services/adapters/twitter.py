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
from .social_filtros import Criterios, repartir_en_lotes

_HASHTAG_RE = re.compile(r"#([\w]+)")
API_BASE = "https://api.twitter.com/2"
# Longitud máxima que acepta la consulta de la búsqueda reciente de X (caracteres).
# No limita cuántos valores puedes escribir: si no caben, se hacen varias consultas.
MAX_CONSULTA = 500


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

        criterios = Criterios.desde_query(query)
        if criterios.vacio:
            return []

        if criterios.usuario and not (criterios.palabras or criterios.hashtags):
            # Solo el usuario: su timeline reciente (más resultados que la búsqueda)
            handle = criterios.usuario.strip().lstrip("@")
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
            # Búsqueda con TODOS los criterios (X los combina con AND):
            #   from:usuario #hashtag1 #hashtag2 "palabra clave" …
            # Admite N valores sin límite: si no caben en una consulta, se hacen varias
            # (una por lote) y sus resultados se unen; después el filtro local exige
            # todos los criterios igualmente.
            terminos: list[str] = []
            if criterios.usuario:
                terminos.append(f"from:{criterios.usuario.strip().lstrip('@')}")
            terminos += [f"#{tag}" for tag in criterios.hashtags]
            terminos += [f'"{p}"' if " " in p else p for p in criterios.palabras]
            if not terminos:
                return []
            data = {"data": [], "includes": {"media": [], "users": []}}
            vistos_tw: set[str] = set()
            for lote in repartir_en_lotes(terminos, MAX_CONSULTA):
                parcial = client.get_json(
                    f"{API_BASE}/tweets/search/recent",
                    params={"query": " ".join(lote),
                            "max_results": str(min(query.limit, 10)), **common},
                    headers=headers,
                )
                for tw in parcial.get("data", []) or []:
                    clave = str(tw.get("id"))
                    if clave not in vistos_tw:
                        vistos_tw.add(clave)
                        data["data"].append(tw)
                incluye = parcial.get("includes", {}) or {}
                data["includes"]["media"] += incluye.get("media", []) or []
                data["includes"]["users"] += incluye.get("users", []) or []

        media = {
            m["media_key"]: m
            for m in data.get("includes", {}).get("media", [])
            if m.get("type") == "photo"
        }
        users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

        out: list[Artwork] = []
        for tw in data.get("data", []):
            user = users.get(tw.get("author_id"), {})
            username = user.get("username", "")
            text = tw.get("text") or ""
            etiquetas = _HASHTAG_RE.findall(text)
            if not criterios.cumple(texto=text, etiquetas=etiquetas, autor=username):
                continue
            for key in (tw.get("attachments") or {}).get("media_keys", []):
                m = media.get(key)
                if not m:
                    continue
                url = m.get("url") or m.get("preview_image_url")
                if not url:
                    continue
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
