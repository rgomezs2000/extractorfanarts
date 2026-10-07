"""Galería tipo carrusel y visor ampliado (lightbox) para la ventana principal.

- `GaleriaWidget`: carrusel alineado en rejilla (contador arriba, imagen grande en
  el centro con flechas ◀ ▶ y tira de miniaturas debajo, exactamente del mismo
  ancho que la imagen). Muestra **una casilla por cada resultado** de la búsqueda
  o descarga y va rellenando las miniaturas conforme llegan.
- `Lightbox`: superposición **dentro de la propia ventana** (no abre otra ventana),
  estilo *fancybox*: fondo oscurecido, zoom con la rueda, arrastre para mover,
  flechas ‹ ›, doble clic para ajustar y Esc para cerrar.

Las miniaturas que no se hayan cargado todavía se piden **bajo demanda** cuando el
usuario llega a ellas (así se pueden mostrar 50 resultados sin lanzar 50 peticiones
de golpe, respetando el ritmo de peticiones del cliente HTTP).
"""
from __future__ import annotations

import logging

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QWidget,
)

logger = logging.getLogger("extractorfanarts")

MENSAJE_INICIAL = "🖼️ (aquí se mostrará una galería con las imágenes encontradas)"
MENSAJE_BUSCANDO = "⏳ (buscando imágenes…)"
MENSAJE_VACIO = "⚠️ (no se pudieron cargar imágenes de esta búsqueda)"
MENSAJE_CARGANDO = "⏳ (cargando la imagen {i} de {n}…)"
MENSAJE_FALLIDA = "⚠️ (no se pudo cargar la imagen {i} de {n})"
MENSAJE_SIN_URL = "🚫 (esta obra no tiene miniatura disponible)"

LADO_MINIATURA = 64


def _placeholder(numero: int) -> QPixmap:
    """Miniatura gris con el número, para las casillas aún sin cargar."""
    lienzo = QPixmap(LADO_MINIATURA, LADO_MINIATURA)
    lienzo.fill(QColor(232, 232, 232))
    pintor = QPainter(lienzo)
    pintor.setPen(QPen(QColor(190, 190, 190)))
    pintor.drawRect(0, 0, LADO_MINIATURA - 1, LADO_MINIATURA - 1)
    pintor.setPen(QColor(150, 150, 150))
    fuente = pintor.font()
    fuente.setPointSize(10)
    pintor.setFont(fuente)
    pintor.drawText(lienzo.rect(), Qt.AlignCenter, str(numero))
    pintor.end()
    return lienzo


