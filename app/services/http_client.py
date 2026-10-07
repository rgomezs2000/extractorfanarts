"""Cliente HTTP educado: cooldown por dominio, backoff y pausa ante bloqueos.

Transportes:
  - httpx (por defecto).
  - curl_cffi con huella de navegador (impersonate="chrome") para los dominios
    protegidos por Cloudflare configurados en CF_DOMAINS. Esto NO resuelve ni
    evade ningún desafío: reutiliza la acreditación (cf_clearance) que el usuario
    obtuvo resolviendo el CAPTCHA en su propio navegador, presentando la misma
    huella de cliente que ese navegador.

Registra en consola y en el archivo .log cada petición y respuesta (con las
claves enmascaradas) y avisa a la UI mediante `on_event`.
"""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

from .. import config

logger = logging.getLogger("extractorfanarts")

try:  # transporte opcional con huella de navegador
    from curl_cffi import requests as _curl_requests

    _CURL_OK = True
except Exception:  # noqa: BLE001
    _curl_requests = None
    _CURL_OK = False

_SECRET_KEYS = (
    "api_key", "key", "apikey", "token", "access_token", "api_secret",
    "client_secret", "password", "session",
)


class ConfigError(Exception):
    """Falta configurar algo (p. ej. credenciales de una plataforma)."""


class BlockedError(Exception):
    """La fuente rechaza/bloquea las peticiones (bloqueo o CAPTCHA)."""


class CancelledError(Exception):
    """El usuario canceló la operación."""


class _Respuesta:
    """Interfaz mínima común para respuestas de httpx y curl_cffi."""

    def __init__(self, raw):
        self._raw = raw
        self.status_code = raw.status_code
        self.headers = raw.headers
        self.content = raw.content
        self.text = getattr(raw, "text", "") or ""

    def json(self):
        return self._raw.json()


def _mask(value: object) -> str:
    """Enmascara credenciales para poder registrarlas sin exponerlas."""
    text = str(value or "")
    if not text:
        return "(vacío)"
    if len(text) <= 8:
        return "***"
    return f"{text[:6]}…{text[-4:]}[{len(text)}]"


def _safe_url(url: str, params: dict | None = None) -> str:
    parsed = urlparse(url)
    partes: list[str] = []
    for clave, valor in (params or {}).items():
        if clave.lower() in _SECRET_KEYS:
            partes.append(f"{clave}={_mask(valor)}")
        else:
            partes.append(f"{clave}={valor}")
    consulta = "&".join(partes)
    return f"{parsed.netloc}{parsed.path}" + (f"?{consulta}" if consulta else "")


def _challenge_kind(resp) -> str | None:
    """Detecta páginas de CAPTCHA/Cloudflare servidas en lugar del JSON."""
    ctype = (resp.headers.get("content-type") or "").lower()
    if "html" not in ctype:
        return None
    try:
        cuerpo = resp.text[:8000].lower()
    except Exception:  # noqa: BLE001
        return "HTML"
    if "captcha" in cuerpo:
        return "CAPTCHA de Cloudflare"
    if "cloudflare" in cuerpo or "cloudflare" in (resp.headers.get("server") or "").lower():
        return "bloqueo de Cloudflare"
    return "página HTML"


