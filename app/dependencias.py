"""Estado y actualización de lo que el programa necesita para funcionar.

Qué comprueba:

  - El **intérprete de Python** que se está usando.
  - Los **paquetes esenciales** (Qt/PySide6, Pillow, httpx, curl_cffi y sus
    dependencias): versión instalada frente a la última publicada en PyPI.
  - Los **motores de IA** (Real-ESRGAN / waifu2x) presentes en el paquete.

Dos situaciones muy distintas:

  - **Empaquetado** (el `.exe` del release): las dependencias viajan dentro del
    programa, así que no hay nada que actualizar por separado — se actualizan con
    el propio Imaginteca (**🔄 Actualizaciones**). Aquí solo se informa.
  - **Desde el código** (con las dependencias en `vendor/`): sí se pueden
    actualizar. Se lanza un proceso aparte que **espera a que la aplicación se
    cierre**, actualiza los paquetes, la **vuelve a abrir** y deja la **consola
    abierta** con el informe (la consola no se cierra ni se reinicia; el programa
    sí).
"""
from __future__ import annotations

import importlib
import importlib.metadata as metadatos
import importlib.util
import json
import logging
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from . import config, consola

logger = logging.getLogger("imaginteca")

PYPI = "https://pypi.org/pypi"
_CABECERAS = {"User-Agent": f"{config.APP_NAME}-dependencias"}

# (nombre del paquete, módulo que se importa, nombre en PyPI)
# OJO: no siempre coinciden (Pillow se importa como «PIL»), y de eso depende que el
# informe pueda leer la versión real de lo que está en uso.
ESENCIALES: tuple[tuple[str, str, str], ...] = (
    ("PySide6", "PySide6", "PySide6"),
    ("shiboken6", "shiboken6", "shiboken6"),
    ("Pillow", "PIL", "pillow"),
    ("httpx", "httpx", "httpx"),
    ("httpcore", "httpcore", "httpcore"),
    ("h11", "h11", "h11"),
    ("anyio", "anyio", "anyio"),
    ("certifi", "certifi", "certifi"),
    ("curl_cffi", "curl_cffi", "curl-cffi"),
)

MOTORES = ("realesrgan-ncnn-vulkan", "waifu2x-ncnn-vulkan")


# ------------------------------------------------------------------ versiones
def _clave(texto: str) -> tuple:
    """Clave comparable tolerante para versiones de paquetes (PEP 440 en lo básico).

    «6.11.2» → (6, 11, 2); las pre-versiones (`rc`, `b`, `dev`) quedan por debajo
    de la versión final del mismo número, que es lo correcto al comparar.
    """
    texto = (texto or "").strip()
    trozos = re.findall(r"\d+|[a-zA-Z]+", texto)
    clave: list[tuple[int, int]] = []
    for trozo in trozos:
        if trozo.isdigit():
            clave.append((1, int(trozo)))
        else:
            letra = trozo.lower()
            # Una etiqueta de pre-versión ordena ANTES que el número final.
            clave.append((0, -1 if letra in ("dev", "a", "alpha", "b", "beta",
                                             "rc", "pre", "preview") else 1))
    # Una versión final es SIEMPRE mayor que su pre-versión (1.0 > 1.0rc1).
    if not re.search(r"[a-zA-Z]", texto):
        clave.append((2, 0))
    return tuple(clave)


def hay_novedad(instalada: str | None, publicada: str | None) -> bool:
    if not instalada or not publicada:
        return False
    return _clave(publicada) > _clave(instalada)


def _carpetas_dependencias() -> list[Path]:
    """Dónde pueden estar los paquetes: `vendor/` y la carpeta interna del paquete."""
    carpetas: list[Path] = []
    raiz = Path(__file__).resolve().parents[1]
    carpetas.append(raiz / "vendor")
    if getattr(sys, "frozen", False):
        interior = getattr(sys, "_MEIPASS", None)
        if interior:
            carpetas.append(Path(interior))
    return [c for c in carpetas if c.is_dir()]