class VisorImagen(QLabel):
    """Imagen grande del carrusel; al pulsarla se abre el visor ampliado."""

    pulsada = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(220, 140)   # pequeño a propósito: la ventana puede encogerse
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("border: 1px solid #999; background: #f5f5f5; color: #666;")
        self._original: QPixmap | None = None

    def poner(self, pixmap: QPixmap | None) -> None:
        self._original = pixmap
        if pixmap is None or pixmap.isNull():
            return
        self.setPixmap(
            pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def texto(self, mensaje: str) -> None:
        self._original = None
        self.setPixmap(QPixmap())      # quita la imagen anterior
        self.setText(mensaje)

    def original(self) -> QPixmap | None:
        return self._original

    def resizeEvent(self, evento):  # noqa: N802
        super().resizeEvent(evento)
        if self._original is not None and not self._original.isNull():
            self.setPixmap(self._original.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def mouseReleaseEvent(self, evento):  # noqa: N802
        if evento.button() == Qt.LeftButton and self._original is not None:
            self.pulsada.emit()
        super().mouseReleaseEvent(evento)


class Lightbox(QWidget):
    """Visor ampliado superpuesto a la ventana (estilo fancybox)."""

    def __init__(self, galeria: "GaleriaWidget"):
        super().__init__(galeria.window())
        self._galeria = galeria
        self.setObjectName("lightbox")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setVisible(False)
        self._indice = 0
        self._zoom = 1.0
        self._desplazamiento = QPoint(0, 0)
        self._arrastrando = False
        self._ultimo = QPoint()
        galeria.imagen_lista.connect(self._al_llegar_imagen)

    # ------------------------------------------------------------------ API
    def abrir(self, indice: int = 0) -> None:
        if self._galeria.total() <= 0:
            return
        self._indice = max(0, min(indice, self._galeria.total() - 1))
        self._zoom = 1.0
        self._desplazamiento = QPoint(0, 0)
        self._galeria.pedir_imagen_de(self._indice)
        self.setGeometry(self.window().rect())
        self.show()
        self.raise_()
        self.setFocus(Qt.OtherFocusReason)
        self.update()

    def cerrar(self) -> None:
        self.setVisible(False)
        self._arrastrando = False

    def ir(self, indice: int) -> None:
        total = self._galeria.total()
        if total <= 0:
            return
        self._indice = indice % total
        self._zoom = 1.0
        self._desplazamiento = QPoint(0, 0)
        self._galeria.pedir_imagen_de(self._indice)
        self.update()

    def siguiente(self) -> None:
        self.ir(self._indice + 1)

    def anterior(self) -> None:
        self.ir(self._indice - 1)

    # ------------------------------------------------------------------ geometría
    def _pixmap(self) -> QPixmap | None:
        return self._galeria.pixmap(self._indice)

    def _objetivo(self) -> tuple[int, int] | None:
        pixmap = self._pixmap()
        if pixmap is None or pixmap.isNull():
            return None
        disponible = QSize(max(80, int(self.width() * 0.9)),
                           max(80, int(self.height() * 0.82)))
        ajustada = pixmap.size().scaled(disponible, Qt.KeepAspectRatio)
        return (max(16, int(ajustada.width() * self._zoom)),
                max(16, int(ajustada.height() * self._zoom)))

    def _zona_imagen(self):
        objetivo = self._objetivo()
        if objetivo is None:
            return None
        ancho, alto = objetivo
        return ((self.width() - ancho) // 2 + self._desplazamiento.x(),
                (self.height() - alto) // 2 + self._desplazamiento.y(),
                ancho, alto)

    # ------------------------------------------------------------------ pintura
    def paintEvent(self, evento):  # noqa: N802
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.Antialiasing, True)
        pintor.setRenderHint(QPainter.SmoothPixmapTransform, True)
        pintor.fillRect(self.rect(), QColor(0, 0, 0, 215))

        total = max(1, self._galeria.total())
        zona = self._zona_imagen()
        if zona is not None:
            x, y, ancho, alto = zona
            pintor.setPen(QColor(245, 245, 245, 220))
            pintor.drawRect(x - 4, y - 4, ancho + 7, alto + 7)
            pintor.drawPixmap(x, y, ancho, alto, self._pixmap())
        else:
            pintor.setPen(QColor(235, 235, 235, 220))
            fuente = pintor.font()
            fuente.setPointSize(fuente.pointSize() + 2)
            pintor.setFont(fuente)
            pintor.drawText(self.rect(), Qt.AlignCenter,
                            MENSAJE_CARGANDO.format(i=self._indice + 1, n=total))

        pintor.setPen(QColor(255, 255, 255, 235))
        fuente = pintor.font()
        fuente.setPointSize(max(10, fuente.pointSize()))
        fuente.setBold(True)
        pintor.setFont(fuente)
        pintor.drawText(0, 26, self.width(), 30, Qt.AlignHCenter | Qt.AlignVCenter,
                        f"{self._indice + 1} / {total}"
                        f"   ·   zoom {int(self._zoom * 100)} %")
        fuente.setBold(False)
        pintor.setFont(fuente)
        pintor.setPen(QColor(230, 230, 230, 190))
        pintor.drawText(0, self.height() - 44, self.width(), 30,
                        Qt.AlignHCenter | Qt.AlignVCenter,
                        "rueda: zoom · arrastra: mover · doble clic: ajustar · "
                        "← →: cambiar · Esc o clic fuera: cerrar")

        if total > 1:
            pintor.setPen(QColor(255, 255, 255, 200))
            fuente.setPointSize(fuente.pointSize() + 12)
            pintor.setFont(fuente)
            pintor.drawText(0, 0, 70, self.height(), Qt.AlignCenter, "‹")
            pintor.drawText(self.width() - 70, 0, 70, self.height(), Qt.AlignCenter, "›")

    # ------------------------------------------------------------------ eventos
    def resizeEvent(self, evento):  # noqa: N802
        super().resizeEvent(evento)
        self.setGeometry(self.window().rect())

    def _al_llegar_imagen(self, indice: int) -> None:
        if indice == self._indice:
            self.update()

    def wheelEvent(self, evento):  # noqa: N802
        pasos = evento.angleDelta().y() / 120.0
        if not pasos:
            return
        factor = 1.15 if pasos > 0 else 1 / 1.15
        self._zoom = max(1.0, min(8.0, self._zoom * factor))
        if self._zoom <= 1.0:
            self._desplazamiento = QPoint(0, 0)
        self.update()

    def mousePressEvent(self, evento):  # noqa: N802
        if evento.button() != Qt.LeftButton:
            return
        x = evento.position().x()
        if self._galeria.total() > 1 and x < 70:
            self.anterior()
            return
        if self._galeria.total() > 1 and x > self.width() - 70:
            self.siguiente()
            return
        zona = self._zona_imagen()
        dentro = False
        if zona is not None:
            ix, iy, ancho, alto = zona
            dentro = ix <= x <= ix + ancho and iy <= evento.position().y() <= iy + alto
        if not dentro:
            self.cerrar()          # clic fuera de la imagen: cerrar (estilo fancybox)
            return
        self._arrastrando = True
        self._ultimo = evento.position().toPoint()
        self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, evento):  # noqa: N802
        if not self._arrastrando:
            return
        posicion = evento.position().toPoint()
        self._desplazamiento += posicion - self._ultimo
        self._ultimo = posicion
        self.update()

    def mouseReleaseEvent(self, evento):  # noqa: N802
        self._arrastrando = False
        self.setCursor(Qt.PointingHandCursor)

    def mouseDoubleClickEvent(self, evento):  # noqa: N802
        self._zoom = 1.0
        self._desplazamiento = QPoint(0, 0)
        self.update()

    def keyPressEvent(self, evento):  # noqa: N802
        tecla = evento.key()
        if tecla == Qt.Key_Escape:
            self.cerrar()
        elif tecla in (Qt.Key_Right, Qt.Key_Space):
            self.siguiente()
        elif tecla == Qt.Key_Left:
            self.anterior()
        elif tecla in (Qt.Key_Plus, Qt.Key_Equal):
            self._zoom = min(8.0, self._zoom * 1.2)
            self.update()
        elif tecla == Qt.Key_Minus:
            self._zoom = max(1.0, self._zoom / 1.2)
            self.update()
        elif tecla == Qt.Key_0:
            self._zoom = 1.0
            self._desplazamiento = QPoint(0, 0)
            self.update()
        else:
            super().keyPressEvent(evento)


