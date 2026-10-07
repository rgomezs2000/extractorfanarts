"""Vista principal de escritorio (PySide6): formulario de filtros, botones
Buscar / Descargar↔Cancelar / Limpiar, galería de ejemplo (carrusel) y resultados.

Reglas de UI:
  - Limpiar limpia el formulario (sin descargas) y queda BLOQUEADO mientras se descarga.
  - Descargar se convierte en Cancelar durante la descarga.
  - Al cancelar se restaura todo como estaba, sin restablecer el formulario,
    y la galería se mantiene.
  - La galería se recarga (se vacía) en cada búsqueda o descarga nueva, y al pulsar
    una imagen se abre el visor ampliado DENTRO de la ventana (estilo fancybox).
"""
from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSlider, QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)

from .. import config
from ..controllers.main_controller import MainController
from ..services.adapters import BOORU_ADAPTERS, SOCIAL_ADAPTERS, WIKI_ADAPTERS
from .flujo import FlowLayout
from .galeria import MENSAJE_BUSCANDO, MENSAJE_VACIO, GaleriaWidget, Lightbox

logger = logging.getLogger("extractorfanarts")

TIPOS = ("Red social", "Booru", "Wiki fandom")


class MainWindow(QMainWindow):
    def __init__(self, controller: MainController):
        super().__init__()
        self.controller = controller
        self.setWindowTitle(f"🎨 {config.APP_NAME} — archivo personal de fanarts")
        self._muestra_recibida = False
        self._tarea = "descargar"
        self._lightbox: Lightbox | None = None
        self._build_ui()
        self._connect()
        self._set_tipo(TIPOS[0])
        self._set_idle()
        # Icono de la ventana (además del que fija main.py para toda la app)
        try:
            from PySide6.QtGui import QIcon

            from ..icono import ruta_icono
            ruta = ruta_icono()
            if ruta is not None:
                self.setWindowIcon(QIcon(str(ruta)))
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ construcción
    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        # El contenido va dentro de un área desplazable: así la ventana puede ser
        # más pequeña que el contenido (pantallas pequeñas) sin salirse de la
        # zona útil ni tapar la barra de tareas.
        desplazable = QScrollArea()
        desplazable.setWidgetResizable(True)
        desplazable.setFrameShape(QScrollArea.NoFrame)
        desplazable.setWidget(central)
        self.setCentralWidget(desplazable)

        # Fuente (también en flujo: en ventanas estrechas la plataforma pasa a otra línea)
        fuente_box = QGroupBox("🔎 Fuente de búsqueda")
        fl = FlowLayout(hspacing=10, vspacing=4)
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(TIPOS)
        self.cmb_tipo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmb_plataforma = QComboBox()
        # Permite encogerse (con puntos suspensivos) en ventanas estrechas
        self.cmb_plataforma.setSizeAdjustPolicy(
            QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_plataforma.setMinimumContentsLength(14)
        self.cmb_plataforma.setMinimumWidth(190)
        self.cmb_plataforma.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        fl.addWidget(QLabel("🗂️ Tipo:"))
        fl.addWidget(self.cmb_tipo)
        fl.addWidget(QLabel("🌐 Plataforma:"))
        fl.addWidget(self.cmb_plataforma)
        fuente_box.setLayout(fl)
        root.addWidget(fuente_box)

        # Filtros por tipo (stacked)
        self.stack = QStackedWidget()

        self.page_social = QWidget()
        v = QVBoxLayout(self.page_social)
        aviso_social = QLabel(
            "Combina @usuario, palabra clave y/o #hashtag "
            "(usa el algoritmo nativo de la plataforma):"
        )
        aviso_social.setWordWrap(True)   # se ajusta al ancho de la ventana
        v.addWidget(aviso_social)
        self.ed_usuario = QLineEdit()
        self.ed_usuario.setPlaceholderText("👤 @usuario  (o @usuario@instancia)")
        self.ed_keyword = QLineEdit()
        self.ed_keyword.setPlaceholderText("🔤 palabra clave")
        self.ed_hashtag = QLineEdit()
        self.ed_hashtag.setPlaceholderText("#️⃣ #hashtag")
        v.addWidget(self.ed_usuario)
        v.addWidget(self.ed_keyword)
        v.addWidget(self.ed_hashtag)
        self.ed_instancia = QLineEdit()
        self.ed_instancia.setPlaceholderText(
            "🌐 Instancia (opcional): ej. baraag.net · Misskey: ej. misskey.io — "
            "si escribes @usuario@instancia se usa esa automáticamente"
        )
        v.addWidget(self.ed_instancia)

        self.page_booru = QWidget()
        v = QVBoxLayout(self.page_booru)
        v.addWidget(QLabel("🏷️ Tags del booru (las que el booru permita):"))
        self.ed_tags = QLineEdit()
        self.ed_tags.setPlaceholderText("🏷️ ej. hatsune_miku solo")
        v.addWidget(self.ed_tags)

        self.page_wiki = QWidget()
        v = QVBoxLayout(self.page_wiki)
        v.addWidget(QLabel("📚 Fandom (franquicia):"))
        self.ed_fandom = QLineEdit()
        self.ed_fandom.setPlaceholderText("📚 ej. naruto")
        v.addWidget(self.ed_fandom)
        v.addWidget(QLabel("🎭 Personaje y/o concepto:"))
        self.ed_character = QLineEdit()
        self.ed_character.setPlaceholderText("🎭 ej. naruto_uzumaki")
        v.addWidget(self.ed_character)
        v.addWidget(QLabel("🔗 URL de la wiki (opcional):"))
        self.ed_wiki_url = QLineEdit()
        self.ed_wiki_url.setPlaceholderText("🔗 ej. https://naruto.fandom.com")
        v.addWidget(self.ed_wiki_url)

        # Mínimo pequeño en los campos de texto: así el texto de ayuda (placeholder)
        # o el contenido no imponen el ancho de la ventana (se recorta con scroll).
        for campo in (self.ed_usuario, self.ed_keyword, self.ed_hashtag, self.ed_instancia,
                      self.ed_tags, self.ed_fandom, self.ed_character, self.ed_wiki_url):
            campo.setMinimumWidth(70)

        self.stack.addWidget(self.page_social)
        self.stack.addWidget(self.page_booru)
        self.stack.addWidget(self.page_wiki)
        root.addWidget(self.stack)

        # Opciones (layout de flujo: se reparten en varias líneas si la ventana
        # es estrecha y vuelven a una sola cuando hay espacio)
        self.filtros_box = QGroupBox("⚙️ Opciones")
        ov = QVBoxLayout(self.filtros_box)
        fl2 = FlowLayout(hspacing=14, vspacing=4)
        self.chk_liberado = QCheckBox("⚖️ Solo material con licencia liberada")
        self.chk_liberado.setToolTip(
            "Si se marca, solo se procesan obras con licencia permisiva explícita "
            "(CC0/CC-BY/dominio público). La mayoría del fanart no la tiene."
        )
        self.chk_adulto = QCheckBox("🔞 Permitir contenido adulto")
        self.chk_adulto.setToolTip(
            "Confirmo que soy mayor de edad en mi jurisdicción. "
            "Por defecto se omiten los ratings questionable/explicit."
        )
        self.chk_mejorar = QCheckBox("✨ Mejorar calidad (upscale IA/Lanczos)")
        self.chk_mejorar.setChecked(config.ENHANCE_DEFAULT_ON)
        self.chk_mejorar.setToolTip(
            "Controla SOLO el upscaling y la definición. El guardado en .webp se aplica "
            "SIEMPRE (el original nunca se conserva). Reglas: <700px→4x · 700-799px→3x · "
            "800-1500px→2x · 1501-1599px→1x · 1600px+→2x, con tope de 8K (7680 px)."
        )
        self.chk_ia = QCheckBox("🤖 Modo IA (waifu2x/Real-ESRGAN)")
        self.chk_ia.setToolTip(
            "Usa el motor IA Vulkan si está instalado (python scripts\\setup_vendor.py --ai); "
            "si no está disponible, usa Lanczos + afilado suave automáticamente."
        )
        fl2.addWidget(self.chk_liberado)
        fl2.addWidget(self.chk_adulto)
        fl2.addWidget(self.chk_mejorar)
        fl2.addWidget(self.chk_ia)
        ov.addLayout(fl2)

        # Calidad WebP (el deslizador se estira con la ventana)
        fl3 = QHBoxLayout()
        fl3.addWidget(QLabel("🎚️ Calidad WebP:"))
        self.sld_calidad = QSlider(Qt.Horizontal)
        self.sld_calidad.setRange(1, 100)
        self.sld_calidad.setValue(config.WEBP_QUALITY_DEFAULT)
        self.sld_calidad.setMinimumWidth(120)
        self.sld_calidad.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.lbl_calidad_val = QLabel(str(config.WEBP_QUALITY_DEFAULT))
        self.lbl_calidad_val.setMinimumWidth(28)
        self.sld_calidad.valueChanged.connect(
            lambda v: self.lbl_calidad_val.setText(str(v))
        )
        fl3.addWidget(self.sld_calidad, 1)
        fl3.addWidget(self.lbl_calidad_val)
        ov.addLayout(fl3)

        # Límite de cantidad de descargas (también en flujo)
        fl4 = FlowLayout(hspacing=14, vspacing=4)
        self.chk_limite = QCheckBox("🔢 Limitar cantidad de descargas")
        self.chk_limite.setToolTip(
            "Si se marca, se descarga solo la cantidad indicada. Si no, se "
            "descarga todo lo encontrado (hasta el tope de seguridad de config.py)."
        )
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setRange(1, 1000)
        self.spin_cantidad.setValue(50)
        self.spin_cantidad.setEnabled(False)
        self.chk_limite.toggled.connect(self.spin_cantidad.setEnabled)
        fl4.addWidget(self.chk_limite)
        fl4.addWidget(QLabel("🔢 Cantidad:"))
        fl4.addWidget(self.spin_cantidad)
        self.chk_sidecar = QCheckBox("🏷️ Guardar metadatos .json")
        self.chk_sidecar.setChecked(config.WRITE_SIDECAR_JSON)
        self.chk_sidecar.setToolTip(
            "Guarda un archivo .json junto a cada imagen con autoría, origen y "
            "licencia. Desactivado: solo se guarda la imagen."
        )
        fl4.addWidget(self.chk_sidecar)
        ov.addLayout(fl4)
        root.addWidget(self.filtros_box)

        # Carpeta de salida
        carpeta_box = QGroupBox("📁 Carpeta de salida")
        cl = QHBoxLayout(carpeta_box)
        self.ed_carpeta = QLineEdit(str(config.DEFAULT_OUTPUT_DIR))
        self.btn_carpeta = QPushButton("📂")
        self.btn_carpeta.setFixedWidth(44)
        self.btn_carpeta.setToolTip("Elegir carpeta de salida")
        cl.addWidget(QLabel("Salida:"))
        cl.addWidget(self.ed_carpeta, 1)
        cl.addWidget(self.btn_carpeta)
        root.addWidget(carpeta_box)

        # Botones
        botones = QHBoxLayout()
        self.btn_buscar = QPushButton("🔍 Buscar")
        self.btn_descargar = QPushButton("⬇️ Descargar")
        self.btn_limpiar = QPushButton("🧹 Limpiar")
        botones.addWidget(self.btn_buscar)
        botones.addWidget(self.btn_descargar)
        botones.addWidget(self.btn_limpiar)
        botones.addStretch(1)
        root.addLayout(botones)

        # Resultados
        self.galeria = GaleriaWidget()
        self.galeria.setMinimumHeight(200)
        self.lst_resultados = QListWidget()
        self.lst_resultados.setMinimumHeight(70)

        res_box = QGroupBox("🖼️ Resultados")
        rv = QVBoxLayout(res_box)
        rv.addWidget(self.galeria, 1)
        rv.addWidget(QLabel("📋 Resultados encontrados:"))
        rv.addWidget(self.lst_resultados)
        root.addWidget(res_box, 1)

        # Progreso (solo descargas: la barra muestra el icono de descarga)
        self.progress = QProgressBar()
        self.progress.setFormat("⬇️ %p%")
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        # Estatus de conexión (última petición/respuesta)
        self.lbl_conexion = QLabel("📡 Conexión: —")
        self.lbl_conexion.setStyleSheet("color: #444444;")
        self.lbl_conexion.setWordWrap(True)   # no fuerza el ancho de la ventana
        self.lbl_conexion.setToolTip("Última actividad HTTP: peticiones, respuestas y pausas")
        root.addWidget(self.lbl_conexion)

        self.statusBar().showMessage("Listo")

    # ------------------------------------------------------------------ conexiones
    def _connect(self) -> None:
        self.cmb_tipo.currentTextChanged.connect(self._set_tipo)
        self.btn_carpeta.clicked.connect(self._elegir_carpeta)
        self.btn_buscar.clicked.connect(self._on_buscar)
        self.btn_descargar.clicked.connect(self._on_descargar)
        self.btn_limpiar.clicked.connect(self._on_limpiar)

        c = self.controller
        c.status_changed.connect(lambda m: self.statusBar().showMessage(m))
        c.results_ready.connect(self._on_results)
        c.galeria_total_ready.connect(self._on_galeria_total)
        c.galeria_item_ready.connect(self._on_galeria_item)
        self.galeria.pedir_lightbox.connect(self._abrir_lightbox)
        self.galeria.pedir_imagen.connect(c.solicitar_miniatura)
        c.progress_changed.connect(self._on_progress)
        c.error.connect(self._on_error)
        c.state_changed.connect(self._on_state)
        c.job_finished.connect(self._on_job_finished)
        c.http_event.connect(self._on_http_event)

    # ------------------------------------------------------------------ dinámica
    def _set_tipo(self, tipo: str) -> None:
        if tipo == "Red social":
            self.cmb_plataforma.clear()
            self.cmb_plataforma.addItems(list(SOCIAL_ADAPTERS))
            self.stack.setCurrentWidget(self.page_social)
        elif tipo == "Booru":
            self.cmb_plataforma.clear()
            self.cmb_plataforma.addItems(list(BOORU_ADAPTERS))
            self.stack.setCurrentWidget(self.page_booru)
        else:
            self.cmb_plataforma.clear()
            self.cmb_plataforma.addItems(list(WIKI_ADAPTERS))
            self.stack.setCurrentWidget(self.page_wiki)

    def _elegir_carpeta(self) -> None:
        try:
            carpeta = QFileDialog.getExistingDirectory(
                self, "Elegir carpeta de salida", self.ed_carpeta.text()
            )
            if carpeta:
                self.ed_carpeta.setText(carpeta)
        except Exception as exc:
            logger.exception("excepcion en _elegir_carpeta")
            QMessageBox.critical(self, "Error", f"Error inesperado: {exc}")

    # ------------------------------------------------------------------ diálogos
    def _on_error(self, mensaje: str) -> None:
        """Error fatal: diálogo crítico + detalle en el log."""
        logger.error("%s", mensaje)
        QMessageBox.critical(
            self,
            "Error",
            f"{mensaje}\n\nLos detalles están en el log (consola y archivo .log).",
        )

    def _on_http_event(self, mensaje: str) -> None:
        """Estatus de conexión en vivo: peticiones, respuestas, pausas y errores."""
        try:
            corto = mensaje if len(mensaje) <= 150 else mensaje[:147] + "…"
            self.lbl_conexion.setText(f"Conexión: {corto}")
            self.lbl_conexion.setToolTip(mensaje)
            problema = any(
                marca in mensaje
                for marca in ("CAPTCHA", "HTTP 4", "HTTP 5", "⏸", "bloqueo", "pausa")
            )
            self.lbl_conexion.setStyleSheet(
                "color: #b00020;" if problema else "color: #1b5e20;"
            )
        except Exception:
            logger.exception("excepcion en _on_http_event")

    def _on_job_finished(self, resumen: dict) -> None:
        """Diálogos de resultado: descargas y avisos cuando nada pasó los filtros."""
        try:
            # Si esta búsqueda no trajo imágenes, no dejar las anteriores a medias
            if not self._muestra_recibida:
                self.galeria.poner_mensaje(MENSAJE_VACIO)
            tipo = resumen.get("tipo")
            estado = resumen.get("estado", "")
            descartados = resumen.get("descartados") or {}
            encontrados = resumen.get("encontrados", 0)

            # Nada pasó los filtros: explicar el porqué (evita el "no hace nada")
            if estado == "sin resultados" or (tipo == "busqueda" and resumen.get("total", 0) == 0
                                              and (descartados or encontrados == 0)):
                if encontrados:
                    texto = (f"Se encontraron {encontrados} resultados, pero ninguno pasó "
                             "los filtros del proyecto.")
                else:
                    texto = "La búsqueda no devolvió resultados para esos filtros."
                if descartados:
                    detalle = "\n".join(f"• {k}: {v}" for k, v in sorted(descartados.items()))
                    texto += f"\n\nDescartados por:\n{detalle}"
                if any("rating" in clave for clave in descartados):
                    texto += ('\n\nSugerencia: si quieres contenido adulto, marca '
                              '"Permitir contenido adulto" en Opciones.')
                if any("pago" in clave for clave in descartados):
                    texto += ("\nLos resultados que enlazan plataformas de pago se descartan "
                              "siempre (criterio ético/legal del proyecto).")
                if descartados and resumen.get("limitar"):
                    texto += ("\n\nNota: tienes activo \"Limitar cantidad de descargas\"; "
                              "la búsqueda solo pidió esa cantidad.")
                QMessageBox.information(self, "Sin resultados", texto)
                return

            if tipo != "descarga":
                return
            if estado == "completada":
                texto = (
                    f"Se descargaron {resumen.get('guardados', 0)} de "
                    f"{resumen.get('total', 0)} archivos."
                )
                if resumen.get("fallas"):
                    texto += f"\nCon {resumen['fallas']} fallo(s)."
                texto += f"\n\nCarpeta: {resumen.get('carpeta', '')}"
                QMessageBox.information(self, "Descarga completada", texto)
            elif estado == "cancelada":
                QMessageBox.information(
                    self, "Descarga cancelada", "La descarga fue cancelada por el usuario."
                )
            elif estado == "error":
                detalle = resumen.get("error") or "Error desconocido"
                QMessageBox.critical(
                    self, "Error en la descarga",
                    f"{detalle}\n\nDetalles en el log (consola y archivo .log).",
                )
        except Exception as exc:
            logger.exception("excepcion en _on_job_finished")
            QMessageBox.critical(self, "Error", f"Error inesperado: {exc}")

    # ------------------------------------------------------------------ acciones
    def _settings(self) -> dict:
        return {
            "tipo": self.cmb_tipo.currentText(),
            "plataforma": self.cmb_plataforma.currentText(),
            "usuario": self.ed_usuario.text(),
            "instancia": self.ed_instancia.text(),
            "keyword": self.ed_keyword.text(),
            "hashtag": self.ed_hashtag.text(),
            "tags": self.ed_tags.text(),
            "fandom": self.ed_fandom.text(),
            "character": self.ed_character.text(),
            "wiki_url": self.ed_wiki_url.text(),
            "carpeta": self.ed_carpeta.text().strip(),
            "solo_liberado": self.chk_liberado.isChecked(),
            "permitir_adulto": self.chk_adulto.isChecked(),
            "mejorar": self.chk_mejorar.isChecked(),
            "modo_ia": self.chk_ia.isChecked(),
            "calidad_webp": self.sld_calidad.value(),
            "limitar": self.chk_limite.isChecked(),
            "cantidad": self.spin_cantidad.value(),
            "sidecar_json": self.chk_sidecar.isChecked(),
        }

    def _validar(self, s: dict) -> str | None:
        if s["tipo"] == "Red social":
            if not (s["usuario"] or s["keyword"] or s["hashtag"]):
                return "Ingresa @usuario, palabra clave y/o #hashtag."
        elif s["tipo"] == "Booru":
            if not s["tags"]:
                return "Ingresa al menos una tag para el booru."
        else:
            if not (s["fandom"] or s["character"] or s["wiki_url"]):
                return "Ingresa el fandom, el personaje/concepto o la URL de la wiki."
        if not s["carpeta"]:
            return "Elige una carpeta de salida."
        return None

    def _on_buscar(self) -> None:
        try:
            if self.controller.is_busy():
                return
            s = self._settings()
            error = self._validar(s)
            if error:
                self.statusBar().showMessage(f"⚠ {error}")
                return
            self._preparar_busqueda_nueva()
            self._tarea = "buscar"          # la barra de progreso lo refleja
            self.controller.buscar(s)
        except Exception as exc:
            logger.exception("excepcion en _on_buscar")
            QMessageBox.critical(self, "Error", f"Error inesperado: {exc}\n\nDetalles en el log.")

    def _on_descargar(self) -> None:
        try:
            if self.controller.is_busy():
                self.controller.cancelar()  # el botón actúa como Cancelar
                return
            s = self._settings()
            error = self._validar(s)
            if error:
                self.statusBar().showMessage(f"⚠ {error}")
                return
            # Confirmación antes de iniciar la descarga
            detalle = (
                f"Plataforma: {s['plataforma']}\n"
                f"Carpeta: {s['carpeta'] or config.DEFAULT_OUTPUT_DIR}\n"
                f"Límite: {s['cantidad']} archivos\n" if s["limitar"]
                else f"Plataforma: {s['plataforma']}\n"
                     f"Carpeta: {s['carpeta'] or config.DEFAULT_OUTPUT_DIR}\n"
                     f"Límite: sin límite (todo lo encontrado)\n"
            )
            respuesta = QMessageBox.question(
                self,
                "Iniciar descarga",
                f"¿Deseas iniciar la descarga?\n\n{detalle}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if respuesta != QMessageBox.Yes:
                self.statusBar().showMessage("Descarga no iniciada")
                return
            self._preparar_busqueda_nueva()
            self._tarea = "descargar"       # la barra de progreso lo refleja
            self.controller.descargar(s)
        except Exception as exc:
            logger.exception("excepcion en _on_descargar")
            QMessageBox.critical(self, "Error", f"Error inesperado: {exc}\n\nDetalles en el log.")

    def _on_limpiar(self) -> None:
        try:
            if self.controller.is_busy():
                return  # bloqueado mientras se descarga
            for w in (self.ed_usuario, self.ed_keyword, self.ed_hashtag, self.ed_instancia,
                      self.ed_tags, self.ed_fandom, self.ed_character, self.ed_wiki_url):
                w.clear()
            self.lst_resultados.clear()
            self.galeria.limpiar()
            self.progress.setVisible(False)
            self.controller.limpiar()
            self.statusBar().showMessage("Formulario limpio")
        except Exception as exc:
            logger.exception("excepcion en _on_limpiar")
            QMessageBox.critical(self, "Error", f"Error inesperado: {exc}\n\nDetalles en el log.")

    # ------------------------------------------------------------------ slots del controlador
    def _preparar_busqueda_nueva(self) -> None:
        """Al iniciar una búsqueda/descarga: limpia resultados y la imagen anterior."""
        self.lst_resultados.clear()
        self._muestra_recibida = False
        self.galeria.limpiar(MENSAJE_BUSCANDO)
        self.progress.setValue(0)

    def _on_results(self, items: list) -> None:
        self.lst_resultados.addItems(items)

    def _on_galeria_total(self, total: int) -> None:
        """El controlador anuncia cuántas imágenes tendrá el carrusel."""
        self.galeria.definir_total(total)

    def _on_galeria_item(self, posicion: int, datos: bytes) -> None:
        """Llega una miniatura: se añade al carrusel (la primera se muestra ya)."""
        if self.galeria.agregar(posicion, datos):
            self._muestra_recibida = True

    def _abrir_lightbox(self, indice: int) -> None:
        """Visor ampliado dentro de la ventana (estilo fancybox)."""
        if not self.galeria.total():
            return
        if self._lightbox is None:
            self._lightbox = Lightbox(self.galeria)
        self._lightbox.abrir(indice)

    # ------------------------------------------------------------------ tamaño en pantalla
    def ajustar_a_pantalla(self) -> None:
        """Ajusta la ventana a la zona útil de la pantalla (sin tapar la barra de tareas).

        En Windows/macOS/Linux `availableGeometry()` ya descuenta la barra de tareas
        (o el dock/panel). Si la pantalla es pequeña, la ventana se reduce y el
        contenido se puede desplazar (QScrollArea) en lugar de salirse.
        """
        pantalla = self.screen() or QApplication.primaryScreen()
        if pantalla is None:
            self.resize(980, 760)
            return
        util = pantalla.availableGeometry()
        margen = 24
        ancho = max(520, min(1020, util.width() - margen))
        alto = max(420, min(820, util.height() - margen))
        self.resize(ancho, alto)
        self.move(util.x() + max(0, (util.width() - ancho) // 2),
                  util.y() + max(0, (util.height() - alto) // 2))
        logger.info("ventana ajustada a %dx%d (pantalla útil %dx%d)",
                    ancho, alto, util.width(), util.height())

    def showEvent(self, evento):  # noqa: N802
        super().showEvent(evento)
        if not getattr(self, "_ajustada", False):
            self._ajustada = True
            self.ajustar_a_pantalla()

    def resizeEvent(self, evento):  # noqa: N802
        super().resizeEvent(evento)
        if self._lightbox is not None and self._lightbox.isVisible():
            self._lightbox.setGeometry(self.rect())

    def _on_progress(self, done: int, total: int) -> None:
        self.progress.setVisible(True)
        self.progress.setRange(0, total)
        self.progress.setValue(done)

    def _on_state(self, state: str) -> None:
        if state == "running":
            self._set_running()
        else:
            self._set_idle()

    # ------------------------------------------------------------------ estados de UI
    def _set_running(self) -> None:
        self.btn_descargar.setText("⏹️ Cancelar")
        self.btn_buscar.setEnabled(False)
        self.btn_limpiar.setEnabled(False)
        self.cmb_tipo.setEnabled(False)
        self.cmb_plataforma.setEnabled(False)
        self.stack.setEnabled(False)
        self.filtros_box.setEnabled(False)
        self.ed_carpeta.setEnabled(False)
        self.btn_carpeta.setEnabled(False)
        # La barra refleja la función en curso: buscar (indeterminado) o descargar (%)
        self.progress.setValue(0)
        if getattr(self, "_tarea", "descargar") == "buscar":
            self.progress.setRange(0, 0)
            self.progress.setFormat("🔍 buscando…")
        else:
            self.progress.setRange(0, 0)  # indeterminado hasta el primer avance
            self.progress.setFormat("⬇️ %p%")
        self.progress.setVisible(True)

    def _set_idle(self) -> None:
        self.btn_descargar.setText("⬇️ Descargar")
        self.btn_buscar.setEnabled(True)
        self.btn_limpiar.setEnabled(True)
        self.cmb_tipo.setEnabled(True)
        self.cmb_plataforma.setEnabled(True)
        self.stack.setEnabled(True)
        self.filtros_box.setEnabled(True)
        self.ed_carpeta.setEnabled(True)
        self.btn_carpeta.setEnabled(True)
        self.progress.setVisible(False)  # sin tarea activa no hay progreso que mostrar
        # Al cancelar se conservan el formulario, los resultados y la imagen de ejemplo.