def version_instalada(nombre: str) -> str | None:
    """Versión del paquete instalado (entorno o `vendor/`), o None si no está."""
    try:
        return metadatos.version(nombre)
    except Exception:  # noqa: BLE001  (no instalado o sin metadatos)
        pass
    for carpeta in _carpetas_dependencias():
        for dist in carpeta.glob(f"{nombre.replace('-', '_')}*.dist-info"):
            try:
                for linea in (dist / "METADATA").read_text(encoding="utf-8",
                                                           errors="replace").splitlines():
                    if linea.lower().startswith("version:"):
                        return linea.split(":", 1)[1].strip()
            except OSError:
                continue
    return None


def version_publicada(nombre_pypi: str, timeout: int | None = None) -> str | None:
    """Última versión publicada en PyPI (o None si no se pudo consultar)."""
    if timeout is None:
        timeout = int(getattr(config, "UPDATE_TIMEOUT", 15))
    try:
        peticion = urllib.request.Request(f"{PYPI}/{nombre_pypi}/json", headers=_CABECERAS)
        with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
            datos = json.loads(respuesta.read().decode("utf-8"))
        return str((datos.get("info") or {}).get("version") or "") or None
    except Exception as exc:  # noqa: BLE001
        logger.info("no se pudo consultar PyPI (%s): %s", nombre_pypi, exc)
        return None


def motores_ia() -> dict[str, bool]:
    """¿Están los motores de IA en el paquete?"""
    resultado = {nombre: False for nombre in MOTORES}
    override = getattr(config, "AI_EXE_OVERRIDE", "") or ""
    if override and Path(override).is_file():
        for nombre in MOTORES:
            if nombre in Path(override).name.lower():
                resultado[nombre] = True
    for carpeta in _carpetas_dependencias():
        for nombre in MOTORES:
            if not resultado[nombre] and list(carpeta.glob(f"{nombre}*")):
                resultado[nombre] = True
    return resultado


def empaquetado() -> bool:
    return bool(getattr(sys, "frozen", False))


# ------------------------------------------------------------------ estado
def _version_del_modulo(importable: str) -> tuple[str | None, bool]:
    """(versión, ¿está?) leyendo el módulo que el programa tiene **en uso**.

    Es la comprobación de verdad: si se puede importar, la dependencia está ahí,
    aunque sus metadatos no aparezcan (es lo que pasa dentro del ejecutable
    empaquetado, donde las dependencias van incluidas y no hay `.dist-info`).
    """
    try:
        modulo = importlib.import_module(importable)
    except Exception:  # noqa: BLE001  (no está, o falla al cargar)
        try:
            return None, importlib.util.find_spec(importable) is not None
        except Exception:  # noqa: BLE001
            return None, False
    for atributo in ("__version__", "version", "VERSION", "version_info"):
        valor = getattr(modulo, atributo, None)
        if isinstance(valor, str) and valor.strip():
            return valor.strip(), True
        if isinstance(valor, tuple) and valor:
            return ".".join(str(p) for p in valor), True
    return None, True


def _versiones_anotadas() -> dict:
    """Versiones que quedaron anotadas al compilar/empaquetar.

    Se miran dos sitios: la marca de la release (`release.json`, la escribe el flujo
    de publicación) y la nota de la compilación (`dependencies.json`, la escribe
    `scripts\\build_exe.py`). Dentro del ejecutable no quedan los `.dist-info`, así que
    esta es la forma de saber la versión exacta de cada paquete.
    """
    datos: dict = {}
    try:
        from . import canal

        datos.update(dict((canal.marca() or {}).get("dependencias") or {}))
    except Exception:  # noqa: BLE001
        pass
    candidatas = []
    interior = getattr(sys, "_MEIPASS", None)
    if interior:
        candidatas.append(Path(interior) / "dependencies.json")
    if getattr(sys, "frozen", False):
        candidatas.append(Path(sys.executable).resolve().parent / "dependencies.json")
    candidatas.append(Path(__file__).resolve().parents[1] / "dependencies.json")
    for ruta in candidatas:
        try:
            if ruta.is_file():
                contenido = json.loads(ruta.read_text(encoding="utf-8"))
                datos.update(dict(contenido.get("dependencias") or {}))
                break
        except (OSError, ValueError):
            continue
    return datos


