"""Adaptador de DeviantArt (OAuth2 client credentials; sin login de usuario).

Requiere DEVIANTART_CLIENT_ID/CLIENT_SECRET en app/config.py.
"""
from __future__ import annotations

import logging
import time

from ... import config
from ...models.artwork import Artwork, SearchQuery
from ..http_client import BlockedError, ConfigError, PoliteClient
from .base import SearchAdapter
from .social_filtros import Criterios

logger = logging.getLogger("imaginteca")

TOKEN_URL = "https://www.deviantart.com/oauth2/token"
API_BASE = "https://www.deviantart.com/api/v1/oauth2"


def _variantes_de_tag(texto: str) -> list[str]:
    """Formas válidas de un tag de DeviantArt a partir de lo que escribe el usuario.

    Su API rechaza los tags con espacios o con guiones que no existan («Tag not found»,
    HTTP 400) mientras que los tags reales van sin separadores o con guion bajo. Por eso se
    prueban todas las formas razonables: «Rita Loud» → ritaloud / rita_loud / RitaLoud, y
    «my_melody» → my_melody / mymelody / MyMelody / my-melody. Si la frase tiene varias
    palabras se prueban también por separado, como último recurso.
    """
    limpio = " ".join(str(texto or "").replace("#", " ").split())
    if not limpio:
        return []
    partes = [parte for parte in limpio.replace("_", " ").replace("-", " ").split() if parte]
    if not partes:
        return []
    candidatos = [
        "".join(partes),                              # mymelody / ritaloud
        "_".join(partes),                             # my_melody / rita_loud
        "".join(p.capitalize() for p in partes),      # MyMelody / RitaLoud
        "-".join(partes),                             # my-melody / rita-loud
        "_".join(p.capitalize() for p in partes),     # My_Melody
        " ".join(partes),                             # «my melody» (por si acaso)
    ]
    variantes: list[str] = []
    for candidato in candidatos:
        if candidato and candidato not in variantes:
            variantes.append(candidato)
    if len(partes) > 1:
        for parte in partes:
            if len(parte) > 2 and parte not in variantes:
                variantes.append(parte)
    return variantes


class DeviantArtAdapter(SearchAdapter):
    name = "DeviantArt"

    def __init__(self):
        self._token: str | None = None
        self._token_expira: float = 0.0

    # ------------------------------------------------------------------ token
    def _ensure_token(self, client: PoliteClient) -> str:
        if self._token:
            return self._token
        if not config.DEVIANTART_CLIENT_ID or not config.DEVIANTART_CLIENT_SECRET:
            raise ConfigError(
                "DeviantArt necesita client credentials: pon DEVIANTART_CLIENT_ID y "
                "DEVIANTART_CLIENT_SECRET en TU config_local.py (el de junto al "
                "ejecutable, o app/config_local.py si ejecutas el código).\n"
                "Aviso: si la línea empieza por # no cuenta. Las claves se sacan en "
                "https://www.deviantart.com/developers/apps"
            )
        data = client.post_form(TOKEN_URL, {
            "grant_type": "client_credentials",
            "client_id": config.DEVIANTART_CLIENT_ID,
            "client_secret": config.DEVIANTART_CLIENT_SECRET,
        })
        self._token = data.get("access_token")
        if not self._token:
            raise ConfigError("no se pudo obtener el token de DeviantArt")
        # El token caduca (una hora): se apunta cuándo para renovarlo a tiempo en vez de
        # seguir usando uno viejo y recibir «401 autenticación rechazada».
        try:
            segundos = float(data.get("expires_in") or 3600)
        except (TypeError, ValueError):
            segundos = 3600.0
        self._token_expira = time.monotonic() + max(60.0, segundos - 120)
        logger.info("DeviantArt: token obtenido (válido %.0f minutos)", segundos / 60)
        return self._token

    def _olvidar_token(self) -> None:
        self._token = None
        self._token_expira = 0.0

    def _get_api(self, client: PoliteClient, ruta: str, params: dict) -> dict:
        """Pide a la API con el token; si el sitio lo rechaza, lo renueva y reintenta."""
        if self._token and time.monotonic() >= self._token_expira:
            logger.info("DeviantArt: el token caducó, se renueva antes de pedir")
            self._olvidar_token()
        token = self._ensure_token(client)
        try:
            return client.get_json(f"{API_BASE}{ruta}", params=params,
                                   headers={"Authorization": f"Bearer {token}"})
        except BlockedError as exc:
            if "401" not in str(exc):
                raise
            logger.info("DeviantArt: token rechazado (401), se renueva y se reintenta")
            self._olvidar_token()
            token = self._ensure_token(client)
            return client.get_json(f"{API_BASE}{ruta}", params=params,
                                   headers={"Authorization": f"Bearer {token}"})

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        token = self._ensure_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        criterios = Criterios.desde_query(query)
        if criterios.vacio:
            return []

        results: list[dict] = []
        vistos: set[str] = set()
        if criterios.usuario:
            username = criterios.usuario.strip().lstrip("@")
            data = self._get_api(client, f"/browse/user/{username}",
                                 {"limit": "24", "mature_content": "true"})
            results = data.get("results", [])
        else:
            # N valores sin límite: se consulta cada etiqueta o palabra clave y se unen
            terminos = list(criterios.hashtags) + list(criterios.palabras)
            if not terminos:
                return []
            for tag in terminos:
                # La API SOLO acepta tags reales: si se envía «Rita Loud» responde
                # HTTP 400 «Tag not found». Se prueban las formas que sí existen
                # (ritaloud, rita_loud, RitaLoud…) y, si ninguna vale, las palabras
                # sueltas. Así una frase del usuario ya no devuelve cero resultados.
                for variante in _variantes_de_tag(tag):
                    try:
                        data = self._get_api(client, "/browse/tags",
                                             {"tag": variante, "limit": "24",
                                              "mature_content": "true"})
                    except Exception as exc:  # noqa: BLE001
                        logger.info("DeviantArt: «%s» no se pudo consultar (%s)",
                                    variante, exc)
                        continue
                    for item in data.get("results", []) or []:
                        clave = str(item.get("deviationid"))
                        if clave not in vistos:
                            vistos.add(clave)
                            results.append(item)

        out: list[Artwork] = []
        for item in results:
            texto = f"{item.get('title') or ''} {item.get('description') or ''}"
            etiquetas = list(item.get("tags") or []) + list(item.get("tag_list") or [])
            if not criterios.cumple(texto=texto, etiquetas=etiquetas,
                                    autor=(item.get("author") or {}).get("username") or ""):
                continue
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
