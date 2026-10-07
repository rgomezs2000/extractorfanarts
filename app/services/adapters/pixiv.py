"""Adaptador de Pixiv (API oficial de la app, con TU cuenta).

Pixiv no tiene API pública anónima: todo requiere autenticación. Este adaptador
usa la **App-API oficial** (`app-api.pixiv.net`) con un **refresh token** propio
(en `PIXIV_REFRESH_TOKEN`), igual que los clientes de Pixiv conocidos. No se
guarda tu contraseña ni se hace scraping de la web.

Cómo obtener el refresh token:  python scripts\\pixiv_token.py

Capacidades:
  - palabra clave / #hashtag → /v1/search/illust (búsqueda por etiquetas)
  - @usuario o id numérico   → /v1/user/illusts (obras del usuario)
  - Varias páginas por obra (meta_pages) se guardan como archivos separados.
  - Animaciones **ugoira**: se descarga el ZIP de fotogramas (/v1/ugoira_metadata)
    y se componen en un **WebP animado** (servicio app/services/ugoira.py).
"""
from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

from ... import config
from ...models.artwork import Artwork, SearchQuery
from ..http_client import BlockedError, ConfigError, PoliteClient
from .base import SearchAdapter

logger = logging.getLogger("extractorfanarts")

API = "https://app-api.pixiv.net"
TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"
HASH_SECRET = "28c1fdd170a5204386cb1313c7077b34f83e4aaf4aa829ce78c231e05b0bae2c"
APP_UA = "PixivAndroidApp/5.0.234 (Android 10; Pixel 3)"


