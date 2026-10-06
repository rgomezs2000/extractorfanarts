"""Vista principal de escritorio (PySide6): formulario de filtros, botones
Buscar / Descargar↔Cancelar / Limpiar, imagen de ejemplo y resultados.

Reglas de UI:
  - Limpiar limpia el formulario (sin descargas) y queda BLOQUEADO mientras se descarga.
  - Descargar se convierte en Cancelar durante la descarga.
  - Al cancelar se restaura todo como estaba, sin restablecer el formulario,
    y la imagen de ejemplo se mantiene.
"""
from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QMainWindow, QProgressBar, QPushButton,
    QSlider, QStackedWidget, QVBoxLayout, QWidget,
)

from .. import config
from ..controllers.main_controller import MainController
from ..services.adapters import BOORU_ADAPTERS, SOCIAL_ADAPTERS, WIKI_ADAPTERS

TIPOS = ("Red social", "Booru", "Wiki fandom")


class MainWindow(QMainWindow):
    def __init__(self, controller: MainController):
        super().__init__()
        self.controller = controller
        self.setWindowTitle(f"{config.APP_NAME} — archivo personal de fanarts")
        self._build_ui()
        self._connect()
        self._set_tipo(TIPOS[0])
        self._set_idle()

    # ------------------------------------------------------------------ construcción
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Fuente
        fuente_box = QGroupBox("Fuente de búsqueda")
        fl = QHBoxLayout(fuente_box)
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(TIPOS)
        self.cmb_plataforma = QComboBox()
        fl.addWidget(QLabel("Tipo:"))
        fl.addWidget(self.cmb_tipo)
        fl.addWidget(QLabel("Plataforma:"))
        fl.addWidget(self.cmb_plataforma, 1)
        root.addWidget(fuente_box)

        # Filtros por tipo (stacked)
        self.stack = QStackedWidget()

        self.page_social = QWidget()
        v = QVBoxLayout(self.page_social)
        v.addWidget(QLabel("Combina @usuario, palabra clave y/o #hashtag (usa el algoritmo nativo de la plataforma):"))
        self.ed_usuario = QLineEdit()
        self.ed_usuario.setPlaceholderText("@usuario  (o @usuario@instancia)")
        self.ed_keyword = QLineEdit()
        self.ed_keyword.setPlaceholderText("palabra clave")
        self.ed_hashtag = QLineEdit()
        self.ed_hashtag.setPlaceholderText("#hashtag")
        v.addWidget(self.ed_usuario)
        v.addWidget(self.ed_keyword)
        v.addWidget(self.ed_hashtag)

        self.page_booru = QWidget()
        v = QVBoxLayout(self.page_booru)
        v.addWidget(QLabel("Tags del booru (las que el booru permita):"))
        self.ed_tags = QLineEdit()
        self.ed_tags.setPlaceholderText("ej. hatsune_miku solo")
        v.addWidget(self.ed_tags)

        self.page_wiki = QWidget()
        v = QVBoxLayout(self.page_wiki)
        v.addWidget(QLabel("Fandom (franquicia):"))
        self.ed_fandom = QLineEdit()
        self.ed_fandom.setPlaceholderText("ej. naruto")
        v.addWidget(self.ed_fandom)
        v.addWidget(QLabel("Personaje y/o concepto:"))
        self.ed_character = QLineEdit()
        self.ed_character.setPlaceholderText("ej. naruto_uzumaki")
        v.addWidget(self.ed_character)
        v.addWidget(QLabel("URL de la wiki (opcional):"))
        self.ed_wiki_url = QLineEdit()
        self.ed_wiki_url.setPlaceholderText("ej. https://naruto.fandom.com")
        v.addWidget(self.ed_wiki_url)

        self.stack.addWidget(self.page_social)
        self.stack.addWidget(self.page_booru)
        self.stack.addWidget(self.page_wiki)
        root.addWidget(self.stack)

        # Opciones
        self.filtros_box = QGroupBox("Opciones")
        ov = QVBoxLayout(self.filtros_box)
        fl2 = QHBoxLayout()
        self.chk_liberado = QCheckBox("Solo material con licencia liberada")
        self.chk_liberado.setToolTip(
            "Si se marca, solo se procesan obras con licencia permisiva explícita "
            "(CC0/CC-BY/dominio público). La mayoría del fanart no la tiene."
        )
        self.chk_adulto = QCheckBox("Permitir contenido adulto")
        self.chk_adulto.setToolTip(
            "Confirmo que soy mayor de edad en mi jurisdicción. "
            "Por defecto se omiten los ratings questionable/explicit."
        )
        self.chk_mejorar = QCheckBox("Mejorar calidad (upscale IA/Lanczos)")
        self.chk_mejorar.setChecked(config.ENHANCE_DEFAULT_ON)
        self.chk_mejorar.setToolTip(
            "Controla SOLO el upscaling. El guardado en .webp se aplica SIEMPRE "
            "(el original nunca se conserva). Reglas: <700px→4x · 700-799px→3x · "
            "800-1500px→2x · 1501-1599px→1x · ≥1600px solo WebP."
        )
        self.chk_ia = QCheckBox("Modo IA (waifu2x/Real-ESRGAN)")
        self.chk_ia.setToolTip(
            "Usa el motor IA Vulkan si está instalado (python scripts\\setup_vendor.py --ai); "
            "si no está disponible, usa Lanczos + afilado suave automáticamente."
        )
        fl2.addWidget(self.chk_liberado)
        fl2.addWidget(self.chk_adulto)
        fl2.addWidget(self.chk_mejorar)
        fl2.addWidget(self.chk_ia)
        fl2.addStretch(1)
        ov.addLayout(fl2)

        # Calidad WebP
        fl3 = QHBoxLayout()
        fl3.addWidget(QLabel("Calidad WebP:"))
        self.sld_calidad = QSlider(Qt.Horizontal)
        self.sld_calidad.setRange(1, 100)
        self.sld_calidad.setValue(config.WEBP_QUALITY_DEFAULT)
        self.sld_calidad.setFixedWidth(220)
        self.lbl_calidad_val = QLabel(str(config.WEBP_QUALITY_DEFAULT))
        self.lbl_calidad_val.setMinimumWidth(28)
        self.sld_calidad.valueChanged.connect(
            lambda v: self.lbl_calidad_val.setText(str(v))
        )
        fl3.addWidget(self.sld_calidad)
        fl3.addWidget(self.lbl_calidad_val)
        fl3.addStretch(1)
        ov.addLayout(fl3)
        root.addWidget(self.filtros_box)

        # Carpeta de salida
        carpeta_box = QGroupBox("Carpeta de salida")
        cl = QHBoxLayout(carpeta_box)
        self.ed_carpeta = QLineEdit(str(config.DEFAULT_OUTPUT_DIR))
        self.btn_carpeta = QPushButton("…")
        self.btn_carpeta.setFixedWidth(36)
        self.btn_carpeta.setToolTip("Elegir carpeta de salida")
        cl.addWidget(QLabel("Salida:"))
        cl.addWidget(self.ed_carpeta, 1)
        cl.addWidget(self.btn_carpeta)
        root.addWidget(carpeta_box)

        # Botones
        botones = QHBoxLayout()
        self.btn_buscar = QPushButton("Buscar")
        self.btn_descargar = QPushButton("Descargar")
        self.btn_limpiar = QPushButton("Limpiar")
        botones.addWidget(self.btn_buscar)
        botones.addWidget(self.btn_descargar)
        botones.addWidget(self.btn_limpiar)
        botones.addStretch(1)
        root.addLayout(botones)

        # Resultados
        self.lbl_muestra = QLabel("(aquí se mostrará una imagen de ejemplo de la búsqueda)")
        self.lbl_muestra.setAlignment(Qt.AlignCenter)
        self.lbl_muestra.setMinimumSize(420, 280)
        self.lbl_muestra.setStyleSheet("border: 1px solid #999; background: #f5f5f5;")
        self.lst_resultados = QListWidget()
        self.lst_resultados.setMinimumHeight(120)

        res_box = QGroupBox("Resultados")
        rv = QVBoxLayout(res_box)
        rv.addWidget(self.lbl_muestra)
        rv.addWidget(QLabel("Resultados encontrados:"))
        rv.addWidget(self.lst_resultados)
        root.addWidget(res_box, 1)

        # Progreso
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        root.addWidget(self.progress)

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
        c.sample_ready.connect(self._on_sample)
        c.progress_changed.connect(self._on_progress)
        c.error.connect(lambda m: self.statusBar().showMessage(f"⚠ {m}"))
        c.state_changed.connect(self._on_state)

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
        carpeta = QFileDialog.getExistingDirectory(
            self, "Elegir carpeta de salida", self.ed_carpeta.text()
        )
        if carpeta:
            self.ed_carpeta.setText(carpeta)

    # ------------------------------------------------------------------ acciones
    def _settings(self) -> dict:
        return {
            "tipo": self.cmb_tipo.currentText(),
            "plataforma": self.cmb_plataforma.currentText(),
            "usuario": self.ed_usuario.text(),
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
        if self.controller.is_busy():
            return
        s = self._settings()
        error = self._validar(s)
        if error:
            self.statusBar().showMessage(f"⚠ {error}")
            return
        self.lst_resultados.clear()
        self.controller.buscar(s)

    def _on_descargar(self) -> None:
        if self.controller.is_busy():
            self.controller.cancelar()  # el botón actúa como Cancelar
            return
        s = self._settings()
        error = self._validar(s)
        if error:
            self.statusBar().showMessage(f"⚠ {error}")
            return
        self.lst_resultados.clear()
        self.controller.descargar(s)

    def _on_limpiar(self) -> None:
        if self.controller.is_busy():
            return  # bloqueado mientras se descarga
        for w in (self.ed_usuario, self.ed_keyword, self.ed_hashtag,
                  self.ed_tags, self.ed_fandom, self.ed_character, self.ed_wiki_url):
            w.clear()
        self.lst_resultados.clear()
        self.lbl_muestra.setText("(aquí se mostrará una imagen de ejemplo de la búsqueda)")
        self.progress.setVisible(False)
        self.controller.limpiar()
        self.statusBar().showMessage("Formulario limpio")

    # ------------------------------------------------------------------ slots del controlador
    def _on_results(self, items: list) -> None:
        self.lst_resultados.addItems(items)

    def _on_sample(self, data: bytes) -> None:
        pix = QPixmap()
        if pix.loadFromData(QByteArray(data)):
            scaled = pix.scaled(
                self.lbl_muestra.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.lbl_muestra.setPixmap(scaled)
        else:
            self.lbl_muestra.setText("(no se pudo mostrar la imagen de ejemplo)")

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
        self.btn_descargar.setText("Cancelar")
        self.btn_buscar.setEnabled(False)
        self.btn_limpiar.setEnabled(False)
        self.cmb_tipo.setEnabled(False)
        self.cmb_plataforma.setEnabled(False)
        self.stack.setEnabled(False)
        self.filtros_box.setEnabled(False)
        self.ed_carpeta.setEnabled(False)
        self.btn_carpeta.setEnabled(False)
        self.progress.setValue(0)
        self.progress.setVisible(True)

    def _set_idle(self) -> None:
        self.btn_descargar.setText("Descargar")
        self.btn_buscar.setEnabled(True)
        self.btn_limpiar.setEnabled(True)
        self.cmb_tipo.setEnabled(True)
        self.cmb_plataforma.setEnabled(True)
        self.stack.setEnabled(True)
        self.filtros_box.setEnabled(True)
        self.ed_carpeta.setEnabled(True)
        self.btn_carpeta.setEnabled(True)
        # Al cancelar se conservan el formulario, los resultados y la imagen de ejemplo.
