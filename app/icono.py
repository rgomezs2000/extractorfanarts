"""Localiza y aplica el icono de la aplicación (en desarrollo y empaquetada).

El icono vive en `assets/` (generado con `python scripts/make_icon.py`):
  - `icon.ico`  → Windows (multi-tamaño, también es el icono del .exe)
  - `icon.png`  → macOS / Linux (1024 px)
  - `icon_256.png` → respaldo para el icono de ventana
"""
from __future__ import annotations

import sys
from pathlib import Path

# En Windows el .ico da el mejor resultado (varios tamaños); en el resto, PNG
_PREFERIDOS_WIN = ("icon.ico", "icon.png", "icon_256.png")
_PREFERIDOS_UNIX = ("icon.png", "icon_256.png", "icon.ico")


def _bases() -> list[Path]:
    bases: list[Path] = []
    if getattr(sys, "frozen", False):
        bases.append(Path(sys.executable).resolve().parent)
        interior = getattr(sys, "_MEIPASS", None)
        if interior:
            bases.append(Path(interior))
    bases.append(Path(__file__).resolve().parents[1])  # raíz del proyecto
    return bases


def ruta_icono() -> Path | None:
    """Primera ruta de icono existente, o None."""
    nombres = _PREFERIDOS_WIN if sys.platform.startswith("win") else _PREFERIDOS_UNIX
    for base in _bases():
        for nombre in nombres:
            candidato = base / "assets" / nombre
            if candidato.is_file():
                return candidato
    return None


def aplicar_icono(app) -> bool:
    """Pone el icono en la aplicación (afecta a todas las ventanas y a la barra)."""
    ruta = ruta_icono()
    if ruta is None:
        return False
    try:
        from PySide6.QtGui import QIcon

        icono = QIcon(str(ruta))
        if icono.isNull():
            return False
        app.setWindowIcon(icono)
        return True
    except Exception:  # noqa: BLE001
        return False


def configurar_app_user_model_id(nombre: str = "ExtractorFanarts.App") -> bool:
    """Windows: identificador propio para que la BARRA DE TAREAS use nuestro icono.

    Sin esto, Windows agrupa el proceso bajo el ejecutable anfitrión (python.exe) y
    la barra de tareas muestra el icono de Python en vez del nuestro. Debe llamarse
    ANTES de crear la QApplication.
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(nombre)
        return True
    except Exception:  # noqa: BLE001
        return False
