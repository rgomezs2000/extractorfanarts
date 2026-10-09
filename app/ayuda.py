"""Ventana de ayuda: el manual de uso, punto por punto, con índice y buscador.

El contenido NO se duplica aquí: se lee el manual que viaja con la aplicación
(`README.md`, que es la guía del usuario) y se muestra seccionado por sus títulos
`## `. En desarrollo se usa `README-USUARIO.md` de la raíz del proyecto.

Qt sabe renderizar Markdown (incluidas las tablas del manual), así que el texto se
muestra formateado sin conversiones propias.
"""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSplitter, QTextBrowser, QVBoxLayout, QWidget,
)

from . import config

logger = logging.getLogger("imaginteca")

# Se busca el manual en este orden: primero lo que viaja con el paquete.
_NOMBRES_PAQUETE = ("README.md", "README-USUARIO.md")
_NOMBRES_PROYECTO = ("README-USUARIO.md", "README.md")

_TEXTO_MINIMO = """# Ayuda de {nombre}

No se encontró el manual completo junto a la aplicación.

Mientras tanto, esto es lo esencial:

1. Elige **Tipo** y **Plataforma**.
2. Escribe lo que buscas y pulsa **Buscar**.
3. Revisa la galería y pulsa **Descargar**.
4. Tus imágenes quedan siempre en `.webp` dentro de la carpeta **Salida**.
"""


def rutas_manual() -> list[Path]:
    """Candidatos del manual, del más prioritario al menos."""
    candidatos: list[Path] = []
    bases = []
    import sys

    if getattr(sys, "frozen", False):
        bases.append(Path(sys.executable).resolve().parent)
        interior = getattr(sys, "_MEIPASS", None)
        if interior:
            bases.append(Path(interior))
    bases.append(Path(__file__).resolve().parents[1])
    # El manual de USUARIO tiene preferencia; en el paquete viaja como README.md.
    for base in bases:
        for nombre in _NOMBRES_PROYECTO:
            candidatos.append(base / nombre)
        for nombre in _NOMBRES_PAQUETE:
            candidatos.append(base / nombre)
    vistos: set[str] = set()
    unicos: list[Path] = []
    for ruta in candidatos:
        clave = str(ruta).lower()
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(ruta)
    return unicos


def localizar_manual() -> Path | None:
    for ruta in rutas_manual():
        try:
            if ruta.is_file() and ruta.stat().st_size > 0:
                return ruta
        except OSError:
            continue
    return None


def dividir_secciones(markdown: str) -> tuple[str, list[tuple[str, str]]]:
    """(título del documento, [(título de sección, markdown de esa sección), …])."""
    lineas = markdown.splitlines()
    titulo = config.APP_NAME
    for linea in lineas:
        if linea.startswith("# "):
            titulo = linea[2:].strip()
            break

    secciones: list[tuple[str, list[str]]] = []
    actual: list[str] | None = None
    for linea in lineas:
        if linea.startswith("## "):
            if actual is not None:
                secciones.append((encabezado, actual))
            encabezado = linea[3:].strip()
            actual = []
            continue
        if actual is not None:
            actual.append(linea)
    if actual is not None:
        secciones.append((encabezado, actual))

    # El texto que va ANTES de la primera sección (portada/índice) se muestra como
    # sección de bienvenida si tiene contenido útil.
    portada: list[str] = []
    for linea in lineas:
        if linea.startswith("## "):
            break
        portada.append(linea)
    limpias = [(nombre, "\n".join(cuerpo).strip()) for nombre, cuerpo in secciones]
    limpias = [(nombre, cuerpo) for nombre, cuerpo in limpias if cuerpo]
    if not limpias:
        return titulo, [("Manual", markdown.strip())]
    return titulo, limpias


def cargar_manual() -> tuple[str, list[tuple[str, str]], Path | None]:
    """Lee el manual y lo devuelve seccionado (con la ruta usada, si hubo)."""
    ruta = localizar_manual()
    if ruta is None:
        texto = _TEXTO_MINIMO.format(nombre=config.APP_NAME)
        titulo, secciones = dividir_secciones(texto)
        return titulo, secciones, None
    try:
        markdown = ruta.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.warning("no se pudo leer el manual (%s): %s", ruta, exc)
        texto = _TEXTO_MINIMO.format(nombre=config.APP_NAME)
        titulo, secciones = dividir_secciones(texto)
        return titulo, secciones, None
    titulo, secciones = dividir_secciones(markdown)
    return titulo, secciones, ruta


