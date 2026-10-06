"""Punto de entrada de ExtractorFanarts (aplicación de escritorio)."""
import sys
from pathlib import Path

# Permite ejecutar con las dependencias instaladas en ./vendor (auto-contenido)
_VENDOR = Path(__file__).resolve().parent / "vendor"
if _VENDOR.is_dir() and str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

from PySide6.QtWidgets import QApplication

from app import config
from app.controllers.main_controller import MainController
from app.views.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setStyle("Fusion")

    controller = MainController()
    window = MainWindow(controller)
    window.resize(980, 760)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
