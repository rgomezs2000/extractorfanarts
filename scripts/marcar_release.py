"""Escribe la marca de producción dentro del paquete que se va a publicar.

Lo llama el flujo de compilación (GitHub Actions) **antes** de empaquetar, para que
la marca:

  1. viaje **dentro** del ejecutable (`--add-data`, se lee en `sys._MEIPASS`), y
  2. quede **junto al ejecutable** (`dist/Imaginteca/release.json`).

Gracias a ella, los paquetes del release se reconocen como **producción** (con las
actualizaciones activadas) y cualquier copia hecha en un equipo —el código fuente o
un `.exe` compilado a mano— se reconoce como **desarrollo** (sin actualizaciones).

    python scripts\\marcar_release.py --version 0.1.5-beta.8 --destino dist/Imaginteca
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import config  # noqa: E402

DESTINO_MARCA = ROOT / "build" / "release.json"     # se empaqueta dentro del .exe
NOMBRE = "release.json"


def contenido(version: str, etiqueta: str) -> dict:
    return {
        "canal": "produccion",
        "version": version,
        "etiqueta": etiqueta or f"v{version}",
        "fecha": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "sistema": f"{platform.system()} {platform.release()}",
        "origen": "GitHub Actions",
        "flujo": os.environ.get("GITHUB_RUN_ID", ""),
        "commit": os.environ.get("GITHUB_SHA", ""),
        "dependencias": versiones_dependencias(),
        "nota": ("Marca de la release: hace que esta copia se reconozca como "
                 "producción y active las actualizaciones."),
    }


def versiones_dependencias() -> dict:
    """Versiones de las dependencias esenciales justo cuando se empaqueta.

    Se anotan en la marca para que el programa pueda decir **qué lleva dentro**
    aunque dentro del ejecutable no queden los `.dist-info` (que es lo normal).
    """
    try:
        from app import dependencias
    except Exception as exc:  # noqa: BLE001
        print(f"[aviso] no se pudieron leer las dependencias: {exc}")
        return {}
    datos: dict = {}
    for nombre, importable, _pypi in dependencias.ESENCIALES:
        version, _origen, presente = dependencias.version_en_uso(nombre, importable)
        if presente and version:
            datos[nombre] = str(version)
    return datos


def main() -> int:
    analizador = argparse.ArgumentParser(description="Marca el paquete como producción.")
    analizador.add_argument("--version", default=config.APP_VERSION)
    analizador.add_argument("--etiqueta", default=os.environ.get("GITHUB_REF_NAME", ""))
    analizador.add_argument("--destino", default=str(ROOT / "dist" / config.APP_NAME),
                            help="carpeta del paquete (se escribe release.json dentro)")
    argumentos = analizador.parse_args()

    datos = contenido(argumentos.version, argumentos.etiqueta)
    texto = json.dumps(datos, ensure_ascii=False, indent=2) + "\n"

    DESTINO_MARCA.parent.mkdir(parents=True, exist_ok=True)
    DESTINO_MARCA.write_text(texto, encoding="utf-8")
    print(f"[ok] marca para empaquetar dentro: {DESTINO_MARCA}")

    destino = Path(argumentos.destino)
    if destino.is_dir():
        (destino / NOMBRE).write_text(texto, encoding="utf-8")
        print(f"[ok] marca junto al programa: {destino / NOMBRE}")
        # En macOS el paquete es un .app: la marca también dentro, junto al binario
        for app in destino.glob("*.app"):
            macos = app / "Contents" / "MacOS"
            if macos.is_dir():
                (macos / NOMBRE).write_text(texto, encoding="utf-8")
                print(f"[ok] marca en el paquete de macOS: {macos / NOMBRE}")
    else:
        print(f"[aviso] todavía no existe la carpeta del paquete: {destino}")
    print(f"[info] canal de esta publicación: producción ({datos['version']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
