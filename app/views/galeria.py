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

**Menú contextual:** al hacer clic derecho sobre la imagen grande, sobre una miniatura
o dentro del visor ampliado, la galería emite `menu_contextual(indice, posicion_global)`
y es la ventana principal quien construye el menú (copiar imagen, guardar imagen, guardar
como…, abrir la imagen original en el navegador y copiar su enlace).

**Muestras en dos niveles (nítidas y ligeras):**
  - `_pixmaps`: muestra pequeña de cada casilla (la miniatura de la API convertida a
    .webp), que rellena la tira de 64 px y sirve de adelanto mientras llega la grande.
  - `_muestras`: muestra GRANDE de la imagen que se está viendo, pedida al llegar a ella
    (`pedir_muestra`) y construida por el controlador desde la imagen original en .webp
    acotado. Se conservan solo las últimas que quepan en
    `GALERIA_MUESTRAS_EN_MEMORIA` (las demás se vuelven a pedir si hacen falta), así un
    carrusel de 100 imágenes no llena la memoria.
El visor y el visor ampliado usan siempre la mejor disponible (`pixmap()`).
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

from .. import config

logger = logging.getLogger("imaginteca")

MENSAJE_INICIAL = "🖼️ (aquí se mostrará una galería con las imágenes encontradas)"
MENSAJE_BUSCANDO = "⏳ (buscando imágenes…)"
MENSAJE_VACIO = "⚠️ (no se pudieron cargar imágenes de esta búsqueda)"
MENSAJE_CARGANDO = "⏳ (cargando la imagen {i} de {n}…)"
MENSAJE_FALLIDA = "⚠️ (no se pudo cargar la imagen {i} de {n})"
MENSAJE_SIN_URL = "🚫 (esta obra no tiene miniatura disponible)"

LADO_MINIATURA = 64

# Zoom del visor ampliado: se puede ALEJAR por debajo del tamaño de ajuste (10 %) y
# acercar hasta el 800 %.
ZOOM_MIN = 0.1
ZOOM_MAX = 8.0


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
    """Imagen grande del carrusel; al pulsarla (o con Enter) se abre el visor ampliado."""

    pulsada = Signal()
    peticion_menu = Signal(QPoint)   # clic derecho sobre la imagen (posición global)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(200, 110)   # pequeño a propósito: la ventana puede encogerse
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("border: 1px solid #999; background: #f5f5f5; color: #666;")
        self.setFocusPolicy(Qt.StrongFocus)   # se puede llegar con Tab y abrir con Enter
        self.setToolTip("Enter (o clic) para verla ampliada")
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

    def keyPressEvent(self, evento):  # noqa: N802
        """Enter/Espacio sobre la imagen enfocada: abrirla ampliada (como un clic)."""
        if evento.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space) \
                and self._original is not None:
            self.pulsada.emit()
            return
        super().keyPressEvent(evento)

    def contextMenuEvent(self, evento):  # noqa: N802
        """Clic derecho sobre la imagen: la ventana muestra su menú contextual."""
        if self._original is None or self._original.isNull():
            return
        evento.accept()
        self.peticion_menu.emit(evento.globalPos())


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
        self._galeria.pedir_muestra_de(self._indice)     # imagen grande nítida
        self._galeria.proteger_muestra(self._indice)
        self.setGeometry(self.window().rect())
        self.show()
        self.raise_()
        self.setFocus(Qt.OtherFocusReason)
        self.update()

    def cerrar(self) -> None:
        self.setVisible(False)
        self._arrastrando = False
        self._galeria.proteger_muestra(None)

    def ir(self, indice: int) -> None:
        total = self._galeria.total()
        if total <= 0:
            return
        self._indice = indice % total
        self._zoom = 1.0
        self._desplazamiento = QPoint(0, 0)
        self._galeria.pedir_imagen_de(self._indice)
        self._galeria.pedir_muestra_de(self._indice)     # imagen grande nítida
        self._galeria.proteger_muestra(self._indice)
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
                        "rueda: acercar/alejar · arrastra: mover · doble clic: ajustar · "
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
        """Rueda del ratón: acerca y ALEJA el zoom (de 10 % a 800 %)."""
        pasos = evento.angleDelta().y() / 120.0
        if not pasos:
            return
        factor = 1.15 if pasos > 0 else 1 / 1.15
        self._zoom = max(ZOOM_MIN, min(ZOOM_MAX, self._zoom * factor))
        if self._zoom <= 1.0:
            self._desplazamiento = QPoint(0, 0)   # al alejar, la imagen vuelve al centro
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

    def contextMenuEvent(self, evento):  # noqa: N802
        """Clic derecho sobre la imagen ampliada: menú contextual de esa imagen."""
        zona = self._zona_imagen()
        if zona is not None:
            ix, iy, ancho, alto = zona
            dentro = (ix <= evento.pos().x() <= ix + ancho
                      and iy <= evento.pos().y() <= iy + alto)
            if not dentro:
                return          # clic derecho fuera de la imagen: no hay menú
        evento.accept()
        self._galeria.pedir_menu(self._indice, evento.globalPos())

    def keyPressEvent(self, evento):  # noqa: N802
        tecla = evento.key()
        if tecla == Qt.Key_Escape:
            self.cerrar()
        elif tecla in (Qt.Key_Right, Qt.Key_Space):
            self.siguiente()
        elif tecla == Qt.Key_Left:
            self.anterior()
        elif tecla in (Qt.Key_Plus, Qt.Key_Equal):
            self._zoom = min(ZOOM_MAX, self._zoom * 1.2)
            self.update()
        elif tecla == Qt.Key_Minus:
            self._zoom = max(ZOOM_MIN, self._zoom / 1.2)
            self.update()
        elif tecla == Qt.Key_0:
            self._zoom = 1.0
            self._desplazamiento = QPoint(0, 0)
            self.update()
        else:
            super().keyPressEvent(evento)


