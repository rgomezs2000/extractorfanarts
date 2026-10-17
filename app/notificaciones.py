"""Sistema de notificaciones de Imaginteca.

Reúne en un solo sitio los avisos importantes del programa:

  · **Actualizaciones**: cuando hay una versión nueva.
  · **Búsquedas y descargas**: completadas (o cuando no devolvieron nada).
  · **Errores**: lo que falla de verdad.
  · **Estado de los servicios** (redes sociales y plataformas): si están operativos.

Se cuentan y se muestran de tres maneras:

  1. En la **ventana**: un botón con el número sin leer y una lista de avisos.
  2. Cuando la ventana está **minimizada** (o escondida): como **notificación del
     sistema** (Windows, macOS y Linux) y en la **insignia del icono** de la barra de
     tareas / Dock, con el número de avisos sin leer.
  3. En el **registro** (consola y archivo .log), siempre.

El icono que se usa es **el mismo de la aplicación** (`app/icono.py`), así que la bandeja,
la insignia y la barra de tareas hablan del mismo programa.
"""
from __future__ import annotations

import logging
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QSystemTrayIcon

from . import config, icono

logger = logging.getLogger("imaginteca")

NIVELES = ("info", "exito", "aviso", "error")
ICONOS_TRAY = {
    "info": QSystemTrayIcon.MessageIcon.Information,
    "exito": QSystemTrayIcon.MessageIcon.Information,
    "aviso": QSystemTrayIcon.MessageIcon.Warning,
    "error": QSystemTrayIcon.MessageIcon.Critical,
}


@dataclass
class Aviso:
    """Un aviso concreto, tal como se guarda y se muestra."""

    categoria: str          # actualización / búsqueda / descarga / error / servicio
    titulo: str
    mensaje: str = ""
    nivel: str = "info"     # info / exito / aviso / error
    momento: datetime = field(default_factory=datetime.now)
    leido: bool = False

    def como_linea(self) -> str:
        hora = self.momento.strftime("%H:%M")
        texto = f"{self.titulo}"
        if self.mensaje:
            texto += f" — {self.mensaje}"
        return f"{hora} · {texto}"

    def __str__(self) -> str:
        return self.como_linea()


