"""Endurecimiento de seguridad del sistema (integridad, no credenciales).

Medidas aplicadas, todas verificables con `python main.py --seguridad`:

  · **Bombas de descompresión**: Pillow tiene un tope de píxeles (`MAX_IMAGE_PIXELS`) y se
    rechazan imágenes cuyas dimensiones declaradas superen ese tope antes de decodificar.
  · **ZIP hostiles** (ugoira de Pixiv, paquetes de actualización): se limitan el número de
    entradas, el tamaño de cada una y el total, y se rechazan rutas absolutas o con `..`
    (zip-slip / path traversal).
  · **Nombre de archivo seguro**: al guardar se sanean los nombres que vienen de la red
    (sin separadores, sin `..`, sin caracteres reservados de Windows).
  · **Procesos externos**: siempre con lista de argumentos (nunca `shell=True`), con
    timeouts y con ejecutables resueltos a rutas reales.
  · **Secretos**: las claves se enmascaran en los registros, y los archivos de configuración
    con claves no se publican.
  · **Descargas**: topes de bytes por petición (`max_bytes`), verificación TLS activa y
    transporte sin desactivar certificados.
"""
from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path

logger = logging.getLogger("imaginteca")

# Topes de seguridad
MAX_ZIP_ENTRADAS = 5000
MAX_ZIP_MIEMBRO_MB = 60
MAX_ZIP_TOTAL_MB = 400
MAX_PIXELES_IMAGEN = 120_000_000        # ~120 MP: por encima es una bomba, no un fanart

