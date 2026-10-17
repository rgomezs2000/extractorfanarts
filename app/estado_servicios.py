"""Estado de las redes sociales y plataformas que usa Imaginteca.

Comprueba, para cada plataforma, si su servicio **responde** en este momento y en qué
estado está. La comprobación es deliberadamente ligera y sin credenciales: se pide un
recurso pequeño del propio sitio (`/robots.txt`, o el punto de salud público cuando lo
hay) y se mira:

  · **operativo**                → responde con normalidad (2xx/3xx).
  · **operativo (bloquea robots)** → responde, pero no a programas (401/403/429): el
                                    servicio está en pie; lo que hace es filtrar.
  · **con problemas**            → el servidor responde con errores (5xx).
  · **sin respuesta**            → no contesta a tiempo o el dominio no resuelve.
  · **desconocido**              → otro código inesperado.

Es una foto del **servicio**, no de tus permisos: que una red esté «operativa (bloquea
robots)» no significa que vaya a funcionar sin identificarte.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

logger = logging.getLogger("imaginteca")

SIN_DATOS = "—"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# (nombre visible, dirección de prueba, página de estado del servicio)
PLATAFORMAS: tuple[tuple[str, str, str], ...] = (
    ("X (Twitter)", "https://x.com/robots.txt", "https://status.twitterstat.us/"),
    ("Pinterest", "https://www.pinterest.com/robots.txt", ""),
    ("DeviantArt", "https://www.deviantart.com/robots.txt", "https://status.deviantart.com/"),
    ("Tumblr", "https://www.tumblr.com/robots.txt", "https://status.tumblr.com/"),
    ("Pixiv", "https://www.pixiv.net/robots.txt", ""),
    ("Bluesky", "https://public.api.bsky.app/xrpc/_health", "https://status.bsky.app/"),
    ("Mastodon", "https://mastodon.social/health", "https://status.joinmastodon.org/"),
    ("Fandom (wikis)", "https://www.fandom.com/robots.txt", ""),
)

# Estados posibles (el orden importa: es de mejor a peor)
OPERATIVO = "operativo"
BLOQUEA = "operativo (bloquea robots)"
CON_PROBLEMAS = "con problemas"
SIN_RESPUESTA = "sin respuesta"
DESCONOCIDO = "desconocido"

COLORES = {
    OPERATIVO: "#2e7d32",
    BLOQUEA: "#f9a825",
    CON_PROBLEMAS: "#e65100",
    SIN_RESPUESTA: "#c62828",
    DESCONOCIDO: "#6d6d6d",
}


@dataclass
class EstadoServicio:
    nombre: str
    estado: str = DESCONOCIDO
    detalle: str = ""
    latencia: float = 0.0
    pagina: str = ""

    @property
    def operativo(self) -> bool:
        return self.estado in (OPERATIVO, BLOQUEA)

    def como_linea(self) -> str:
        latencia = f"{self.latencia * 1000:.0f} ms" if self.latencia else SIN_DATOS
        detalle = f" · {self.detalle}" if self.detalle else ""
        return f"{self.nombre}: {self.estado} ({latencia}){detalle}"


def _clasificar(estado_http: int) -> str:
    if 200 <= estado_http < 400:
        return OPERATIVO
    if estado_http in (401, 403, 429):
        return BLOQUEA
    if estado_http >= 500:
        return CON_PROBLEMAS
    return DESCONOCIDO


def comprobar_uno(nombre: str, url: str, pagina: str = "",
                  segundos: float = 8.0) -> EstadoServicio:
    """Pide el recurso de prueba y traduce la respuesta a un estado legible."""
    comienzo = time.monotonic()
    try:
        with httpx.Client(timeout=segundos, follow_redirects=True, headers={"User-Agent": UA}) as c:
            respuesta = c.get(url)
        latencia = time.monotonic() - comienzo
        estado = _clasificar(respuesta.status_code)
        return EstadoServicio(nombre=nombre, estado=estado,
                              detalle=f"HTTP {respuesta.status_code}",
                              latencia=latencia, pagina=pagina)
    except httpx.TimeoutException:
        return EstadoServicio(nombre=nombre, estado=SIN_RESPUESTA,
                              detalle="no respondió a tiempo",
                              latencia=time.monotonic() - comienzo, pagina=pagina)
    except Exception as exc:  # noqa: BLE001
        mensaje = str(exc).strip().splitlines()[0] if str(exc).strip() else type(exc).__name__
        return EstadoServicio(nombre=nombre, estado=SIN_RESPUESTA,
                              detalle=mensaje[:70],
                              latencia=time.monotonic() - comienzo, pagina=pagina)


def comprobar(segundos: float = 8.0, progreso=None) -> list[EstadoServicio]:
    """Comprueba todas las plataformas (una detrás de otra, con cortesía).

    `progreso(hechas, total, estado)` se llama tras cada plataforma, para que la ventana
    vaya enseñando los resultados según llegan.
    """
    resultados: list[EstadoServicio] = []
    total = len(PLATAFORMAS)
    for posicion, (nombre, url, pagina) in enumerate(PLATAFORMAS, start=1):
        estado = comprobar_uno(nombre, url, pagina, segundos)
        resultados.append(estado)
        logger.info("estado de %s", estado.como_linea())
        if progreso is not None:
            try:
                progreso(posicion, total, estado)
            except Exception:  # noqa: BLE001
                pass
    return resultados


def resumen(resultados: list[EstadoServicio]) -> str:
    """Frase corta con el reparto de estados."""
    if not resultados:
        return "sin datos"
    caidas = [r for r in resultados if not r.operativo]
    if not caidas:
        return f"las {len(resultados)} plataformas responden"
    nombres = ", ".join(r.nombre for r in caidas[:4])
    if len(caidas) > 4:
        nombres += f" y {len(caidas) - 4} más"
    return f"{len(caidas)} con problemas: {nombres}"
