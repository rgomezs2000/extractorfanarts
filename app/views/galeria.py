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

from PySide6.QtCore import QRect, QVariantAnimation, QEasingCurve, QPoint, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QKeySequence, QPainter, QPen, QPixmap, QShortcut
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


def _iniciar_arrastre(widget, pixmap, enlace: str = "") -> bool:
    """Arrastra la imagen fuera de la app (Word, Discord, Telegram, navegador…)."""
    try:
        if pixmap is None or pixmap.isNull():
            return False
        from PySide6.QtCore import QMimeData, QUrl
        from PySide6.QtGui import QDrag

        datos = QMimeData()
        datos.setImageData(pixmap.toImage())
        if enlace:
            datos.setUrls([QUrl(str(enlace))])
            datos.setText(str(enlace))
        else:
            datos.setText("imaginteca")
        arrastre = QDrag(widget)
        arrastre.setMimeData(datos)
        arrastre.setPixmap(pixmap.scaled(180, 180, Qt.KeepAspectRatio,
                                         Qt.SmoothTransformation))
        arrastre.exec(Qt.CopyAction)
        return True
    except Exception:  # noqa: BLE001
        return False


class _MarcoVisor(QWidget):
    """Contenedor que recorta: permite DESLIZAR el visor de lado (efecto de página)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._hijo: QWidget | None = None
        self.animando = False
        self.setMinimumHeight(120)

    def poner(self, hijo: QWidget) -> None:
        self._hijo = hijo
        hijo.setParent(self)
        hijo.setGeometry(self.rect())

    def resizeEvent(self, evento):  # noqa: N802
        super().resizeEvent(evento)
        # Mientras hay animación manda la animación; si no, el visor ocupa todo el marco.
        if self._hijo is not None and not self.animando:
            self._hijo.setGeometry(self.rect())


class VisorImagen(QLabel):
    """Imagen grande del carrusel; al pulsarla (o con Enter) se abre el visor ampliado."""

    _desliz: float = 0.0   # desplazamiento animado (0 = centrada)

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


    # ---------------------------------------------------------------- arrastrar fuera
    def mousePressEvent(self, evento):  # noqa: N802
        if evento.button() == Qt.LeftButton:
            self._arrastre_desde = evento.position().toPoint()
            self._puede_arrastrar = True
        super().mousePressEvent(evento)

    def mouseMoveEvent(self, evento):  # noqa: N802
        if getattr(self, "_puede_arrastrar", False) and (evento.buttons() & Qt.LeftButton):
            inicio = getattr(self, "_arrastre_desde", None)
            if inicio is not None:
                if (evento.position().toPoint() - inicio).manhattanLength() > 12:
                    self._puede_arrastrar = False
                    self._arrastro_hecho = True
                    if _iniciar_arrastre(self, self.pixmap(),
                                         getattr(self, "enlace", "") or ""):
                        return
        super().mouseMoveEvent(evento)

    def mouseReleaseEvent(self, evento):  # noqa: N802
        # Clic normal (sin arrastre) = abrir el visor ampliado, como siempre.
        if (evento.button() == Qt.LeftButton
                and not getattr(self, "_arrastro_hecho", False)):
            pixmap = self.pixmap()
            if pixmap is not None and not pixmap.isNull():
                self.pulsada.emit()
        self._puede_arrastrar = False
        self._arrastro_hecho = False
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
        # Transición de desplazamiento (efecto de página) al cambiar de imagen.
        self._previa: QPixmap | None = None
        self._desliz = 0.0
        self._desliz_dir = 1
        # Animación de agrandado al abrirse desde la galería (crece hasta su tamaño final).
        self._apertura = 1.0
        self._rect_inicio = None
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
        self._preparar_apertura()
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
        anterior = self._indice
        nueva = indice % total
        # Se guarda la imagen que se está viendo: sale deslizándose al navegar.
        previa = self._pixmap()
        self._previa = previa.copy() if previa is not None and not previa.isNull() else None
        self._desliz_dir = 1 if (nueva > anterior or (anterior == total - 1 and nueva == 0)) else -1
        self._indice = nueva
        self._zoom = 1.0
        self._desplazamiento = QPoint(0, 0)
        if self._previa is not None and nueva != anterior:
            self._animar_deslizamiento()
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
    def _preparar_apertura(self) -> None:
        """Prepara el agrandado: la imagen arranca en el sitio que ocupa en la galería."""
        try:
            origen = getattr(self._galeria, "_marco_visor", None)
            if origen is None:
                origen = getattr(self._galeria, "visor", None)
            self._rect_inicio = None
            if origen is not None and origen.width() > 2:
                # El visor no está dentro del visor ampliado (es una capa hermana): se
                # convierte desde la ventana, que es el sistema de coordenadas común.
                ventana = self.window()
                esquina = origen.mapTo(ventana, QPoint(0, 0))
                esquina = self.mapFrom(ventana, esquina)
                self._rect_inicio = QRect(esquina, origen.size())
            self._apertura = 0.0
            from PySide6.QtCore import QEasingCurve, QVariantAnimation

            animacion = getattr(self, "_anim_apertura", None)
            if animacion is None:
                animacion = QVariantAnimation(self)
                animacion.setDuration(220)
                animacion.setEasingCurve(QEasingCurve.OutCubic)
                animacion.valueChanged.connect(self._paso_apertura)
                animacion.finished.connect(self._fin_apertura)
                self._anim_apertura = animacion
            animacion.stop()
            animacion.setStartValue(0.0)
            animacion.setEndValue(1.0)
            animacion.start()
        except Exception as exc:  # noqa: BLE001
            logger.debug("no se pudo animar la apertura del visor: %s", exc)
            self._apertura = 1.0
            self._rect_inicio = None

    def _paso_apertura(self, valor) -> None:
        try:
            self._apertura = float(valor)
        except (TypeError, ValueError):
            self._apertura = 1.0
        self.update()

    def _fin_apertura(self) -> None:
        self._apertura = 1.0
        self._rect_inicio = None
        self.update()

    def _animar_deslizamiento(self) -> None:
        """Anima la entrada de la nueva imagen desde el lado de la navegación."""
        try:
            from PySide6.QtCore import QEasingCurve, QVariantAnimation

            animacion = getattr(self, "_anim_desliz", None)
            if animacion is None:
                animacion = QVariantAnimation(self)
                animacion.setDuration(190)
                animacion.setEasingCurve(QEasingCurve.OutCubic)
                animacion.valueChanged.connect(self._paso_desliz)
                animacion.finished.connect(self._fin_desliz)
                self._anim_desliz = animacion
            animacion.stop()
            animacion.setStartValue(1.0)
            animacion.setEndValue(0.0)
            animacion.start()
        except Exception:  # noqa: BLE001
            self._desliz = 0.0
            self._previa = None
            self.update()

    def _paso_desliz(self, valor) -> None:
        try:
            self._desliz = float(valor)
        except (TypeError, ValueError):
            self._desliz = 0.0
        self.update()

    def _fin_desliz(self) -> None:
        self._desliz = 0.0
        self._previa = None
        self.update()

    def paintEvent(self, evento):  # noqa: N802
        pintor = QPainter(self)
        # Recorte al área del visor: la imagen nunca se dibuja sobre el carrusel.
        pintor.setClipRect(self.rect())
        pintor.setRenderHint(QPainter.Antialiasing, True)
        pintor.setRenderHint(QPainter.SmoothPixmapTransform, True)
        pintor.fillRect(self.rect(), QColor(0, 0, 0, 215))

        total = max(1, self._galeria.total())
        zona = self._zona_imagen()
        if zona is not None:
            x, y, ancho, alto = zona
            # TRANSICIÓN DE DESPLAZAMIENTO: mientras dura, la imagen anterior sale por un
            # lado y la nueva entra por el otro (efecto de página, no de fundido).
            progreso = float(getattr(self, "_desliz", 0.0) or 0.0)
            previa = getattr(self, "_previa", None)
            direccion = int(getattr(self, "_desliz_dir", 1) or 1)
            apertura = float(getattr(self, "_apertura", 1.0) or 1.0)
            inicio = getattr(self, "_rect_inicio", None)
            if apertura < 0.999 and inicio is not None:
                # Efecto de agrandado: se interpola del hueco de la galería al tamaño final.
                p = apertura
                ax = int(inicio.x() + (x - inicio.x()) * p)
                ay = int(inicio.y() + (y - inicio.y()) * p)
                aw = int(inicio.width() + (ancho - inicio.width()) * p)
                ah = int(inicio.height() + (alto - inicio.height()) * p)
                pintor.setPen(QColor(245, 245, 245, int(220 * p)))
                pintor.drawRect(ax - 4, ay - 4, aw + 7, ah + 7)
                pintor.drawPixmap(ax, ay, aw, ah, self._pixmap())
                return
            if previa is not None and not previa.isNull() and progreso > 0.001:
                corrimiento_nueva = int(direccion * progreso * self.width())
                corrimiento_previa = int(-direccion * (1.0 - progreso) * self.width())
                pintor.setPen(QColor(245, 245, 245, 160))
                pintor.drawRect(x - 4 + corrimiento_previa, y - 4, ancho + 7, alto + 7)
                pintor.drawPixmap(x + corrimiento_previa, y, ancho, alto, previa)
                pintor.setPen(QColor(245, 245, 245, 220))
                pintor.drawRect(x - 4 + corrimiento_nueva, y - 4, ancho + 7, alto + 7)
                pintor.drawPixmap(x + corrimiento_nueva, y, ancho, alto, self._pixmap())
            else:
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
                        "rueda: acercar/alejar · arrastra: mover · Ctrl+arrastra: llevarla a "
                        "otro programa · doble clic: ajustar · ← →: cambiar · Esc o clic "
                        "fuera: cerrar")

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
        if evento.modifiers() & Qt.ControlModifier:
            # Ctrl + arrastrar: lleva la imagen a otro programa (no desplaza el zoom).
            if _iniciar_arrastre(self, self._pixmap(), getattr(self, "enlace", "") or ""):
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
    si se hiciera clic en la imagen de muestra. **F3** abre la miniatura sobre la que
    esté parado el ratón, sin tener que seleccionarla antes.
    """

    abrir_con_enter = Signal(int)   # fila (0..n-1) que se quiere ver ampliada

    def __init__(self, *argumentos, **opciones):
        super().__init__(*argumentos, **opciones)
        self._fila_cursor = -1
        # Seguimiento del ratón: así se sabe sobre qué miniatura está parado el cursor.
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)

    def fila_bajo_cursor(self) -> int:
        """Fila de la miniatura sobre la que está el ratón (-1 si no hay ninguna)."""
        return self._fila_cursor

    def mouseMoveEvent(self, evento):  # noqa: N802
        elemento = self.itemAt(evento.pos())
        self._fila_cursor = self.row(elemento) if elemento is not None else -1
        super().mouseMoveEvent(evento)

    def leaveEvent(self, evento):  # noqa: N802
        self._fila_cursor = -1
        super().leaveEvent(evento)

    def keyPressEvent(self, evento):  # noqa: N802
        if evento.key() in (Qt.Key_Return, Qt.Key_Enter):
            fila = self.currentRow()
            if fila >= 0:
                self.abrir_con_enter.emit(fila)
                return
        if evento.key() == Qt.Key_F3:
            fila = self._fila_cursor if self._fila_cursor >= 0 else self.currentRow()
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
        # El visor vive dentro de un marco que recorta: así se puede deslizar al navegar.
        self._marco_visor = _MarcoVisor()
        self.visor = VisorImagen(self._marco_visor)
        self.visor.setMinimumHeight(120)
        self._marco_visor.poner(self.visor)
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
        self.tira.setToolTip("Miniaturas: clic o Enter para verla ampliada; F3 abre la "
                            "que está bajo el ratón (flechas para moverse)")
        # Clic derecho en la tira y en la imagen grande → menú contextual (lo arma la ventana)
        self.tira.setContextMenuPolicy(Qt.CustomContextMenu)

        # F3: abre ampliada la miniatura sobre la que está parado el ratón (o la que se
        # está viendo). Vale desde cualquier punto de la ventana.
        self.atajo_f3 = QShortcut(QKeySequence("F3"), self)
        self.atajo_f3.setContext(Qt.WindowShortcut)
        self.atajo_f3.activated.connect(self.abrir_bajo_cursor)

        cuadricula.addWidget(self.lbl_contador, 0, 0, 1, 3)
        cuadricula.addWidget(self.btn_anterior, 1, 0, Qt.AlignVCenter)
        cuadricula.addWidget(self._marco_visor, 1, 1)
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

    def _deslizar(self, direccion: int, anterior: int) -> None:
        """Desliza la imagen: entra desde el lado hacia el que se navega (efecto libro).

        La imagen anterior sale por el lado contrario y la nueva entra desde el lado de la
        flecha. Se anima la POSICIÓN de los dos widgets dentro del marco que recorta.
        """
        marco = getattr(self, "_marco_visor", None)
        visor = getattr(self, "visor", None)
        if marco is None or visor is None:
            return
        try:
            from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation

            ancho = max(1, marco.width())
            alto = max(1, marco.height())
            # Copia de lo que se estaba viendo, para que salga deslizándose.
            previa = getattr(self, "_desliz_previa", None)
            self._desliz_previa = None
            if previa is None or previa.isNull():
                return
            fantasma = QLabel(marco)
            fantasma.setPixmap(previa)
            fantasma.setScaledContents(True)
            fantasma.setGeometry(0, 0, ancho, alto)
            fantasma.show()
            fantasma.raise_()
            visor.raise_()
            marco.animando = True
            visor.setGeometry(direccion * ancho, 0, ancho, alto)
            grupo = QParallelAnimationGroup(self)
            for objetivo, desde, hasta in ((visor, direccion * ancho, 0),
                                           (fantasma, 0, -direccion * ancho)):
                animacion = QPropertyAnimation(objetivo, b"pos", self)
                animacion.setDuration(190)
                animacion.setEasingCurve(QEasingCurve.OutCubic)
                animacion.setStartValue(QPoint(desde, 0))
                animacion.setEndValue(QPoint(hasta, 0))
                grupo.addAnimation(animacion)

            def _terminar() -> None:
                marco.animando = False
                visor.setGeometry(marco.rect())
                fantasma.deleteLater()

            grupo.finished.connect(_terminar)
            self._anim_desliz = grupo      # se guarda para que no lo recoja el GC
            grupo.start()
        except Exception:  # noqa: BLE001
            marco.animando = False
            visor.setGeometry(marco.rect())

    def _animar_muestra(self) -> None:
        """Fundido al cambiar de imagen (efecto visual al navegar con flechas o teclado)."""
        try:
            from PySide6.QtCore import QEasingCurve, QPropertyAnimation
            from PySide6.QtWidgets import QGraphicsOpacityEffect

            efecto = getattr(self.visor, "_efecto_opacidad", None)
            if efecto is None:
                efecto = QGraphicsOpacityEffect(self.visor)
                efecto.setOpacity(1.0)
                self.visor.setGraphicsEffect(efecto)
                self.visor._efecto_opacidad = efecto      # type: ignore[attr-defined]
            animacion = getattr(self, "_anim_muestra", None)
            if animacion is None:
                animacion = QPropertyAnimation(efecto, b"opacity", self)
                animacion.setDuration(170)
                animacion.setEasingCurve(QEasingCurve.OutCubic)
                animacion.setStartValue(0.25)
                animacion.setEndValue(1.0)
                self._anim_muestra = animacion
            animacion.stop()
            animacion.start()
        except Exception:  # noqa: BLE001
            pass

    def mostrar(self, indice: int) -> None:
        if not self._pixmaps:
            return
        anterior = self._indice
        # Copia de lo que se está viendo ANTES de cambiarlo: es la imagen que sale
        # deslizándose hacia el lado contrario al navegar (efecto de página).
        self._desliz_previa = None
        visor = getattr(self, "visor", None)
        if visor is not None and visor.width() > 2 and visor.height() > 2:
            try:
                copia = visor.grab()
                if not copia.isNull():
                    self._desliz_previa = copia
            except Exception:  # noqa: BLE001
                self._desliz_previa = None
        self._indice = indice % len(self._pixmaps)
        # Efecto de desplazamiento: la muestra entra desde el lado de la navegación.
        if self._indice != anterior:
            direccion = 1 if self._indice > anterior else -1
            # Casos de borde (0 -> último y último -> 0): se respeta el sentido.
            if anterior == len(self._pixmaps) - 1 and self._indice == 0:
                direccion = 1
            elif anterior == 0 and self._indice == len(self._pixmaps) - 1:
                direccion = -1
            if self.tira.currentRow() != self._indice:
                self._sincronizando = True
                self.tira.setCurrentRow(self._indice)
                self._sincronizando = False
            self._mostrar_actual()
            self._deslizar(direccion, anterior)
            return
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

    def abrir_bajo_cursor(self) -> None:
        """**F3**: abre ampliada la miniatura sobre la que está parado el ratón.

        Si el ratón no está sobre ninguna miniatura (o se pulsa desde el teclado), se
        abre la que se esté viendo en el carrusel. Es el atajo cómodo para mirar una
        imagen de ejemplo sin tener que seleccionarla antes.
        """
        if not self._pixmaps:
            return
        fila = self.tira.fila_bajo_cursor()
        if fila < 0 or fila >= len(self._pixmaps):
            fila = self._indice
        if fila < 0 or fila >= len(self._pixmaps):
            return
        self.mostrar(fila)
        self.tira.setCurrentRow(fila)
        self.pedir_lightbox.emit(fila)

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
