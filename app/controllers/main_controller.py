"""Controlador principal: orquesta búsqueda y descarga en hilos de fondo.

Estados: idle → running → idle. Durante "running" la vista bloquea el
formulario y Limpiar, y el botón Descargar actúa como Cancelar. Al cancelar,
la UI se restaura tal como estaba (sin restablecer el formulario) y la imagen
de ejemplo se conserva.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from .. import config
from ..models.artwork import Artwork, SearchQuery
from ..models.store import DownloadStore
from ..services import enhance, filters, muestras, ugoira
from ..services.adapters import adapter_for
from ..services.http_client import (
    BlockedError,
    CancelledError,
    ConfigError,
    PoliteClient,
    SinResultados,
)

logger = logging.getLogger("extractorfanarts")

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


def _borrar_si_existe(ruta: Path) -> None:
    """Borra un archivo descartado (nunca deja basura en el archivo local)."""
    try:
        ruta.unlink()
    except OSError:
        pass


def _procesar_obra(
    client: PoliteClient,
    art: Artwork,
    outdir: Path,
    settings: dict,
    *,
    sidecar: bool = False,
    subcarpeta: bool = True,
    nombre: str | None = None,
    aviso=None,
) -> tuple[Path, dict | None]:
    """Descarga UNA obra y le aplica la política de calidad del proyecto.

    Es la ruta ÚNICA (una sola implementación) que comparten la descarga masiva y
    las acciones individuales del menú contextual (copiar/guardar una imagen), de
    modo que el resultado es idéntico: mismo nombre de archivo, misma subcarpeta
    por plataforma, conversión OBLIGATORIA a .webp y mejora (Lanczos/IA) según las
    casillas de la ventana, con reintento si la descarga llega corrupta.

    `subcarpeta=False` se usa para el procesado temporal de "copiar imagen", donde
    la ruta no importa (solo los bytes .webp resultantes); `nombre` permite guardar
    con el nombre exacto que elija el usuario en "Guardar como…".

    Devuelve (ruta_final, metadata_de_mejora). Lanza ImagenCorruptaError si el
    archivo descargado no es una imagen válida ni tras el reintento.
    """
    sub = (outdir / _safe_name(art.site)) if subcarpeta else outdir
    archivo = nombre or _filename_for(art)
    mejora_meta: dict | None = None

    if art.animacion:
        # ANIMACIÓN (ugoira de Pixiv): se compone el WebP animado
        dest = (sub / archivo).with_suffix(".webp")
        dest, mejora_meta = ugoira.procesar(client, art, dest, settings)
    else:
        dest = sub / archivo
        client.download_to(art.url, dest)   # si ya existe, se sobreescribe (requisito)
        # Conversión/mejora: con un reintento si llegó corrupta. Los fallos de
        # mejora NO desechan el archivo (solo los corruptos).
        for intento in (1, 2):
            try:
                dest, mejora_meta = enhance.postprocess(dest, settings)
                break
            except enhance.ImagenCorruptaError as exc:
                # El archivo descargado no es una imagen: no se deja basura.
                _borrar_si_existe(dest)
                if intento == 1:
                    logger.warning("imagen corrupta (%s); reintentando la descarga", exc)
                    client.download_to(art.url, dest)
                    continue
                raise
            except ConfigError as exc:
                logger.warning("no se pudo convertir a WebP: %s", exc)
                if aviso is not None:
                    aviso(f"⚠ no se pudo convertir a WebP: {exc}")
                break
            except Exception as exc:  # noqa: BLE001
                logger.warning("conversion a WebP fallida", exc_info=True)
                if aviso is not None:
                    aviso(f"⚠ conversión a WebP fallida: {exc}")
                break

    if sidecar:
        _write_sidecar(dest, art, mejora_meta)
    if mejora_meta is not None:
        # Texto listo para la UI y el registro: «153x153 → 612x612 · Lanczos 4x»
        mejora_meta["resumen"] = enhance.resumen_mejora(mejora_meta)
    return dest, mejora_meta


class _JobSignals(QObject):
    status = Signal(str)
    progress = Signal(int, int)
    results = Signal(list)
    galeria_total = Signal(int)         # cuántas imágenes tendrá el carrusel
    galeria_item = Signal(int, bytes)   # (posición 1..n, datos de la miniatura)
    http = Signal(str)          # estatus de conexión (peticiones/respuestas)
    resumen = Signal(dict)      # resumen final de la operación
    done = Signal(bool, str)    # (cancelado, motivo)
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
    galeria_total_ready = Signal(int)
    galeria_item_ready = Signal(int, bytes)
    galeria_muestra_ready = Signal(int, bytes)   # muestra grande (nítida) de una casilla
    finished = Signal(str)
    error = Signal(str)
    state_changed = Signal(str)  # "idle" | "running"
    job_finished = Signal(dict)  # resumen final para diálogos de la UI
    http_event = Signal(str)     # estatus de conexión para la UI (y consola/log)
    carpeta_cambiada = Signal(str)  # la carpeta de salida no era escribible: se usó otra
    # Acciones individuales del menú contextual (clic derecho sobre una imagen):
    individual_iniciado = Signal(int, str)             # (posición 1..n, acción)
    individual_listo = Signal(int, str, bytes, dict)   # (posición, ruta, .webp, metadata)
    individual_error = Signal(int, str)                # (posición, motivo)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._cancel: threading.Event | None = None
        self._busy = False
        self._cerrado = False                # shutdown() solo actúa una vez
        self._store = DownloadStore(config.DB_PATH)
        self.results: list[Artwork] = []
        self._token_galeria = 0
        self._settings_busqueda: dict = {}   # configuración de la búsqueda en curso
        self._individuales: set[tuple[int, str]] = set()   # acciones individuales activas
        self._lock_individual = threading.Lock()
        self._lock_muestra = threading.Lock()      # turno entre peticiones de muestra
        self._ultima_muestra = 0.0

    # ------------------------------------------------------------------ API pública
    def is_busy(self) -> bool:
        return self._busy

    def buscar(self, settings: dict) -> None:
        self._start(settings, download=False)

    def descargar(self, settings: dict) -> None:
        self._start(settings, download=True)

    def cancelar(self) -> None:
        try:
            if self._busy and self._cancel is not None:
                self._cancel.set()
                self.status_changed.emit("Cancelando…")
        except Exception:
            logger.exception("excepcion en cancelar()")
            self.error.emit("Error interno al cancelar (ver log).")

    def limpiar(self) -> None:
        try:
            if self._busy:
                return  # Limpiar está bloqueado mientras se descarga
            self.results = []
            self._token_galeria += 1     # anula miniaturas pendientes
            self.status_changed.emit("Formulario limpio")
        except Exception:
            logger.exception("excepcion en limpiar()")
            self.error.emit("Error interno al limpiar (ver log).")

    def solicitar_miniatura(self, posicion: int) -> None:
        """Carga (en segundo plano) la muestra pequeña de la tira de miniaturas.

        La galería la pide solo cuando el usuario llega a esa imagen, de modo que
        puede mostrar todos los resultados sin lanzar todas las peticiones a la vez.
        Se entrega en .webp ligero y se parte de la miniatura de la API (no de la
        imagen completa): la tira de 64 px no necesita más.
        """
        try:
            obras = list(self.results or [])
            if not (1 <= posicion <= len(obras)):
                return
            obra = obras[posicion - 1]
            if not (obra.preview_url or obra.url):
                self.galeria_item_ready.emit(posicion, b"")
                return
            token = self._token_galeria

            def tarea(_sig) -> None:
                cliente = PoliteClient(
                    cancel_event=None,
                    min_interval=config.MIN_REQUEST_INTERVAL,
                    block_pause=config.BLOCK_PAUSE,
                )
                datos = b""
                try:
                    self._esperar_turno()
                    datos = self._muestra_de(cliente, obra, grande=False)
                except Exception:
                    logger.debug("miniatura %d no disponible", posicion, exc_info=True)
                finally:
                    cliente.close()
                if token == self._token_galeria:      # sigue siendo la búsqueda actual
                    try:
                        self.galeria_item_ready.emit(posicion, datos)
                    except RuntimeError:
                        pass          # la aplicación se está cerrando

            logger.debug("galería: cargando miniatura %d bajo demanda", posicion)
            trabajo = _Job(tarea)
            trabajo.signals.error.connect(
                lambda msg: logger.warning("galería: fallo al cargar una miniatura: %s", msg))
            self._pool.start(trabajo)
        except Exception:
            logger.exception("excepcion en solicitar_miniatura()")

    def solicitar_muestra(self, posicion: int) -> None:
        """Carga (en segundo plano) la muestra GRANDE de la imagen que se está viendo.

        Se construye desde la imagen ORIGINAL y se entrega como .webp nítida y
        acotada (`MUESTRA_LADO_MAX`): así el visor y el zoom no se ven borrosos y
        tampoco se manejan imágenes enormes para una simple vista previa.
        """
        try:
            obras = list(self.results or [])
            if not (1 <= posicion <= len(obras)):
                return
            obra = obras[posicion - 1]
            token = self._token_galeria

            def tarea(_sig) -> None:
                cliente = PoliteClient(
                    cancel_event=None,
                    min_interval=config.MIN_REQUEST_INTERVAL,
                    block_pause=config.BLOCK_PAUSE,
                )
                datos = b""
                try:
                    self._esperar_turno()
                    datos = self._muestra_de(cliente, obra, grande=True)
                except Exception:
                    logger.debug("muestra grande %d no disponible", posicion, exc_info=True)
                finally:
                    cliente.close()
                if token == self._token_galeria:
                    try:
                        self.galeria_muestra_ready.emit(posicion, datos)
                    except RuntimeError:
                        pass          # la aplicación se está cerrando

            logger.debug("galería: cargando muestra grande %d bajo demanda", posicion)
            trabajo = _Job(tarea)
            trabajo.signals.error.connect(
                lambda msg: logger.warning("galería: fallo al cargar una muestra: %s", msg))
            self._pool.start(trabajo)
        except Exception:
            logger.exception("excepcion en solicitar_muestra()")

    # ------------------------------------------------------------------ muestras de la galería
    def _urls_de_muestra(self, obra: Artwork, grande: bool) -> list[str]:
        """URLs candidatas para la muestra, en orden (se usa la primera que funcione).

        La muestra grande sale de la imagen ORIGINAL (nítida); la de la tira, de la
        miniatura de la API (ligera). Las animaciones (ugoira) usan siempre su
        miniatura, porque su URL original es un ZIP de fotogramas.
        """
        if grande and getattr(config, "MUESTRAS_ORIGINALES", True) and not obra.animacion:
            candidatas = [obra.url, obra.preview_url]
        else:
            candidatas = [obra.preview_url, obra.url]
        vistas: list[str] = []
        for url in candidatas:
            if url and url not in vistas:
                vistas.append(url)
        return vistas

    def _muestra_de(self, cliente: PoliteClient, obra: Artwork, *, grande: bool) -> bytes:
        """Descarga y prepara la muestra .webp (nítida y ligera) de una obra."""
        lado_max = (getattr(config, "MUESTRA_LADO_MAX", 1600) if grande
                    else getattr(config, "MUESTRA_ICONO_LADO_MAX", 512))
        for url in self._urls_de_muestra(obra, grande):
            try:
                datos = cliente.get_bytes(url, max_bytes=config.MAX_MUESTRA_BYTES)
            except Exception:
                logger.debug("muestra no descargable (%s)", url, exc_info=True)
                continue
            if not datos:
                continue
            # La muestra grande SÍ se realza con la configuración de la búsqueda
            # ("Mejorar calidad") para que no se vea borrosa; la de la tira de 64 px
            # no necesita upscaling (sería trabajo inútil).
            webp = muestras.preparar_muestra(datos, self._settings_busqueda,
                                             lado_max=lado_max,
                                             mejorar=None if grande else False)
            return webp or datos     # si no se pudo convertir, se muestra el original
        return b""

    def _esperar_turno(self) -> None:
        """Cortesía entre muestras: respeta MIN_REQUEST_INTERVAL entre peticiones.

        Cada muestra usa su propio cliente HTTP (no comparten estado de cancelación),
        así que el intervalo se comparte aquí: si el usuario navega rápido por el
        carrusel, las muestras se piden espaciadas en vez de todas de golpe.
        """
        with self._lock_muestra:
            espera = config.MIN_REQUEST_INTERVAL - (time.monotonic() - self._ultima_muestra)
            if espera > 0:
                time.sleep(espera)
            self._ultima_muestra = time.monotonic()

    def _registrar_historial(self, art: Artwork, dest: Path) -> None:
        """Apunta la descarga en el historial local SIN poder tumbar la descarga.

        El archivo ya está guardado en disco: un fallo del historial (base de datos
        bloqueada por otra instancia, carpeta de usuario de solo lectura, etc.) solo
        se registra en el log; nunca convierte una descarga correcta en un error.
        """
        try:
            self._store.add(art.md5 or _hash_url(art.url), art.url, str(dest))
        except Exception:  # noqa: BLE001
            logger.warning("no se pudo registrar en el historial: %s", dest,
                           exc_info=True)

    def obra_en(self, posicion: int) -> Artwork | None:
        """La obra (con su URL original) que ocupa una casilla del carrusel (1..n)."""
        try:
            obras = list(self.results or [])
            if 1 <= posicion <= len(obras):
                return obras[posicion - 1]
        except Exception:  # noqa: BLE001
            logger.exception("excepcion en obra_en()")
        return None

    def nombre_sugerido(self, posicion: int) -> str:
        """Nombre de archivo sugerido (ya en .webp) para «Guardar como…»."""
        obra = self.obra_en(posicion)
        if obra is None:
            return "imagen.webp"
        try:
            return Path(_filename_for(obra)).with_suffix(".webp").name
        except Exception:  # noqa: BLE001
            logger.exception("excepcion en nombre_sugerido()")
            return "imagen.webp"

    # ------------------------------------------------------------------ acciones individuales
    def procesar_individual(self, posicion: int, settings: dict, accion: str = "guardar",
                            destino: Path | None = None) -> None:
        """Guarda o copia UNA imagen del carrusel aplicando la calidad configurada.

        Se ejecuta en segundo plano (la ventana no se bloquea) y usa la MISMA ruta
        que la descarga masiva (`_procesar_obra`): nombre de archivo, subcarpeta por
        plataforma, conversión obligatoria a .webp y mejora (Lanczos/IA) según las
        casillas de la ventana.

        Acciones:
          - "guardar": escribe el .webp en la carpeta de salida (con sidecar .json si
            está activado) igual que la descarga masiva; emite la ruta final.
          - "guardar_como": igual, pero en la ruta exacta que eligió el usuario en el
            diálogo (nunca busca carpetas alternativas).
          - "copiar": procesa la imagen en una carpeta temporal y entrega los bytes
            .webp ya convertidos/mejorados para el portapapeles (sin dejar archivos).

        Contrato de señales: una petición aceptada emite `individual_iniciado` y
        después exactamente un `individual_listo` o un `individual_error`; una
        petición rechazada emite solo `individual_error` (salvo el duplicado, que se
        ignora porque ya hay una idéntica en curso).
        """
        try:
            accion = accion if accion in ("copiar", "guardar_como") else "guardar"
            obra = self.obra_en(posicion)
            if obra is None:
                return
            if not obra.url:
                self.individual_error.emit(
                    posicion, "esta obra no tiene URL de imagen original")
                return
            if self._busy:
                self.individual_error.emit(
                    posicion, "hay una búsqueda o descarga en curso; espera a que termine")
                return
            if accion == "guardar_como" and destino is None:
                self.individual_error.emit(posicion, "no se indicó dónde guardar la imagen")
                return
            clave = (posicion, accion)
            with self._lock_individual:
                if clave in self._individuales:
                    return          # ya se está procesando: no se duplica la petición
                self._individuales.add(clave)

            settings = dict(settings or {})
            if accion == "guardar":
                carpeta = Path(settings.get("carpeta") or config.DEFAULT_OUTPUT_DIR)
                lista, carpeta = self._preparar_carpeta(carpeta, obligatoria=True)
                if not lista:
                    # _preparar_carpeta ya emitió el error con instrucciones
                    with self._lock_individual:
                        self._individuales.discard(clave)
                    self.individual_error.emit(
                        posicion, "no se pudo escribir en la carpeta de salida")
                    return
                settings["carpeta"] = str(carpeta)

            self.individual_iniciado.emit(posicion, accion)

            def tarea(_sig) -> None:
                # MISMO cliente y mismos avisos que la descarga masiva: pausas,
                # estatus de conexión y avisos de conversión llegan a la UI igual.
                cliente = PoliteClient(
                    cancel_event=None,
                    on_pause=lambda sec, why: self.status_changed.emit(
                        f"⏸ Pausa {int(sec)} s — {why}"),
                    on_event=lambda mensaje: self.http_event.emit(mensaje),
                )
                aviso = lambda mensaje: self.status_changed.emit(mensaje)  # noqa: E731
                try:
                    if accion == "copiar":
                        # La copia también pasa por la política de calidad: se procesa
                        # en una carpeta temporal y solo se entregan los bytes .webp.
                        temporal = Path(tempfile.mkdtemp(prefix="extractorfanarts-"))
                        try:
                            dest, meta = _procesar_obra(cliente, obra, temporal, settings,
                                                        subcarpeta=False, aviso=aviso)
                            datos = dest.read_bytes()
                        finally:
                            shutil.rmtree(temporal, ignore_errors=True)
                        logger.info("imagen %d procesada para el portapapeles (%s)",
                                    posicion, (meta or {}).get("resumen")
                                    or (meta or {}).get("modo", "?"))
                        self.individual_listo.emit(posicion, "", datos, dict(meta or {}))
                    elif accion == "guardar_como":
                        destino.parent.mkdir(parents=True, exist_ok=True)
                        dest, meta = _procesar_obra(
                            cliente, obra, destino.parent, settings,
                            sidecar=bool(settings.get("sidecar_json")),
                            subcarpeta=False, nombre=destino.name, aviso=aviso,
                        )
                        self._registrar_historial(obra, dest)
                        logger.info("imagen %d guardada como %s (%s)",
                                    posicion, dest, (meta or {}).get("resumen")
                                    or (meta or {}).get("modo", "?"))
                        self.individual_listo.emit(posicion, str(dest), b"", dict(meta or {}))
                    else:
                        outdir = Path(settings.get("carpeta") or config.DEFAULT_OUTPUT_DIR)
                        outdir.mkdir(parents=True, exist_ok=True)
                        dest, meta = _procesar_obra(
                            cliente, obra, outdir, settings,
                            sidecar=bool(settings.get("sidecar_json")), aviso=aviso,
                        )
                        self._registrar_historial(obra, dest)
                        logger.info("imagen %d guardada individualmente: %s (%s)",
                                    posicion, dest, (meta or {}).get("resumen")
                                    or (meta or {}).get("modo", "?"))
                        self.individual_listo.emit(posicion, str(dest), b"", dict(meta or {}))
                except Exception as exc:  # noqa: BLE001
                    logger.warning("acción individual (%s) fallida: %s", accion, exc,
                                   exc_info=True)
                    try:
                        self.individual_error.emit(posicion, str(exc))
                    except RuntimeError:
                        pass          # la aplicación se está cerrando
                finally:
                    cliente.close()
                    with self._lock_individual:
                        self._individuales.discard(clave)

            trabajo = _Job(tarea)
            trabajo.signals.error.connect(
                lambda msg: logger.warning("acción individual: %s", msg))
            self._pool.start(trabajo)
        except Exception as exc:  # noqa: BLE001
            logger.exception("excepcion en procesar_individual()")
            self.individual_error.emit(posicion, f"error interno: {exc}")

    def _cargar_resto_galeria(self, obras: list, ya_cargadas: int) -> None:
        """Carga en segundo plano las muestras pequeñas (tira) que falten.

        Se parte de la miniatura de la API y se entrega en .webp ligero. Respeta el
        intervalo entre peticiones del cliente HTTP (cortesía con el servidor) y se
        cancela sola si el usuario lanza otra búsqueda o pulsa Limpiar.
        """
        token = self._token_galeria

        def tarea(_sig) -> None:
            cliente = PoliteClient(
                cancel_event=None,
                min_interval=config.MIN_REQUEST_INTERVAL,
                block_pause=config.BLOCK_PAUSE,
            )
            cargadas = 0
            try:
                for posicion, obra in enumerate(obras, 1):
                    if posicion <= ya_cargadas:
                        continue
                    if token != self._token_galeria:
                        logger.debug("galería: carga en segundo plano cancelada")
                        break
                    datos = b""
                    try:
                        datos = self._muestra_de(cliente, obra, grande=False)
                    except Exception:
                        logger.debug("miniatura %d no disponible", posicion, exc_info=True)
                    if token != self._token_galeria:
                        break
                    try:
                        self.galeria_item_ready.emit(posicion, datos)
                    except RuntimeError:
                        break        # la aplicación se está cerrando
                    cargadas += 1
                logger.info("galería: %d miniaturas más cargadas en segundo plano",
                            cargadas)
            finally:
                cliente.close()

        trabajo = _Job(tarea)
        trabajo.signals.error.connect(
            lambda msg: logger.warning("galería: fallo en la carga de fondo: %s", msg))
        self._pool.start(trabajo)

    def shutdown(self) -> None:
        """Cierre ordenado (idempotente): espera a las tareas de fondo y cierra el almacén.

        Se llama al cerrar la ventana (Alt+F4, la X, la barra de tareas…) y desde
        `app.aboutToQuit`, así que puede invocarse más de una vez sin efectos raros.
        """
        if self._cerrado:
            return
        self._cerrado = True
        try:
            if self._busy and self._cancel is not None:
                self._cancel.set()          # no dejar descargas a medias al salir
            self._pool.waitForDone(3000)
        except Exception:  # noqa: BLE001
            logger.debug("no se pudieron esperar las tareas de fondo al cerrar",
                         exc_info=True)
        try:
            self._store.close()
        except Exception:  # noqa: BLE001
            logger.debug("no se pudo cerrar el almacén", exc_info=True)
        logger.info("aplicación cerrada correctamente")

    # ------------------------------------------------------------------ carpeta de salida
    def _carpetas_alternativas(self) -> list[Path]:
        """Carpetas de reserva si la elegida no se puede escribir."""
        return [
            Path.home() / "Downloads" / config.APP_NAME,
            Path.home() / ".extractorfanarts" / "descargas",
            Path.home() / config.APP_NAME,
            # Último recurso: junto a la aplicación. Es la única que funciona si el
            # proceso está confinado a la carpeta del proyecto (app lanzada desde la
            # terminal de un agente/IDE con sandbox): así la descarga no se pierde.
            config.carpeta_junto_a_la_app(),
        ]

    @staticmethod
    def _escribible(carpeta: Path) -> tuple[bool, str]:
        """¿Se puede crear y escribir en esa carpeta? Devuelve (ok, motivo)."""
        try:
            carpeta.mkdir(parents=True, exist_ok=True)
            prueba = carpeta / ".escritura_ok"
            prueba.write_text("ok", encoding="utf-8")
            prueba.unlink()
            return True, ""
        except OSError as exc:
            return False, str(exc)

    def comprobar_carpeta_salida(self, carpeta: str | Path) -> tuple[bool, str, Path | None]:
        """Comprueba la carpeta de salida SIN cambiarla (aviso al arrancar).

        Devuelve (es_escribible, motivo, primera_alternativa_escribible). La UI lo usa
        para avisar desde el principio de que las descargas acabarán en otra carpeta,
        en vez de que el usuario lo descubra al intentar guardar.
        """
        candidata = Path(carpeta or config.DEFAULT_OUTPUT_DIR)
        ok, motivo = self._escribible(candidata)
        if ok:
            return True, "", None
        for alternativa in self._carpetas_alternativas():
            if self._escribible(alternativa)[0]:
                return False, motivo, alternativa
        return False, motivo, None

    def _preparar_carpeta(self, carpeta: Path, obligatoria: bool) -> tuple[bool, Path]:
        """Crea la carpeta de salida y comprueba que se puede escribir.

        - En una BÚSQUEDA, un fallo nunca es motivo de error (solo aviso): buscar no
          necesita escribir archivos.
        - En una DESCARGA se prueban carpetas alternativas. Si ninguna sirve, se
          explica el motivo con instrucciones (permisos, protección contra
          ransomware, políticas) y se devuelve False.
        """
        intentos = [carpeta] + (self._carpetas_alternativas() if obligatoria else [])
        ultimo_error: Exception | None = None
        fallidas: list[str] = []

        for candidata in intentos:
            ok, motivo = self._escribible(candidata)
            if ok:
                if candidata != carpeta:
                    logger.warning("carpeta de salida original no escribible; se usa %s", candidata)
                    aviso = f"⚠ Carpeta no escribible; se usará: {candidata}"
                    if candidata == config.carpeta_junto_a_la_app():
                        aviso += ("  (esta app no puede escribir en tus carpetas: ábrela con "
                                  "doble clic desde el Explorador)")
                    self.status_changed.emit(aviso)
                    self.carpeta_cambiada.emit(str(candidata))
                return True, candidata
            ultimo_error = OSError(motivo)
            fallidas.append(f"{candidata}  →  {motivo}")
            logger.warning("no se pudo usar la carpeta %s: %s", candidata, motivo)

        detalle = "\n".join(f"  · {linea}" for linea in fallidas)
        if obligatoria:
            logger.error("ninguna carpeta de salida es escribible:\n%s", detalle)
            self.error.emit(
                "No se puede escribir en la carpeta de salida.\n\n"
                f"{detalle}\n\n"
                "Causa más habitual (si lanzaste la app desde la terminal de un agente/IDE\n"
                "con sandbox): el proceso solo puede escribir DENTRO de la carpeta del\n"
                "proyecto, así que Windows rechaza Imágenes, Descargas, Documentos… aunque\n"
                "tus permisos sean correctos. Solución: cierra la app y ábrela con doble clic\n"
                "desde el Explorador (ExtractorFanarts.exe o ejecutar.bat) o desde una consola\n"
                "normal.\n\n"
                "Otras causas habituales en Windows:\n"
                "  · Protección contra ransomware (Seguridad de Windows → Protección\n"
                "    contra virus y amenazas → Protección contra ransomware → Acceso\n"
                "    controlado a carpetas): añade ExtractorFanarts.exe a las\n"
                "    aplicaciones permitidas.\n"
                "  · Permisos de la carpeta o carpeta marcada como solo lectura.\n"
                "  · Una política de tu organización (WDAC/AppLocker).\n\n"
                "Solución rápida: pulsa 📂 y elige otra carpeta (por ejemplo, una\n"
                "dentro de tu carpeta de usuario) o define DEFAULT_OUTPUT_DIR en\n"
                "app/config_local.py. Para un diagnóstico completo:\n"
                "ExtractorFanarts.exe --selftest  (deja un selftest.txt con el detalle)."
            )
        else:
            logger.warning("no se pudo preparar la carpeta de salida (%s); la búsqueda continúa",
                           ultimo_error)
            self.status_changed.emit(
                f"⚠ No se pudo preparar la carpeta de salida ({ultimo_error}); "
                "la búsqueda continúa igualmente."
            )
        return False, carpeta

    # ------------------------------------------------------------------ arranque de trabajos
    def _start(self, settings: dict, download: bool) -> None:
        try:
            if self._busy:
                return
            # La carpeta de salida se crea automáticamente si no existe. En una
            # búsqueda un fallo NO impide buscar (solo avisa).
            carpeta = Path(settings.get("carpeta") or config.DEFAULT_OUTPUT_DIR)
            lista, carpeta = self._preparar_carpeta(carpeta, obligatoria=download)
            if download and not lista:
                return
            if lista:
                settings = dict(settings)
                settings["carpeta"] = str(carpeta)
            self._busy = True
            self.state_changed.emit("running")
            self._cancel = threading.Event()
            self._token_galeria += 1     # las miniaturas anteriores ya no valen
            # Las muestras de la galería (nítidas y en .webp) siguen la configuración
            # de esta búsqueda: "Mejorar calidad" decide si se realzan al mostrarlas.
            self._settings_busqueda = dict(settings)
            job = _Job(lambda sig: self._run(sig, settings, download, self._cancel))
            job.signals.status.connect(self.status_changed)
            job.signals.progress.connect(self.progress_changed)
            job.signals.results.connect(self.results_ready)
            job.signals.galeria_total.connect(self.galeria_total_ready)
            job.signals.galeria_item.connect(self.galeria_item_ready)
            job.signals.http.connect(self.http_event)
            job.signals.resumen.connect(self.job_finished)
            job.signals.error.connect(self.error)
            job.signals.done.connect(self._on_done)
            self._pool.start(job)
            logger.info("operacion iniciada: %s en %s", "descarga" if download else "busqueda",
                        settings.get("plataforma", "?"))
        except Exception:
            logger.exception("excepcion al iniciar la operacion")
            self._busy = False
            self.state_changed.emit("idle")
            self.error.emit("Error interno al iniciar la operación (ver log).")

    def _on_done(self, cancelled: bool, reason: str):
        try:
            self._busy = False
            self.state_changed.emit("idle")
            self.finished.emit("cancelada" if cancelled else "completada")
            logger.debug("operacion terminada: cancelada=%s motivo=%s", cancelled, reason)
        except Exception:
            logger.exception("excepcion en _on_done")

    # ------------------------------------------------------------------ trabajo en hilo
    def _run(self, sig: _JobSignals, settings: dict, download: bool, cancel: threading.Event):
        resumen: dict = {
            "tipo": "descarga" if download else "busqueda",
            "estado": "completada",
            "guardados": 0,
            "total": 0,
            "encontrados": 0,
            "descartados": {},
            "fallas": 0,
            "detalle_fallas": [],
            "carpeta": str(settings.get("carpeta") or config.DEFAULT_OUTPUT_DIR),
            "error": "",
        }
        client = PoliteClient(
            cancel_event=cancel,
            on_pause=lambda sec, why: sig.status.emit(f"⏸ Pausa {int(sec)} s — {why}"),
            on_event=lambda msg: sig.http.emit(msg),
        )
        try:
            query = self._query_from_settings(settings)
            adapter = adapter_for(query.kind, query.platform)
            if adapter is None:
                raise ConfigError(f"plataforma no disponible: {query.platform}")

            sig.status.emit(f"Buscando en {query.platform}…")
            logger.info("busqueda iniciada: tipo=%s plataforma=%s", query.kind, query.platform)
            arts = adapter.search(client, query)
            resumen["encontrados"] = len(arts)

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
            # Límite de cantidad configurado en la UI (si está activo)
            if settings.get("limitar"):
                kept = kept[: int(settings.get("cantidad") or 50)]
            self.results = kept
            sig.results.emit([a.summary() for a in kept])
            if rejected:
                detalle = ", ".join(f"{k}: {v}" for k, v in sorted(rejected.items()))
                resumen["descartados"] = dict(rejected)
                logger.info("resultados filtrados: %d aceptados; descartados -> %s", len(kept), detalle)
                sig.status.emit(f"Resultados: {len(kept)} aceptados · descartados → {detalle}")
            else:
                sig.status.emit(f"Resultados: {len(kept)} aceptados")

            # Galería: una casilla por CADA resultado. Se cargan ya las primeras y,
            # si CARGAR_GALERIA_COMPLETA está activo, el resto se sigue cargando en
            # segundo plano (respetando el intervalo entre peticiones) para que el
            # carrusel acabe mostrando TODAS las imágenes. Las muestras se entregan
            # en .webp ligero (tira) y la imagen grande se pide aparte, bajo demanda.
            if kept:
                limite = config.MUESTRAS_GALERIA if not download \
                    else min(4, config.MUESTRAS_GALERIA)
                limite = max(0, min(limite, len(kept)))
                sig.galeria_total.emit(len(kept))
                for posicion, obra in enumerate(kept[:limite], 1):
                    datos = b""
                    try:
                        datos = self._muestra_de(client, obra, grande=False)
                    except Exception:
                        logger.debug("no se pudo cargar la miniatura %d", posicion,
                                     exc_info=True)
                    sig.galeria_item.emit(posicion, datos)
                logger.info("galería: %d casillas (%d de inicio, resto en segundo plano)",
                            len(kept), limite)
                if config.CARGAR_GALERIA_COMPLETA and limite < len(kept):
                    tope = min(len(kept), max(limite, config.GALERIA_MAX_SEGUNDO_PLANO))
                    self._cargar_resto_galeria(list(kept[:tope]), limite)

            if not download:
                sig.status.emit("Búsqueda completada. Presiona Descargar para guardar los archivos.")
                resumen["total"] = len(kept)
                sig.resumen.emit(resumen)
                sig.done.emit(False, "busqueda")
                return
            if not kept:
                resumen["estado"] = "sin resultados"
                sig.resumen.emit(resumen)
                sig.done.emit(False, "sin resultados")
                return

            outdir = Path(settings.get("carpeta") or config.DEFAULT_OUTPUT_DIR)
            outdir.mkdir(parents=True, exist_ok=True)
            total = len(kept)
            resumen["total"] = total
            guardados = 0
            for i, art in enumerate(kept, 1):
                if cancel.is_set():
                    raise CancelledError()
                try:
                    # MISMA ruta que las acciones individuales del menú contextual:
                    # descarga + conversión obligatoria a .webp + mejora (Lanczos/IA).
                    dest, mejora_meta = _procesar_obra(
                        client, art, outdir, settings,
                        sidecar=bool(settings.get("sidecar_json")),
                        aviso=lambda mensaje: sig.status.emit(mensaje),
                    )
                    if art.animacion:
                        sig.status.emit(
                            f"[{i}/{total}] {art.site}: {dest.name} "
                            f"(animación, {(mejora_meta or {}).get('fotogramas')} fotogramas)"
                        )
                    else:
                        detalle = ((mejora_meta or {}).get("resumen")
                                   or (mejora_meta or {}).get("modo")
                                   or "sin mejora")
                        sig.status.emit(f"[{i}/{total}] {art.site}: {dest.name} ({detalle})")
                    self._registrar_historial(art, dest)
                    guardados += 1
                    sig.progress.emit(i, total)
                    pct = int(i * 100 / total) if total else 100
                    logger.info(
                        "[progreso] %d/%d (%d%%) %s: %s", i, total, pct, art.site, dest.name
                    )
                except enhance.ImagenCorruptaError as exc:
                    # _procesar_obra ya borró el archivo descartado: aquí solo se informa
                    logger.warning("descarga corrupta descartada (%s): %s", art.url, exc)
                    resumen["fallas"] += 1
                    if len(resumen["detalle_fallas"]) < 5:
                        resumen["detalle_fallas"].append(
                            f"{art.site} {art.site_id}: descarga corrupta (descartada)"
                        )
                    sig.status.emit(
                        f"⚠ descarga corrupta descartada: {art.site} {art.site_id}"
                    )
                except CancelledError:
                    raise
                except Exception as exc:
                    resumen["fallas"] += 1
                    if len(resumen["detalle_fallas"]) < 5:
                        resumen["detalle_fallas"].append(f"{art.site} {art.site_id}: {exc}")
                    logger.warning(
                        "descarga fallida %s/%s: %s", art.site, art.site_id, exc, exc_info=True
                    )
                    sig.status.emit(f"⚠ no se pudo descargar {art.page_url or art.url}: {exc}")

            resumen["guardados"] = guardados
            logger.info("descarga completada: %d/%d en %s", guardados, total, outdir)
            sig.status.emit(f"Descarga completada: {guardados}/{total} archivos en {outdir}")
            sig.resumen.emit(resumen)
            sig.done.emit(False, "descarga")
        except CancelledError:
            resumen["estado"] = "cancelada"
            logger.info("operacion cancelada por el usuario")
            sig.resumen.emit(resumen)
            sig.done.emit(True, "cancelada")
        except SinResultados as exc:
            # No es un fallo: simplemente no existe lo pedido. Un ÚNICO aviso (el de
            # «sin resultados», con el motivo en una línea); el detalle va al registro.
            resumen["estado"] = "sin resultados"
            resumen["motivo"] = str(exc)
            logger.warning("sin resultados: %s", exc)
            sig.resumen.emit(resumen)
            sig.done.emit(False, "sin resultados")
        except (BlockedError, ConfigError) as exc:
            resumen["estado"] = "error"
            resumen["error"] = str(exc)
            logger.error("error fatal en la operacion: %s", exc)
            sig.error.emit(str(exc))
            sig.resumen.emit(resumen)
            sig.done.emit(True, "error")
        except Exception as exc:
            resumen["estado"] = "error"
            resumen["error"] = str(exc)
            logger.exception("excepcion inesperada en la operacion")
            sig.error.emit(f"Error inesperado: {exc}")
            sig.resumen.emit(resumen)
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
            q.instance = (settings.get("instancia") or "").strip()
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
        # Límite de resultados: cantidad configurada o el tope de seguridad
        if settings.get("limitar"):
            q.limit = int(settings.get("cantidad") or 50)
        else:
            q.limit = config.MAX_RESULTS_PER_SOURCE
        return q
