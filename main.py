"""Punto de entrada de ExtractorFanarts (aplicación de escritorio).

Opciones de línea de comandos:
    --selftest    comprueba el entorno (dependencias, adaptadores, carpetas) y sale
    --version     muestra la versión
"""
from __future__ import annotations

import sys
from pathlib import Path


def _preparar_rutas() -> None:
    """Permite ejecutar con las dependencias de ./vendor (dev y empaquetado)."""
    candidatos = []
    if getattr(sys, "frozen", False):  # ejecutable PyInstaller
        candidatos.append(Path(sys.executable).resolve().parent / "vendor")
        interior = getattr(sys, "_MEIPASS", None)
        if interior:
            candidatos.append(Path(interior) / "vendor")
    candidatos.append(Path(__file__).resolve().parent / "vendor")
    for ruta in candidatos:
        if ruta.is_dir() and str(ruta) not in sys.path:
            sys.path.insert(0, str(ruta))


_preparar_rutas()

from PySide6.QtWidgets import QApplication  # noqa: E402

from app import config  # noqa: E402
from app.controllers.main_controller import MainController  # noqa: E402
from app.icono import aplicar_icono, configurar_app_user_model_id  # noqa: E402
from app.logging_setup import setup_logging  # noqa: E402
from app.views.main_window import MainWindow  # noqa: E402


