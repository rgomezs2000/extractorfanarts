"""Estado de las plataformas que usa Imaginteca: redes sociales, boorus y wikis.

Comprueba, para cada plataforma, si su servicio **responde** en este momento y en qué
estado está. La comprobación es deliberadamente ligera y sin credenciales: se pide la
portada del servicio (o un recurso pequeño como `/robots.txt`) y se mira el resultado:

  · **operativo**                  → responde con normalidad (2xx/3xx).
  · **operativo (bloquea robots)** → responde, pero no a programas (401/403/429): el
                                    servicio está en pie; lo que hace es filtrar.
  · **con problemas**              → el servidor responde con errores (5xx).
  · **sin respuesta**              → no contesta a tiempo o el dominio no resuelve.
  · **desconocido**                → otro código inesperado.

La lista **no se escribe a mano**: las redes sociales están aquí, los **boorus** salen de
la configuración del programa (`BOORU_SITES`, así salen los que tengas tú, incluidos los
añadidos en `config_local.py`) y las **wikis** son la plataforma de fandom.

Es una foto del **servicio**, no de tus permisos: que un booru esté «operativo (bloquea
robots)» no significa que vaya a dejarte pedir datos.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

from . import config

logger = logging.getLogger("imaginteca")

SIN_DATOS = "—"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# Tipos de plataforma (se muestran en la ventana)
SOCIAL = "Red social"
BOORU = "Booru"
WIKI = "Wiki de fandom"

# Redes sociales: (nombre, dirección de prueba, página de estado del servicio)
SOCIALES: tuple[tuple[str, str, str], ...] = (
    ("X (Twitter)", "https://x.com/robots.txt", "https://status.twitterstat.us/"),
    ("Pinterest", "https://www.pinterest.com/robots.txt", ""),
    ("DeviantArt", "https://www.deviantart.com/robots.txt", "https://status.deviantart.com/"),
    ("Tumblr", "https://www.tumblr.com/robots.txt", "https://status.tumblr.com/"),
    ("Pixiv", "https://www.pixiv.net/robots.txt", ""),
    ("Bluesky", "https://public.api.bsky.app/xrpc/_health", "https://status.bsky.app/"),
    ("Mastodon", "https://mastodon.social/health", "https://status.joinmastodon.org/"),
    ("Inkbunny", "https://inkbunny.net/robots.txt", ""),
)

# Wikis de fandom (la plataforma con la que se leen los fandoms)
WIKIS: tuple[tuple[str, str, str], ...] = (
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
    tipo: str = SOCIAL

    @property
    def operativo(self) -> bool:
        return self.estado in (OPERATIVO, BLOQUEA)

    def como_linea(self) -> str:
        latencia = f"{self.latencia * 1000:.0f} ms" if self.latencia else SIN_DATOS
        detalle = f" · {self.detalle}" if self.detalle else ""
        return f"{self.nombre}: {self.estado} ({latencia}){detalle}"


def _direccion_de_booru(base: str) -> str:
    """Dirección de prueba de un booru: su portada (sirve aunque no tenga robots.txt)."""
    return (base or "").rstrip("/") + "/"


def boorus() -> list[tuple[str, str, str]]:
    """(nombre, dirección de prueba, página) de los boorus configurados."""
    salida: list[tuple[str, str, str]] = []
    for sitio in getattr(config, "BOORU_SITES", ()) or ():
        nombre = str(sitio.get("name") or "").strip()
        base = str(sitio.get("base") or "").strip()
        if not nombre or not base:
            continue
        salida.append((nombre, _direccion_de_booru(base), ""))
    return salida


def instancias_fediverso() -> list[tuple[str, str, str]]:
    """Instancias del fediverso a comprobar, como (nombre, url de prueba, página).

    El fediverso no es «Mastodon»: cada instancia es un mundo (Mastodon, Misskey,
    CherryPick…). La lista sale de `FEDIVERSE_INSTANCIAS` en config.py, que se puede
    ampliar en config_local.py con las que uses tú.
    """
    salida: list[tuple[str, str, str]] = []
    vistas: set[str] = set()
    for dominio in getattr(config, "FEDIVERSE_INSTANCIAS", ()) or ():
        limpio = str(dominio or "").strip().strip("/").lower()
        if not limpio or limpio in vistas:
            continue
        vistas.add(limpio)
        base = limpio if "://" in limpio else f"https://{limpio}"
        nombre = limpio.split("://")[-1]
        salida.append((f"Fediverso · {nombre}", f"{base}/robots.txt", ""))
    return salida


def plataformas() -> list[tuple[str, str, str, str]]:
    """Todas las plataformas: (nombre, tipo, dirección de prueba, página de estado)."""
    lista: list[tuple[str, str, str, str]] = []
    lista.extend((nombre, SOCIAL, url, pagina) for nombre, url, pagina in SOCIALES)
    lista.extend((nombre, SOCIAL, url, pagina) for nombre, url, pagina in instancias_fediverso())
    lista.extend((nombre, BOORU, url, "") for nombre, url, _ in boorus())
    lista.extend((nombre, WIKI, url, pagina) for nombre, url, pagina in WIKIS)
    return lista


def _clasificar(estado_http: int) -> str:
    if 200 <= estado_http < 400:
        return OPERATIVO
    if estado_http in (401, 403, 429):
        return BLOQUEA
    if estado_http >= 500:
        return CON_PROBLEMAS
    return DESCONOCIDO


def comprobar_uno(nombre: str, url: str, pagina: str = "",
                  segundos: float = 8.0, tipo: str = SOCIAL) -> EstadoServicio:
    """Pide la dirección de prueba y traduce la respuesta a un estado legible."""
    comienzo = time.monotonic()
    try:
        with httpx.Client(timeout=segundos, follow_redirects=True,
                          headers={"User-Agent": UA}) as c:
            respuesta = c.get(url)
        latencia = time.monotonic() - comienzo
        estado = _clasificar(respuesta.status_code)
        return EstadoServicio(nombre=nombre, estado=estado,
                              detalle=f"HTTP {respuesta.status_code}",
                              latencia=latencia, pagina=pagina, tipo=tipo)
    except httpx.TimeoutException:
        return EstadoServicio(nombre=nombre, estado=SIN_RESPUESTA,
                              detalle="no respondió a tiempo",
                              latencia=time.monotonic() - comienzo, pagina=pagina, tipo=tipo)
    except Exception as exc:  # noqa: BLE001
        mensaje = str(exc).strip().splitlines()[0] if str(exc).strip() else type(exc).__name__
        return EstadoServicio(nombre=nombre, estado=SIN_RESPUESTA,
                              detalle=mensaje[:70],
                              latencia=time.monotonic() - comienzo, pagina=pagina, tipo=tipo)


def comprobar(segundos: float = 8.0, progreso=None) -> list[EstadoServicio]:
    """Comprueba todas las plataformas (una detrás de otra, con cortesía).

    `progreso(hechas, total, estado)` se llama tras cada plataforma, para que la ventana
    vaya enseñando los resultados según llegan.
    """
    resultados: list[EstadoServicio] = []
    lista = plataformas()
    total = len(lista)
    for posicion, (nombre, tipo, url, pagina) in enumerate(lista, start=1):
        estado = comprobar_uno(nombre, url, pagina, segundos, tipo)
        resultados.append(estado)
        logger.info("estado de %s", estado.como_linea())
        if progreso is not None:
            try:
                progreso(posicion, total, estado)
            except Exception:  # noqa: BLE001
                pass
    return resultados


def resumen(resultados: list[EstadoServicio]) -> str:
    """Frase corta con el reparto de estados, separando por tipo."""
    if not resultados:
        return "sin datos"
    caidas = [r for r in resultados if not r.operativo]
    if not caidas:
        tipos = {r.tipo for r in resultados}
        detalle = ", ".join(sorted(tipos))
        return f"las {len(resultados)} plataformas responden ({detalle.lower()})"
    nombres = ", ".join(r.nombre for r in caidas[:4])
    if len(caidas) > 4:
        nombres += f" y {len(caidas) - 4} más"
    return f"{len(caidas)} con problemas: {nombres}"