_RESERVADOS_WINDOWS = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}
_NO_VALIDOS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def endurecer_entorno() -> None:
    """Aplica los límites globales del proceso. Se llama al arrancar."""
    try:
        from PIL import Image

        Image.MAX_IMAGE_PIXELS = MAX_PIXELES_IMAGEN
        logger.info("seguridad: tope de imagen en %d MP", MAX_PIXELES_IMAGEN // 1_000_000)
    except Exception:  # noqa: BLE001
        logger.debug("seguridad: no se pudo fijar el tope de Pillow", exc_info=True)


# ---------------------------------------------------------------------- permisos (multiplataforma)
def proteger_archivo(ruta: Path, solo_lectura_dueno: bool = True) -> bool:
    """Restringe un archivo con claves a su dueño (0600) en macOS/Linux.

    En Windows no existe esa semántica POSIX: allí el archivo vive en el perfil del usuario
    y hereda las ACL de Windows. Devuelve True si quedó restringido en este sistema.
    """
    if os.name == "nt":
        return False
    try:
        modo = 0o600 if solo_lectura_dueno else 0o644
        os.chmod(ruta, modo)
        logger.info("seguridad: permisos %o aplicados a %s", modo, ruta.name)
        return True
    except OSError as exc:
        logger.warning("seguridad: no se pudieron ajustar permisos de %s: %s", ruta, exc)
        return False


def proteger_carpeta(ruta: Path) -> bool:
    """Carpeta privada del programa (~/.imaginteca): 0700 en macOS/Linux."""
    if os.name == "nt":
        return False
    try:
        os.chmod(ruta, 0o700)
        return True
    except OSError:
        return False


def sistema() -> str:
    """Nombre legible del sistema para la comprobación de seguridad."""
    if os.name == "nt":
        return "Windows"
    if sys.platform == "darwin":
        return "macOS"
    return "Linux/Unix"


# ---------------------------------------------------------------------- nombres
def nombre_seguro(texto: str, maximo: int = 120) -> str:
    """Nombre de archivo sin rutas, sin `..` y sin caracteres prohibidos en Windows."""
    limpio = _NO_VALIDOS.sub("_", str(texto or "")).strip(" .")
    limpio = limpio.replace("..", "_")
    if not limpio:
        return "archivo"
    base = limpio.split(".")[0].lower()
    if base in _RESERVADOS_WINDOWS:
        limpio = f"_{limpio}"
    return limpio[:maximo]


def ruta_dentro_de(base: Path, relativa: str) -> Path | None:
    """Resuelve `relativa` dentro de `base`, o None si se escapa (path traversal)."""
    try:
        candidata = (base / relativa).resolve()
        raiz = base.resolve()
    except (OSError, RuntimeError):
        return None
    try:
        candidata.relative_to(raiz)
    except ValueError:
        return None
    return candidata


# ---------------------------------------------------------------------- ZIP
def miembro_zip_seguro(nombre: str) -> str | None:
    """Nombre normalizado de una entrada de ZIP, o None si es hostil (zip-slip)."""
    texto = str(nombre or "").replace("\\", "/")
    if not texto or texto.startswith("/") or re.match(r"^[A-Za-z]:", texto):
        return None
    if ".." in texto.split("/"):
        return None
    return texto


def revisar_zip(archivo) -> list[str]:
    """Comprueba un ZipFile abierto. Devuelve la lista de problemas (vacía si está bien).

    Se miran: número de entradas, tamaño de cada una (sin descomprimir) y total. Un ZIP
    puede declarar 10 KB y expandirse a gigabytes: por eso se valida antes de leer nada.
    """
    problemas: list[str] = []
    try:
        infos = archivo.infolist()
    except Exception as exc:  # noqa: BLE001
        return [f"no se pudo listar el ZIP: {exc}"]
    if len(infos) > MAX_ZIP_ENTRADAS:
        problemas.append(f"demasiadas entradas ({len(infos)} > {MAX_ZIP_ENTRADAS})")
    total = 0
    for info in infos:
        tamano = int(getattr(info, "file_size", 0) or 0)
        total += tamano
        if tamano > MAX_ZIP_MIEMBRO_MB * 1024 * 1024:
            problemas.append(f"entrada demasiado grande: {info.filename} "
                             f"({tamano / 1024 / 1024:.0f} MB)")
            break
        if miembro_zip_seguro(info.filename) is None:
            problemas.append(f"ruta no permitida en el ZIP: {info.filename}")
            break
    if total > MAX_ZIP_TOTAL_MB * 1024 * 1024:
        problemas.append(f"el ZIP se expandiría a {total / 1024 / 1024:.0f} MB")
    return problemas


def imagenes_sanas() -> list[str]:
    """Comprobaciones que se muestran en `--seguridad` (devuelve fallos)."""
    fallos: list[str] = []
    try:
        from PIL import Image

        if Image.MAX_IMAGE_PIXELS != MAX_PIXELES_IMAGEN:
            fallos.append("MAX_IMAGE_PIXELS no está aplicado")
    except Exception as exc:  # noqa: BLE001
        fallos.append(f"Pillow no disponible: {exc}")

    # Se comprueba el INVARIANTE (que no queden separadores ni «..»), no el texto exacto.
    peligroso = nombre_seguro("../../etc/passwd")
    if "/" in peligroso or "\\" in peligroso or ".." in peligroso:
        fallos.append("nombre_seguro no neutraliza rutas")
    if nombre_seguro("CON.txt").startswith("CON"):
        fallos.append("nombre_seguro no protege nombres reservados")
    import tempfile

    with tempfile.TemporaryDirectory() as carpeta:
        base = Path(carpeta)
        if ruta_dentro_de(base, "../fuera.txt") is not None:
            fallos.append("ruta_dentro_de permite salir de la carpeta")
        if ruta_dentro_de(base, "dentro.txt") is None:
            fallos.append("ruta_dentro_de rechaza rutas válidas")
    if miembro_zip_seguro("../../x") is not None:
        fallos.append("miembro_zip_seguro permite zip-slip")
    if miembro_zip_seguro("/abs/x") is not None:
        fallos.append("miembro_zip_seguro permite rutas absolutas")
    return fallos