def version_en_uso(nombre: str, importable: str | None = None) -> tuple[str | None, str, bool]:
    """(versión, de dónde sale, ¿está presente?) de una dependencia esencial.

    Se mira, por este orden: el **módulo importado** (lo que se usa de verdad), los
    metadatos del entorno o de `vendor/`, y lo que quedó **anotado** al compilar.
    """
    importable = importable or nombre
    version, presente = _version_del_modulo(importable)
    origen = ""
    if presente:
        origen = "paquete" if empaquetado() else "en uso"
    if not version:
        metadatos_version = version_instalada(nombre)
        if metadatos_version:
            version = metadatos_version
            if not presente:
                origen = "paquete" if empaquetado() else "vendor"
    if not version:
        anotada = _versiones_anotadas().get(nombre)
        if anotada:
            version = str(anotada)
            origen = "paquete" if empaquetado() else "anotada"
    return version, origen or "—", bool(presente or version)


def estado(comprobar_red: bool = True) -> dict:
    """Estado completo: Python, paquetes esenciales y motores de IA."""
    paquetes = []
    for nombre, importable, en_pypi in ESENCIALES:
        version, origen, presente = version_en_uso(nombre, importable)
        publicada = version_publicada(en_pypi) if comprobar_red else None
        paquetes.append({
            "paquete": nombre,
            "pypi": en_pypi,
            "instalada": version,
            "origen": origen,
            "presente": presente,
            "publicada": publicada,
            "novedad": hay_novedad(version, publicada),
        })
    return {
        "python": sys.version.split()[0],
        "python_ruta": sys.executable,
        "empaquetado": empaquetado(),
        "paquetes": paquetes,
        "motores": motores_ia(),
        "actualizables": [p["paquete"] for p in paquetes if p["novedad"]],
    }


def resumen(estado_datos: dict) -> list[str]:
    """Líneas de informe (para la consola y para el cuadro de diálogo)."""
    lineas = []
    modo = "empaquetado (las dependencias van dentro)" if estado_datos["empaquetado"] \
        else "desde el código (dependencias en vendor/)"
    lineas.append(f"Python {estado_datos['python']} · {modo}")
    lineas.append(f"intérprete: {estado_datos['python_ruta']}")
    lineas.append("")
    lineas.append(f"{'paquete':<12} {'en uso':<11} {'de dónde':<10} {'última':<11} estado")
    lineas.append("-" * 62)
    for p in estado_datos["paquetes"]:
        version = p.get("instalada") or "—"
        publicada = p.get("publicada") or "—"
        origen = p.get("origen") or "—"
        if not p.get("presente"):
            estado_txt = "NO ENCONTRADO"
        elif not version.strip("—") or version == "—":
            estado_txt = "presente (versión no legible)"
        elif p.get("publicada") is None:
            estado_txt = "presente (sin comprobar)"
        elif p.get("novedad"):
            estado_txt = "HAY NOVEDAD"
        else:
            estado_txt = "al día"
        lineas.append(f"{p['paquete']:<12} {version:<11} {origen:<10} {publicada:<11} "
                      f"{estado_txt}")
    lineas.append("")
    presentes = sum(1 for p in estado_datos["paquetes"] if p.get("presente"))
    lineas.append(f"dependencias presentes: {presentes} de {len(estado_datos['paquetes'])}")
    if estado_datos["empaquetado"]:
        lineas.append("(en la copia empaquetada las dependencias viajan dentro del "
                      "programa: «paquete»)")
    lineas.append("")
    for nombre, presente in estado_datos["motores"].items():
        lineas.append(f"motor IA {nombre}: {'sí' if presente else 'no'}")
    return lineas


def escribir_en_consola(lineas: list[str]) -> bool:
    """Muestra el informe en la consola (la crea si hace falta). Devuelve si pudo."""
    if not consola.asegurar_consola(f"{config.APP_NAME} — dependencias"):
        return False
    try:
        print("", flush=True)
        for linea in lineas:
            print(linea, flush=True)
        print("", flush=True)
        return True
    except Exception:  # noqa: BLE001
        return False


