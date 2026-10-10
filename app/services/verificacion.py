"""Comprobación «Verification» de algunos boorus: se resuelve **el usuario**, a mano.

Algunos sitios (por ejemplo `booru.allthefallen.moe`) no devuelven datos a programas:
responden una página con **JavaScript** que plantea una comprobación anti-bot.

Imaginteca **no la resuelve por su cuenta** (eso sería comportarse como un robot y el
sitio lo prohíbe): lo que hace es **abrir una ventana con el navegador incrustado**, en la
que la resuelve la persona —igual que en su navegador de siempre— y, cuando está
superada, esa misma ventana **se cierra** y la operación (búsqueda o descarga) continúa.

Este módulo solo **reconoce** la página de comprobación (para saber cuándo hay que abrir
la ventana) y define el aviso que se lanza cuando hace falta.
"""
from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger("imaginteca")

MARCAS = ("powSeed", "challenge_id", "pow_nonce", "challenge-checkbox")

# Títulos que usan estas páginas («… | Verification», «Just a moment…», etc.)
TITULOS = ("verification", "just a moment", "checking your browser", "attention required",
           "one more step", "ddos protection")


class VerificacionRequerida(Exception):
    """El sitio pide una comprobación que debe resolver la persona en la ventana."""

    def __init__(self, dominio: str, url: str, detalle: str = ""):
        self.dominio = dominio
        self.url = url
        self.detalle = detalle
        super().__init__(
            f"{dominio} pide una comprobación antes de entregar los datos. "
            "Resuélvela en la ventana que se abre y la operación continuará sola."
        )


def dominio_de(url: str) -> str:
    return urlparse(url).netloc or url


# Comprobaciones ya superadas en esta sesión: {dominio: {"cookies": …, "agente": …}}.
# Las rellena la ventana cuando la persona resuelve la comprobación, y las usan todos
# los clientes HTTP que se creen después (el sitio asocia cookie y User-Agent).
_VERIFICADOS: dict[str, dict] = {}


def guardar_verificacion(dominio: str, cookies: str, agente: str = "") -> None:
    """Apunta las cookies (y el User-Agent) con las que el sitio ya deja pasar."""
    if not dominio:
        return
    _VERIFICADOS[dominio.lower()] = {
        "cookies": (cookies or "").strip(),
        "agente": (agente or "").strip(),
    }
    logger.info("comprobación guardada para %s (%d cookies)",
                dominio, len((cookies or "").split(";")) if cookies else 0)


def verificacion_de(dominio: str) -> dict:
    """Datos de la comprobación de ese dominio (o {} si no se ha superado)."""
    buscado = (dominio or "").lower()
    for guardado, datos in _VERIFICADOS.items():
        if buscado.endswith(guardado) or guardado.endswith(buscado):
            return datos
    return {}


def verificaciones() -> dict[str, dict]:
    return dict(_VERIFICADOS)


def parece_reto(html: str) -> bool:
    """¿Este HTML es una página de comprobación (prueba de trabajo o similar)?"""
    if not html:
        return False
    if any(marca in html for marca in MARCAS):
        return True
    titular = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if titular:
        titulo = titular.group(1).strip().lower()
        if any(clave in titulo for clave in TITULOS):
            return True
    return False


def datos_del_reto(html: str, url_base: str = "") -> dict | None:
    """Datos del reto (para el registro y para saber la dificultad); no se resuelve."""
    if not parece_reto(html):
        return None
    def dato(patron: str) -> str | None:
        hallado = re.search(patron, html)
        return hallado.group(1).strip() if hallado else None

    host = dato(r'post_to\s*=\s*"([^"]+)"') or dato(r'host\s*=\s*"([^"]+)"') or ""
    if host and not host.startswith("http"):
        host = f"https://{host}"
    return {
        "challenge_id": dato(r'challenge_id\s*=\s*"([^"]+)"') or "",
        "prefijo": dato(r'powPrefix\s*=\s*"0"\.repeat\((\d+)\)') or "",
        "url": host or url_base,
    }
