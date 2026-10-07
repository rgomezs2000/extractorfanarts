"""Empaqueta ExtractorFanarts en un ejecutable con PyInstaller.

Uso:
    python scripts\\build_exe.py              # carpeta dist/ExtractorFanarts/ (onedir)
    python scripts\\build_exe.py --onefile    # un único archivo
    python scripts\\build_exe.py --consola    # conserva la ventana de consola
    python scripts\\build_exe.py --probar     # además ejecuta --selftest del resultado

IMPORTANTE (PyInstaller NO compila cruzado):
    - el .exe se genera en Windows,
    - el binario/.app de macOS se genera en macOS,
    - el binario de Linux se genera en Linux.
Para los tres de una vez usa el workflow de GitHub Actions incluido
(.github/workflows/build.yml), que compila en los tres sistemas.

Requisitos en la máquina que compila:
    pip install PySide6 httpx Pillow curl_cffi pyinstaller
    (o:  python scripts\\setup_vendor.py vendor  &&  python scripts\\setup_vendor.py vendor --ai)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
NOMBRE = "ExtractorFanarts"

# Permite usar el PyInstaller instalado en ./vendor (sin instalación global)
if VENDOR.is_dir() and str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

# Módulos de Qt que la app no usa (slim del paquete)
EXCLUIR = [
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.QtQuick3D", "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets", "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.QtDesigner", "PySide6.QtHelp",
    "PySide6.QtUiTools", "PySide6.QtTest", "PySide6.QtSql", "PySide6.QtBluetooth",
    "PySide6.QtNfc", "PySide6.QtPositioning", "PySide6.QtSensors", "PySide6.QtSerialPort",
    "PySide6.QtWebSockets", "PySide6.QtWebChannel", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
    "tkinter", "matplotlib", "numpy", "pandas", "scipy", "IPython", "pytest",
]

PLANTILLA_CONFIG = '''"""Ajustes y credenciales locales de ExtractorFanarts.

Este archivo vive JUNTO AL EJECUTABLE (o en ~/.extractorfanarts/config_local.py).
Cualquier constante en MAYÚSCULAS sobreescribe app/config.py.

Ejemplos:
    RULE34_API_KEY = "..."
    RULE34_USER_ID = "..."
    CF_CLEARANCE = "..."
    CF_USER_AGENT = "..."
    X_BEARER_TOKEN = "..."
    PIXIV_REFRESH_TOKEN = "..."
    WEBP_QUALITY_DEFAULT = 92
    ALLOW_ADULT_RATINGS = ["general", "sensitive", "questionable", "explicit"]
"""
'''


def _pyinstaller_disponible() -> bool:
    try:
        import PyInstaller  # noqa: F401
        return True
    except ImportError:
        return False


def _rutas_datos_ia() -> list[tuple[Path, str]]:
    """(origen, destino dentro del paquete) para los motores IA y sus modelos."""
    entradas: list[tuple[Path, str]] = []
    if not VENDOR.is_dir():
        return entradas
    nombres = ("realesrgan-ncnn-vulkan", "waifu2x-ncnn-vulkan")
    for elemento in sorted(VENDOR.iterdir()):
        if elemento.name == "models" and elemento.is_dir():
            entradas.append((elemento, "vendor/models"))
            continue
        if not elemento.name.startswith(nombres):
            continue
        if elemento.is_file() and elemento.suffix.lower() == ".exe":
            entradas.append((elemento, "vendor"))
        elif elemento.is_dir():
            entradas.append((elemento, f"vendor/{elemento.name}"))
    return entradas


def _argumentos(onefile: bool, consola: bool, limpiar: bool) -> list[str]:
    separador = ";" if sys.platform.startswith("win") else ":"
    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--name", NOMBRE,
        "--onefile" if onefile else "--onedir",
        "--paths", str(ROOT),
    ]
    if limpiar:
        args.append("--clean")

    if VENDOR.is_dir():
        args += ["--paths", str(VENDOR)]
    # El transporte con huella de navegador trae su propia DLL/libcurl
    args += ["--collect-all", "curl_cffi"]
    args += ["--collect-all", "certifi"]
    for modulo in EXCLUIR:
        args += ["--exclude-module", modulo]
    for origen, destino in _rutas_datos_ia():
        args += ["--add-data", f"{origen}{separador}{destino}"]
    # El archivo de credenciales del usuario NO se empaqueta (se lee de fuera)
    args += ["--exclude-module", "app.config_local"]

    if sys.platform.startswith("win") and not consola:
        args.append("--windowed")
    elif sys.platform == "darwin" and not consola:
        args.append("--windowed")
    args.append(str(ROOT / "main.py"))
    return args


def _crear_plantilla(destino: Path) -> None:
    try:
        destino.mkdir(parents=True, exist_ok=True)
        archivo = destino / "config_local.py"
        if not archivo.exists():
            archivo.write_text(PLANTILLA_CONFIG, encoding="utf-8")
            print(f"[ok] plantilla de configuración: {archivo}")
    except OSError as exc:
        print(f"[aviso] no se pudo crear la plantilla: {exc}")


def _probar(destino: Path) -> int:
    if sys.platform.startswith("win"):
        ejecutable = destino / f"{NOMBRE}.exe"
    elif sys.platform == "darwin":
        ejecutable = destino / f"{NOMBRE}.app" / "Contents" / "MacOS" / NOMBRE
        if not ejecutable.exists():
            ejecutable = destino / NOMBRE
    else:
        ejecutable = destino / NOMBRE
    if not ejecutable.exists():
        print(f"[aviso] no se encontró el ejecutable para probar en {destino}")
        return 1
    print(f"\n[prueba] {ejecutable} --selftest")
    try:
        return subprocess.call([str(ejecutable), "--selftest"], cwd=str(destino))
    except OSError as exc:
        print(f"[aviso] no se pudo ejecutar: {exc}")
        return 1


def main() -> int:
    onefile = "--onefile" in sys.argv
    consola = "--consola" in sys.argv
    probar = "--probar" in sys.argv

    if not _pyinstaller_disponible():
        print("[error] falta PyInstaller. Instálalo con:")
        print("        python -m pip install pyinstaller   (o)   "
              "python scripts\\setup_vendor.py vendor --only=pyinstaller,...")
        return 1

    print(f"[info] compilando para {sys.platform} / {os.environ.get('PROCESSOR_ARCHITECTURE', '')}")
    print(f"[info] modo: {'onefile' if onefile else 'onedir'} · "
          f"consola: {'sí' if consola else 'no'}")

    entorno = dict(os.environ)
    if VENDOR.is_dir():
        previo = entorno.get("PYTHONPATH", "")
        entorno["PYTHONPATH"] = str(VENDOR) + (os.pathsep + previo if previo else "")

    codigo = subprocess.call(_argumentos(onefile, consola, limpiar=True),
                             cwd=str(ROOT), env=entorno)
    if codigo != 0:
        print(f"[error] PyInstaller terminó con código {codigo}")
        return codigo

    destino = ROOT / "dist" / (NOMBRE if not onefile else "")
    _crear_plantilla(ROOT / "dist" / NOMBRE if onefile else destino)
    print(f"\n[ok] paquete generado en: {ROOT / 'dist'}")

    if probar:
        return _probar(ROOT / "dist" / NOMBRE)
    print("     Pruébalo con:  " + str(ROOT / "dist" / NOMBRE / f"{NOMBRE}.exe")
          if sys.platform.startswith("win") else
          "     Pruébalo ejecutando el binario de dist/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
