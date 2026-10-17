"""Ventana del menú Ayuda: «Estado de las redes sociales y plataformas».

Comprueba cada plataforma (¿responde?, ¿en qué estado?) y lo enseña en una tabla. Además
deja el resultado a mano de las **notificaciones**: si alguna plataforma deja de responder,
se avisa (en la ventana o, si está minimizada, en el sistema).
"""
from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .. import estado_servicios

logger = logging.getLogger("imaginteca")

Columnas = ("Tipo", "Plataforma", "Estado", "Latencia", "Detalle")


class _Senales(QObject):
    progreso = Signal(int, int, object)      # (hechas, total, EstadoServicio)
    terminado = Signal(list)                 # [EstadoServicio]


class _Trabajo(QRunnable):
    """Comprueba las plataformas fuera del hilo de la ventana."""

    def __init__(self, segundos: float):
        super().__init__()
        self.segundos = segundos
        self.senales = _Senales()

    def run(self) -> None:  # noqa: D401
        try:
            resultados = estado_servicios.comprobar(
                self.segundos,
                progreso=self._avisar_progreso,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("fallo comprobando el estado de los servicios")
            resultados = []
            logger.error("estado de servicios: %s", exc)
        try:
            self.senales.terminado.emit(resultados)
        except Exception:      # noqa: BLE001
            pass                 # la ventana se cerró mientras tanto: no pasa nada

    def _avisar_progreso(self, hechas: int, total: int, estado) -> None:
        """Emite el avance sin romper nada si la ventana ya se cerró."""
        try:
            self.senales.progreso.emit(hechas, total, estado)
        except Exception:      # noqa: BLE001
            pass


class VentanaEstadoServicios(QDialog):
    """Tabla con el estado de cada plataforma y un botón para volver a comprobar."""

    def __init__(self, notificador=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Estado de las redes sociales y plataformas")
        self.resize(760, 520)
        self._notificador = notificador
        self._resultados: list = []
        self._pool = QThreadPool.globalInstance()

        self.lbl_resumen = QLabel("Pulsa «Comprobar ahora» para saber cómo están.")
        self.lbl_resumen.setWordWrap(True)
        self._trabajo = None
        self._cerrada = False

        self.tabla = QTableWidget(0, len(Columnas))
        self.tabla.setHorizontalHeaderLabels(Columnas)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        cabecera.setSectionResizeMode(4, QHeaderView.Stretch)
        self.tabla.doubleClicked.connect(self._abrir_pagina)

        self.btn_comprobar = QPushButton("🔄 Comprobar ahora")
        self.btn_comprobar.clicked.connect(self.comprobar)
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.clicked.connect(self.accept)

        botones = QHBoxLayout()
        botones.addWidget(self.btn_comprobar)
        botones.addStretch(1)
        botones.addWidget(self.btn_cerrar)

        disposicion = QVBoxLayout(self)
        disposicion.addWidget(self.lbl_resumen)
        disposicion.addWidget(self.tabla, 1)
        disposicion.addLayout(botones)

        self._preparar_tabla()
        self.comprobar()          # se comprueba nada más abrirla

    # ------------------------------------------------------------------ tabla
    def _preparar_tabla(self) -> None:
        lista = estado_servicios.plataformas()
        self.tabla.setRowCount(len(lista))
        for fila, (nombre, tipo, _url, pagina) in enumerate(lista):
            self._poner(fila, 0, tipo)
            self._poner(fila, 1, nombre)
            self._poner(fila, 2, "comprobando…")
            self._poner(fila, 3, "—")
            self._poner(fila, 4, f"estado: {pagina}" if pagina else "esperando…")
            elemento = self.tabla.item(fila, 1)
            if elemento is not None:
                elemento.setData(Qt.UserRole, pagina)

    def _poner(self, fila: int, columna: int, texto: str, color: str = "") -> None:
        elemento = self.tabla.item(fila, columna)
        if elemento is None:
            elemento = QTableWidgetItem()
            self.tabla.setItem(fila, columna, elemento)
        elemento.setText(texto)
        if color:
            elemento.setForeground(QColor(color))

    def _fila_de(self, nombre: str) -> int:
        for fila in range(self.tabla.rowCount()):
            elemento = self.tabla.item(fila, 1)
            if elemento is not None and elemento.text() == nombre:
                return fila
        return -1

    def _pintar(self, estado) -> None:
        fila = self._fila_de(estado.nombre)
        if fila < 0:
            return
        color = estado_servicios.COLORES.get(estado.estado, "#6d6d6d")
        self._poner(fila, 2, estado.estado, color)
        latencia = f"{estado.latencia * 1000:.0f} ms" if estado.latencia else "—"
        self._poner(fila, 3, latencia)
        detalle = estado.detalle or "—"
        if estado.pagina:
            detalle += f"  ·  doble clic: {estado.pagina}"
        self._poner(fila, 4, detalle)
        negrita = QFont(self.font())
        negrita.setBold(not estado.operativo)
        self.tabla.item(fila, 2).setFont(negrita)

    # ------------------------------------------------------------------ comprobación
    def comprobar(self) -> None:
        self.btn_comprobar.setEnabled(False)
        self.lbl_resumen.setText("Comprobando… (unas cuantas peticiones, con calma)")
        self._preparar_tabla()
        trabajo = _Trabajo(segundos=8.0)
        trabajo.senales.progreso.connect(self._al_progresar)
        trabajo.senales.terminado.connect(self._al_terminar)
        self._trabajo = trabajo          # se guarda: si no, Qt lo recicla y falla
        self._pool.start(trabajo)

    def _al_progresar(self, hechas: int, total: int, estado) -> None:
        if self._cerrada:
            return
        self._pintar(estado)
        self.lbl_resumen.setText(f"Comprobando… {hechas} de {total}")

    def _al_terminar(self, resultados: list) -> None:
        if self._cerrada:
            return
        self._resultados = list(resultados)
        self.btn_comprobar.setEnabled(True)
        self.lbl_resumen.setText(estado_servicios.resumen(self._resultados).capitalize() + ".")
        # Se avisa de las que están mal (la ventana decide si fuera del sistema o no).
        if self._notificador is not None and self._resultados:
            caidas = [r for r in self._resultados if not r.operativo]
            if caidas:
                self._notificador.avisar(
                    "servicio",
                    "Servicios con problemas",
                    estado_servicios.resumen(self._resultados),
                    nivel="aviso")
            else:
                self._notificador.avisar(
                    "servicio",
                    "Servicios operativos",
                    f"Las {len(self._resultados)} plataformas responden.",
                    nivel="exito")

    def _abrir_pagina(self) -> None:
        fila = self.tabla.currentRow()
        if fila < 0:
            return
        elemento = self.tabla.item(fila, 1)
        if elemento is None:
            return
        rol = elemento.data(Qt.UserRole) if elemento is not None else None
        if rol:
            QDesktopServices.openUrl(QUrl(str(rol)))

    def closeEvent(self, evento):  # noqa: N802
        """Al cerrar, se dejan de atender los avisos del hilo de comprobación."""
        self._cerrada = True
        try:
            if self._trabajo is not None:
                self._trabajo.senales.progreso.disconnect()
                self._trabajo.senales.terminado.disconnect()
        except Exception:      # noqa: BLE001
            pass
        super().closeEvent(evento)

    def reject(self) -> None:  # noqa: D401
        self._cerrada = True
        super().reject()
