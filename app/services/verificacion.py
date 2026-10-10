"""Comprobación «Verification» de algunos boorus: prueba de trabajo resoluble.

Algunos sitios (por ejemplo `booru.allthefallen.moe`) no devuelven datos a programas:
responden una página con **JavaScript** que plantea una **prueba de trabajo**:

  1. El HTML trae `powSeed`, `powPrefix` (p. ej. `"0"` repetido 5 veces),
     `challenge_id`, `challenge_generated` y `challenge_cookie_expires`.
  2. Hay que encontrar un `nonce` tal que `sha1(powSeed + ":" + nonce)` (en hexadecimal)
     **empiece** por ese prefijo.
  3. Se espera el tiempo que pide la página (`delay`, unos segundos).
  4. Se envía el resultado por **POST** (JSON) al propio host con
     `X-Verification-Challenge: 1`, y el servidor responde con la **cookie** que ya
     permite pedir los datos como si fuera un navegador.

Esto **no es saltarse un CAPTCHA**: es resolver, con el mismo trabajo que haría el
navegador, el reto que el sitio pide. La cookie dura lo que diga
`challenge_cookie_expires` (aquí, unos 7 días).
"""
from __future__ import annotations

import hashlib
import logging
import re
import time

logger = logging.getLogger("imaginteca")

MARCAS = ("powSeed", "challenge_id", "pow_nonce")

# Margen de seguridad: si el reto no se resuelve en este tiempo, se rinde y se informa.
SEGUNDOS_MAXIMOS = 25


def _dato(texto: str, patron: str) -> str | None:
    hallado = re.search(patron, texto)
    return hallado.group(1).strip() if hallado else None


def parece_reto(html: str) -> bool:
    """¿Este HTML es la página de verificación con prueba de trabajo?"""
    return bool(html) and all(marca in html for marca in MARCAS)


def datos_del_reto(html: str, url_base: str = "") -> dict | None:
    """Saca los datos del reto del HTML (o None si no es un reto reconocible)."""
    if not parece_reto(html):
        return None
    semilla = _dato(html, r'powSeed\s*=\s*"([^"]+)"')
    repeticiones = _dato(html, r'powPrefix\s*=\s*"0"\.repeat\((\d+)\)')
    identificador = _dato(html, r'challenge_id\s*=\s*"([^"]+)"')
    generado = _dato(html, r'challenge_generated\s*=\s*"([^"]+)"')
    expira = _dato(html, r'challenge_cookie_expires\s*=\s*"([^"]+)"')
    host = _dato(html, r'post_to\s*=\s*"([^"]+)"') or _dato(html, r'host\s*=\s*"([^"]+)"')
    retardo = _dato(html, r'const\s+delay\s*=\s*([\d.]+)')
    if not (semilla and identificador):
        return None
    ceros = int(repeticiones) if repeticiones and repeticiones.isdigit() else 5
    if host and not host.startswith("http"):
        host = f"https://{host}"
    return {
        "semilla": semilla,
        "prefijo": "0" * ceros,
        "challenge_id": identificador,
        "challenge_generated": generado or "",
        "challenge_cookie_expires": expira or "",
        "url": host or url_base,
        "retardo": float(retardo) if retardo else 5.0,
    }


def resolver(datos: dict, segundos_maximos: float = SEGUNDOS_MAXIMOS) -> dict | None:
    """Encuentra el nonce cuya huella sha1 empieza por el prefijo pedido."""
    prefijo = datos["prefijo"]
    limite = time.monotonic() + max(1.0, segundos_maximos)
    nonce = 0
    inicio = time.monotonic()
    while time.monotonic() < limite:
        for _ in range(20000):          # en tandas, para comprobar el tiempo
            huella = hashlib.sha1(f"{datos['semilla']}:{nonce}".encode("utf-8")).hexdigest()
            if huella.startswith(prefijo):
                logger.info("reto resuelto: nonce=%s en %.1f s (%s intentos)",
                            nonce, time.monotonic() - inicio, nonce + 1)
                return {"pow_nonce": str(nonce), "pow_hash": huella}
            nonce += 1
    logger.warning("no se pudo resolver la comprobación del sitio en %.0f s", segundos_maximos)
    return None


def cuerpo_del_envio(datos: dict, solucion: dict) -> dict:
    """Cuerpo JSON que espera el sitio para canjear la solución por la cookie."""
    return {
        "challenge_id": datos["challenge_id"],
        "challenge_generated": datos["challenge_generated"],
        "challenge_cookie_expires": datos["challenge_cookie_expires"],
        "pow_nonce": solucion["pow_nonce"],
        "pow_hash": solucion["pow_hash"],
    }


CABECERAS_ENVIO = {
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest",
    "X-Verification-Challenge": "1",
}
