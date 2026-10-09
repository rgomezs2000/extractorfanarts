"""Canal de esta copia del programa: **desarrollo** o **producción**.

Regla (pedida por el autor del proyecto):

  - **Desarrollo**: el código fuente (`python main.py`) y **cualquier compilación
    propia** (el `.exe` que sale de `scripts\\build_exe.py` en tu equipo). Aquí las
    actualizaciones —el sistema, sus dependencias y el comando de actualización—
    están **desactivadas**.
  - **Producción**: los paquetes que reparte el proyecto: el que instala el
    instalador, el portable y el que se ejecuta desde la consola, porque los genera
    el flujo de publicación y llevan dentro el **archivo de marca**
    (`release.json`). Aquí las actualizaciones están **activadas**.

¿Cómo se sabe? Por la marca que escribe el flujo al empaquetar
(`scripts\\marcar_release.py`), que viaja **dentro** del paquete y junto al
ejecutable. Si no está, la copia es de desarrollo. Se puede forzar con `CANAL` en
`config_local.py` (`"desarrollo"` o `"produccion"`).
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from . import config

logger = logging.getLogger("imaginteca")

DESARROLLO = "desarrollo"
PRODUCCION = "produccion"
ARCHIVO_MARCA = "release.json"

_cache: dict | None = None


def _rutas_marca() -> list[Path]:
    """Dónde puede estar la marca: dentro del paquete y junto al ejecutable."""
    rutas: list[Path] = []
    interior = getattr(sys, "_MEIPASS", None)
    if interior:
        rutas.append(Path(interior) / ARCHIVO_MARCA)
    raiz = Path(__file__).resolve().parents[1]
    rutas.append(raiz / ARCHIVO_MARCA)                    # ejecutando desde el código
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve().parent
        rutas.append(exe / ARCHIVO_MARCA)                 # junto al ejecutable
        # En macOS el binario vive en Imaginteca.app/Contents/MacOS
        rutas.append(exe.parent / "Resources" / ARCHIVO_MARCA)
        rutas.append(exe.parent / ARCHIVO_MARCA)
        rutas.append(exe.parent.parent / ARCHIVO_MARCA)
    return rutas


def marca() -> dict | None:
    """Contenido del archivo de marca de la release, o None si no existe."""
    global _cache
    if _cache is not None:
        return _cache or None
    for ruta in _rutas_marca():
        try:
            if ruta.is_file():
                datos = json.loads(ruta.read_text(encoding="utf-8"))
                if isinstance(datos, dict):
                    _cache = datos
                    logger.info("copia de producción (marca %s): %s", ruta, datos)
                    return datos
        except (OSError, ValueError) as exc:
            logger.info("marca ilegible (%s): %s", ruta, exc)
    _cache = {}
    return None


def canal() -> str:
    """«desarrollo» o «produccion»."""
    forzado = str(getattr(config, "CANAL", "") or "").strip().lower()
    if forzado in (DESARROLLO, "dev", "development"):
        return DESARROLLO
    if forzado in (PRODUCCION, "prod", "production"):
        return PRODUCCION
    return PRODUCCION if marca() else DESARROLLO


def es_produccion() -> bool:
    """¿Esta copia viene de una release (instalador, portable o consola)?"""
    return canal() == PRODUCCION


def es_desarrollo() -> bool:
    return canal() == DESARROLLO


def actualizaciones_activas() -> bool:
    """Las actualizaciones solo se permiten en copias de producción."""
    return es_produccion()


def descripcion() -> str:
    """Texto corto para la interfaz y los informes."""
    datos = marca() or {}
    if es_produccion():
        version = datos.get("version") or config.APP_VERSION
        origen = datos.get("origen") or "release"
        return f"producción ({origen} {version})"
    if getattr(sys, "frozen", False):
        return "desarrollo (compilación propia)"
    return "desarrollo (código fuente)"


def motivo_desactivado() -> str:
    """Explicación para cuando algo está desactivado por ser copia de desarrollo."""
    return ("Esta es una copia de **desarrollo** —código fuente o compilación propia—:"
            " las actualizaciones (el programa, sus dependencias y el comando de"
            " actualización) están **desactivadas**. Descarga la versión de producción"
            " (release) para recibir actualizaciones.")
