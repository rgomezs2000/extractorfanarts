"""Vista principal de escritorio (PySide6): formulario de filtros, botones
Buscar / Descargar↔Cancelar / Limpiar, galería de ejemplo (carrusel) y resultados.

Reglas de UI:
  - Limpiar limpia el formulario (sin descargas) y queda BLOQUEADO mientras se descarga.
  - Descargar se convierte en Cancelar durante la descarga.
  - Al cancelar se restaura todo como estaba, sin restablecer el formulario,
    y la galería se mantiene.
  - La galería se recarga (se vacía) en cada búsqueda o descarga nueva, y al pulsar
    una imagen se abre el visor ampliado DENTRO de la ventana (estilo fancybox).
  - Clic derecho sobre cualquier imagen (imagen grande, miniatura o visor ampliado)
    abre el menú contextual: copiar imagen, guardar imagen, guardar como…, abrir la
    imagen original en el navegador predeterminado y copiar su enlace. Copiar y
    guardar de forma individual pasan por la MISMA política de calidad que la
    descarga masiva (conversión obligatoria a .webp + mejora Lanczos/IA según las
    casillas).
"""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import (
    QByteArray, QEvent, QMimeData, QObject, QRunnable, Qt, QThreadPool, QTimer,
    QUrl, Signal,
)
from PySide6.QtGui import QAction, QDesktopServices, QImage, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QMainWindow, QMenu, QMessageBox, QProgressBar, QPushButton, QSizePolicy,
    QSlider, QSpinBox, QStackedWidget, QTextBrowser, QToolBar, QVBoxLayout, QWidget,
)

from .. import ayuda, config, updater
from ..controllers.main_controller import MainController
from ..services import filters as filtros
from ..services.adapters import BOORU_ADAPTERS, SOCIAL_ADAPTERS, WIKI_ADAPTERS
from .galeria import MENSAJE_BUSCANDO, MENSAJE_VACIO, GaleriaWidget, Lightbox

logger = logging.getLogger("imaginteca")

TIPOS = ("Red social", "Booru", "Wiki fandom")


