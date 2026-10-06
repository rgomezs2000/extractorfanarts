"""Controlador principal: orquesta búsqueda y descarga en hilos de fondo.

Estados: idle → running → idle. Durante "running" la vista bloquea el
formulario y Limpiar, y el botón Descargar actúa como Cancelar. Al cancelar,
la UI se restaura tal como estaba (sin restablecer el formulario) y la imagen
de ejemplo se conserva.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from .. import config
from ..models.artwork import Artwork, SearchQuery
from ..models.store import DownloadStore
from ..services import enhance, filters
from ..services.adapters import adapter_for
from ..services.http_client import BlockedError, CancelledError, ConfigError, PoliteClient

_SAFE_RE = re.compile(r"[^\w.\- ]+")
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".bmp"}


def _safe_name(text: str, max_len: int = 40) -> str:
    out = _SAFE_RE.sub("_", str(text)).strip("_ .")[:max_len]
    return out or "archivo"


def _hash_url(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _filename_for(art: Artwork) -> str:
    ext = Path(urlparse(art.url).path).suffix.lower()
    if ext not in _IMAGE_EXTS:
        ext = ".jpg"
    base = _safe_name(art.site)
    if art.md5:
        return f"{base}_{art.site_id}_{art.md5[:8]}{ext}"
    return f"{base}_{art.site_id}_{_hash_url(art.url)[:8]}{ext}"


def _write_sidecar(dest: Path, art: Artwork, mejora: dict | None = None) -> None:
    meta = {
        "sitio": art.site,
        "id_sitio": art.site_id,
        "artista": art.author,
        "origen": art.page_url or art.url,
        "licencia": art.license,
        "tags": art.tags,
        "rating": art.rating,
        "fecha": art.created_at,
    }
    if mejora:
        meta["mejora"] = mejora
    dest.with_suffix(".json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


class _JobSignals(QObject):
    status = Signal(str)
    progress = Signal(int, int)
    results = Signal(list)
    sample = Signal(bytes)
    done = Signal(bool, str)  # (cancelado, motivo)
    error = Signal(str)


class _Job(QRunnable):
    def __init__(self, fn):
        super().__init__()
        self._fn = fn
        self.signals = _JobSignals()
        self.setAutoDelete(True)

    def run(self):
        try:
            self._fn(self.signals)
        except CancelledError:
            self.signals.done.emit(True, "cancelada")
        except Exception as exc:  # red de seguridad
            self.signals.error.emit(str(exc))
            self.signals.done.emit(True, "error")


class MainController(QObject):
    status_changed = Signal(str)
    progress_changed = Signal(int, int)
    results_ready = Signal(list)
    sample_ready = Signal(bytes)
    finished = Signal(str)
    error = Signal(str)
    state_changed = Signal(str)  # "idle" | "running"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._cancel: threading.Event | None = None
        self._busy = False
        self._store = DownloadStore(config.DB_PATH)
        self.results: list[Artwork] = []

    # ------------------------------------------------------------------ API pública
    def is_busy(self) -> bool:
        return self._busy

    def buscar(self, settings: dict) -> None:
        self._start(settings, download=False)

    def descargar(self, settings: dict) -> None:
        self._start(settings, download=True)

    def cancelar(self) -> None:
        if self._busy and self._cancel is not None:
            self._cancel.set()
            self.status_changed.emit("Cancelando…")

    def limpiar(self) -> None:
        if self._busy:
            return  # Limpiar está bloqueado mientras se descarga
        self.results = []
        self.status_changed.emit("Formulario limpio")

    def shutdown(self) -> None:
        self._store.close()

    # ------------------------------------------------------------------ arranque de trabajos
    def _start(self, settings: dict, download: bool) -> None:
        if self._busy:
            return
        self._busy = True
        self.state_changed.emit("running")
        self._cancel = threading.Event()
        job = _Job(lambda sig: self._run(sig, settings, download, self._cancel))
        job.signals.status.connect(self.status_changed)
        job.signals.progress.connect(self.progress_changed)
        job.signals.results.connect(self.results_ready)
        job.signals.sample.connect(self.sample_ready)
        job.signals.error.connect(self.error)
        job.signals.done.connect(self._on_done)
        self._pool.start(job)

    def _on_done(self, cancelled: bool, reason: str):
        self._busy = False
        self.state_changed.emit("idle")
        self.finished.emit("cancelada" if cancelled else "completada")

    # ------------------------------------------------------------------ trabajo en hilo
    def _run(self, sig: _JobSignals, settings: dict, download: bool, cancel: threading.Event):
        client = PoliteClient(
            cancel_event=cancel,
            on_pause=lambda sec, why: sig.status.emit(f"⏸ Pausa {int(sec)} s — {why}"),
        )
        try:
            query = self._query_from_settings(settings)
            adapter = adapter_for(query.kind, query.platform)
            if adapter is None:
                raise ConfigError(f"plataforma no disponible: {query.platform}")

            sig.status.emit(f"Buscando en {query.platform}…")
            arts = adapter.search(client, query)

            # Dedupe SOLO dentro de la búsqueda actual: cada Descargar vuelve a
            # descargar todo y sobreescribe los archivos existentes (requisito).
            if settings.get("permitir_adulto"):
                allow = ["general", "sensitive", "questionable", "explicit"]
            else:
                allow = config.ALLOW_ADULT_RATINGS
            kept, rejected = filters.apply_filters(
                arts,
                allow_adult_ratings=allow,
                require_free_license=bool(settings.get("solo_liberado")),
                seen_hashes=None,
                limit=config.MAX_RESULTS_PER_SOURCE,
            )
            self.results = kept
            sig.results.emit([a.summary() for a in kept])
            if rejected:
                detalle = ", ".join(f"{k}: {v}" for k, v in sorted(rejected.items()))
                sig.status.emit(f"Resultados: {len(kept)} aceptados · descartados → {detalle}")
            else:
                sig.status.emit(f"Resultados: {len(kept)} aceptados")

            # Imagen de ejemplo de la búsqueda (solo una: la primera)
            if kept:
                preview = kept[0].preview_url or kept[0].url
                try:
                    sig.sample.emit(client.get_bytes(preview, max_bytes=config.MAX_PREVIEW_BYTES))
                except Exception:
                    pass

            if not download:
                sig.status.emit("Búsqueda completada. Presiona Descargar para guardar los archivos.")
                sig.done.emit(False, "busqueda")
                return
            if not kept:
                sig.done.emit(False, "sin resultados")
                return

            outdir = Path(settings.get("carpeta") or config.DEFAULT_OUTPUT_DIR)
            outdir.mkdir(parents=True, exist_ok=True)
            total = len(kept)
            guardados = 0
            for i, art in enumerate(kept, 1):
                if cancel.is_set():
                    sig.done.emit(True, "cancelada")
                    return
                try:
                    sub = outdir / _safe_name(art.site)
                    dest = sub / _filename_for(art)
                    # requisito: si el archivo existe, se sobreescribe
                    client.download_to(art.url, dest)
                    # REQUISITO: todo lo descargado se convierte SIEMPRE a .webp
                    # y el original no se conserva ("mejorar" solo controla el upscaling).
                    mejora_meta: dict | None = None
                    try:
                        dest, mejora_meta = enhance.postprocess(dest, settings)
                        sig.status.emit(
                            f"[{i}/{total}] {art.site}: {dest.name} ({mejora_meta.get('modo')})"
                        )
                    except ConfigError as exc:
                        sig.status.emit(f"⚠ no se pudo convertir a WebP: {exc}")
                    except Exception as exc:
                        sig.status.emit(f"⚠ conversión a WebP fallida: {exc}")
                    _write_sidecar(dest, art, mejora_meta)
                    h = art.md5 or _hash_url(art.url)
                    self._store.add(h, art.url, str(dest))
                    guardados += 1
                    sig.progress.emit(i, total)
                except CancelledError:
                    sig.done.emit(True, "cancelada")
                    return
                except Exception as exc:
                    sig.status.emit(f"⚠ no se pudo descargar {art.page_url or art.url}: {exc}")

            sig.status.emit(f"Descarga completada: {guardados}/{total} archivos en {outdir}")
            sig.done.emit(False, "descarga")
        except CancelledError:
            sig.done.emit(True, "cancelada")
        except (BlockedError, ConfigError) as exc:
            sig.error.emit(str(exc))
            sig.done.emit(True, "error")
        finally:
            client.close()

    # ------------------------------------------------------------------ mapeo de la UI a la consulta
    @staticmethod
    def _query_from_settings(settings: dict) -> SearchQuery:
        tipo = settings.get("tipo", "")
        q = SearchQuery()
        q.platform = settings.get("plataforma", "")
        if tipo == "Red social":
            q.kind = "social"
            q.usuario = (settings.get("usuario") or "").strip()
            q.keyword = (settings.get("keyword") or "").strip()
            q.hashtag = (settings.get("hashtag") or "").strip()
        elif tipo == "Booru":
            q.kind = "booru"
            q.tags = (settings.get("tags") or "").strip()
        else:
            q.kind = "wiki"
            q.fandom = (settings.get("fandom") or "").strip()
            q.character = (settings.get("character") or "").strip()
            q.wiki_url = (settings.get("wiki_url") or "").strip()
        return q