class _TiraMiniaturas(QListWidget):
    """Tira de miniaturas: con el teclado se recorre y **Enter** la muestra ampliada.

    Las flechas ya cambian de miniatura (y con ella la imagen grande del carrusel);
    al pulsar Enter sobre la que esté seleccionada se abre el visor ampliado, igual que
    si se hiciera clic en la imagen de muestra.
    """

    abrir_con_enter = Signal(int)   # fila (0..n-1) que se quiere ver ampliada

    def keyPressEvent(self, evento):  # noqa: N802
        if evento.key() in (Qt.Key_Return, Qt.Key_Enter):
            fila = self.currentRow()
            if fila >= 0:
                self.abrir_con_enter.emit(fila)
                return
        super().keyPressEvent(evento)


class GaleriaWidget(QWidget):
    """Carrusel alineado: contador, imagen grande con flechas y tira de miniaturas."""

    pedir_lightbox = Signal(int)   # el usuario quiere verla ampliada
    pedir_imagen = Signal(int)     # (posición 1..n) cargar la muestra pequeña
    pedir_muestra = Signal(int)    # (posición 1..n) cargar la muestra grande y nítida
    imagen_lista = Signal(int)     # (índice 0..n-1) ya hay imagen en esa casilla
    menu_contextual = Signal(int, QPoint)   # (índice 0..n-1, posición global del clic)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._pixmaps: list[QPixmap | None] = []
        self._fallidas: set[int] = set()
        self._muestras: dict[int, QPixmap] = {}     # muestras grandes en memoria (LRU)
        self._orden_muestras: list[int] = []        # orden de uso (la última, la más nueva)
        self._muestras_pedidas: set[int] = set()
        self._muestras_fallidas: set[int] = set()
        self._protegida: int | None = None          # no descartar la que se ve ampliada
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

        self.tira = _TiraMiniaturas()
        self.tira.setViewMode(QListWidget.IconMode)
        self.tira.setFlow(QListWidget.LeftToRight)
        self.tira.setMovement(QListWidget.Static)
        self.tira.setResizeMode(QListWidget.Adjust)
        self.tira.setIconSize(QSize(LADO_MINIATURA, LADO_MINIATURA))
        self.tira.setFixedHeight(LADO_MINIATURA + 34)
        self.tira.setSpacing(4)
        self.tira.setToolTip("Miniaturas: clic o Enter para verla ampliada (flechas para moverse)")
        # Clic derecho en la tira y en la imagen grande → menú contextual (lo arma la ventana)
        self.tira.setContextMenuPolicy(Qt.CustomContextMenu)

        cuadricula.addWidget(self.lbl_contador, 0, 0, 1, 3)
        cuadricula.addWidget(self.btn_anterior, 1, 0, Qt.AlignVCenter)
        cuadricula.addWidget(self.visor, 1, 1)
        cuadricula.addWidget(self.btn_siguiente, 1, 2, Qt.AlignVCenter)
        cuadricula.addWidget(self.tira, 2, 1)
        cuadricula.setRowStretch(1, 1)

        self.visor.texto(MENSAJE_INICIAL)
        self.tira.setVisible(False)      # sin resultados, la tira no ocupa espacio
        self.btn_anterior.clicked.connect(self.anterior)
        self.btn_siguiente.clicked.connect(self.siguiente)
        self.visor.pulsada.connect(self._abrir_ampliada)
        self.tira.currentRowChanged.connect(self._desde_tira)
        self.tira.abrir_con_enter.connect(self._abrir_de_la_tira)
        self.visor.peticion_menu.connect(self._menu_de_la_imagen)
        self.tira.customContextMenuRequested.connect(self._menu_de_la_tira)
        self._actualizar_botones()

    # ------------------------------------------------------------------ API
    def limpiar(self, mensaje: str = MENSAJE_INICIAL) -> None:
        """Vacía el carrusel (se llama al iniciar cada búsqueda/descarga)."""
        self._pixmaps = []
        self._fallidas = set()
        self._muestras = {}
        self._orden_muestras = []
        self._muestras_pedidas = set()
        self._muestras_fallidas = set()
        self._protegida = None
        self._indice = 0
        self._sincronizando = True
        self.tira.clear()
        self._sincronizando = False
        self.tira.setVisible(False)   # sin imágenes, la tira no ocupa espacio
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
        self._muestras = {}
        self._orden_muestras = []
        self._muestras_pedidas = set()
        self._muestras_fallidas = set()
        self._protegida = None
        self._sincronizando = True
        self.tira.clear()
        for numero in range(1, total + 1):
            elemento = QListWidgetItem(QIcon(_placeholder(numero)), "")
            elemento.setToolTip(f"Imagen {numero}")
            self.tira.addItem(elemento)
        self._sincronizando = False
        self.tira.setVisible(total > 0)   # solo ocupa espacio si hay casillas
        self.lbl_contador.setText(f"0 / {total}" if total else "0 / 0")
        self._actualizar_botones()
        if total:
            self.mostrar(0)
        else:
            self.visor.texto(MENSAJE_VACIO)

    def agregar(self, posicion: int, datos: bytes) -> bool:
        """Llega (o falla) la muestra pequeña de la casilla `posicion` (1..n)."""
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
        self._actualizar_icono(indice)
        self.imagen_lista.emit(indice)
        if indice == self._indice:
            self._mostrar_actual()
        return True

    def agregar_muestra(self, posicion: int, datos: bytes) -> bool:
        """Llega (o falla) la muestra GRANDE de la casilla `posicion` (1..n).

        Sustituye a la muestra pequeña en el visor (y en la tira) para que la imagen
        se vea nítida. Se conservan solo las últimas muestras en memoria.
        """
        indice = posicion - 1
        if not (0 <= indice < len(self._pixmaps)):
            return False
        pixmap = QPixmap()
        if not datos or not pixmap.loadFromData(datos):
            # sin muestra grande: se queda la pequeña (o el aviso de fallo)
            self._muestras_fallidas.add(indice)
            if indice == self._indice:
                self._mostrar_actual()
            return False
        self._muestras[indice] = pixmap
        self._recordar_muestra(indice)
        self._actualizar_icono(indice)
        if indice == self._indice:
            self._mostrar_actual()
        return True

    def _recordar_muestra(self, indice: int) -> None:
        """Marca la muestra como la última usada y descarta las más antiguas."""
        if indice in self._orden_muestras:
            self._orden_muestras.remove(indice)
        self._orden_muestras.append(indice)
        tope = max(1, int(getattr(config, "GALERIA_MUESTRAS_EN_MEMORIA", 12)))
        while len(self._orden_muestras) > tope:
            viejo = self._orden_muestras[0]
            if viejo == self._indice or viejo == self._protegida:
                # nunca se descarta la que se está viendo: se pospone al final
                self._orden_muestras.remove(viejo)
                self._orden_muestras.append(viejo)
                if all(i in (self._indice, self._protegida) for i in self._orden_muestras):
                    break
                continue
            self._orden_muestras.pop(0)
            self._muestras.pop(viejo, None)

    def _actualizar_icono(self, indice: int) -> None:
        """Miniatura de la tira: la mejor imagen disponible para esa casilla."""
        elemento = self.tira.item(indice)
        pixmap = self.pixmap(indice)
        if elemento is None or pixmap is None or pixmap.isNull():
            return
        elemento.setIcon(QIcon(pixmap.scaled(
            LADO_MINIATURA, LADO_MINIATURA, Qt.KeepAspectRatio,
            Qt.SmoothTransformation)))

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
        """La mejor imagen disponible de esa casilla (muestra grande o pequeña)."""
        if not (0 <= indice < len(self._pixmaps)):
            return None
        grande = self._muestras.get(indice)
        if grande is not None and not grande.isNull():
            return grande
        return self._pixmaps[indice]

    def indice(self) -> int:
        return self._indice

    def pedir_imagen_de(self, indice: int) -> None:
        """Pide la muestra pequeña de esa casilla si aún no está (ni ha fallado)."""
        if not (0 <= indice < len(self._pixmaps)):
            return
        if self._pixmaps[indice] is None and indice not in self._fallidas:
            self.pedir_imagen.emit(indice + 1)

    def pedir_muestra_de(self, indice: int) -> None:
        """Pide la muestra GRANDE (nítida) de esa casilla, una sola vez por imagen."""
        if not (0 <= indice < len(self._pixmaps)):
            return
        if indice in self._muestras or indice in self._muestras_pedidas \
                or indice in self._muestras_fallidas:
            return
        self._muestras_pedidas.add(indice)
        self.pedir_muestra.emit(indice + 1)

    def proteger_muestra(self, indice: int | None) -> None:
        """Marca la muestra que NO debe descartarse (la que se ve en el visor ampliado)."""
        if indice is not None and 0 <= indice < len(self._pixmaps):
            self._protegida = indice
        else:
            self._protegida = None
        if self._protegida is not None and self._protegida in self._muestras:
            self._recordar_muestra(self._protegida)

    # ------------------------------------------------------------------ interno
    def _mostrar_actual(self) -> None:
        total = len(self._pixmaps)
        pixmap = self.pixmap(self._indice)      # la mejor disponible ahora mismo
        if pixmap is not None and not pixmap.isNull():
            self.visor.poner(pixmap)
        elif self._indice in self._fallidas:
            self.visor.texto(MENSAJE_FALLIDA.format(i=self._indice + 1, n=total))
        else:
            self.visor.texto(MENSAJE_CARGANDO.format(i=self._indice + 1, n=total))
            self.pedir_imagen_de(self._indice)
        # Siempre se pide (una vez) la muestra grande: si llega, la imagen se ve nítida.
        self.pedir_muestra_de(self._indice)
        self.lbl_contador.setText(f"{self._indice + 1} / {total}"
                                  if total else "0 / 0")
        self._actualizar_botones()

    def _desde_tira(self, fila: int) -> None:
        if self._sincronizando or fila < 0:
            return
        self.mostrar(fila)

    def pedir_menu(self, indice: int, global_pos: QPoint) -> None:
        """Avisa a la ventana de que hay que mostrar el menú de esa casilla.

        Se usa desde la imagen grande, la tira de miniaturas y el visor ampliado.
        La ventana es quien construye el menú (copiar/guardar/abrir enlace).
        """
        if 0 <= indice < len(self._pixmaps):
            self.menu_contextual.emit(indice, global_pos)

    def _menu_de_la_imagen(self, global_pos: QPoint) -> None:
        """Clic derecho sobre la imagen grande del carrusel."""
        self.pedir_menu(self._indice, global_pos)

    def _menu_de_la_tira(self, pos: QPoint) -> None:
        """Clic derecho sobre una miniatura: se selecciona y se abre su menú."""
        elemento = self.tira.itemAt(pos)
        if elemento is None:
            return
        fila = self.tira.row(elemento)
        self.mostrar(fila)          # la miniatura señalada pasa a ser la mostrada
        self.pedir_menu(fila, self.tira.viewport().mapToGlobal(pos))

    def _abrir_ampliada(self) -> None:
        if self._pixmaps:
            self.pedir_lightbox.emit(self._indice)

    def _abrir_de_la_tira(self, fila: int) -> None:
        """Enter sobre una miniatura: se selecciona y se muestra ampliada."""
        if fila < 0:
            return
        self.mostrar(fila)
        self._abrir_ampliada()

    def _actualizar_botones(self) -> None:
        hay = len(self._pixmaps) > 1
        self.btn_anterior.setEnabled(hay)
        self.btn_siguiente.setEnabled(hay)
