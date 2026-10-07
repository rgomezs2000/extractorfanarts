"""Prueba end-to-end sin GUI visible: descarga real + sobreescritura.

Ejecuta dos pasadas de Descargar sobre Safebooru (3 resultados) y comprueba:
  - que se crean los archivos y sus sidecars JSON en la carpeta de salida,
  - que la segunda pasada SOBRESCRIBE los archivos existentes.

Uso:
    python scripts/e2e_test.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
_VENDOR = _ROOT / "vendor"
if _VENDOR.is_dir() and str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import app.config as config  # noqa: E402

config.DB_PATH = _ROOT / ".e2e_history.db"
config.MAX_RESULTS_PER_SOURCE = 3
config.MIN_REQUEST_INTERVAL = 0.5

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402
from app.controllers.main_controller import MainController  # noqa: E402
from app.logging_setup import setup_logging  # noqa: E402

LOG_DIR = _ROOT / ".e2e_logs"
setup_logging(LOG_DIR)

OUT = _ROOT / ".e2e_out"
SETTINGS = {
    "tipo": "Booru",
    "plataforma": "Safebooru",
    "tags": "hatsune_miku",
    "usuario": "", "keyword": "", "hashtag": "",
    "fandom": "", "character": "", "wiki_url": "",
    "carpeta": str(OUT / "nueva" / "subcarpeta"),  # NO existe: debe crearse sola
    "solo_liberado": False,
    "permitir_adulto": False,
    "mejorar": False,       # upscaling DESACTIVADO: debe convertir igualmente a .webp
    "modo_ia": False,
    "calidad_webp": 85,
    "limitar": True,        # límite de cantidad activo
    "cantidad": 2,          # descargar máximo 2
    "sidecar_json": False,  # NO generar archivos .json (por defecto)
}


def main() -> int:
    app = QApplication([])
    c = MainController()
    state = {"runs": 0, "mtime1": {}, "mtime2": {}}

    def on_finished(estado: str) -> None:
        state["runs"] += 1
        print(f"[e2e] pasada {state['runs']} terminada: {estado}", flush=True)
        if state["runs"] == 1:
            for p in OUT.rglob("*"):
                if p.is_file():
                    state["mtime1"][str(p)] = p.stat().st_mtime_ns
            c.descargar(SETTINGS)  # segunda pasada: debe sobreescribir
        else:
            for p in OUT.rglob("*"):
                if p.is_file():
                    state["mtime2"][str(p)] = p.stat().st_mtime_ns
            QTimer.singleShot(0, app.quit)

    c.finished.connect(on_finished)
    c.error.connect(lambda m: print(f"[e2e] ERROR: {m}", flush=True))
    c.descargar(SETTINGS)
    QTimer.singleShot(180_000, app.quit)  # vigilante

    app.exec()

    files1 = sorted(state["mtime1"])
    changed = [
        f for f in files1
        if f in state["mtime2"] and state["mtime2"][f] != state["mtime1"][f]
    ]
    mejoras: dict = {}
    for p in OUT.rglob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if "mejora" in data:
                mejoras[p.name] = data["mejora"]
        except Exception:
            pass
    imgs = [f for f in files1 if not f.endswith(".json")]
    todos_webp = bool(imgs) and all(f.endswith(".webp") for f in imgs)
    log_tail = []
    log_file = LOG_DIR / "app.log"
    if log_file.exists():
        lineas = log_file.read_text(encoding="utf-8").splitlines()
        log_tail = lineas[-5:]
    resumen = {
        "pasadas_completadas": state["runs"],
        "archivos_creados": files1,
        "sidecars_json": [f for f in files1 if f.endswith(".json")],
        "json_generados": len([f for f in files1 if f.endswith(".json")]),
        "solo_imagenes_webp": [f for f in files1 if f.endswith(".webp")],
        "sobrescritos_en_2da_pasada": len(changed),
        "todos_webp": todos_webp,
        "mejoras_aplicadas": mejoras,
        "log_existe": log_file.exists(),
        "log_tail": log_tail,
    }
    print(json.dumps(resumen, ensure_ascii=False, indent=2), flush=True)
    c.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
