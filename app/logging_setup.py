"""Configuración de logging: un `.log` por DÍA + los mismos registros en la consola.

- **Un archivo nuevo cada día**: `app-AAAA-MM-DD.log` en la carpeta de logs. Los días
  anteriores se conservan (se borran solo los más viejos que `LOG_DIAS_A_CONSERVAR`).
  Si la app sigue abierta al cambiar el día, pasa sola al archivo del día nuevo.
- **La consola recibe EXACTAMENTE los mismos registros** que el archivo, así se puede
  ver en vivo lo que está pasando. En el `.exe` de Windows la consola la crea
  `app/consola.py`; ejecutando `python main.py` es tu propia terminal.
- **Cada arranque deja una cabecera de sesión** (fecha, versión, PID y archivo del
  día): el `.log` se lee por sesiones y la consola empieza limpia en cada apertura.

Carpeta del log (la primera que se pueda escribir):
  `~/.extractorfanarts/logs`  →  `<proyecto>/logs`  →  `<temporal>/ExtractorFanarts/logs`
"""
from __future__ import annotations

import logging
import os
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from . import config
from .consola import hay_consola

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


class HandlerPorDia(logging.FileHandler):
    """Escribe en `app-<fecha>.log` y cambia de archivo cuando cambia el día.

    Un fallo del archivo (carpeta bloqueada, disco lleno, sandbox…) **nunca** puede
    tumbar la app: si no se puede abrir o escribir, el manejador se desactiva y se
    avisa una sola vez por stderr.
    """

    def __init__(self, carpeta: Path, prefijo: str = "app"):
        self.carpeta = Path(carpeta)
        self.prefijo = prefijo
        self._dia = date.today()
        self._roto = False
        # Sin delay: se abre aquí, para detectar el fallo al configurar (no al primer log)
        super().__init__(self.ruta_del_dia(self._dia), encoding="utf-8")

    def ruta_del_dia(self, dia: date) -> Path:
        return self.carpeta / f"{self.prefijo}-{dia:%Y-%m-%d}.log"

    def _abrir_nuevo(self, dia: date) -> None:
        """Cierra el archivo actual y abre el del día indicado."""
        try:
            self.close()
        except Exception:  # noqa: BLE001
            pass
        self.baseFilename = str(self.ruta_del_dia(dia))
        self.stream = self._open()

    def emit(self, registro: logging.LogRecord) -> None:
        if self._roto:
            return
        try:
            hoy = date.today()
            if hoy != self._dia:      # la app sigue abierta y ha cambiado el día
                self._dia = hoy
                self._abrir_nuevo(hoy)
            super().emit(registro)
        except OSError:
            # No se puede escribir el .log: la app sigue funcionando, solo sin archivo
            self._roto = True
            self.handleError(registro)


def _carpeta_de_logs(log_dir: Path | None) -> Path | None:
    """Primera carpeta **escribible** para los registros (o None si no hay ninguna).

    Se comprueba de verdad (se crea y se escribe un archivo de prueba), porque en un
    entorno restringido la carpeta puede existir y aun así no dejar escribir; en ese
    caso se usa la carpeta `logs` **junto a la aplicación** (que sí es escribible) y,
    como último recurso, la temporal del sistema.
    """
    if getattr(sys, "frozen", False):
        junto_a_la_app = Path(sys.executable).resolve().parent / "logs"
    else:
        junto_a_la_app = Path(__file__).resolve().parents[1] / "logs"
    candidatas = [
        log_dir or config.LOG_DIR,
        junto_a_la_app,
        Path(tempfile.gettempdir()) / config.APP_NAME / "logs",
    ]
    for candidata in candidatas:
        try:
            candidata.mkdir(parents=True, exist_ok=True)
            prueba = candidata / ".escritura_ok"
            prueba.write_text("ok", encoding="utf-8")
            prueba.unlink()
            return candidata
        except OSError:
            continue
    return None


def _limpiar_antiguos(carpeta: Path, prefijo: str = "app") -> None:
    """Borra los .log de más de `LOG_DIAS_A_CONSERVAR` días (0 = no borrar nunca)."""
    try:
        dias = int(getattr(config, "LOG_DIAS_A_CONSERVAR", 30) or 0)
    except (TypeError, ValueError):
        return
    if dias <= 0:
        return
    limite = datetime.now() - timedelta(days=dias)
    for archivo in carpeta.glob(f"{prefijo}-*.log"):
        try:
            if datetime.fromtimestamp(archivo.stat().st_mtime) < limite:
                archivo.unlink()
        except OSError:
            continue


def setup_logging(log_dir: Path | None = None) -> logging.Logger:
    logger = logging.getLogger("extractorfanarts")
    if logger.handlers:
        return logger  # ya configurado

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(_FORMAT)

    # Consola: los MISMOS registros que el archivo (en el .exe la crea app/consola.py)
    if hay_consola():
        consola = logging.StreamHandler()
        consola.setFormatter(fmt)
        logger.addHandler(consola)

    # Archivo del día
    carpeta = _carpeta_de_logs(log_dir)
    if carpeta is None:
        logger.warning("no se pudo crear ninguna carpeta de registros")
        return logger

    try:
        archivo = HandlerPorDia(carpeta)
        archivo.setFormatter(fmt)
        logger.addHandler(archivo)
    except OSError as exc:
        # La carpeta pasa la prueba de escritura pero el archivo no se puede abrir
        # (otra instancia con bloqueo exclusivo, permisos raros…): la app sigue sin log
        logger.warning("no se pudo crear el archivo de log en %s: %s", carpeta, exc)
        return logger

    _limpiar_antiguos(carpeta)
    # Cabecera de sesión: así el .log se lee por sesiones y la consola empieza limpia
    logger.info("=" * 68)
    logger.info("%s %s — sesión iniciada (%s) · PID %s", config.APP_NAME, config.APP_VERSION,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), os.getpid())
    logger.info("registro del día: %s", archivo.ruta_del_dia(date.today()))
    logger.info("=" * 68)
    logger.info("consola de registros: %s", "sí" if hay_consola() else "no disponible")
    return logger