class GaleriaWidget(QWidget):
    """Carrusel alineado: contador, imagen grande con flechas y tira de miniaturas."""

    pedir_lightbox = Signal(int)   # el usuario quiere verla ampliada
    pedir_imagen = Signal(int)     # (posición 1..n) cargar bajo demanda
    imagen_lista = Signal(int)     # (índice 0..n-1) ya hay imagen en esa casilla

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._pixmaps: list[QPixmap | None] = []
        self._fallidas: set[int] = set()
        self._indice = 0
        self._sincronizando = False

        # Rejilla: el contador ocupa toda la fila y la tira queda exactamente
        # debajo de la imagen (misma columna), así no hay desalineación.
        cuadricula = QGridLayout(self)
        cuadricula.setContentsMargins(0, 0, 0, 0)
        cuadricula.setHorizontalSpacing(6)
        cuadricula.setVerticalSpacing(6)

        self.lbl_contador = QLabel("0 / 0")
        self.lbl_contador.setAlignment(Qt.AlignCenter)
        self.btn_anterior = QPushButton("◀")
        self.btn_anterior.setFixedWidth(36)
        self.btn_anterior.setToolTip("Imagen anterior (←)")
        self.visor = VisorImagen()
        self.btn_siguiente = QPushButton("▶")
        self.btn_siguiente.setFixedWidth(36)
        self.btn_siguiente.setToolTip("Imagen siguiente (→)")

        self.tira = QListWidget()
        self.tira.setViewMode(QListWidget.IconMode)
        self.tira.setFlow(QListWidget.LeftToRight)
        self.tira.setMovement(QListWidget.Static)
        self.tira.setResizeMode(QListWidget.Adjust)
        self.tira.setIconSize(QSize(LADO_MINIATURA, LADO_MINIATURA))
        self.tira.setFixedHeight(LADO_MINIATURA + 34)
        self.tira.setSpacing(4)
        self.tira.setToolTip("Miniaturas: haz clic para saltar a esa imagen")

        cuadricula.addWidget(self.lbl_contador, 0, 0, 1, 3)
        cuadricula.addWidget(self.btn_anterior, 1, 0, Qt.AlignVCenter)
        cuadricula.addWidget(self.visor, 1, 1)
        cuadricula.addWidget(self.btn_siguiente, 1, 2, Qt.AlignVCenter)
        cuadricula.addWidget(self.tira, 2, 1)
        cuadricula.setRowStretch(1, 1)

        self.visor.texto(MENSAJE_INICIAL)
        self.btn_anterior.clicked.connect(self.anterior)
        self.btn_siguiente.clicked.connect(self.siguiente)
        self.visor.pulsada.connect(self._abrir_ampliada)
        self.tira.currentRowChanged.connect(self._desde_tira)
        self._actualizar_botones()

    # ------------------------------------------------------------------ API
    def limpiar(self, mensaje: str = MENSAJE_INICIAL) -> None:
        """Vacía el carrusel (se llama al iniciar cada búsqueda/descarga)."""
        self._pixmaps = []
        self._fallidas = set()
        self._indice = 0
        self._sincronizando = True
        self.tira.clear()
        self._sincronizando = False
        self.visor.texto(mensaje)
        self.lbl_contador.setText("0 / 0")
        self._actualizar_botones()

    def poner_mensaje(self, mensaje: str) -> None:
        if self.cargadas() == 0:
            self.visor.texto(mensaje)

    def definir_total(self, total: int) -> None:
        """Crea una casilla por resultado (todas visibles en el carrusel)."""
        total = max(0, int(total))
        self._pixmaps = [None] * total
        self._fallidas = set()
        self._sincronizando = True
        self.tira.clear()
        for numero in range(1, total + 1):
            elemento = QListWidgetItem(QIcon(_placeholder(numero)), "")
            elemento.setToolTip(f"Imagen {numero}")
            self.tira.addItem(elemento)
        self._sincronizando = False
        self.lbl_contador.setText(f"0 / {total}" if total else "0 / 0")
        self._actualizar_botones()
        if total:
            self.mostrar(0)
        else:
            self.visor.texto(MENSAJE_VACIO)

    def agregar(self, posicion: int, datos: bytes) -> bool:
        """Llega (o falla) la miniatura de la casilla `posicion` (1..n)."""
        indice = posicion - 1
        if not (0 <= indice < len(self._pixmaps)):
            return False
        pixmap = QPixmap()
        if not datos or not pixmap.loadFromData(datos):
            self._fallidas.add(indice)
            if indice == self._indice:
                self._mostrar_actual()
            return False
        self._pixmaps[indice] = pixmap
        self._fallidas.discard(indice)
        elemento = self.tira.item(indice)
        if elemento is not None:
            elemento.setIcon(QIcon(pixmap.scaled(
                LADO_MINIATURA, LADO_MINIATURA, Qt.KeepAspectRatio,
                Qt.SmoothTransformation)))
        self.imagen_lista.emit(indice)
        if indice == self._indice:
            self._mostrar_actual()
        return True

    def mostrar(self, indice: int) -> None:
        if not self._pixmaps:
            return
        self._indice = indice % len(self._pixmaps)
        if self.tira.currentRow() != self._indice:
            self._sincronizando = True
            self.tira.setCurrentRow(self._indice)
            self._sincronizando = False
        self._mostrar_actual()

    def siguiente(self) -> None:
        if self._pixmaps:
            self.mostrar(self._indice + 1)

    def anterior(self) -> None:
        if self._pixmaps:
            self.mostrar(self._indice - 1)

    def total(self) -> int:
        return len(self._pixmaps)

    def cargadas(self) -> int:
        return sum(1 for p in self._pixmaps if p is not None)

    def pixmap(self, indice: int) -> QPixmap | None:
        if 0 <= indice < len(self._pixmaps):
            return self._pixmaps[indice]
        return None

    def indice(self) -> int:
        return self._indice

    def pedir_imagen_de(self, indice: int) -> None:
        """Pide la miniatura de esa casilla si aún no está (ni ha fallado)."""
        if not (0 <= indice < len(self._pixmaps)):
            return
        if self._pixmaps[indice] is None and indice not in self._fallidas:
            self.pedir_imagen.emit(indice + 1)

    # ------------------------------------------------------------------ interno
    def _mostrar_actual(self) -> None:
        total = len(self._pixmaps)
        pixmap = self._pixmaps[self._indice]
        if pixmap is not None:
            self.visor.poner(pixmap)
        elif self._indice in self._fallidas:
            self.visor.texto(MENSAJE_FALLIDA.format(i=self._indice + 1, n=total))
        else:
            self.visor.texto(MENSAJE_CARGANDO.format(i=self._indice + 1, n=total))
            self.pedir_imagen_de(self._indice)
        self.lbl_contador.setText(f"{self._indice + 1} / {total}"
                                  if total else "0 / 0")
        self._actualizar_botones()

    def _desde_tira(self, fila: int) -> None:
        if self._sincronizando or fila < 0:
            return
        self.mostrar(fila)

    def _abrir_ampliada(self) -> None:
        if self._pixmaps:
            self.pedir_lightbox.emit(self._indice)

    def _actualizar_botones(self) -> None:
        hay = len(self._pixmaps) > 1
        self.btn_anterior.setEnabled(hay)
        self.btn_siguiente.setEnabled(hay)
