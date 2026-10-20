"""Adaptador de Inkbunny (https://inkbunny.net) — API oficial con tu cuenta.

Inkbunny no tiene búsqueda anónima: su API pide **usuario y contraseña** para abrir una
sesión (`sid`) y, además, la cuenta debe tener **«API Access» activado** en los ajustes
(Account Settings → API). Con esa sesión se busca por texto y se devuelven las imágenes.

Credenciales en TU `config_local.py` (no en el código):

    INKBUNNY_USERNAME = "tu_usuario"
    INKBUNNY_PASSWORD = "tu_contraseña"

La sesión se reutiliza entre búsquedas; si el sitio la caduca, se vuelve a abrir sola.
"""
from __future__ import annotations

import logging
import time

from ... import config
from ...models.artwork import Artwork, SearchQuery
from ..http_client import ConfigError, PoliteClient
from .base import SearchAdapter
from .social_filtros import Criterios

logger = logging.getLogger("imaginteca")

BASE = "https://inkbunny.net"
LOGIN_URL = f"{BASE}/api_login.php"
SEARCH_URL = f"{BASE}/api_search.php"
# Cortesía entre peticiones (Inkbunny limita el ritmo de su API).
PAUSA = float(getattr(config, "INKBUNNY_PAUSA", 1.0) or 1.0)
POR_PAGINA = 50
MAX_PAGINAS = int(getattr(config, "INKBUNNY_MAX_PAGINAS", 6) or 6)


class InkbunnyAdapter(SearchAdapter):
    name = "Inkbunny"

    def __init__(self):
        self._sid = ""
        self._ultima = 0.0

    # ------------------------------------------------------------------ sesión
    def _esperar(self) -> None:
        if PAUSA <= 0:
            return
        if self._ultima:
            desde = time.monotonic() - self._ultima
            if desde < PAUSA:
                time.sleep(PAUSA - desde)
        self._ultima = time.monotonic()

    def _pedir(self, client: PoliteClient, url: str, datos: dict) -> dict:
        self._esperar()
        datos = {**datos, "output_mode": "json"}
        return client.post_form(url, datos)

    def _entrar(self, client: PoliteClient) -> str:
        if self._sid:
            return self._sid
        usuario = str(getattr(config, "INKBUNNY_USERNAME", "") or "").strip()
        clave = str(getattr(config, "INKBUNNY_PASSWORD", "") or "")
        if not usuario or not clave:
            raise ConfigError(
                "Inkbunny necesita tu cuenta: pon INKBUNNY_USERNAME e INKBUNNY_PASSWORD en "
                "TU config_local.py (el de junto al ejecutable, o app/config_local.py si "
                "ejecutas el código).\n"
                "Aviso: si la línea empieza por # no cuenta.\n"
                "Además, en la web de Inkbunny hay que activar «API Access» en los ajustes "
                "de la cuenta (Account Settings → API)."
            )
        respuesta = self._pedir(client, LOGIN_URL, {"username": usuario, "password": clave})
        if respuesta.get("error_code") not in (0, None) or not respuesta.get("sid"):
            raise ConfigError(
                "Inkbunny rechazó el acceso: "
                + str(respuesta.get("error_message") or "sin detalle")
                + "\nRevisa usuario/contraseña y que la cuenta tenga «API Access» activado."
            )
        self._sid = str(respuesta.get("sid") or "")
        logger.info("Inkbunny: sesión abierta para %s", usuario)
        return self._sid

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        criterios = Criterios.desde_query(query)
        if criterios.vacio:
            return []
        # Con un texto (palabra clave) se busca por contenido; con @usuario, por autor.
        texto = " ".join([p for p in criterios.palabras] + [f"#{t}" for t in criterios.hashtags]).strip()
        autor = (criterios.usuario or "").strip().lstrip("@")
        if not texto and not autor:
            return []
        sid = self._entrar(client)

        salida: list[Artwork] = []
        pagina = 1
        while len(salida) < query.limit and pagina <= MAX_PAGINAS:
            datos: dict = {"sid": sid, "page": str(pagina),
                           "submissions_per_page": str(POR_PAGINA)}
            if texto:
                datos["text"] = texto
            if autor:
                datos["username"] = autor
            respuesta = self._pedir(client, SEARCH_URL, datos)
            codigo = respuesta.get("error_code")
            if codigo == 2:            # sesión caducada: se renueva y se reintenta una vez
                logger.info("Inkbunny: la sesión caducó, se renueva")
                self._sid = ""
                datos["sid"] = self._entrar(client)
                respuesta = self._pedir(client, SEARCH_URL, datos)
                codigo = respuesta.get("error_code")
            if codigo not in (0, None):
                raise ConfigError(
                    "Inkbunny respondió: "
                    + str(respuesta.get("error_message") or f"error {codigo}")
                )
            envios = respuesta.get("submissions") or []
            if not envios:
                break
            for envio in envios:
                salida.extend(self._arte(envio, criterios))
                if len(salida) >= query.limit:
                    break
            if len(envios) < POR_PAGINA:
                break
            pagina += 1
        logger.info("Inkbunny: %d imágenes para «%s»", len(salida),
                    texto or f"@{autor}")
        return salida[: query.limit]

    # ------------------------------------------------------------------ normalizar
    def _arte(self, envio: dict, criterios) -> list[Artwork]:
        if not isinstance(envio, dict):
            return []
        texto = f"{envio.get('title') or ''} {envio.get('description') or ''}"
        etiquetas = [str(t.get("tag_name") if isinstance(t, dict) else t)
                     for t in (envio.get("tags") or [])]
        autor = str(envio.get("username") or "")
        if not criterios.cumple(texto=texto, etiquetas=etiquetas, autor=autor):
            return []
        titulo = str(envio.get("title") or "").strip()
        url_pagina = str(envio.get("url") or "")
        sensible = bool(envio.get("rating_id") and int(envio.get("rating_id") or 0) > 2)
        salida: list[Artwork] = []
        for archivo in envio.get("files") or []:
            if not isinstance(archivo, dict):
                continue
            url = str(archivo.get("file_url_full") or archivo.get("file_url_screen") or "")
            if not url:
                continue
            # Solo imágenes: la app es un extractor de imágenes.
            tipo = str(archivo.get("mime_type") or "")
            if tipo and not tipo.startswith("image/"):
                continue
            salida.append(Artwork(
                site=self.name,
                site_id=str(archivo.get("file_id") or archivo.get("submission_id") or ""),
                url=url,
                preview_url=str(archivo.get("file_url_screen") or url),
                page_url=url_pagina,
                tags=[t for t in etiquetas if t],
                rating="sensitive" if sensible else "general",
                md5=None,
                author=(f"@{autor}" if autor else None),
                license=None,
                created_at=str(envio.get("create_datetime") or "") or None,
                content_text=titulo or None,
                source_field="inkbunny",
                raw=envio,
            ))
        return salida