def selftest() -> int:
    """Comprueba que el empaquetado tiene todo lo necesario (sin abrir la ventana).

    Guarda el informe en `selftest.txt` junto al ejecutable (útil con --windowed,
    donde no hay consola) y también lo imprime si hay consola.
    """
    logger = setup_logging()
    lineas: list[str] = []

    def decir(texto: str = "") -> None:
        lineas.append(texto)
        try:
            print(texto)
        except Exception:  # noqa: BLE001
            pass

    # Windows: identificador propio (barra de tareas con NUESTRO icono)
    from app.icono import configurar_app_user_model_id
    decir(f"AppUserModelID: {'aplicado' if configurar_app_user_model_id() else 'no aplica'}")
    decir(f"{config.APP_NAME} {config.APP_VERSION}")
    decir(f"  python      : {sys.version.split()[0]}")
    decir(f"  congelado   : {bool(getattr(sys, 'frozen', False))}")
    decir(f"  log         : {config.LOG_DIR}")
    decir(f"  carpeta base: {config.DEFAULT_OUTPUT_DIR}")
    try:
        from app.icono import ruta_icono
        ruta = ruta_icono()
        decir(f"  icono       : {ruta if ruta else 'no encontrado (assets/icon.ico)'}")
    except Exception as exc:  # noqa: BLE001
        decir(f"  icono       : FALLO ({exc})")

    problemas = 0
    try:
        import PySide6  # noqa: F401
        from PySide6 import QtCore
        decir(f"  PySide6     : OK (Qt {QtCore.qVersion()})")
    except Exception as exc:  # noqa: BLE001
        decir(f"  PySide6     : FALLO ({exc})")
        problemas += 1
    for nombre in ("httpx", "PIL", "certifi"):
        try:
            __import__(nombre)
            decir(f"  {nombre:11} : OK")
        except Exception as exc:  # noqa: BLE001
            decir(f"  {nombre:11} : FALLO ({exc})")
            problemas += 1
    try:
        import curl_cffi  # noqa: F401
        decir("  curl_cffi   : OK (transporte con huella de navegador)")
    except Exception as exc:  # noqa: BLE001
        decir(f"  curl_cffi   : no disponible ({exc}) — opcional: Cloudflare")

    try:
        from app.services.adapters import BOORU_ADAPTERS, SOCIAL_ADAPTERS, WIKI_ADAPTERS
        decir(f"  adaptadores : {len(BOORU_ADAPTERS)} boorus, "
             f"{len(SOCIAL_ADAPTERS)} redes, {len(WIKI_ADAPTERS)} wikis")
    except Exception as exc:  # noqa: BLE001
        decir(f"  adaptadores : FALLO ({exc})")
        problemas += 1

    try:
        from app.services import enhance
        exe_ia = enhance._find_ai_exe()
        decir(f"  motor IA    : {'sí (' + exe_ia.name + ')' if exe_ia else 'no (se usará Lanczos)'}")
    except Exception as exc:  # noqa: BLE001
        decir(f"  motor IA    : FALLO ({exc})")
        problemas += 1

    try:
        config.DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        prueba = config.DEFAULT_OUTPUT_DIR / ".escritura_ok"
        prueba.write_text("ok", encoding="utf-8")
        prueba.unlink()
        decir("  escritura   : OK en la carpeta de salida")
    except Exception as exc:  # noqa: BLE001
        try:
            import tempfile as _tempfile
            with _tempfile.TemporaryDirectory() as temporal:
                (Path(temporal) / "prueba.txt").write_text("ok", encoding="utf-8")
            decir(f"  escritura   : aviso — la carpeta de salida no es escribible ({exc}); "
                  "el sistema de archivos sí lo permite")
        except Exception:  # noqa: BLE001
            decir(f"  escritura   : FALLO ({exc})")
            problemas += 1

    try:
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        aplicacion = QApplication.instance() or QApplication([])
        controlador = MainController()
        ventana = MainWindow(controlador)
        ventana.ajustar_a_pantalla()
        controlador.shutdown()
        del aplicacion
        decir("  interfaz    : OK (ventana construida en segundo plano)")
        decir(f"  controles   : {ventana.btn_buscar.text()} | "
              f"{ventana.btn_descargar.text()} | {ventana.btn_limpiar.text()} | "
              f"{ventana.chk_limite.text()}")
        pantalla = ventana.screen() or aplicacion.primaryScreen()
        if pantalla is not None:
            util = pantalla.availableGeometry()
            decir(f"  ventana     : {ventana.width()}x{ventana.height()} "
                  f"(pantalla útil {util.width()}x{util.height()})")
            cabe = (ventana.width() <= util.width()
                    and ventana.height() <= util.height())
            decir(f"  cabe en la pantalla: {'sí' if cabe else 'NO'}")
    except Exception as exc:  # noqa: BLE001
        decir(f"  interfaz    : FALLO ({exc})")
        problemas += 1

    decir("")
    decir(f"RESULTADO: {'OK' if problemas == 0 else str(problemas) + ' problema(s)'}")
    logger.info("selftest: %d problema(s)", problemas)

    # Informe a archivo (imprescindible en compilaciones sin consola)
    texto = "\n".join(lineas) + "\n"
    destinos = []
    if getattr(sys, "frozen", False):
        destinos.append(Path(sys.executable).resolve().parent / "selftest.txt")
    else:
        destinos.append(Path(__file__).resolve().parent / "selftest.txt")
    import tempfile as _tempfile2
    destinos.append(Path(_tempfile2.gettempdir()) / "ExtractorFanarts-selftest.txt")
    for destino in destinos:
        try:
            destino.write_text(texto, encoding="utf-8")
            break
        except OSError:
            continue

    return 0 if problemas == 0 else 1


def main() -> int:
    if "--version" in sys.argv:
        print(f"{config.APP_NAME} {config.APP_VERSION}")
        return 0
    if "--selftest" in sys.argv:
        return selftest()

    setup_logging()  # log a consola + archivo .log

    try:
        # Windows: identificador propio ANTES de crear la app, para que la barra de
        # tareas muestre NUESTRO icono (si no, muestra el de python.exe).
        configurar_app_user_model_id()

        app = QApplication(sys.argv)
        app.setApplicationName(config.APP_NAME)
        app.setStyle("Fusion")
        aplicar_icono(app)  # 🎨 icono de la app (ventana, barra de tareas y .exe)

        controller = MainController()
        window = MainWindow(controller)
        window.ajustar_a_pantalla()   # no salirse de la barra de tareas
        window.show()

        return app.exec()
    except Exception:
        import logging

        logging.getLogger("extractorfanarts").exception("error fatal al iniciar la aplicación")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