class PoliteClient:
    def __init__(
        self,
        cancel_event: threading.Event | None = None,
        on_pause=None,   # callback(segundos, motivo) para informar a la UI
        on_event=None,   # callback(mensaje) para el estatus de conexión (UI + log)
        min_interval: float | None = None,
        backoff_base: float | None = None,
        backoff_max: float | None = None,
        block_pause: float | None = None,
        max_retries: int | None = None,
    ):
        self.cancel_event = cancel_event
        self.on_pause = on_pause
        self.on_event = on_event
        self.min_interval = min_interval or config.MIN_REQUEST_INTERVAL
        self.backoff_base = backoff_base or config.BACKOFF_BASE
        self.backoff_max = backoff_max or config.BACKOFF_MAX
        self.block_pause = block_pause or config.BLOCK_PAUSE
        self.max_retries = max_retries if max_retries is not None else config.MAX_RETRIES
        self._last_request: dict[str, float] = {}
        self._lock = threading.Lock()
        # Referer por dominio (p. ej. el CDN de Pixiv exige Referer)
        self._referers: dict[str, str] = dict(getattr(config, "REFERER_DOMAINS", {}) or {})
        self._httpx = httpx.Client(
            follow_redirects=True,
            timeout=30.0,
            headers={
                "User-Agent": config.USER_AGENT,
                "Accept": "application/json, text/plain, */*",
            },
        )

        # Cloudflare: cookie cf_clearance + User-Agent del navegador que resolvió
        # el CAPTCHA (aportados por el usuario). Solo para CF_DOMAINS.
        self._cf_headers: dict[str, str] = {}
        self._cf_domains: tuple[str, ...] = tuple(getattr(config, "CF_DOMAINS", ()) or ())
        clearance = getattr(config, "CF_CLEARANCE", "")
        ua_navegador = getattr(config, "CF_USER_AGENT", "")
        if clearance and ua_navegador and self._cf_domains:
            self._cf_headers = {
                "Cookie": f"cf_clearance={clearance}",
                "User-Agent": ua_navegador,
            }
            logger.info(
                "Cloudflare: cf_clearance configurado para %s", ", ".join(self._cf_domains)
            )

        # Transporte con huella de navegador para los dominios protegidos
        self._curl = None
        self._browser_domains: tuple[str, ...] = tuple(
            getattr(config, "BROWSER_DOMAINS", ()) or self._cf_domains
        )
        self._browser_ua = (
            getattr(config, "CF_USER_AGENT", "")
            or getattr(config, "DEFAULT_BROWSER_UA", "")
        )
        impersonar = getattr(config, "BROWSER_IMPERSONATE", "") or "chrome"
        if self._browser_domains:
            if _CURL_OK:
                self._curl = _curl_requests.Session(impersonate=impersonar, timeout=30)
                logger.info(
                    "transporte con huella de navegador activo (impersonate=%s, UA=%s…) para %s",
                    impersonar, (self._browser_ua or "?")[:32], ", ".join(self._browser_domains),
                )
            else:
                logger.warning(
                    "hacen falta dominios con aspecto de navegador (%s) pero curl_cffi no está "
                    "instalado: ejecuta python scripts\\setup_vendor.py --only=curl_cffi,cffi,pycparser",
                    ", ".join(self._browser_domains),
                )

    # ------------------------------------------------------------------ utilidades
    def _es_dominio_cf(self, url: str) -> bool:
        dominio = urlparse(url).netloc
        return bool(self._cf_domains) and any(dominio.endswith(d) for d in self._cf_domains)

    def _es_dominio_navegador(self, url: str) -> bool:
        """Dominios que reciben transporte con huella de Chrome y UA de navegador."""
        dominio = urlparse(url).netloc
        return bool(self._browser_domains) and any(
            dominio.endswith(d) for d in self._browser_domains
        )

    def _headers_for(self, url: str, extra: dict | None) -> dict | None:
        """Fusiona headers del llamador, la acreditación de Cloudflare y el Referer."""
        headers: dict[str, str] = dict(extra or {})
        dominio = urlparse(url).netloc
        if self._cf_headers and self._es_dominio_cf(url):
            headers.update(self._cf_headers)
        for sufijo, referer in self._referers.items():
            if dominio.endswith(sufijo):
                headers.setdefault("Referer", referer)
                break
        return headers or None

    def _send(self, method: str, url: str, *, params=None, headers=None,
              json=None, data=None) -> _Respuesta:
        es_navegador = self._es_dominio_navegador(url)
        headers = self._headers_for(url, headers)
        if es_navegador and self._browser_ua:
            # User-Agent de navegador explícito: imprescindible contra el
            # bot-check de Cloudflare (basta con esto, verificado con Fandom).
            headers = dict(headers or {})
            headers["User-Agent"] = self._browser_ua
        if self._curl is not None and es_navegador:
            resp = self._curl.request(
                method, url, params=params, headers=headers, json=json, data=data,
                allow_redirects=True, timeout=30,
            )
        else:
            resp = self._httpx.request(
                method, url, params=params, headers=headers, json=json, data=data
            )
        return _Respuesta(resp)

    def _event(self, mensaje: str, nivel: int = logging.INFO) -> None:
        logger.log(nivel, mensaje)
        if self.on_event is not None:
            try:
                self.on_event(mensaje)
            except Exception:  # noqa: BLE001
                pass

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
        self._event(f"⏸ pausa {int(seconds)} s — {reason}", logging.WARNING)
        if self.on_pause is not None:
            try:
                self.on_pause(seconds, reason)
            except Exception:  # noqa: BLE001
                pass

    @staticmethod
    def _tamano(resp) -> str:
        try:
            return f"{len(resp.content) / 1024:.1f} KB"
        except Exception:  # noqa: BLE001
            return "?"

    # ------------------------------------------------------------------ peticiones
    def _request_with_backoff(self, method: str, url: str, **kwargs):
        domain = urlparse(url).netloc or "local"
        descripcion = _safe_url(url, kwargs.get("params"))
        pause = self.backoff_base
        retries = 0
        while True:
            self._cooldown(domain)
            self._event(f"→ {method} {descripcion}")
            t0 = time.monotonic()
            resp = self._send(method, url, **kwargs)
            tardanza = time.monotonic() - t0
            ctype = (resp.headers.get("content-type") or "?").split(";")[0]
            self._event(
                f"← HTTP {resp.status_code} {ctype} {self._tamano(resp)} en {tardanza:.2f} s "
                f"({domain})"
            )

            reto = _challenge_kind(resp)
            if reto is not None:
                if not self._es_dominio_navegador(url):
                    pista = (
                        " Este dominio no está en BROWSER_DOMAINS: añádelo en "
                        "app/config_local.py (p. ej. BROWSER_DOMAINS = [\"rule34.xxx\", "
                        "\"fandom.com\", \"nocookie.net\"]) para que use el transporte con "
                        "aspecto de navegador."
                    )
                elif self._curl is None:
                    pista = (
                        " Falta el transporte con huella de navegador: ejecuta "
                        "python scripts\\setup_vendor.py --only=curl_cffi,cffi,pycparser"
                    )
                elif self._es_dominio_cf(url) and self._cf_headers:
                    pista = (
                        " La acreditación cf_clearance puede haber caducado: vuelve a resolver "
                        "el CAPTCHA en el navegador y actualiza CF_CLEARANCE / CF_USER_AGENT."
                    )
                else:
                    pista = (
                        " El sitio sigue bloqueando la petición: actualiza DEFAULT_BROWSER_UA "
                        "(o CF_USER_AGENT) en app/config_local.py con el UA real de tu navegador."
                    )
                raise BlockedError(
                    f"{domain} exige superar un {reto} (HTTP {resp.status_code}) en lugar de "
                    "devolver datos." + pista
                )

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
                    f"autenticación rechazada en {domain} (HTTP 401): revisa las claves "
                    "en app/config_local.py"
                )

            if resp.status_code == 403:
                # 403 sin CAPTCHA → UNA pausa prudente y un único reintento
                if retries >= 1:
                    raise BlockedError(
                        f"posible bloqueo en {domain} (HTTP 403) tras pausa y reintento"
                    )
                self._notify_pause(self.block_pause, f"posible bloqueo (HTTP 403) en {domain}")
                self._sleep(self.block_pause)
                retries += 1
                continue

            if resp.status_code == 404:
                raise BlockedError(f"recurso no encontrado en {domain} ({descripcion})")

            if resp.status_code >= 400:
                # Incluye el motivo que devuelve el servidor (p. ej. Mastodon:
                # {"error":"This method requires an authenticated user"})
                detalle = ""
                try:
                    fragmento = (resp.text or "").strip().replace("\n", " ")[:200]
                except Exception:  # noqa: BLE001
                    fragmento = ""
                if fragmento:
                    detalle = f": {fragmento}"
                raise BlockedError(f"{domain} devolvió HTTP {resp.status_code}{detalle}")
            return resp

    def _json_of(self, resp, descripcion: str):
        ctype = (resp.headers.get("content-type") or "").lower()
        if "html" in ctype:
            raise BlockedError(
                f"{descripcion} devolvió HTML en lugar de JSON (posible CAPTCHA/bloqueo)"
            )
        try:
            return resp.json()
        except Exception as exc:  # noqa: BLE001
            fragmento = resp.text[:200].replace("\n", " ")
            raise BlockedError(
                f"{descripcion} no devolvió JSON válido ({exc}). Inicio: {fragmento}"
            ) from exc

    def get_json(self, url: str, params: dict | None = None, headers: dict | None = None):
        resp = self._request_with_backoff("GET", url, params=params, headers=headers)
        return self._json_of(resp, _safe_url(url, params))

    def post_json(self, url: str, payload: dict, headers: dict | None = None):
        resp = self._request_with_backoff("POST", url, json=payload, headers=headers)
        return self._json_of(resp, _safe_url(url))

    def post_form(self, url: str, data: dict, headers: dict | None = None):
        resp = self._request_with_backoff("POST", url, data=data, headers=headers)
        return self._json_of(resp, _safe_url(url))

    def get_bytes(self, url: str, max_bytes: int | None = None) -> bytes:
        resp = self._request_with_backoff("GET", url)
        data = resp.content
        if max_bytes and len(data) > max_bytes:
            raise ValueError(f"respuesta demasiado grande en {url}")
        return data

    def get_text(self, url: str, params: dict | None = None,
                 headers: dict | None = None) -> str:
        """Texto plano (RSS/XML/HTML) con el mismo control de cortesía y bloqueos."""
        resp = self._request_with_backoff("GET", url, params=params, headers=headers)
        return resp.text

    def download_to(self, url: str, dest: Path) -> Path:
        """Descarga el archivo a `dest`. Si existe, se sobreescribe (requisito)."""
        domain = urlparse(url).netloc or "local"
        t0 = time.monotonic()
        resp = self._request_with_backoff("GET", url)
        if self.cancel_event is not None and self.cancel_event.is_set():
            raise CancelledError()

        ctype = (resp.headers.get("content-type") or "").lower()
        if ctype and not ctype.startswith("image/"):
            raise ValueError(f"{url} no es una imagen (content-type: {ctype})")

        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        with open(tmp, "wb") as fh:
            fh.write(resp.content)
        tmp.replace(dest)  # sobreescribe el archivo existente
        self._event(
            f"⇩ {dest.name} descargado: {len(resp.content) / 1024:.0f} KB "
            f"({ctype.split(';')[0]}) en {time.monotonic() - t0:.2f} s"
        )
        return dest

    def close(self) -> None:
        try:
            self._httpx.close()
        except Exception:  # noqa: BLE001
            pass
        if self._curl is not None:
            try:
                self._curl.close()
            except Exception:  # noqa: BLE001
                pass
