"""Autocompletado del campo de tags de los boorus, con color por categoría.

Se consulta la **biblioteca real** del booru seleccionado (personajes, franquicias,
artistas, metadatos), **al escribir** y con la red en modo asíncrono de Qt
(`QNetworkAccessManager`), así la ventana nunca se queda esperando ni hacen falta hilos.

Colores: general azul · artista rojo · copyright morado · personaje verde · meta ámbar.
"""
from __future__ import annotations

import logging
import urllib.parse

from PySide6.QtCore import QObject, QTimer, QUrl, Qt
from PySide6.QtGui import QColor, QStandardItem, QStandardItemModel
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import QCompleter, QLineEdit

from .. import config
from ..services import tags_booru

logger = logging.getLogger("imaginteca")

COLORES = {
    "general": "#1565C0",     # azul
    "artist": "#C62828",      # rojo
    "copyright": "#6A1B9A",   # morado
    "character": "#2E7D32",   # verde
    "meta": "#B58900",        # ámbar
}

RETARDO_MS = 260
MINIMO_LETRAS = 2


class CompletadorTags(QObject):
    """Sugerencias de tags del booru seleccionado, al escribir en el campo."""

    def __init__(self, campo: QLineEdit, parent: QObject | None = None):
        super().__init__(parent)
        self._campo = campo
        self._plataforma = ""
        self._cache: dict[tuple[str, str], list[dict]] = {}
        self._pendiente: str = ""
        self._prefijo_pedido: str = ""

        self._red = QNetworkAccessManager(self)
        self._red.finished.connect(self._respuesta)

        self._modelo = QStandardItemModel(self)
        self._completer = QCompleter(self._modelo, self)
        self._completer.setWidget(campo)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setMaxVisibleItems(12)
        self._completer.activated.connect(lambda _t: self.ocultar())

        self._temporizador = QTimer(self)
        self._temporizador.setSingleShot(True)
        self._temporizador.setInterval(RETARDO_MS)
        self._temporizador.timeout.connect(self._consultar)

        campo.textEdited.connect(self._al_escribir)

    # ------------------------------------------------------------------ API
    def plataforma(self, nombre: str) -> None:
        """Fija el booru cuyas etiquetas se sugieren ('' lo desactiva)."""
        self._plataforma = str(nombre or "")
        if not self._plataforma:
            self.ocultar()

    def ocultar(self) -> None:
        try:
            self._completer.popup().hide()
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ interno
    def _token(self) -> str:
        """Palabra en curso (separada por espacios o comas)."""
        texto = self._campo.text()[: self._campo.cursorPosition()]
        for separador in (" ", ",", "\t"):
            if separador in texto:
                texto = texto.rsplit(separador, 1)[-1]
        return texto.strip()

    def _al_escribir(self, _texto: str = "") -> None:
        token = self._token()
        if len(token) < MINIMO_LETRAS or not self._plataforma:
            self.ocultar()
            return
        guardado = self._cache.get((self._plataforma, token.lower()))
        if guardado is not None:
            self._pintar(token, guardado)
            return
        self._pendiente = token
        self._temporizador.start()

    def _url(self, plataforma: str, prefijo: str) -> str:
        sitio = tags_booru.sitio_de(plataforma)
        if sitio is None:
            return ""
        base = str(sitio.get("base") or "").rstrip("/")
        familia = str(sitio.get("family") or "").lower()
        credenciales = tags_booru.credenciales(sitio)
        if familia == "danbooru":
            consulta = {
                "search[name_matches]": f"{prefijo}*",
                "search[order]": "count",
                "limit": "12",
                **credenciales,
            }
            return f"{base}/tags.json?" + urllib.parse.urlencode(consulta)
        consulta = {
            "page": "dapi", "s": "tag", "q": "index", "json": "1",
            "name_pattern": f"{prefijo}%", "limit": "12",
            **credenciales,
        }
        return f"{base}/index.php?" + urllib.parse.urlencode(consulta)

    def _consultar(self) -> None:
        prefijo = self._pendiente or self._token()
        if len(prefijo) < MINIMO_LETRAS or not self._plataforma:
            return
        clave = (self._plataforma, prefijo.lower())
        if clave in self._cache:
            self._pintar(prefijo, self._cache[clave])
            return
        url = self._url(self._plataforma, prefijo.lower())
        if not url:
            return
        self._prefijo_pedido = prefijo.lower()
        peticion = QNetworkRequest(QUrl(url))
        peticion.setRawHeader(b"User-Agent", config.USER_AGENT.encode("utf-8"))
        peticion.setAttribute(QNetworkRequest.CacheLoadControlAttribute,
                              QNetworkRequest.AlwaysNetwork)
        self._red.get(peticion)

    def _respuesta(self, respuesta) -> None:
        prefijo = self._prefijo_pedido
        filas: list[dict] = []
        try:
            datos = bytes(respuesta.readAll())
            texto = datos.decode("utf-8", "replace")
            filas = tags_booru.desde_json(texto) or tags_booru.desde_xml(texto)
        except Exception as exc:  # noqa: BLE001
            logger.info("autocompletado: respuesta ilegible (%s)", exc)
        if prefijo:
            self._cache[(self._plataforma, prefijo)] = filas
        self._pintar(prefijo or self._token(), filas)

    def _pintar(self, prefijo: str, filas: list) -> None:
        if prefijo and prefijo.lower() != self._token().lower():
            return                      # el usuario siguió escribiendo
        self._modelo.clear()
        for fila in list(filas or []):
            etiqueta = str(fila.get("tag") or "")
            categoria = str(fila.get("categoria") or "general")
            if not etiqueta:
                continue
            elemento = QStandardItem(etiqueta)
            elemento.setEditable(False)
            elemento.setForeground(QColor(COLORES.get(categoria, COLORES["general"])))
            elemento.setToolTip(f"{etiqueta} · {categoria}")
            elemento.setData(categoria, Qt.UserRole)
            self._modelo.appendRow(elemento)
        if self._modelo.rowCount():
            self._completer.setCompletionPrefix(self._token())
            self._completer.complete()
        else:
            self.ocultar()