class VentanaAyuda(QDialog):
    """Manual de uso con índice a la izquierda y contenido a la derecha."""

    def __init__(self, padre: QWidget | None = None, seccion_inicial: str = ""):
        super().__init__(padre)
        self.setWindowTitle(f"📖 Ayuda de {config.APP_NAME}")
        titulo, secciones, ruta = cargar_manual()
        self._secciones = secciones
        self._ruta_manual = ruta

        diseño = QVBoxLayout(self)
        encabezado = QLabel(f"<b>{titulo}</b>")
        encabezado.setWordWrap(True)
        diseño.addWidget(encabezado)

        filtro = QLineEdit()
        filtro.setPlaceholderText("🔎 Buscar en el índice…")
        filtro.setClearButtonEnabled(True)
        diseño.addWidget(filtro)

        self.indice = QListWidget()
        self.indice.setMinimumWidth(230)
        for nombre, _cuerpo in self._secciones:
            self.indice.addItem(QListWidgetItem(nombre))
        self.contenido = QTextBrowser()
        self.contenido.setOpenExternalLinks(True)
        self.contenido.setMinimumWidth(420)

        partido = QSplitter(Qt.Horizontal)
        partido.addWidget(self.indice)
        partido.addWidget(self.contenido)
        partido.setStretchFactor(0, 0)
        partido.setStretchFactor(1, 1)
        diseño.addWidget(partido, 1)

        fila = QHBoxLayout()
        self.btn_manual = QPushButton("🗂️ Abrir el manual completo")
        self.btn_manual.setToolTip("Lo abre con el programa que uses para leer texto")
        self.btn_manual.clicked.connect(self._abrir_manual)
        self.btn_manual.setEnabled(ruta is not None)
        fila.addWidget(self.btn_manual)
        fila.addStretch(1)
        boton_cerrar = QPushButton("Cerrar")
        boton_cerrar.clicked.connect(self.accept)
        fila.addWidget(boton_cerrar)
        diseño.addLayout(fila)

        self.indice.currentRowChanged.connect(self._mostrar_seccion)
        filtro.textChanged.connect(self._filtrar)
        QShortcut(QKeySequence("Escape"), self, activated=self.reject)
        QShortcut(QKeySequence("F1"), self, activated=self._siguiente)

        self._mostrar_seccion(self._buscar_indice(seccion_inicial) if seccion_inicial else 0)
        self._ajustar_tamano()

    # ------------------------------------------------------------------ interno
    def _ajustar_tamano(self) -> None:
        pantalla = self.screen()
        if pantalla is not None:
            util = pantalla.availableGeometry()
            ancho = max(560, min(980, util.width() - 80))
            alto = max(420, min(700, util.height() - 80))
            self.resize(ancho, alto)
        else:
            self.resize(860, 620)

    def _buscar_indice(self, texto: str) -> int:
        texto = texto.lower()
        for indice, (nombre, _) in enumerate(self._secciones):
            if texto in nombre.lower():
                return indice
        return 0

    def _filtrar(self, texto: str) -> None:
        texto = texto.strip().lower()
        for indice in range(self.indice.count()):
            item = self.indice.item(indice)
            ocultar = bool(texto) and texto not in item.text().lower()
            item.setHidden(ocultar)
        if texto:
            for indice in range(self.indice.count()):
                if not self.indice.item(indice).isHidden():
                    self.indice.setCurrentRow(indice)
                    break

    def _mostrar_seccion(self, indice: int) -> None:
        if indice < 0 or indice >= len(self._secciones):
            return
        nombre, cuerpo = self._secciones[indice]
        self.contenido.setMarkdown(f"# {nombre}\n\n{cuerpo}")
        self.contenido.verticalScrollBar().setValue(0)

    def _siguiente(self) -> None:
        total = self.indice.count()
        if total:
            self.indice.setCurrentRow((self.indice.currentRow() + 1) % total)

    def _abrir_manual(self) -> None:
        if self._ruta_manual is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._ruta_manual)))


def abrir_ayuda(padre: QWidget | None = None, seccion: str = "") -> None:
    """Abre la ventana de ayuda (modal) centrada en el padre."""
    ventana = VentanaAyuda(padre, seccion)
    if padre is not None:
        try:
            centro = padre.frameGeometry().center()
            marco = ventana.frameGeometry()
            marco.moveCenter(centro)
            ventana.move(marco.topLeft())
        except Exception:  # noqa: BLE001
            pass
    ventana.exec()