class Notificador(QObject):
    """Cuenta y muestra los avisos (ventana, sistema y barra de tareas)."""

    cambio = Signal()        # cambió la lista: la ventana refresca el botón y el panel
    aviso_nuevo = Signal(object)   # se emitió un aviso nuevo (para la barra de estado)

    MAXIMOS = 200

    def __init__(self, parent=None):
        super().__init__(parent)
        self._avisos: list[Aviso] = []
        self._ventana = None
        self._tray: QSystemTrayIcon | None = None
        self._icono = self._cargar_icono()
        self._bandeja_lista = False

    # ------------------------------------------------------------------ preparación
    def _cargar_icono(self) -> QIcon:
        ruta = icono.ruta_icono()
        if ruta is not None:
            icono_qt = QIcon(str(ruta))
            if not icono_qt.isNull():
                return icono_qt
        return QIcon()

    def enlazar_ventana(self, ventana) -> None:
        """La ventana principal: sirve para saber si está minimizada y para enfocarla."""
        self._ventana = ventana
        self._preparar_bandeja()

    def _preparar_bandeja(self) -> None:
        """Icono en la bandeja del sistema (con el icono de la aplicación)."""
        if self._tray is not None:
            return
        try:
            if not QSystemTrayIcon.isSystemTrayAvailable():
                logger.info("este sistema no ofrece bandeja: solo se notificará en la ventana")
                return
            self._tray = QSystemTrayIcon(self._icono, self)
            self._tray.setToolTip(f"{config.APP_NAME} — sin avisos")
            self._tray.activated.connect(self._al_pulsar_bandeja)
            self._tray.show()
            self._bandeja_lista = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("no se pudo preparar la bandeja del sistema: %s", exc)

    def _al_pulsar_bandeja(self, motivo) -> None:
        if motivo in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self.mostrar_ventana()

    def mostrar_ventana(self) -> None:
        """Trae la ventana al frente (al pulsar la notificación o el icono)."""
        if self._ventana is None:
            return
        try:
            self._ventana.showNormal()
            self._ventana.raise_()
            self._ventana.activateWindow()
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ consulta
    def avisos(self) -> list[Aviso]:
        return list(self._avisos)

    def sin_leer(self) -> int:
        return sum(1 for aviso in self._avisos if not aviso.leido)

    def marcar_leidos(self) -> None:
        for aviso in self._avisos:
            aviso.leido = True
        self._actualizar_insignia()
        self.cambio.emit()

    def limpiar(self) -> None:
        self._avisos.clear()
        self._actualizar_insignia()
        self.cambio.emit()

    # ------------------------------------------------------------------ avisar
    def avisar(self, categoria: str, titulo: str, mensaje: str = "",
               nivel: str = "info") -> Aviso:
        """Registra un aviso y lo muestra (en la ventana y, si está minimizada, fuera)."""
        if not getattr(config, "NOTIFICACIONES", True):
            logger.info("aviso (silenciado) [%s] %s — %s", categoria, titulo, mensaje)
            return Aviso(categoria, titulo, mensaje, nivel)

        aviso = Aviso(categoria=categoria, titulo=titulo, mensaje=mensaje,
                      nivel=nivel if nivel in NIVELES else "info")
        self._avisos.append(aviso)
        if len(self._avisos) > self.MAXIMOS:
            del self._avisos[:len(self._avisos) - self.MAXIMOS]

        logger.info("aviso [%s] %s%s", categoria, titulo, f" — {mensaje}" if mensaje else "")
        self.aviso_nuevo.emit(aviso)
        self._actualizar_insignia()
        self._refrescar_bandeja()
        if self._fuera_de_la_vista():
            self._notificar_en_el_sistema(aviso)
        self.cambio.emit()
        return aviso

    # ------------------------------------------------------------------ helpers
    def _fuera_de_la_vista(self) -> bool:
        """¿La ventana está minimizada o escondida? (condición para avisar fuera)."""
        if self._ventana is None:
            return True
        try:
            return bool(self._ventana.isMinimized()) or not self._ventana.isVisible()
        except Exception:  # noqa: BLE001
            return False

    def _notificar_en_el_sistema(self, aviso: Aviso) -> None:
        if self._tray is None:
            return
        try:
            self._tray.showMessage(
                f"{config.APP_NAME} · {aviso.categoria}",
                aviso.como_linea(),
                ICONOS_TRAY.get(aviso.nivel, QSystemTrayIcon.MessageIcon.Information),
                8000,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("no se pudo mostrar la notificación del sistema: %s", exc)

    def _refrescar_bandeja(self) -> None:
        if self._tray is None:
            return
        try:
            sin_leer = self.sin_leer()
            total = len(self._avisos)
            detalle = f"{sin_leer} sin leer" if sin_leer else "sin avisos nuevos"
            self._tray.setToolTip(f"{config.APP_NAME} — {detalle} ({total} en total)")
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ insignia
    def _actualizar_insignia(self) -> None:
        """Número de avisos sin leer en el icono (barra de tareas / Dock)."""
        numero = self.sin_leer()
        # Qt lo soporta en macOS (Dock) y, donde el escritorio lo permita, en otros.
        try:
            QGuiApplication.setBadgeNumber(numero)
        except Exception:  # noqa: BLE001
            pass
        if sys.platform == "win32":
            self._insignia_windows(numero)
        elif self._ventana is not None:
            # Reserva para el resto: el número, en el título de la ventana.
            try:
                base = f"{config.APP_NAME} — tu colección de imágenes"
                self._ventana.setWindowTitle(f"({numero}) {base}" if numero else base)
            except Exception:  # noqa: BLE001
                pass

    def _insignia_windows(self, numero: int) -> None:
        """Dibuja un círculo con el número y lo pone como insignia de la barra (Windows)."""
        if self._ventana is None:
            return
        try:
            import ctypes

            hwnd = ctypes.c_void_p(int(self._ventana.winId()))
            user32 = ctypes.windll.user32
            if numero <= 0:
                user32.SetOverlayIcon(hwnd, None, None)
                return
            ruta = self._archivo_insignia(numero)
            if ruta is None:
                return
            IMAGE_ICON, LR_LOADFROMFILE, LR_DEFAULTSIZE = 1, 0x00000010, 0x00000040
            hicon = user32.LoadImageW(None, str(ruta), IMAGE_ICON, 32, 32,
                                      LR_LOADFROMFILE | LR_DEFAULTSIZE)
            if not hicon:
                return
            user32.SetOverlayIcon(hwnd, ctypes.c_void_p(hicon),
                                  ctypes.c_wchar_p(f"{numero} avisos sin leer"))
            if getattr(self, "_hicon", None):
                try:
                    user32.DestroyIcon(ctypes.c_void_p(self._hicon))
                except Exception:  # noqa: BLE001
                    pass
            self._hicon = hicon
        except Exception as exc:  # noqa: BLE001
            logger.debug("no se pudo poner la insignia en la barra de tareas: %s", exc)

    def _archivo_insignia(self, numero: int) -> Path | None:
        """Crea (y cachea) el .ico de la insignia con el número dentro."""
        try:
            from PIL import Image, ImageDraw, ImageFont

            carpeta = Path(tempfile.gettempdir()) / "imaginteca-insignias"
            carpeta.mkdir(parents=True, exist_ok=True)
            ruta = carpeta / f"insignia-{numero}.ico"
            if ruta.is_file():
                return ruta
            lado = 128
            imagen = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
            dibujo = ImageDraw.Draw(imagen)
            dibujo.ellipse([4, 4, lado - 4, lado - 4], fill=(214, 48, 49, 255),
                           outline=(255, 255, 255, 255), width=6)
            texto = "99+" if numero > 99 else str(numero)
            fuente = None
            for nombre in ("arialbd.ttf", "seguisb.ttf", "DejaVuSans-Bold.ttf"):
                for carpeta_fuente in (r"C:\Windows\Fonts",
                                       "/usr/share/fonts/truetype/dejavu",
                                       "/System/Library/Fonts"):
                    candidata = Path(carpeta_fuente) / nombre
                    if candidata.is_file():
                        try:
                            fuente = ImageFont.truetype(str(candidata),
                                                        int(lado * (0.52 if len(texto) <= 2 else 0.4)))
                            break
                        except OSError:
                            continue
                if fuente:
                    break
            fuente = fuente or ImageFont.load_default()
            caja = dibujo.textbbox((0, 0), texto, font=fuente)
            dibujo.text(((lado - (caja[2] - caja[0])) / 2 - caja[0],
                         (lado - (caja[3] - caja[1])) / 2 - caja[1]), texto,
                        font=fuente, fill=(255, 255, 255, 255))
            imagen.save(ruta, sizes=[(16, 16), (32, 32), (48, 48)])
            return ruta
        except Exception as exc:  # noqa: BLE001
            logger.debug("no se pudo dibujar la insignia: %s", exc)
            return None
