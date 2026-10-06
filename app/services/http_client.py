"""Cliente HTTP educado: cooldown por dominio, backoff y pausa ante bloqueos.

No evita ni elude protecciones: si un sitio responde con bloqueos reiterados,
la petición termina en error y la fuente se descarta (la UI informa al usuario).
"""
from __future__ import annotations

import threading
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

from .. import config


class ConfigError(Exception):
    """Falta configurar algo (p. ej. credenciales de una plataforma)."""


class BlockedError(Exception):
    """La fuente rechaza/bloquea las peticiones después de reintentos prudentes."""


class CancelledError(Exception):
    """El usuario canceló la operación."""


class PoliteClient:
    def __init__(
        self,
        cancel_event: threading.Event | None = None,
        on_pause=None,  # callback(segundos, motivo) para informar a la UI
        min_interval: float | None = None,
        backoff_base: float | None = None,
        backoff_max: float | None = None,
        block_pause: float | None = None,
        max_retries: int | None = None,
    ):
        self.cancel_event = cancel_event
        self.on_pause = on_pause
        self.min_interval = min_interval or config.MIN_REQUEST_INTERVAL
        self.backoff_base = backoff_base or config.BACKOFF_BASE
        self.backoff_max = backoff_max or config.BACKOFF_MAX
        self.block_pause = block_pause or config.BLOCK_PAUSE
        self.max_retries = max_retries or config.MAX_RETRIES
        self._last_request: dict[str, float] = {}
        self._lock = threading.Lock()
        self._client = httpx.Client(
            follow_redirects=True,
            timeout=30.0,
            headers={"User-Agent": config.USER_AGENT},
        )

    # ------------------------------------------------------------------ utilidades
    def _sleep(self, seconds: float) -> None:
        """Duerme en pasos cortos para poder reaccionar a la cancelación."""
        end = time.monotonic() + seconds
        while True:
            if self.cancel_event is not None and self.cancel_event.is_set():
                raise CancelledError()
            remaining = end - time.monotonic()
            if remaining <= 0:
                return
            time.sleep(min(0.25, remaining))

    def _cooldown(self, domain: str) -> None:
        now = time.monotonic()
        with self._lock:
            last = self._last_request.get(domain, 0.0)
            self._last_request[domain] = now
        wait = self.min_interval - (now - last)
        if wait > 0:
            self._sleep(wait)

    def _notify_pause(self, seconds: float, reason: str) -> None:
        if self.on_pause is not None:
            try:
                self.on_pause(seconds, reason)
            except Exception:
                pass

    # ------------------------------------------------------------------ peticiones
    def _request_with_backoff(self, method: str, url: str, **kwargs):
        domain = urlparse(url).netloc or "local"
        pause = self.backoff_base
        retries = 0
        while True:
            self._cooldown(domain)
            resp = self._client.request(method, url, **kwargs)

            if resp.status_code == 429 or resp.status_code >= 500:
                # límite de tasa o error del servidor → pausa creciente y reintento
                if retries >= self.max_retries:
                    raise BlockedError(
                        f"{domain} responde {resp.status_code} tras {retries} reintentos"
                    )
                self._notify_pause(pause, f"límite/error HTTP {resp.status_code} en {domain}")
                self._sleep(pause)
                pause = min(pause * 2, self.backoff_max)
                retries += 1
                continue

            if resp.status_code == 401:
                raise ConfigError(
                    f"autenticación rechazada en {domain} (HTTP 401): revisa las claves en config.py"
                )

            if resp.status_code == 403:
                # posible bloqueo → UNA pausa prudente y un único reintento;
                # si persiste, se descarta la fuente (sin evadir protecciones)
                if retries >= 1:
                    raise BlockedError(
                        f"posible bloqueo en {domain} (HTTP 403) tras pausa y reintento"
                    )
                self._notify_pause(self.block_pause, f"posible bloqueo (HTTP 403) en {domain}")
                self._sleep(self.block_pause)
                retries += 1
                continue

            if resp.status_code == 404:
                raise BlockedError(f"recurso no encontrado en {domain} ({url})")

            resp.raise_for_status()
            return resp

    def get_json(self, url: str, params: dict | None = None, headers: dict | None = None) -> dict:
        resp = self._request_with_backoff("GET", url, params=params, headers=headers)
        return resp.json()

    def post_json(self, url: str, payload: dict, headers: dict | None = None) -> dict:
        resp = self._request_with_backoff("POST", url, json=payload, headers=headers)
        return resp.json()

    def post_form(self, url: str, data: dict, headers: dict | None = None) -> dict:
        resp = self._request_with_backoff("POST", url, data=data, headers=headers)
        return resp.json()

    def get_bytes(self, url: str, max_bytes: int | None = None) -> bytes:
        resp = self._request_with_backoff("GET", url)
        data = resp.content
        if max_bytes and len(data) > max_bytes:
            raise ValueError(f"respuesta demasiado grande en {url}")
        return data

    def download_to(self, url: str, dest: Path) -> Path:
        """Descarga el archivo a `dest`. Si existe, se sobreescribe (requisito)."""
        domain = urlparse(url).netloc or "local"
        pause = self.backoff_base
        retries = 0
        while True:
            self._cooldown(domain)
            with self._client.stream("GET", url) as resp:
                if resp.status_code == 429 or resp.status_code >= 500:
                    if retries >= self.max_retries:
                        raise BlockedError(f"{domain} responde {resp.status_code} al descargar")
                    self._notify_pause(pause, f"límite/error HTTP {resp.status_code} en {domain}")
                    self._sleep(pause)
                    pause = min(pause * 2, self.backoff_max)
                    retries += 1
                    continue
                if resp.status_code in (401, 403):
                    if resp.status_code == 401:
                        raise ConfigError(
                            f"autenticación rechazada al descargar de {domain} (HTTP 401)"
                        )
                    if retries >= 1:
                        raise BlockedError(
                            f"posible bloqueo al descargar de {domain} (HTTP 403)"
                        )
                    self._notify_pause(self.block_pause, f"posible bloqueo (HTTP 403) en {domain}")
                    self._sleep(self.block_pause)
                    retries += 1
                    continue
                resp.raise_for_status()

                ctype = resp.headers.get("content-type", "")
                if ctype and not ctype.startswith("image/"):
                    raise ValueError(f"{url} no es una imagen (content-type: {ctype})")

                dest.parent.mkdir(parents=True, exist_ok=True)
                tmp = dest.with_name(dest.name + ".part")
                with open(tmp, "wb") as fh:
                    for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                        fh.write(chunk)
                        if self.cancel_event is not None and self.cancel_event.is_set():
                            raise CancelledError()
                tmp.replace(dest)  # escritura final reemplaza el archivo existente
                return dest

    def close(self) -> None:
        self._client.close()
