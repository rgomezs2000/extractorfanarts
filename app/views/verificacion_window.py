"""Ventana para resolver **a mano** la comprobación que pide un sitio.

Algunos boorus (ATF Booru, `booru.allthefallen.moe`) no entregan datos a programas hasta
que se supera una comprobación. Imaginteca **no la resuelve por su cuenta** —eso sería
comportarse como un robot—: abre esta ventana con un **navegador incrustado**, la resuelve
la persona (igual que en su navegador de siempre) y, en cuanto está superada, la ventana
**se cierra sola** y la búsqueda o la descarga continúan.

El navegador usa un **perfil propio y persistente** (`~/.imaginteca/verificacion/`), así
que la comprobación se resuelve de vez en cuando y no en cada búsqueda. Las cookies y el
User-Agent de ese navegador se le pasan luego al cliente HTTP, porque el sitio los asocia
entre sí.
"""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtWebEngineCore import QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from .. import config
from ..services import verificacion

logger = logging.getLogger("imaginteca")

ESPERA_ANTES_DE_COMPROBAR = 1500     # ms entre reintentos de comprobación (página cargando)
MAX_COMPROBACIONES = 40              # ~60 s vigilando; después, se puede seguir a mano


class VentanaVerificacion(QDialog):
    """La persona resuelve la comprobación; al superarla, la ventana se cierra sola."""

    def __init__(self, dominio: str, url: str, parent=None):
        super().__init__(parent)
        self.dominio = dominio
        self.url = url or f"https://{dominio}/"
        self._cookies = ""
        self._agente = ""
        self._vueltas = 0
        self._recogidas: list[str] = []

        self.setWindowTitle(f"Comprobación de {dominio}")
        self.setModal(True)
        self.resize(920, 720)

        cabecera = QLabel(
            "<b>Este sitio pide una comprobación antes de entregar los datos.</b><br>"
            "Resuélvela aquí abajo, igual que en tu navegador. En cuanto esté superada, "
            "<b>esta ventana se cerrará sola</b> y continuará la búsqueda o la descarga."
        )
        cabecera.setWordWrap(True)
        self.lbl_estado = QLabel("Esperando a que el sitio cargue…")
        self.lbl_estado.setWordWrap(True)

        self.btn_abrir = QPushButton("🌐 Abrir en mi navegador")
        self.btn_abrir.setToolTip(
            "Si la ventana no te deja resolverla, ábrela en tu navegador de siempre "
            "(la cookie hay que resolverla igualmente aquí para que el programa la use)"
        )
        self.btn_abrir.clicked.connect(self._abrir_fuera)
        self.btn_comprobar = QPushButton("✅ Ya la resolví, comprobar")
        self.btn_comprobar.clicked.connect(self._comprobar_ahora)
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)

        botones = QHBoxLayout()
        botones.addWidget(self.btn_abrir)
        botones.addStretch(1)
        botones.addWidget(self.btn_comprobar)
        botones.addWidget(self.btn_cancelar)

        self.vista = QWebEngineView()
        self._perfil = self._preparar_perfil()
        pagina = self.vista.page()
        pagina.setBackgroundColor(Qt.white)
        try:
            pagina.profile().cookieStore().cookieAdded.connect(self._al_recibir_cookie)
        except Exception:  # noqa: BLE001
            pass
        pagina.loadFinished.connect(self._al_terminar_de_cargar)

        disposicion = QVBoxLayout(self)
        disposicion.addWidget(cabecera)
        disposicion.addWidget(self.lbl_estado)
        disposicion.addWidget(self.vista, 1)
        disposicion.addLayout(botones)

        logger.info("ventana de comprobación abierta para %s (%s)", dominio, self.url)
        self.vista.load(QUrl(self.url))

    # ------------------------------------------------------------------ perfil del navegador
    def _preparar_perfil(self) -> QWebEngineProfile:
        """Perfil propio y persistente: la comprobación se resuelve de vez en cuando."""
        carpeta = Path.home() / ".imaginteca" / "verificacion"
        try:
            carpeta.mkdir(parents=True, exist_ok=True)
        except OSError:
            carpeta = Path.home() / ".imaginteca"
        perfil = QWebEngineProfile("imaginteca-verificacion", self)
        try:
            perfil.setPersistentStoragePath(str(carpeta))
            perfil.setCachePath(str(carpeta / "cache"))
            perfil.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
            agente = getattr(config, "DEFAULT_BROWSER_UA", "") or perfil.httpUserAgent()
            perfil.setHttpUserAgent(agente)
            self._agente = agente
        except Exception as exc:  # noqa: BLE001
            logger.warning("no se pudo preparar el perfil del navegador: %s", exc)
        return perfil

    # ------------------------------------------------------------------ supervisión
    def _al_terminar_de_cargar(self, correcto: bool) -> None:
        if not correcto:
            self.lbl_estado.setText(
                "El sitio no cargó bien. Comprueba tu conexión o inténtalo otra vez.")
            return
        self.lbl_estado.setText("Cuando el sitio te deje pasar, la ventana se cerrará sola…")
        QTimer.singleShot(ESPERA_ANTES_DE_COMPROBAR, self._mirar_si_ya_paso)

    def _mirar_si_ya_paso(self) -> None:
        if self._vueltas >= MAX_COMPROBACIONES:
            self.lbl_estado.setText(
                "No se ha podido comprobar automáticamente. Si ya la resolviste, pulsa "
                "«Ya la resolví, comprobar».")
            return
        self._vueltas += 1
        try:
            self.vista.page().toHtml(self._revisar)
        except Exception:  # noqa: BLE001
            pass
        QTimer.singleShot(ESPERA_ANTES_DE_COMPROBAR, self._mirar_si_ya_paso)

    def _revisar(self, html: str) -> None:
        """Si la página ya no es la comprobación, la persona la ha superado."""
        if html and not verificacion.parece_reto(html):
            self.lbl_estado.setText("¡Comprobación superada! Cerrando y continuando…")
            self._recoger_cookies()

    def _comprobar_ahora(self) -> None:
        try:
            self.vista.page().toHtml(self._revisar_y_avisar)
        except Exception:  # noqa: BLE001
            self._avisar_no_superada()

    def _revisar_y_avisar(self, html: str) -> None:
        if html and not verificacion.parece_reto(html):
            self.lbl_estado.setText("¡Comprobación superada! Cerrando y continuando…")
            self._recoger_cookies()
        else:
            self._avisar_no_superada()

    def _avisar_no_superada(self) -> None:
        self.lbl_estado.setText(
            "La comprobación <b>todavía no está superada</b> (o se resolvió de forma "
            "incorrecta). Resuélvela en la ventana y vuelve a intentarlo.")

    # ------------------------------------------------------------------ cookies
    def _al_recibir_cookie(self, cookie) -> None:
        try:
            dominio = cookie.domain().lstrip(".").lower()
            if self.dominio.lower().endswith(dominio) or dominio.endswith(self.dominio.lower()):
                self._recogidas.append(f"{cookie.name()}={cookie.value()}")
        except Exception:  # noqa: BLE001
            pass

    def _recoger_cookies(self) -> None:
        almacen = None
        try:
            almacen = self.vista.page().profile().cookieStore()
        except Exception:  # noqa: BLE001
            pass
        if almacen is not None:
            try:
                almacen.loadAllCookies()
            except Exception:  # noqa: BLE001
                pass
        # Se da un instante a que lleguen las cookies antes de cerrar.
        QTimer.singleShot(600, self._cerrar_con_cookies)

    def _cerrar_con_cookies(self) -> None:
        self._cookies = "; ".join(dict.fromkeys(self._recogidas))
        if self._cookies:
            logger.info("comprobación superada en %s: %d cookies recogidas",
                        self.dominio, len(self._recogidas))
        else:
            logger.warning("comprobación superada en %s pero sin cookies visibles",
                           self.dominio)
        self.accept()

    # ------------------------------------------------------------------ utilidades
    def cookies(self) -> str:
        return self._cookies

    def agente(self) -> str:
        return self._agente

    def _abrir_fuera(self) -> None:
        """Abre la misma dirección en el navegador del sistema (por si acaso)."""
        from PySide6.QtCore import QUrl as _QUrl
        from PySide6.QtGui import QDesktopServices

        try:
            QDesktopServices.openUrl(_QUrl(self.url))
        except Exception:  # noqa: BLE001
            pass
