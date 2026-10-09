"""Compila el asistente de Pixiv como ejecutable autónomo.

Genera un único archivo (`pixiv-token.exe` en Windows, `pixiv-token` en Linux/macOS)
y lo deja **junto al ejecutable de la aplicación**, dentro del paquete
(`dist/Imaginteca/`), para que quien descarga el release pueda activar Pixiv
sin tener Python instalado.

Uso:
    python scripts\\build_token_exe.py
    python scripts\\build_token_exe.py --destino "D:\\otra\\carpeta"
    python scripts\\build_token_exe.py --probar     # además ejecuta --ayuda del resultado

Nota: `scripts/pixiv_token.py` sigue funcionando como script para desarrollo; este
compilador solo lo empaqueta para el usuario final.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
NOMBRE = "pixiv-token"

# Permite usar el PyInstaller instalado en ./vendor (sin instalación global)
if VENDOR.is_dir() and str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

# El asistente solo necesita httpx (y certifi para los certificados TLS): todo lo
# demás se excluye para que el ejecutable sea pequeño y arranque rápido.
EXCLUIR = [
    "PySide6", "shiboken6", "tkinter", "matplotlib", "numpy", "pandas", "scipy",
    "IPython", "pytest", "PIL", "PyInstaller", "curl_cffi", "sqlite3",
]


def _pyinstaller_disponible() -> bool:
    try:
        import PyInstaller  # noqa: F401
        return True
    except ImportError:
        return False


def _etiqueta_integridad(archivo: Path) -> None:
    """Devuelve la etiqueta de integridad del asistente a «Media» (Windows).

    Sin este paso, un ejecutable compilado dentro de un entorno restringido hereda
    la etiqueta **baja** y Windows lo abre en modo restringido: podría no poder
    escribir el token en `config_local.py`.
    """
    if not sys.platform.startswith("win") or not archivo.is_file():
        return
    icacls = shutil.which("icacls")
    if not icacls:
        return
    try:
        resultado = subprocess.run(
            [icacls, str(archivo), "/setintegritylevel", "Medium"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
    except OSError as exc:
        print(f"[aviso] no se pudo ajustar la etiqueta de integridad: {exc}")
        return
    if resultado.returncode == 0:
        print("[ok] etiqueta de integridad del asistente: Media")
    else:
        print("[aviso] no se pudo ajustar la etiqueta de integridad del asistente")


def main() -> int:
    if not _pyinstaller_disponible():
        print("[error] falta PyInstaller. Instálalo con:")
        print("        python -m pip install pyinstaller")
        print("        (o)  python scripts\\setup_vendor.py vendor --only=pyinstaller,"
              "pyinstaller-hooks-contrib,altgraph,packaging,setuptools,pefile,pywin32-ctypes")
        return 1

    argumentos = sys.argv[1:]
    probar = "--probar" in argumentos
    destino = ROOT / "dist" / "Imaginteca"
    for indice, argumento in enumerate(argumentos):
        if argumento == "--destino" and indice + 1 < len(argumentos):
            destino = Path(argumentos[indice + 1]).expanduser().resolve()

    print(f"[info] compilando el asistente de Pixiv para {sys.platform}")
    print(f"[info] se entregará en: {destino}")

    entorno = dict(os.environ)
    if VENDOR.is_dir():
        previo = entorno.get("PYTHONPATH", "")
        entorno["PYTHONPATH"] = str(VENDOR) + (os.pathsep + previo if previo else "")

    with tempfile.TemporaryDirectory(prefix="ef-token-") as temporal:
        tmp = Path(temporal)
        comando = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--clean",
            "--onefile", "--console",
            "--name", NOMBRE,
            "--paths", str(ROOT),
            "--distpath", str(tmp / "dist"),
            "--workpath", str(tmp / "build"),
            "--specpath", str(tmp),
            "--collect-all", "certifi",
        ]
        if VENDOR.is_dir():
            comando += ["--paths", str(VENDOR)]
        for modulo in EXCLUIR:
            comando += ["--exclude-module", modulo]
        icono = ROOT / "assets" / ("icon.ico" if sys.platform.startswith("win") else "icon.png")
        if icono.is_file():
            comando += ["--icon", str(icono)]
        comando.append(str(ROOT / "scripts" / "pixiv_token.py"))

        codigo = subprocess.call(comando, cwd=str(ROOT), env=entorno)
        if codigo != 0:
            print(f"[error] PyInstaller terminó con código {codigo}")
            return codigo

        nombre_salida = NOMBRE + (".exe" if sys.platform.startswith("win") else "")
        origen = tmp / "dist" / nombre_salida
        if not origen.is_file():
            print(f"[error] no se generó el asistente en {origen}")
            return 1

        try:
            destino.mkdir(parents=True, exist_ok=True)
            final = destino / nombre_salida
            shutil.copy2(origen, final)
        except OSError as exc:
            print(f"[error] no se pudo copiar el asistente a {destino}: {exc}")
            return 1
        print(f"[ok] asistente listo: {final} ({final.stat().st_size / 1024 / 1024:.1f} MB)")

    _etiqueta_integridad(final)

    print()
    print("=" * 74)
    print(f"  LISTO -> {final}")
    print("  Se entrega junto a la aplicación: el usuario solo tiene que hacer")
    print("  doble clic en él para obtener su token de Pixiv.")
    print("=" * 74)

    if probar:
        print(f"\n[prueba] {final} --ayuda")
        try:
            return subprocess.call([str(final), "--ayuda"], cwd=str(destino),
                                   stdin=subprocess.DEVNULL)
        except OSError as exc:
            print(f"[aviso] no se pudo ejecutar: {exc}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