# ------------------------------------------------------------------ actualización
def comando_actualizacion(python: str | None = None) -> list[str]:
    """Orden para actualizar los paquetes esenciales en `vendor/`.

    Se usa el script del proyecto (`setup_vendor.py`), que baja la última versión de
    cada paquete; si no estuviera, se recurre a `pip install --upgrade --target`.
    """
    interprete = python or sys.executable
    raiz = Path(__file__).resolve().parents[1]
    setup = raiz / "scripts" / "setup_vendor.py"
    paquetes = ",".join(en_pypi for _, _, en_pypi in ESENCIALES)
    if setup.is_file():
        return [interprete, str(setup), "vendor", f"--only={paquetes}"]
    return [interprete, "-m", "pip", "install", "--upgrade", "--no-input",
            "--target", str(raiz / "vendor"), *[en_pypi for _, en_pypi in ESENCIALES]]


def escribir_actualizador(destino: Path | None = None) -> Path:
    """Crea el `.bat` que actualiza las dependencias dejando la consola abierta.

    El script: espera a que ESTA aplicación se cierre (si no, Windows no deja
    reemplazar las DLL de Qt), muestra el informe, actualiza los paquetes, vuelve a
    abrir el programa y **no cierra ni reinicia la consola**: solo el programa se
    reinicia.
    """
    raiz = Path(__file__).resolve().parents[1]
    if destino is None:
        import tempfile
        destino = Path(tempfile.mkdtemp(prefix=f"{config.APP_NAME}-deps-")) / "dependencias.bat"
    if empaquetado():
        aplicacion = str(Path(sys.executable))
    else:
        aplicacion = f'"{sys.executable}" "{raiz / "main.py"}"'
    orden = " ".join(f'"{parte}"' if " " in str(parte) else str(parte)
                     for parte in comando_actualizacion())
    guion = destino
    guion.write_text(
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f"title {config.APP_NAME} - dependencias\r\n"
        "echo ======================================================================\r\n"
        f"echo   {config.APP_NAME} - actualizacion de dependencias\r\n"
        "echo ======================================================================\r\n"
        "echo.\r\n"
        "echo   Esperando a que se cierre la aplicacion...\r\n"
        ":espera\r\n"
        f'tasklist /FI "PID eq {os.getpid()}" | find "{os.getpid()}" >nul 2>&1\r\n'
        "if not errorlevel 1 (\r\n"
        "  timeout /t 1 /nobreak >nul\r\n"
        "  goto espera\r\n"
        ")\r\n"
        "echo   Aplicacion cerrada. Actualizando dependencias (puede tardar)...\r\n"
        "echo.\r\n"
        f"{orden}\r\n"
        "set CODIGO=%ERRORLEVEL%\r\n"
        "echo.\r\n"
        "if not \"%CODIGO%\"==\"0\" (\r\n"
        "  echo   [AVISO] la actualizacion termino con codigo %CODIGO%.\r\n"
        "  echo   Puedes volver a intentarlo; la aplicacion se abrira igualmente.\r\n"
        ") else (\r\n"
        "  echo   [OK] dependencias actualizadas.\r\n"
        ")\r\n"
        "echo.\r\n"
        "echo   Abriendo la aplicacion de nuevo...\r\n"
        f"start \"\" {aplicacion}\r\n"
        "echo.\r\n"
        "echo ======================================================================\r\n"
        "echo   Listo. ESTA CONSOLA NO SE CIERRA NI SE REINICIA:\r\n"
        "echo   dejala abierta para leer el informe y cierrala cuando quieras.\r\n"
        "echo   El programa se ha reiniciado por su cuenta.\r\n"
        "echo ======================================================================\r\n",
        encoding="utf-8",
    )
    return guion


def lanzar(guion: Path) -> None:
    """Abre el actualizador en una **consola visible** que permanece abierta."""
    if sys.platform.startswith("win"):
        subprocess.Popen(["cmd", "/c", "start", f"{config.APP_NAME} - dependencias",
                          "cmd", "/k", str(guion)], close_fds=True)
    else:
        subprocess.Popen(["x-terminal-emulator", "-e", f"sh {guion}"], close_fds=True)
