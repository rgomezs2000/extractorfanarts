"""Layout de flujo: coloca los controles en fila y los pasa a la línea siguiente
cuando no caben. Es lo que hace que el formulario se adapte al ancho de la ventana
(las casillas de opciones se reparten en 1, 2, 3 o 4 columnas según el espacio).

Basado en el ejemplo clásico `FlowLayout` de Qt, adaptado a PySide6.
"""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QSizePolicy


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin: int = 0, hspacing: int = 12,
                 vspacing: int = 6):
        super().__init__(parent)
        self._items: list = []
        self._hspacing = hspacing
        self._vspacing = vspacing
        self.setContentsMargins(margin, margin, margin, margin)

    # ------------------------------------------------------------------ API de QLayout
    def addItem(self, item):  # noqa: N802
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, indice: int):  # noqa: N802
        if 0 <= indice < len(self._items):
            return self._items[indice]
        return None

    def takeAt(self, indice: int):  # noqa: N802
        if 0 <= indice < len(self._items):
            return self._items.pop(indice)
        return None

    def expandingDirections(self):  # noqa: N802
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self) -> bool:  # noqa: N802
        return True

    def heightForWidth(self, ancho: int) -> int:  # noqa: N802
        return self._repartir(QRect(0, 0, ancho, 0), probar=True)

    def setGeometry(self, rect: QRect) -> None:  # noqa: N802
        super().setGeometry(rect)
        self._repartir(rect, probar=False)

    def sizeHint(self) -> QSize:  # noqa: N802
        return self.minimumSize()

    def minimumSize(self) -> QSize:  # noqa: N802
        tamano = QSize()
        for item in self._items:
            tamano = tamano.expandedTo(item.minimumSize())
        margenes = self.contentsMargins()
        tamano += QSize(margenes.left() + margenes.right(),
                        margenes.top() + margenes.bottom())
        return tamano

    # ------------------------------------------------------------------ interno
    def _repartir(self, rect: QRect, probar: bool) -> int:
        margenes = self.contentsMargins()
        util = rect.adjusted(margenes.left(), margenes.top(),
                             -margenes.right(), -margenes.bottom())
        x, y, alto_linea = util.x(), util.y(), 0

        for item in self._items:
            tamano = item.sizeHint()
            if x + tamano.width() > util.right() and alto_linea > 0:
                x = util.x()
                y += alto_linea + self._vspacing
                alto_linea = 0
            if not probar:
                item.setGeometry(QRect(QPoint(x, y), tamano))
            x += tamano.width() + self._hspacing
            alto_linea = max(alto_linea, tamano.height())

        return y + alto_linea - rect.y() + margenes.bottom()
