"""Consola de registros para el ejecutable de Windows.

Al abrir el `.exe` compilado no hay ninguna terminal donde ver qué está pasando (a
diferencia de `python main.py`, que escribe en la consola desde la que lo lanzas).
Este módulo **crea una ventana de consola** al arrancar y el registro
(`app/logging_setup.py`) escribe en ella los MISMOS mensajes que van al `.log` del día.

- Solo actúa en **Windows** y con la aplicación **empaquetada** (`frozen`): en
  desarrollo (`python main.py`) no se toca la terminal desde la que lo ejecutas.
- Si el ejecutable ya se compiló **con** consola (`scripts/build_exe.py --consola`) o
  la app se lanzó desde una terminal, no crea nada: reutiliza la que hay.
- Se desactiva con `LOG_EN_CONSOLA = False` en `app/config_local.py`.
- La ventana se deja en UTF-8, con título propio, **sin modo de edición rápida** (un
  clic no congela el registro) y **sin botón de cerrar**: cerrarla mataría la app.
"""
from __future__ import annotations

import logging
import os
import sys

from . import config

logger = logging.getLogger("imaginteca")

_SC_CLOSE = 0xF060            # cerrar (menú de sistema)
_MF_BYCOMMAND = 0x00000000
_ENABLE_QUICK_EDIT_MODE = 0x0040
_ENABLE_EXTENDED_FLAGS = 0x0080
_STD_OUTPUT_HANDLE = -11

_creada_por_nosotros = False


def hay_consola() -> bool:
    """¿Hay una consola utilizable donde escribir? (False en el .exe sin consola)."""
    for flujo in (sys.stdout, sys.stderr):
        if flujo is None:
            continue
        try:
            flujo.fileno()
            return True
        except Exception:  # noqa: BLE001  (sin fileno, cerrado, redirigido a nada…)
            continue
    return False


def consola_propia() -> bool:
    """True si la consola la creó esta app (es suya y se puede cerrar al salir)."""
    return _creada_por_nosotros


def asegurar_consola(titulo: str | None = None) -> bool:
    """Deja lista una consola para los registros. Devuelve True si se puede escribir.

    En Windows empaquetado, si no hay ninguna, la crea; en el resto de casos se limita
    a comprobar si hay una (y devuelve False si no la hay, sin romper nada).
    """
    global _creada_por_nosotros
    if not bool(getattr(config, "LOG_EN_CONSOLA", True)):
        return False
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return hay_consola()          # en desarrollo se usa tu propia terminal
    if hay_consola():
        return True                   # compilado con consola o lanzado desde una terminal

    try:
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        if not kernel32.AllocConsole():
            return False
        try:
            sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace",
                              buffering=1)
            sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace",
                              buffering=1)
        except OSError:
            return False
        try:
            sys.stdin = open("CONIN$", "r", encoding="utf-8", errors="replace")
        except OSError:
            sys.stdin = None
        try:
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
        except Exception:  # noqa: BLE001
            pass
        _creada_por_nosotros = True
        _preparar_ventana(kernel32, titulo or f"{config.APP_NAME} — registros")
        return True
    except Exception:  # noqa: BLE001
        return False


def _preparar_ventana(kernel32, titulo: str) -> None:
    """Título propio, sin botón de cerrar y sin edición rápida."""
    try:
        import ctypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        ventana = kernel32.GetConsoleWindow()
        if ventana:
            user32.SetWindowTextW(ventana, titulo)
            menu = user32.GetSystemMenu(ventana, False)
            if menu:
                user32.DeleteMenu(menu, _SC_CLOSE, _MF_BYCOMMAND)
        manejar = kernel32.GetStdHandle(_STD_OUTPUT_HANDLE)
        modo = ctypes.c_uint32()
        if manejar and kernel32.GetConsoleMode(manejar, ctypes.byref(modo)):
            kernel32.SetConsoleMode(
                manejar, (modo.value & ~_ENABLE_QUICK_EDIT_MODE) | _ENABLE_EXTENDED_FLAGS
            )
    except Exception:  # noqa: BLE001
        pass


def pausa_final(mensaje: str = "Pulse Intro para cerrar…", segundos: int = 120) -> None:
    """Espera antes de cerrar la consola que creamos (para poder leer el mensaje).

    Nunca bloquea de forma indefinida: si la ventana no es visible (p. ej. lanzada
    por un script con la ventana oculta) o pasa el tiempo máximo, sigue adelante.
    """
    if not _creada_por_nosotros:
        return
    try:
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        ventana = kernel32.GetConsoleWindow()
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        if not ventana or not user32.IsWindowVisible(ventana):
            return                      # consola oculta: nadie podría pulsar nada
    except Exception:  # noqa: BLE001
        return
    try:
        import msvcrt
        import time

        print("\n" + mensaje, flush=True)
        limite = time.monotonic() + max(5, int(segundos))
        while time.monotonic() < limite:
            if msvcrt.kbhit():
                msvcrt.getwch()
                return
            time.sleep(0.2)
    except Exception:  # noqa: BLE001
        pass