class MainWindow(QMainWindow):
    def __init__(self, controller: MainController):
        super().__init__()
        self.controller = controller
        self.setWindowTitle(f"🖼️ {config.APP_NAME} — tu colección de imágenes")
        self._muestra_recibida = False
        self._error_mostrado = False      # se avisó de un error crítico en esta operación
        self._tarea = "descargar"
        self._lightbox: Lightbox | None = None
        self._individual_en_curso = 0     # acciones individuales en segundo plano
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
        # Márgenes/espaciado compactos y SIN área desplazable: todo el formulario cabe
        # siempre en la ventana (los campos se estiran y el panel de resultados se
        # lleva el espacio sobrante). La ventana no baja de su tamaño mínimo real.
        root.setContentsMargins(8, 6, 8, 6)
        root.setSpacing(6)
        self.setCentralWidget(central)

        # Fuente: fila normal (los campos se estiran con la ventana)
        fuente_box = QGroupBox("🔎 Fuente de búsqueda")
        fl = QHBoxLayout(fuente_box)
        fl.setContentsMargins(8, 6, 8, 6)
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
        fl.addWidget(self.cmb_plataforma, 1)
        root.addWidget(fuente_box)

        # Filtros por tipo (stacked)
        self.stack = QStackedWidget()

        self.page_social = QWidget()
        v = QVBoxLayout(self.page_social)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)
        aviso_social = QLabel(
            "Combina los campos que quieras (se exigen todos los que rellenes) y admite "
            "varios valores: varios hashtags separados por espacios («#lola_loud "
            "#the_loud_house») y varias palabras clave separadas por comas («Lola Loud, "
            "The Loud House»). De cada campo vale cualquiera de sus valores."
        )
        aviso_social.setWordWrap(True)   # se ajusta al ancho de la ventana
        v.addWidget(aviso_social)
        self.ed_usuario = QLineEdit()
        self.ed_usuario.setPlaceholderText("👤 @usuario  (o @usuario@instancia)")
        self.ed_keyword = QLineEdit()
        self.ed_keyword.setPlaceholderText(
            "🔤 palabra clave — varias: «Lola Loud, The Loud House» (con comas)")
        self.ed_hashtag = QLineEdit()
        self.ed_hashtag.setPlaceholderText(
            "#️⃣ #hashtag — varios: «#lola_loud #the_loud_house»")
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
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)
        v.addWidget(QLabel(
            "🏷️ Tags del booru (los que quieras: se buscan TODOS a la vez; sepáralos con "
            "espacios o comas. También valen operadores: -tag, rating:general, score:>10):"))
        self.ed_tags = QLineEdit()
        self.ed_tags.setPlaceholderText("🏷️ ej. lori_loud 1girl solo blonde_hair")
        v.addWidget(self.ed_tags)

        self.page_wiki = QWidget()
        v = QVBoxLayout(self.page_wiki)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)
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

        # Opciones: rejilla estable de 2 columnas (el alto no cambia al redimensionar,
        # así TODO cabe siempre en la ventana sin barras de desplazamiento)
        self.filtros_box = QGroupBox("⚙️ Opciones")
        ov = QVBoxLayout(self.filtros_box)
        ov.setContentsMargins(8, 6, 8, 6)
        ov.setSpacing(4)
        cuadricula = QGridLayout()
        cuadricula.setHorizontalSpacing(18)
        cuadricula.setVerticalSpacing(2)
        cuadricula.setColumnStretch(0, 1)
        cuadricula.setColumnStretch(1, 1)
        self.chk_liberado = QCheckBox("⚖️ Solo licencia liberada")
        self.chk_liberado.setToolTip(
            "Si se marca, solo se procesan obras con licencia permisiva explícita "
            "(CC0/CC-BY/dominio público). La mayoría del fanart no la tiene."
        )
        self.chk_adulto = QCheckBox("🔞 Contenido adulto")
        self.chk_adulto.setToolTip(
            "Confirmo que soy mayor de edad en mi jurisdicción. "
            "Por defecto se omiten los ratings questionable/explicit."
        )
        self.chk_mejorar = QCheckBox("✨ Mejorar calidad")
        self.chk_mejorar.setChecked(config.ENHANCE_DEFAULT_ON)
        self.chk_mejorar.setToolTip(
            "Controla SOLO el upscaling y la definición. El guardado en .webp se aplica "
            "SIEMPRE (el original nunca se conserva). Reglas: hasta 699px→4x · "
            "700-799px→3x · 800px o más→2x, con tope de 8K (7680 px). Por encima de "
            "7679 px no se reescala. Al guardar verás el tamaño de partida y el "
            "resultado real en la barra de estado."
        )
        self.chk_ia = QCheckBox("🤖 Modo IA")
        self.chk_ia.setToolTip(
            "Usa el motor IA Vulkan si está instalado (python scripts\\setup_vendor.py --ai); "
            "si no está disponible, usa Lanczos + afilado suave automáticamente."
        )
        cuadricula.addWidget(self.chk_liberado, 0, 0)
        cuadricula.addWidget(self.chk_adulto, 0, 1)
        cuadricula.addWidget(self.chk_mejorar, 1, 0)
        cuadricula.addWidget(self.chk_ia, 1, 1)
        ov.addLayout(cuadricula)

        # Ver la lista negra y los filtros que se aplican siempre (solo lectura)
        fila_filtros = QHBoxLayout()
        self.btn_filtros = QPushButton("ℹ️ ¿Qué se filtra? (lista negra)")
        self.btn_filtros.setFlat(True)
        self.btn_filtros.setToolTip(
            "Muestra la lista negra de tags, las plataformas de pago excluidas y el resto "
            "de filtros que se aplican siempre antes de mostrar o descargar resultados"
        )
        self.btn_filtros.setCursor(Qt.PointingHandCursor)
        self.btn_filtros.clicked.connect(self._mostrar_filtros)
        fila_filtros.addWidget(self.btn_filtros)
        fila_filtros.addStretch(1)
        ov.addLayout(fila_filtros)

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

        # Límite de cantidad de descargas
        fl4 = QHBoxLayout()
        fl4.setSpacing(10)
        self.chk_limite = QCheckBox("🔢 Limitar cantidad")
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
        self.chk_sidecar = QCheckBox("🏷️ Guardar .json")
        self.chk_sidecar.setChecked(config.WRITE_SIDECAR_JSON)
        self.chk_sidecar.setToolTip(
            "Guarda un archivo .json junto a cada imagen con autoría, origen y "
            "licencia. Desactivado: solo se guarda la imagen."
        )
        fl4.addWidget(self.chk_sidecar)
        fl4.addStretch(1)
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
        self.galeria.setMinimumHeight(130)
        self.lst_resultados = QListWidget()
        self.lst_resultados.setMinimumHeight(45)

        res_box = QGroupBox("🖼️ Resultados")
        rv = QVBoxLayout(res_box)
        rv.addWidget(self.galeria, 1)
        rv.addWidget(QLabel("📋 Resultados encontrados:"))
        rv.addWidget(self.lst_resultados)
        root.addWidget(res_box, 1)

        # Progreso: siempre visible (en reposo marca 0 %; al buscar/descargar avanza)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("⬇️ 0% · en reposo")
        self.progress.setToolTip("Progreso de la operación (búsqueda o descarga)")
        root.addWidget(self.progress)

        # Estatus de conexión (última petición/respuesta)
        self.lbl_conexion = QLabel("📡 Conexión: —")
        self.lbl_conexion.setStyleSheet("color: #444444;")
        self.lbl_conexion.setWordWrap(True)   # no fuerza el ancho de la ventana
        self.lbl_conexion.setToolTip("Última actividad HTTP: peticiones, respuestas y pausas")
        root.addWidget(self.lbl_conexion)

        self.statusBar().showMessage("Listo")

        self._crear_acciones_imagen()

    # ------------------------------------------------------------------ menú contextual
    def _crear_acciones_imagen(self) -> None:
        """Acciones del menú contextual (clic derecho) sobre una imagen.

        Se crean UNA vez y viven en la ventana: así funcionan tanto en el menú
        emergente como con sus atajos de teclado (Ctrl+C / Ctrl+S / Ctrl+Shift+C).
        """
        self.act_copiar_imagen = QAction("📋 Copiar imagen", self)
        self.act_copiar_imagen.setShortcut(QKeySequence.Copy)
        self.act_copiar_imagen.setToolTip(
            "Copia la imagen ORIGINAL al portapapeles aplicando la calidad "
            "configurada (conversión a .webp y mejora si está marcada). Ctrl+C"
        )
        self.act_copiar_imagen.triggered.connect(lambda: self._accion_imagen("copiar"))

        self.act_guardar_imagen = QAction("💾 Guardar imagen", self)
        self.act_guardar_imagen.setShortcut(QKeySequence.Save)
        self.act_guardar_imagen.setToolTip(
            "Guarda la imagen ORIGINAL en la carpeta de salida con la misma "
            "conversión a .webp y mejora que la descarga masiva. Ctrl+S"
        )
        self.act_guardar_imagen.triggered.connect(lambda: self._accion_imagen("guardar"))

        self.act_guardar_como = QAction("🗂️ Guardar como…", self)
        self.act_guardar_como.setShortcut(QKeySequence.SaveAs)
        self.act_guardar_como.setToolTip(
            "Guarda la imagen ORIGINAL donde tú elijas (carpeta y nombre), con la "
            "misma conversión a .webp y mejora que la descarga masiva. Ctrl+Shift+S"
        )
        self.act_guardar_como.triggered.connect(self._guardar_como)

        self.act_abrir_original = QAction("🌐 Abrir imagen original en el navegador", self)
        self.act_abrir_original.setToolTip(
            "Abre la URL original de la imagen en el navegador predeterminado del sistema"
        )
        self.act_abrir_original.triggered.connect(lambda: self._accion_imagen("abrir"))

        self.act_copiar_enlace = QAction("🔗 Copiar enlace de la imagen original", self)
        self.act_copiar_enlace.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.act_copiar_enlace.setToolTip(
            "Copia al portapapeles la URL original de la imagen. Ctrl+Shift+C"
        )
        self.act_copiar_enlace.triggered.connect(lambda: self._accion_imagen("enlace"))

        # Solo las tres primeras descargan y procesan (necesitan red y no deben
        # solaparse con una búsqueda/descarga en curso).
        self._acciones_con_red = (self.act_copiar_imagen, self.act_guardar_imagen,
                                  self.act_guardar_como)
        self._acciones_sin_red = (self.act_abrir_original, self.act_copiar_enlace)
        for accion in self._acciones_con_red + self._acciones_sin_red:
            self.addAction(accion)
        self._actualizar_acciones_imagen()

    def _actualizar_acciones_imagen(self) -> None:
        """Habilita las acciones del menú solo cuando tienen sentido."""
        hay_imagenes = self.galeria.total() > 0
        libre = not self.controller.is_busy() and self._individual_en_curso == 0
        for accion in self._acciones_con_red:
            accion.setEnabled(hay_imagenes and libre)
        for accion in self._acciones_sin_red:
            accion.setEnabled(hay_imagenes)   # no usan red: siempre disponibles
        carpeta = self.ed_carpeta.text().strip() or str(config.DEFAULT_OUTPUT_DIR)
        self.act_guardar_imagen.setToolTip(
            "Guarda la imagen ORIGINAL en la carpeta de salida "
            f"({carpeta}) con la misma conversión a .webp y mejora que la "
            "descarga masiva. Ctrl+S"
        )

    def _construir_menu_imagen(self) -> QMenu:
        """El menú emergente del clic derecho (sin mostrarlo)."""
        menu = QMenu(self)
        menu.addAction(self.act_copiar_imagen)
        menu.addAction(self.act_guardar_imagen)
        menu.addAction(self.act_guardar_como)
        menu.addSeparator()
        menu.addAction(self.act_abrir_original)
        menu.addAction(self.act_copiar_enlace)
        return menu

    def _on_menu_contextual(self, indice: int, pos_global) -> None:
        """Clic derecho sobre una imagen de la galería (o en el visor ampliado)."""
        try:
            self.galeria.mostrar(indice)   # el menú actúa sobre la imagen señalada
            self._actualizar_acciones_imagen()
            self._construir_menu_imagen().exec(pos_global)
        except Exception as exc:  # noqa: BLE001
            logger.exception("excepcion en _on_menu_contextual")
            QMessageBox.critical(self, "Error", f"Error inesperado: {exc}")

    def _accion_imagen(self, accion: str) -> None:
        """Ejecuta una acción del menú sobre la imagen que se está mostrando."""
        try:
            if not self.galeria.total():
                return
            indice = self.galeria.indice()
            obra = self.controller.obra_en(indice + 1)
            if obra is None:
                return
            if accion == "abrir":
                self._abrir_en_navegador(obra.url)
                return
            if accion == "enlace":
                if not obra.url:
                    self.statusBar().showMessage("⚠ Esta obra no tiene enlace original")
                    return
                QApplication.clipboard().setText(obra.url)
                self.statusBar().showMessage(
                    "🔗 Enlace de la imagen original copiado al portapapeles")
                logger.info("enlace original copiado: %s", obra.url)
                return
            if self.controller.is_busy():
                self.statusBar().showMessage(
                    "⚠ Hay una operación en curso; espera a que termine o cancélala")
                return
            if self._individual_en_curso:
                self.statusBar().showMessage("⏳ Ya se está procesando otra imagen…")
                return
            verbo = "Copiando" if accion == "copiar" else "Guardando"
            self.statusBar().showMessage(
                f"⏳ {verbo} la imagen {indice + 1} de {self.galeria.total()}…")
            # La MISMA configuración de la ventana: la calidad (.webp + mejora
            # Lanczos/IA) viaja en `settings`, igual que en la descarga masiva.
            self.controller.procesar_individual(indice + 1, self._settings(), accion)
        except Exception as exc:  # noqa: BLE001
            logger.exception("excepcion en _accion_imagen")
            QMessageBox.critical(self, "Error", f"Error inesperado: {exc}")

    def _guardar_como(self) -> None:
        """«Guardar como…»: el usuario elige carpeta y nombre para esa imagen.

        El archivo final es siempre .webp (aunque escribas otro sufijo) y pasa por
        la misma conversión y mejora que la descarga masiva.
        """
        try:
            if not self.galeria.total() or self.controller.is_busy() or self._individual_en_curso:
                return
            indice = self.galeria.indice()
            obra = self.controller.obra_en(indice + 1)
            if obra is None:
                return
            carpeta = self.ed_carpeta.text().strip() or str(config.DEFAULT_OUTPUT_DIR)
            sugerido = str(Path(carpeta) / self.controller.nombre_sugerido(indice + 1))
            ruta, _filtro = QFileDialog.getSaveFileName(
                self, "Guardar imagen como", sugerido,
                "Imagen WebP (*.webp);;Todos los archivos (*)",
            )
            if not ruta:
                self.statusBar().showMessage("Guardado cancelado")
                return
            destino = Path(ruta).expanduser()
            if destino.suffix.lower() != ".webp":
                destino = destino.with_suffix(".webp")
            # Comprobación de escritura aquí: si la carpeta elegida no sirve, se dice
            # con un diálogo claro en vez de encadenar un fallo en segundo plano.
            try:
                destino.parent.mkdir(parents=True, exist_ok=True)
                prueba = destino.parent / ".escritura_ok"
                prueba.write_text("ok", encoding="utf-8")
                prueba.unlink()
            except OSError as exc:
                logger.warning("carpeta elegida no escribible (%s): %s", destino.parent, exc)
                QMessageBox.critical(
                    self, "No se puede guardar",
                    f"No se puede escribir en la carpeta elegida:\n{destino.parent}\n\n{exc}\n\n"
                    "Si lanzaste la app desde la terminal de un agente/IDE con sandbox, el\n"
                    "proceso solo puede escribir dentro del proyecto: cierra la app y ábrela\n"
                    "con doble clic desde el Explorador (o desde una consola normal).")
                return
            self.statusBar().showMessage(f"⏳ Guardando la imagen {indice + 1} como {destino.name}…")
            # MISMA configuración de calidad que la descarga masiva
            self.controller.procesar_individual(
                indice + 1, self._settings(), "guardar_como", destino=destino)
        except Exception as exc:  # noqa: BLE001
            logger.exception("excepcion en _guardar_como")
            QMessageBox.critical(self, "Error", f"Error inesperado: {exc}")

    def _abrir_en_navegador(self, url: str) -> None:
        """Abre la URL en el navegador predeterminado del sistema."""
        if not url:
            self.statusBar().showMessage("⚠ Esta obra no tiene enlace original")
            return
        if QDesktopServices.openUrl(QUrl(url)):
            self.statusBar().showMessage(f"🌐 Abriendo en el navegador: {url}")
            logger.info("imagen original abierta en el navegador: %s", url)
        else:
            self.statusBar().showMessage(f"⚠ No se pudo abrir el enlace: {url}")
            logger.warning("QDesktopServices no pudo abrir la URL: %s", url)

    # ------------------------------------------------------------------ resultados individuales
    def _on_individual_iniciado(self, posicion: int, accion: str) -> None:
        self._individual_en_curso += 1
        self._actualizar_acciones_imagen()
        verbo = "Copiando" if accion == "copiar" else "Guardando"
        self.statusBar().showMessage(f"⏳ {verbo} la imagen {posicion}…")

    def _on_individual_listo(self, posicion: int, ruta: str, datos: bytes, meta: dict) -> None:
        """Llegó una imagen procesada: se guarda (ruta) o se copia (datos .webp)."""
        try:
            self._individual_en_curso = max(0, self._individual_en_curso - 1)
            self._actualizar_acciones_imagen()
            modo = (meta or {}).get("modo") or ""
            # El resumen trae los tamaños («153x153 → 612x612 · Lanczos 4x»), que es lo
            # que permite comprobar de un vistazo que la mejora se aplicó de verdad.
            detalle = (meta or {}).get("resumen") or modo
            if ruta:
                texto = f"✅ Guardado: {ruta}"
                if detalle:
                    texto += f"  ·  {detalle}"
                self.statusBar().showMessage(texto)
                logger.info("imagen %d guardada: %s (%s)", posicion, ruta, detalle)
                return
            if not datos:
                self.statusBar().showMessage("⚠ La imagen llegó vacía; no se pudo copiar")
                return
            correcto, motivo = self._copiar_imagen(datos)
            if correcto:
                extra = f"  ·  {detalle}" if detalle else ""
                self.statusBar().showMessage(
                    f"📋 Imagen {posicion} copiada al portapapeles en .webp{extra}")
                logger.info("imagen %d copiada al portapapeles (%s)", posicion, detalle)
            else:
                self.statusBar().showMessage(f"⚠ No se pudo copiar la imagen: {motivo}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("excepcion en _on_individual_listo")
            QMessageBox.critical(self, "Error", f"Error inesperado: {exc}")

    def _on_individual_error(self, posicion: int, mensaje: str) -> None:
        """Una acción individual falló: aviso breve, sin diálogo modal."""
        self._individual_en_curso = max(0, self._individual_en_curso - 1)
        self._actualizar_acciones_imagen()
        corto = mensaje if len(mensaje) <= 160 else mensaje[:157] + "…"
        self.statusBar().showMessage(f"⚠ Imagen {posicion}: {corto}")
        logger.warning("acción individual sobre la imagen %d fallida: %s", posicion, mensaje)

    def _copiar_imagen(self, datos: bytes) -> tuple[bool, str]:
        """Pone en el portapapeles la imagen .webp ya convertida/mejorada.

        Se publica como `image/webp` (el formato obligatorio del proyecto) y, además,
        como imagen Qt estándar (PNG/DIB) para que se pueda pegar en cualquier
        programa. Si Qt no pudiera decodificar el .webp se reintenta con Pillow.
        """
        portapapeles = QApplication.clipboard()
        if portapapeles is None:      # plataforma sin portapapeles (raro)
            return False, "el sistema no tiene portapapeles"
        imagen = QImage.fromData(QByteArray(datos), "WEBP")
        if imagen.isNull():
            try:
                import io

                from PIL import Image
                with Image.open(io.BytesIO(datos)) as abierta:
                    buffer = io.BytesIO()
                    abierta.convert("RGBA" if "A" in abierta.getbands() else "RGB").save(
                        buffer, "PNG")
                imagen = QImage.fromData(QByteArray(buffer.getvalue()), "PNG")
            except Exception:  # noqa: BLE001
                logger.warning("no se pudo decodificar el .webp para el portapapeles",
                               exc_info=True)
        contenido = QMimeData()
        contenido.setData("image/webp", QByteArray(datos))
        if not imagen.isNull():
            contenido.setImageData(imagen)
        portapapeles.setMimeData(contenido)
        if imagen.isNull():
            return True, "solo como image/webp (no se pudo decodificar para pegar)"
        return True, ""

    # ------------------------------------------------------------------ conexiones
    # ------------------------------------------------------------------ atajos de teclado
    def _atajos_de_teclado(self) -> None:
        """Teclado: Enter busca, Shift+Enter descarga, Esc cancela, Enter en los botones.

        - **Enter** en cualquier campo o control de búsqueda (y en el cuadro de cantidad)
          lanza la **búsqueda**; **Shift+Enter** lanza la **descarga**.
        - En **Salida** (carpeta) Enter abre el diálogo para elegir carpeta, no busca.
        - **Enter** sobre un botón enfocado (Buscar, Descargar/Cancelar, Limpiar) lo pulsa;
          si hay una operación en curso, Descargar es **Cancelar**: Enter y **Esc** cancelan.
        - **Enter** sobre la imagen del carrusel (o su miniatura) abre el visor ampliado.
        """
        self._campos_enter = [self.ed_usuario, self.ed_keyword, self.ed_hashtag,
                              self.ed_instancia, self.ed_tags, self.ed_fandom,
                              self.ed_character, self.ed_wiki_url]
        # Controles que también buscan con Enter (las casillas y deslizadores no usan
        # Enter para nada propio; los desplegables solo si están cerrados).
        self._controles_enter = [self.cmb_tipo, self.cmb_plataforma, self.chk_liberado,
                                 self.chk_adulto, self.chk_mejorar, self.chk_ia,
                                 self.sld_calidad, self.chk_limite, self.chk_sidecar]
        for campo in self._campos_enter + self._controles_enter:
            campo.installEventFilter(self)
        # El cuadro de cantidad es un QSpinBox: su editor es quien recibe la tecla
        editor = getattr(self.spin_cantidad, "lineEdit", lambda: None)()
        if editor is not None:
            editor.installEventFilter(self)
        # En Salida, Enter elige carpeta (excepción pedida: ahí no se busca)
        self.ed_carpeta.returnPressed.connect(self._elegir_carpeta)

        # Enter sobre un botón enfocado = pulsarlo (WidgetShortcut: solo con el foco ahí)
        self._atajos = {}
        for nombre, boton in (("buscar", self.btn_buscar),
                              ("descargar", self.btn_descargar),
                              ("limpiar", self.btn_limpiar)):
            atajos = []
            for tecla in (Qt.Key_Return, Qt.Key_Enter):
                atajo = QShortcut(QKeySequence(tecla), boton)
                atajo.setContext(Qt.WidgetShortcut)
                atajo.activated.connect(boton.click)
                atajos.append(atajo)
            self._atajos[nombre] = atajos

        # Esc: cancela la operación en curso (y el visor ampliado, si está abierto)
        self.atajo_escape = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.atajo_escape.activated.connect(self._on_escape)

        # Alt+F4 (y Ctrl+Q) cierran la app pasando por el cierre ordenado
        self.atajos_cerrar = []
        for secuencia in ("Alt+F4", "Ctrl+Q"):
            atajo = QShortcut(QKeySequence(secuencia), self)
            atajo.setContext(Qt.WindowShortcut)
            atajo.activated.connect(self.close)
            self.atajos_cerrar.append(atajo)

        for boton, ayuda in ((self.btn_buscar, "Enter en cualquier campo"),
                             (self.btn_descargar, "Shift+Enter en cualquier campo"),
                             (self.btn_limpiar, "Enter con el botón enfocado")):
            extra = f" — {ayuda}"
            if extra not in boton.toolTip():
                boton.setToolTip((boton.toolTip() or "") + extra)

    def _combo_desplegado(self, objeto) -> bool:
        """¿El desplegable indicado tiene su lista abierta? (entonces Enter no busca)"""
        vista = getattr(objeto, "view", None)
        try:
            return bool(vista is not None and vista().isVisible())
        except Exception:  # noqa: BLE001
            return False

    def eventFilter(self, objeto, evento):  # noqa: N802
        """Enter en campos y controles de búsqueda: Enter busca, Shift+Enter descarga."""
        try:
            if (evento.type() == QEvent.KeyPress
                    and evento.key() in (Qt.Key_Return, Qt.Key_Enter)
                    and objeto is not self.ed_carpeta
                    and not self._combo_desplegado(objeto)):
                if evento.modifiers() & Qt.ShiftModifier:
                    self._on_descargar()
                else:
                    self._on_buscar()
                return True
        except Exception:  # noqa: BLE001
            logger.exception("excepcion al manejar Enter en un control")
        return super().eventFilter(objeto, evento)

    def _on_escape(self) -> None:
        """Esc: cierra el visor ampliado o cancela la búsqueda/descarga en curso."""
        try:
            if self._lightbox is not None and self._lightbox.isVisible():
                self._lightbox.cerrar()
                return
            if self.controller.is_busy():
                self.controller.cancelar()
                self.statusBar().showMessage("⏹️ Cancelando…")
        except Exception:  # noqa: BLE001
            logger.exception("excepcion en _on_escape")

    def closeEvent(self, evento):  # noqa: N802
        """Cierre ordenado de la app (Alt+F4, Ctrl+Q, la X o la barra de tareas).

        Si hay una búsqueda o descarga en curso se pregunta antes; al salir se cancela
        el trabajo pendiente, se espera a las tareas de fondo y se cierra el almacén,
        para no dejar archivos a medias ni la base de datos abierta.
        """
        try:
            if self.controller.is_busy():
                respuesta = QMessageBox.question(
                    self,
                    "Salir",
                    "Hay una búsqueda o descarga en curso.\n\n"
                    "¿Cancelarla y salir de todos modos?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if respuesta != QMessageBox.Yes:
                    evento.ignore()
                    self.statusBar().showMessage("Cierre cancelado: la operación continúa")
                    return
                self.controller.cancelar()
                logger.info("cierre solicitado con una operación en curso: se cancela")
            if self._lightbox is not None and self._lightbox.isVisible():
                self._lightbox.cerrar()
            logger.info("cerrando la aplicación (Alt+F4 / ventana)")
            self.controller.shutdown()
        except Exception:  # noqa: BLE001
            logger.exception("excepcion al cerrar la ventana")
        super().closeEvent(evento)

    def _connect(self) -> None:
        self.cmb_tipo.currentTextChanged.connect(self._set_tipo)
        self.btn_carpeta.clicked.connect(self._elegir_carpeta)
        self.btn_buscar.clicked.connect(self._on_buscar)
        self.btn_descargar.clicked.connect(self._on_descargar)
        self.btn_limpiar.clicked.connect(self._on_limpiar)
        self._atajos_de_teclado()
        # Barra de herramientas y menús (después de existir los botones que reflejan)
        self._crear_barra_herramientas()
        self._crear_menus()

        c = self.controller
        c.status_changed.connect(lambda m: self.statusBar().showMessage(m))
        # La carpeta de salida se refleja en las acciones del menú contextual
        self.ed_carpeta.textChanged.connect(lambda _texto: self._actualizar_acciones_imagen())
        c.results_ready.connect(self._on_results)
        c.galeria_total_ready.connect(self._on_galeria_total)
        c.galeria_item_ready.connect(self._on_galeria_item)
        c.galeria_muestra_ready.connect(self.galeria.agregar_muestra)
        self.galeria.pedir_lightbox.connect(self._abrir_lightbox)
        self.galeria.pedir_imagen.connect(c.solicitar_miniatura)
        self.galeria.pedir_muestra.connect(c.solicitar_muestra)
        c.progress_changed.connect(self._on_progress)
        c.error.connect(self._on_error)
        c.state_changed.connect(self._on_state)
        c.job_finished.connect(self._on_job_finished)
        c.http_event.connect(self._on_http_event)
        c.carpeta_cambiada.connect(self._on_carpeta_cambiada)
        # Acciones individuales (menú contextual de las imágenes)
        self.galeria.menu_contextual.connect(self._on_menu_contextual)
        c.individual_iniciado.connect(self._on_individual_iniciado)
        c.individual_listo.connect(self._on_individual_listo)
        c.individual_error.connect(self._on_individual_error)

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
    @staticmethod
    def _resumir_error(mensaje: str, limite: int = 220) -> str:
        """Primera línea del error, acotada: al usuario se le da el resumen, no el volcado.

        El texto completo (con sus pistas y detalles técnicos) queda en el registro.
        """
        texto = (mensaje or "").strip()
        if not texto:
            return "Error inesperado"
        primera = texto.splitlines()[0].strip()
        if len(primera) <= limite:
            return primera
        recorte = primera[:limite]
        if " " in recorte:
            recorte = recorte[:recorte.rfind(" ")]
        return recorte.rstrip(" ,.;:") + "…"

    def _on_error(self, mensaje: str) -> None:
        """Error crítico: UN aviso resumido al usuario y el detalle completo al registro."""
        logger.error("%s", mensaje)          # detalle íntegro (consola y archivo .log)
        if self._error_mostrado:
            return                           # ya se avisó en esta misma operación
        self._error_mostrado = True
        QMessageBox.critical(
            self,
            "Error",
            f"{self._resumir_error(mensaje)}\n\n"
            "El detalle completo está en el registro (consola y archivo .log).",
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

            # Nada pasó los filtros: explicar el porqué (evita el "no hace nada").
            # Si ya se avisó de un error crítico, NO se añade un segundo aviso.
            if estado == "error" or self._error_mostrado:
                return
            if estado == "sin resultados" or (tipo == "busqueda" and resumen.get("total", 0) == 0
                                              and (descartados or encontrados == 0)):
                motivo = self._resumir_error(resumen.get("motivo") or "")
                if encontrados:
                    texto = (f"Se encontraron {encontrados} resultados, pero ninguno pasó "
                             "los filtros del proyecto.")
                elif resumen.get("motivo"):
                    texto = f"La búsqueda no devolvió resultados: {motivo}."
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
                if resumen.get("motivo"):
                    texto += "\n\nEl detalle completo está en el registro (consola y .log)."
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
                detalle = self._resumir_error(resumen.get("error") or "")
                QMessageBox.critical(
                    self, "Error en la descarga",
                    f"{detalle}\n\nEl detalle completo está en el registro (consola y .log).",
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
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.progress.setFormat("⬇️ 0% · en reposo")
            self.controller.limpiar()
            self._actualizar_acciones_imagen()
            self.statusBar().showMessage("Formulario limpio")
        except Exception as exc:
            logger.exception("excepcion en _on_limpiar")
            QMessageBox.critical(self, "Error", f"Error inesperado: {exc}\n\nDetalles en el log.")

    # ------------------------------------------------------------------ slots del controlador
    def _preparar_busqueda_nueva(self) -> None:
        """Al iniciar una búsqueda/descarga: limpia resultados y la imagen anterior."""
        self.lst_resultados.clear()
        self._muestra_recibida = False
        self._error_mostrado = False      # cada operación avisa a lo sumo una vez
        self.galeria.limpiar(MENSAJE_BUSCANDO)
        self.progress.setValue(0)

    def _on_results(self, items: list) -> None:
        self.lst_resultados.addItems(items)

    def _on_galeria_total(self, total: int) -> None:
        """El controlador anuncia cuántas imágenes tendrá el carrusel."""
        self.galeria.definir_total(total)
        self._actualizar_acciones_imagen()

    def _on_galeria_item(self, posicion: int, datos: bytes) -> None:
        """Llega una miniatura: se añade al carrusel (la primera se muestra ya)."""
        if self.galeria.agregar(posicion, datos):
            self._muestra_recibida = True

    def _on_carpeta_cambiada(self, ruta: str) -> None:
        """La carpeta elegida no era escribible: se usa otra (se refleja en la UI)."""
        self.ed_carpeta.setText(ruta)
        self.statusBar().showMessage(f"⚠ Carpeta no escribible; se usará: {ruta}")

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
        (o el dock/panel). El formulario se adapta al tamaño: los campos se estiran,
        el panel de resultados se lleva el espacio sobrante y la ventana nunca baja
        de su tamaño mínimo real (así no aparece ninguna barra de desplazamiento).
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
        if not getattr(self, "_carpeta_comprobada", False):
            self._carpeta_comprobada = True
            # Se comprueba al arrancar (sin cambiar nada) para avisar desde el
            # principio si las descargas no podrán ir a la carpeta configurada.
            QTimer.singleShot(200, self._avisar_si_no_escribible)

    def _mostrar_filtros(self) -> None:
        """Muestra la lista negra y los filtros que se aplican siempre (solo lectura)."""
        try:
            permitidos = list(config.ALLOW_ADULT_RATINGS)
            if self.chk_adulto.isChecked():
                permitidos = ["general", "sensitive", "questionable", "explicit"]
            texto = filtros.describir_filtros(
                allow_adult_ratings=permitidos,
                require_free_license=self.chk_liberado.isChecked(),
            )
            logger.info("se mostraron los filtros activos al usuario")
        except Exception as exc:  # noqa: BLE001
            logger.exception("no se pudo componer la descripción de los filtros")
            texto = f"No se pudo leer la lista de filtros: {exc}"
        caja = QMessageBox(self)
        caja.setWindowTitle("Filtros activos del proyecto")
        caja.setIcon(QMessageBox.Information)
        caja.setText("Qué se descarta en las búsquedas y descargas")
        caja.setInformativeText(texto)
        caja.setDetailedText(
            "La lista negra completa vive en arrays dentro de app/config.py, y el código\n"
            "solo los lee (no hay valores incrustados en el código):\n"
            "  • PROHIBITED_TAG_TOKENS    → tags exactos que descartan\n"
            "  • PROHIBITED_TAG_PREFIXES  → prefijos («pedo» descarta «pedo_x»)\n"
            "  • BLOCKED_PAID_DOMAINS     → dominios de pago excluidos\n"
            "  • EXCLUDED_TAG_TOKENS · EXCLUDED_DOMAINS · EXCLUDED_TEXT_TOKENS → tu lista\n"
            "Para cambiarla NO hace falta tocar el código: copia el array que quieras en\n"
            "config_local.py (junto al .exe, o en ~/.imaginteca/config_local.py) con\n"
            "tus valores y reinicia; config_local.py sobreescribe app/config.py y no se\n"
            "pierde al actualizar. Los valores por defecto traen el ejemplo comentado."
        )
        caja.exec()

    def _avisar_si_no_escribible(self) -> None:
        """Aviso temprano: la carpeta de salida no es escribible (p. ej. sandbox)."""
        try:
            carpeta = self.ed_carpeta.text().strip() or str(config.DEFAULT_OUTPUT_DIR)
            ok, motivo, alternativa = self.controller.comprobar_carpeta_salida(carpeta)
            if ok:
                logger.info("carpeta de salida escribible: %s", carpeta)
                return
            destino = f"se usará {alternativa}" if alternativa else \
                "no hay ninguna carpeta alternativa escribible"
            mensaje = (
                f"⚠ No se puede escribir en la carpeta de salida ({carpeta}): {motivo} — "
                f"{destino}."
            )
            if alternativa == config.carpeta_junto_a_la_app():
                mensaje += (" La app parece abierta desde un entorno restringido "
                            "(p. ej. la terminal de un agente/IDE con sandbox): ábrela con "
                            "doble clic desde el Explorador para usar tus carpetas.")
            self.statusBar().showMessage(mensaje)
            self.lbl_conexion.setText(mensaje)
            self.lbl_conexion.setStyleSheet("color: #b00020;")
            self.lbl_conexion.setToolTip(mensaje)
            logger.warning("carpeta de salida NO escribible al arrancar: %s (%s)", carpeta, motivo)
        except Exception:  # noqa: BLE001
            logger.exception("excepcion al comprobar la carpeta de salida")

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
        self._actualizar_acciones_imagen()   # sin acciones individuales mientras trabaja
        # La barra refleja la función en curso: buscar (indeterminado) o descargar (%)
        self.progress.setValue(0)
        if getattr(self, "_tarea", "descargar") == "buscar":
            self.progress.setRange(0, 0)
            self.progress.setFormat("🔍 buscando…")
        else:
            self.progress.setRange(0, 0)  # indeterminado hasta el primer avance
            self.progress.setFormat("⬇️ %p%")
        self.progress.setVisible(True)
        self._sincronizar_barra()

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
        # La barra de progreso SIEMPRE está visible (en reposo marca 0 %)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("⬇️ 0% · en reposo")
        self.progress.setVisible(True)
        # Al cancelar se conservan el formulario, los resultados y la imagen de ejemplo.
        self._actualizar_acciones_imagen()
        self._sincronizar_barra()

    # ------------------------------------------------------------------ barra de herramientas
    def _crear_barra_herramientas(self) -> None:
        """Barra con las funciones clave: esenciales primero, luego las de apoyo.

        La barra no sustituye a los botones, los REFLEJA: el texto y la habilitación
        se copian del botón correspondiente (`_sincronizar_barra`), así nunca se
        puede pulsar algo que esté deshabilitado en el formulario.
        """
        barra = QToolBar("Funciones", self)
        barra.setObjectName("barra_funciones")
        barra.setMovable(False)
        barra.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(barra)
        self.barra_funciones = barra

        self.act_buscar = self._accion_barra(
            "🔍 Buscar", "Ctrl+B", self._on_buscar,
            "Busca con el criterio del formulario (Enter en cualquier campo)")
        self.act_descargar = self._accion_barra(
            "⬇️ Descargar", "Ctrl+D", self._on_descargar,
            "Descarga los resultados encontrados (Shift+Enter)")
        self.act_limpiar = self._accion_barra(
            "🧹 Limpiar", "Ctrl+L", self._on_limpiar, "Vacía el formulario")
        barra.addSeparator()
        self.act_carpeta = self._accion_barra(
            "📂 Carpeta", "Ctrl+O", self._elegir_carpeta, "Elige la carpeta de salida")
        self.act_filtros = self._accion_barra(
            "🛡️ Filtros", "", self._mostrar_filtros, "Qué se filtra y por qué")
        barra.addSeparator()
        self.act_ayuda = self._accion_barra(
            "📖 Ayuda", "F1", self._abrir_ayuda, "Manual de uso, punto por punto")
        self.act_actualizar = self._accion_barra(
            "🔄 Actualizaciones", "", self._buscar_actualizaciones,
            "Comprueba si hay una versión nueva y la instala")
        self.act_acerca = self._accion_barra(
            "ℹ️ Acerca de", "", self._mostrar_acerca, "Versión, licencia y créditos")
        self._sincronizar_barra()

    def _accion_barra(self, texto: str, atajo: str, manejador, descripcion: str) -> QAction:
        accion = QAction(texto, self)
        if atajo:
            accion.setShortcut(QKeySequence(atajo))
        accion.setToolTip(f"{descripcion}  ({atajo})" if atajo else descripcion)
        accion.triggered.connect(manejador)
        return accion

    def _crear_menus(self) -> None:
        """Menús mínimos: lo mismo que la barra, más la ayuda y la comunidad."""
        archivo = self.menuBar().addMenu("&Archivo")
        archivo.addAction(self.act_carpeta)
        archivo.addSeparator()
        salir = QAction("Salir", self)
        salir.setToolTip("También Alt+F4 o Ctrl+Q")
        salir.triggered.connect(self.close)
        archivo.addAction(salir)

        menu_ayuda = self.menuBar().addMenu("A&yuda")
        menu_ayuda.addAction(self.act_ayuda)
        menu_ayuda.addAction(self.act_actualizar)
        menu_ayuda.addSeparator()
        # Comunidad y asistencia técnica: el foro es donde se pregunta y se comenta,
        # y también donde se hace valer la garantía del autor.
        self.act_foro = self._accion_enlace(
            "💬 Foro y comunidad", config.URL_FORO,
            "Preguntas, comentarios y asistencia técnica (GitHub Discussions)")
        self.act_soporte = self._accion_enlace(
            "🆘 Soporte técnico", config.URL_SOPORTE,
            "Qué incluir para que te ayuden a la primera (registro y selftest.txt)")
        self.act_wiki = self._accion_enlace(
            "🌐 Wiki (documentación)", config.URL_WIKI,
            "Instalación, guía rápida, claves, calidad, datasets…")
        self.act_incidencias = self._accion_enlace(
            "🐞 Reportar un fallo", config.URL_INCIDENCIAS,
            "Fallos y peticiones de mejora con seguimiento")
        menu_ayuda.addAction(self.act_foro)
        menu_ayuda.addAction(self.act_soporte)
        menu_ayuda.addAction(self.act_wiki)
        menu_ayuda.addAction(self.act_incidencias)
        menu_ayuda.addSeparator()
        menu_ayuda.addAction(self.act_acerca)

    def _accion_enlace(self, texto: str, url: str, descripcion: str = "") -> QAction:
        """Acción que abre un enlace del proyecto en el navegador."""
        accion = QAction(texto, self)
        accion.setToolTip(f"{descripcion}\n{url}" if descripcion else url)
        accion.triggered.connect(lambda _=False, destino=url: self._abrir_enlace(destino))
        return accion

    def _abrir_enlace(self, url: str) -> None:
        """Abre un enlace (wiki, foro, incidencias, descargas) en el navegador."""
        try:
            QDesktopServices.openUrl(QUrl(url))
            self.statusBar().showMessage(f"🌐 Abriendo {url}")
            logger.info("enlace abierto: %s", url)
        except Exception as exc:  # noqa: BLE001
            logger.exception("no se pudo abrir el enlace %s", url)
            QMessageBox.warning(
                self, "No se pudo abrir",
                f"No se pudo abrir el navegador.\n\nLa dirección es:\n{url}\n\n{exc}")

    def _sincronizar_barra(self) -> None:
        """Copia a la barra el texto y el estado de los botones del formulario."""
        if not hasattr(self, "act_buscar"):
            return
        # Las tres funciones principales cambian de texto (Descargar↔Cancelar); la de
        # carpeta conserva su etiqueta y solo hereda si está disponible o no.
        for accion, boton in ((self.act_buscar, self.btn_buscar),
                              (self.act_descargar, self.btn_descargar),
                              (self.act_limpiar, self.btn_limpiar)):
            try:
                accion.setText(boton.text())
                accion.setEnabled(boton.isEnabled())
            except RuntimeError:
                continue
        try:
            self.act_carpeta.setEnabled(self.btn_carpeta.isEnabled())
        except RuntimeError:
            pass

    # ------------------------------------------------------------------ ayuda
    def _abrir_ayuda(self, seccion: str = "") -> None:
        """Abre el manual de uso (también con F1)."""
        try:
            ayuda.abrir_ayuda(self, seccion)
        except Exception as exc:  # noqa: BLE001
            logger.exception("no se pudo abrir la ayuda")
            QMessageBox.warning(self, "Ayuda", f"No se pudo abrir la ayuda:\n{exc}")

    def _mostrar_acerca(self) -> None:
        try:
            _DialogoAcerca(self).exec()
        except Exception as exc:  # noqa: BLE001
            logger.exception("no se pudo mostrar «Acerca de»")
            QMessageBox.warning(self, "Acerca de", f"Error: {exc}")

    # ------------------------------------------------------------------ actualizaciones
    def _buscar_actualizaciones(self) -> None:
        """Consulta las versiones publicadas en segundo plano."""
        if getattr(self, "_consulta_actualizacion", False):
            return
        self._consulta_actualizacion = True
        self.act_actualizar.setEnabled(False)
        self.statusBar().showMessage("🔄 Consultando si hay una versión nueva…")
        senales = self._senales_actualizacion()
        QThreadPool.globalInstance().start(_TrabajoActualizacion(senales, consultar=True))

    def _senales_actualizacion(self) -> "_SenalesActualizacion":
        if getattr(self, "_senales_act", None) is None:
            senales = _SenalesActualizacion()
            senales.consulta_lista.connect(self._on_consulta_lista)
            senales.consulta_fallo.connect(self._on_consulta_fallo)
            senales.descarga_avance.connect(self._on_descarga_avance)
            senales.descarga_lista.connect(self._on_descarga_lista)
            senales.descarga_fallo.connect(self._on_descarga_fallo)
            self._senales_act = senales
        return self._senales_act

    def _on_consulta_lista(self, version: dict) -> None:
        self._consulta_actualizacion = False
        self.act_actualizar.setEnabled(True)
        actual = updater.version_actual()
        nueva = str(version.get("version") or "")
        if not updater.hay_novedad(actual, nueva):
            self.statusBar().showMessage(f"✅ Estás al día ({actual})")
            QMessageBox.information(
                self, "Sin novedades",
                f"Tienes la última versión publicada.\n\n"
                f"    Instalada: {actual}\n"
                f"    Publicada: {nueva}")
            return
        self.statusBar().showMessage(f"🎉 Hay una versión nueva: {nueva}")
        self._ofrecer_actualizacion(version)

    def _on_consulta_fallo(self, motivo: str) -> None:
        self._consulta_actualizacion = False
        self.act_actualizar.setEnabled(True)
        self.statusBar().showMessage(f"⚠ No se pudo consultar: {motivo}")
        QMessageBox.warning(
            self, "No se pudo consultar",
            f"No se pudo comprobar si hay versiones nuevas:\n\n{motivo}\n\n"
            f"Puedes mirarlo a mano en https://github.com/{config.UPDATE_REPO}/releases")

    def _ofrecer_actualizacion(self, version: dict) -> None:
        """Diálogo con la versión instalada, la nueva y qué trae."""
        activos = version.get("activos") or []
        paquete = updater.elegir_paquete(activos)
        tamano = ""
        if paquete:
            try:
                tamano = f" ({int(paquete.get('size') or 0) / 1024 / 1024:.0f} MB)"
            except (TypeError, ValueError):
                tamano = ""
        notas = (version.get("notas") or "").strip()
        if len(notas) > 700:
            notas = notas[:700] + "…"
        etiqueta = "beta" if version.get("beta") else "estable"
        texto = (
            f"<b>Versión nueva: {version.get('version')} ({etiqueta})</b><br><br>"
            f"Instalada ahora: <b>{updater.version_actual()}</b><br>"
            f"Disponible: <b>{version.get('version')}</b>"
            + (f" · {str(version.get('publicado'))[:10]}" if version.get("publicado") else "")
        )
        if paquete:
            texto += (f"<br><br>Paquete para {updater.sistema_actual()}: "
                      f"{paquete.get('name')}{tamano}")
        else:
            texto += ("<br><br><b>⚠ Esta versión no trae paquete para "
                      f"{updater.sistema_actual()}.</b>")
        if notas:
            texto += f"<hr>{_markdown_a_html(notas)}"

        caja = QMessageBox(self)
        caja.setWindowTitle("Actualización disponible")
        caja.setTextFormat(Qt.RichText)
        caja.setText(texto)
        boton_instalar = (caja.addButton("⬇️ Descargar e instalar", QMessageBox.AcceptRole)
                          if paquete else None)
        boton_web = caja.addButton("🌐 Ver en GitHub", QMessageBox.ActionRole)
        caja.addButton("Ahora no", QMessageBox.RejectRole)
        caja.exec()
        elegido = caja.clickedButton()
        if boton_instalar is not None and elegido is boton_instalar:
            self._descargar_e_instalar(version)
        elif elegido is boton_web and version.get("url"):
            QDesktopServices.openUrl(QUrl(str(version["url"])))

    def _descargar_e_instalar(self, version: dict) -> None:
        """Descarga el paquete con progreso y, al terminar, ofrece instalarlo."""
        from PySide6.QtWidgets import QProgressDialog   # solo se usa aquí

        self._version_nueva = str(version.get("version") or "")
        ventana = QProgressDialog(
            f"Descargando {self._version_nueva}…\n\nLa aplicación se reiniciará sola.",
            "Cancelar", 0, 0, self)
        ventana.setWindowTitle("Descargando la versión nueva")
        ventana.setWindowModality(Qt.WindowModal)
        ventana.setMinimumDuration(0)
        self._progreso_actualizacion = ventana
        self.statusBar().showMessage("⬇️ Descargando la versión nueva…")
        senales = self._senales_actualizacion()
        QThreadPool.globalInstance().start(
            _TrabajoActualizacion(senales, consultar=False, version=version,
                                  cancelar=ventana))

    def _on_descarga_avance(self, descargado: int, total: int) -> None:
        ventana = getattr(self, "_progreso_actualizacion", None)
        if ventana is None:
            return
        mb = descargado / 1024 / 1024
        if total:
            ventana.setMaximum(100)
            ventana.setValue(int(descargado * 100 / total))
            ventana.setLabelText(f"Descargando… {mb:.0f} MB de {total / 1024 / 1024:.0f} MB")
        else:
            ventana.setMaximum(0)
            ventana.setLabelText(f"Descargando… {mb:.0f} MB")

    def _on_descarga_lista(self, ruta: str, huella_ok: bool) -> None:
        ventana = getattr(self, "_progreso_actualizacion", None)
        if ventana is not None:
            ventana.close()
            self._progreso_actualizacion = None
        paquete = Path(ruta)
        if not huella_ok:
            QMessageBox.critical(
                self, "Descarga dañada",
                "El archivo descargado NO coincide con la huella SHA-256 que publica\n"
                "el Release. Por seguridad no se instala nada.\n\n"
                "Vuelve a intentarlo o descarga el paquete a mano.")
            self.statusBar().showMessage("⚠ La huella del paquete no coincide: no se instala")
            return
        try:
            guion = updater.escribir_actualizador(paquete)
        except Exception as exc:  # noqa: BLE001
            logger.exception("no se pudo preparar la instalación")
            QMessageBox.critical(self, "No se pudo instalar",
                                 f"Error al preparar la instalación:\n{exc}")
            return
        carpeta = updater.carpeta_aplicacion()
        respuesta = QMessageBox.question(
            self, "Instalar y reiniciar",
            f"La versión {getattr(self, '_version_nueva', '')} ya está descargada y "
            f"verificada.\n\nSe instalará en:\n    {carpeta}\n\n"
            f"La aplicación se cerrará y volverá a abrirse sola.\n"
            f"Termina lo que tengas a medias antes de continuar.\n\n¿Instalar ahora?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if respuesta != QMessageBox.Yes:
            self.statusBar().showMessage("Instalación cancelada: el paquete queda descargado")
            return
        try:
            updater.lanzar_actualizador(guion)
        except Exception as exc:  # noqa: BLE001
            logger.exception("no se pudo lanzar el actualizador")
            QMessageBox.critical(
                self, "No se pudo reiniciar",
                f"No se pudo lanzar el instalador:\n{exc}\n\nEl paquete está en:\n{paquete}")
            return
        logger.info("actualización %s preparada: se cierra para instalarla",
                    getattr(self, "_version_nueva", "?"))
        self.statusBar().showMessage("Instalando la versión nueva…")
        QTimer.singleShot(600, QApplication.quit)

    def _on_descarga_fallo(self, motivo: str) -> None:
        ventana = getattr(self, "_progreso_actualizacion", None)
        if ventana is not None:
            ventana.close()
            self._progreso_actualizacion = None
        self.statusBar().showMessage(f"⚠ Falló la descarga: {motivo}")
        if "cancelada" not in motivo.lower():
            QMessageBox.critical(self, "Falló la descarga", motivo)


def _markdown_a_html(texto: str) -> str:
    """Lo justo de Markdown para las notas del Release (negritas, listas, enlaces)."""
    import html
    import re

    lineas = []
    for linea in html.escape(texto).splitlines():
        linea = linea.rstrip()
        if linea.startswith(("- ", "* ")):
            lineas.append(f"• {linea[2:]}")
        elif linea.startswith("#"):
            lineas.append(f"<b>{linea.lstrip('# ').strip()}</b>")
        else:
            lineas.append(linea)
    unido = "<br>".join(lineas)
    unido = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", unido)
    unido = re.sub(r"`(.+?)`", r"<code>\1</code>", unido)
    unido = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', unido)
    return unido


class _SenalesActualizacion(QObject):
    """Señales del trabajo de actualización (se emiten desde otro hilo)."""

    consulta_lista = Signal(dict)
    consulta_fallo = Signal(str)
    descarga_avance = Signal(int, int)
    descarga_lista = Signal(str, bool)
    descarga_fallo = Signal(str)


class _TrabajoActualizacion(QRunnable):
    """Consulta o descarga en segundo plano, sin congelar la ventana."""

    def __init__(self, senales: _SenalesActualizacion, consultar: bool = True,
                 version: dict | None = None, cancelar=None):
        super().__init__()
        self.senales = senales
        self._consultar = consultar
        self._version = version or {}
        self._cancelar = cancelar
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            if self._consultar:
                self.senales.consulta_lista.emit(updater.consultar_ultima())
                return

            def progreso(descargado: int, total: int) -> None:
                if self._cancelar is not None and self._cancelar.wasCanceled():
                    raise InterruptedError("descarga cancelada")
                self.senales.descarga_avance.emit(descargado, total)

            ruta, huella_ok = updater.descargar_version(self._version, progreso)
            self.senales.descarga_lista.emit(str(ruta), bool(huella_ok))
        except InterruptedError:
            self.senales.descarga_fallo.emit("descarga cancelada por el usuario")
        except Exception as exc:  # noqa: BLE001
            logger.exception("fallo en el trabajo de actualización")
            if self._consultar:
                self.senales.consulta_fallo.emit(str(exc))
            else:
                self.senales.descarga_fallo.emit(str(exc))


class _DialogoAcerca(QDialog):
    """«Acerca de»: qué es, versión instalada, licencia, autor y rutas útiles."""

    def __init__(self, padre=None):
        super().__init__(padre)
        self.setWindowTitle(f"Acerca de {config.APP_NAME}")
        self._padre = padre
        diseño = QVBoxLayout(self)
        encabezado = QLabel(f"<h2>{config.APP_NAME}</h2>")
        encabezado.setTextFormat(Qt.RichText)
        diseño.addWidget(encabezado)

        detalles = QTextBrowser()
        detalles.setOpenExternalLinks(True)
        detalles.setHtml(self._html())
        detalles.setMinimumSize(440, 280)
        diseño.addWidget(detalles, 1)

        botones = QDialogButtonBox()
        self.btn_actualizar = botones.addButton("🔄 Buscar actualizaciones",
                                                QDialogButtonBox.ActionRole)
        self.btn_actualizar.setToolTip("Comprueba la última versión publicada y la instala")
        botones.addButton("Cerrar", QDialogButtonBox.RejectRole)
        botones.rejected.connect(self.reject)
        self.btn_actualizar.clicked.connect(self._buscar)
        diseño.addWidget(botones)

        pantalla = self.screen()
        if pantalla is not None:
            util = pantalla.availableGeometry()
            self.resize(max(520, min(760, util.width() - 80)),
                        max(430, min(620, util.height() - 80)))

    def _html(self) -> str:
        import sys

        from PySide6 import QtCore

        filas = "".join(
            f"<tr><td><b>{etiqueta}</b>&nbsp;&nbsp;</td><td><code>{valor}</code></td></tr>"
            for etiqueta, valor in (
                ("Registros", config.LOG_DIR),
                ("Historial", config.DB_PATH),
                ("Config local", config.CONFIG_LOCAL_USADO or "(ninguno)"),
                ("Carpeta de salida", config.DEFAULT_OUTPUT_DIR),
            ))
        modo = "empaquetado" if getattr(sys, "frozen", False) else "desde el código"
        return f"""
        <p><b>Tu colección personal de imágenes.</b><br>
        Busca, ordena y prepara imágenes —y datasets para entrenar modelos— desde
        redes sociales, booros y wikis de fandom.</p>
        <p><b>Versión instalada:</b> {config.APP_VERSION}
        {'(beta)' if 'beta' in config.APP_VERSION else ''}<br>
        <b>Autor:</b> Roger Gomez &lt;{config.CONTACTO_EMAIL}&gt;<br>
        <b>Licencia:</b> propietaria · todos los derechos reservados (ver
        <code>LICENSE</code>)<br>
        <b>Proyecto:</b> <a href="{config.URL_REPO}">{config.REPO_GITHUB}</a></p>
        <p><b>Comunidad y asistencia</b> (la garantía del autor se hace valer aquí):<br>
        💬 <a href="{config.URL_FORO}">Foro y comunidad</a> ·
        🆘 <a href="{config.URL_SOPORTE}">Soporte técnico</a> ·
        🌐 <a href="{config.URL_WIKI}">Wiki</a> ·
        🐞 <a href="{config.URL_INCIDENCIAS}">Incidencias</a> ·
        📥 <a href="{config.URL_DESCARGAS}">Descargas</a></p>
        <p><b>Entorno:</b> Python {sys.version.split()[0]} · Qt {QtCore.qVersion()} ·
        {modo}</p>
        <p><b>Dónde queda todo:</b></p>
        <table cellspacing="3">{filas}</table>
        """

    def _buscar(self) -> None:
        self.accept()
        padre = self._padre
        if padre is not None and hasattr(padre, "_buscar_actualizaciones"):
            padre._buscar_actualizaciones()