class PixivAdapter(SearchAdapter):
    name = "Pixiv"

    _tokens: dict[str, str] = {}  # refresh_token -> (access_token) cache en memoria

    # ------------------------------------------------------------------ auth
    @staticmethod
    def _cabeceras_cliente() -> dict:
        ahora = datetime.now(timezone.utc).isoformat().replace("+00:00", "+00:00")
        huella = hashlib.md5((ahora + HASH_SECRET).encode("utf-8")).hexdigest()
        return {
            "User-Agent": APP_UA,
            "App-OS": "android",
            "App-OS-Version": "10",
            "App-Version": "5.0.234",
            "X-Client-Time": ahora,
            "X-Client-Hash": huella,
        }

    def _access_token(self, client: PoliteClient) -> str:
        refresco = getattr(config, "PIXIV_REFRESH_TOKEN", "")
        if not refresco:
            raise ConfigError(
                "Pixiv requiere un refresh token: ejecuta python scripts\\pixiv_token.py "
                "y pon el resultado en PIXIV_REFRESH_TOKEN de app/config_local.py"
            )
        cacheado = self._tokens.get(refresco)
        if cacheado:
            return cacheado

        datos = client.post_form(
            TOKEN_URL,
            {
                "grant_type": "refresh_token",
                "refresh_token": refresco,
                "client_id": config.PIXIV_CLIENT_ID,
                "client_secret": config.PIXIV_CLIENT_SECRET,
                "include_policy": "true",
            },
            headers=self._cabeceras_cliente(),
        )
        token = (datos or {}).get("access_token")
        if not token:
            raise ConfigError(
                "Pixiv rechazó el refresh token (puede haber caducado o ser inválido): "
                "vuelve a generarlo con python scripts\\pixiv_token.py"
            )
        self._tokens[refresco] = token
        return token

    def _get(self, client: PoliteClient, ruta: str, token: str,
             params: dict | None = None) -> dict:
        cabeceras = {"Authorization": f"Bearer {token}"}
        cabeceras.update({k: v for k, v in self._cabeceras_cliente().items()
                          if k != "X-Client-Hash"})
        return client.get_json(f"{API}{ruta}", params=params, headers=cabeceras)

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        token = self._access_token(client)
        illusts: list[dict] = []

        if query.usuario:
            usuario = query.usuario.strip().lstrip("@")
            user_id = usuario if usuario.isdigit() else self._buscar_usuario_id(
                client, token, usuario
            )
            datos = self._get(client, "/v1/user/illusts", token, {
                "user_id": user_id, "type": "illust", "filter": "for_ios",
            })
            illusts = datos.get("illusts", []) or []
        else:
            palabra = (query.hashtag or query.keyword or "").strip().lstrip("#")
            if not palabra:
                return []
            datos = self._get(client, "/v1/search/illust", token, {
                "word": palabra,
                "search_target": "partial_match_for_tags",
                "sort": "date_desc",
                "filter": "for_ios",
            })
            illusts = datos.get("illusts", []) or []

        out: list[Artwork] = []
        for ilust in illusts:
            if ilust.get("type") == "ugoira":
                generados = self._artwork_ugoira(client, token, ilust)
            else:
                generados = self._normalize(ilust)
            for art in generados:
                out.append(art)
                if len(out) >= query.limit:
                    return out
        return out

    def _artwork_ugoira(self, client: PoliteClient, token: str,
                        ilust: dict) -> list[Artwork]:
        """Animación ugoira: se obtiene el ZIP de fotogramas y sus retrasos."""
        sid = str(ilust.get("id", ""))
        try:
            datos = self._get(client, "/v1/ugoira_metadata", token, {"illust_id": sid})
        except Exception as exc:  # noqa: BLE001
            logger.warning("ugoira %s: no se pudo leer la metadata (%s); se omite", sid, exc)
            return []
        meta = (datos or {}).get("ugoira_metadata") or {}
        urls = meta.get("zip_urls") or {}
        url_zip = urls.get("medium") or urls.get("original") or urls.get("small")
        fotogramas = meta.get("frames") or []
        if not url_zip or not fotogramas:
            logger.warning("ugoira %s: metadata incompleta; se omite", sid)
            return []

        autor = (ilust.get("user") or {}).get("account") \
            or (ilust.get("user") or {}).get("name")
        etiquetas = [t.get("name", "") for t in ilust.get("tags", []) or []]
        return [Artwork(
            site=self.name,
            site_id=sid,
            url=url_zip,
            preview_url=(ilust.get("image_urls") or {}).get("medium") or url_zip,
            page_url=f"https://www.pixiv.net/artworks/{sid}",
            tags=list(dict.fromkeys(t for t in etiquetas if t)),
            rating=self._rating(ilust),
            md5=None,
            author=autor,
            license=None,
            created_at=ilust.get("create_date"),
            content_text=(ilust.get("title") or "")[:2000],
            source_field=None,
            animacion={"tipo": "ugoira", "zip_url": url_zip, "frames": fotogramas},
            raw=ilust,
        )]

    def _buscar_usuario_id(self, client: PoliteClient, token: str, nombre: str) -> str:
        datos = self._get(client, "/v1/search/user", token, {"word": nombre})
        previsualizaciones = datos.get("user_previews", []) or []
        if not previsualizaciones:
            raise BlockedError(
                f"no se encontró el usuario '{nombre}' en Pixiv "
                "(también puedes escribir su id numérico)"
            )
        return str(previsualizaciones[0]["user"]["id"])

    # ------------------------------------------------------------------ normalización
    @staticmethod
    def _rating(ilust: dict) -> str:
        # x_restrict: 0 = todo público, 1 = R-18, 2 = R-18G
        valor = ilust.get("x_restrict", 0)
        if valor == 1:
            return "questionable"
        if valor == 2:
            return "explicit"
        return "general"

    def _normalize(self, ilust: dict) -> list[Artwork]:
        if not ilust:
            return []
        if ilust.get("type") == "ugoira":
            # Las animaciones se gestionan en _artwork_ugoira (rama aparte)
            return []

        sid = str(ilust.get("id", ""))
        autor = (ilust.get("user") or {}).get("account") \
            or (ilust.get("user") or {}).get("name")
        etiquetas = [t.get("name", "") for t in ilust.get("tags", []) or []]
        fecha = ilust.get("create_date")
        rating = self._rating(ilust)
        pagina = f"https://www.pixiv.net/artworks/{sid}"

        urls: list[tuple[str, str]] = []  # (url, sufijo)
        meta_paginas = ilust.get("meta_pages") or []
        if meta_paginas:
            for indice, pagina_meta in enumerate(meta_paginas):
                imagenes = pagina_meta.get("image_urls") or {}
                url = imagenes.get("original") or imagenes.get("large")
                if url:
                    urls.append((url, f"_p{indice}"))
        else:
            imagenes = ilust.get("image_urls") or {}
            url = (ilust.get("meta_single_page") or {}).get("original_image_url") \
                or imagenes.get("large") or imagenes.get("medium")
            if url:
                urls.append((url, ""))

        salida: list[Artwork] = []
        for url, sufijo in urls:
            miniatura = (ilust.get("image_urls") or {}).get("medium") or url
            salida.append(Artwork(
                site=self.name,
                site_id=f"{sid}{sufijo}",
                url=url,
                preview_url=miniatura,
                page_url=pagina,
                tags=list(dict.fromkeys(t for t in etiquetas if t)),
                rating=rating,
                md5=None,
                author=autor,
                license=None,
                created_at=fecha,
                content_text=(ilust.get("title") or "")[:2000],
                source_field=None,
                raw=ilust,
            ))
        return salida
