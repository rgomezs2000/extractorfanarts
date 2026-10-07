"""Configuración de logging: archivo .log (rotativo) + consola.

Errores detallados (con traceback) se escriben en:
  ~/.extractorfanarts/logs/app.log   (por defecto)
Si esa ruta no es escribible (p. ej. sandbox), se usa <proyecto>/logs/app.log.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from . import config

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(log_dir: Path | None = None) -> logging.Logger:
    logger = logging.getLogger("extractorfanarts")
    if logger.handlers:
        return logger  # ya configurado

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(_FORMAT)

    # Consola (stderr)
    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    logger.addHandler(stream)

    # Archivo .log con fallback: carpeta de usuario → junto a la app → temporal
    import tempfile

    file_path: Path | None = None
    candidatos = [
        log_dir or config.LOG_DIR,
        Path(__file__).resolve().parents[1] / "logs",
        Path(tempfile.gettempdir()) / "ExtractorFanarts" / "logs",
    ]
    for candidate in candidatos:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            file_path = candidate / "app.log"
            break
        except OSError:
            continue

    if file_path is not None:
        try:
            fh = RotatingFileHandler(
                file_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
            )
            fh.setFormatter(fmt)
            logger.addHandler(fh)
            logger.info("log iniciado en %s", file_path)
        except OSError:
            logger.warning("no se pudo crear el archivo de log en %s", file_path)

    return logger
