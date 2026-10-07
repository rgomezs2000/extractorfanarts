"""Animaciones "ugoira" de Pixiv: ZIP de fotogramas → WebP animado.

Pixiv entrega las animaciones como un ZIP con los fotogramas numerados más una
lista de retrasos por fotograma (metadata). Aquí se descarga, se ordena y se
compone un **WebP animado**, que es el formato final obligatorio de la app.

Garantías de integridad:
  - el ZIP debe llegar completo y ser válido;
  - se necesitan al menos 2 fotogramas decodificables;
  - el WebP resultante se vuelve a abrir y se comprueba que tenga varios fotogramas;
  - ante cualquier fallo no se guarda un archivo roto (se informa y se descarta).

El CDN de Pixiv (i.pximg.net) exige la cabecera Referer, configurada en
app/config.py (REFERER_DOMAINS).
"""
from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path

from .. import config
from ..models.artwork import Artwork
from .http_client import BlockedError, ConfigError, PoliteClient

logger = logging.getLogger("extractorfanarts")


def _pillow():
    try:
        from PIL import Image
        return Image
    except ImportError:
        raise ConfigError(
            "Falta la librería Pillow en ./vendor: ejecuta python scripts\\setup_vendor.py"
        )


# ------------------------------------------------------------------ descarga
def descargar_zip(client: PoliteClient, url: str, max_mb: int | None = None) -> bytes:
    """Descarga el ZIP de fotogramas (con Referer, si el dominio lo exige)."""
    limite = (max_mb or getattr(config, "UGOIRA_MAX_ZIP_MB", 200)) * 1024 * 1024
    datos = client.get_bytes(url, max_bytes=limite)
    if not datos or not datos.startswith(b"PK"):
        raise BlockedError(
            "el ZIP de la animación no llegó completo o no es un ZIP válido"
        )
    return datos


# ------------------------------------------------------------------ conversión
def convertir_a_webp_animado(
    datos_zip: bytes,
    frames: list[dict] | None,
    destino: Path,
    calidad: int,
    max_frames: int | None = None,
) -> tuple[Path, dict]:
    """Compone el WebP animado y valida el resultado."""
    Image = _pillow()
    limite = max_frames or getattr(config, "UGOIRA_MAX_FRAMES", 400)

    try:
        archivo = zipfile.ZipFile(io.BytesIO(datos_zip))
    except zipfile.BadZipFile as exc:
        raise BlockedError(f"el ZIP de la animación está dañado: {exc}") from exc

    nombres = set(archivo.namelist())
    if frames:
        orden = frames
    else:
        orden = [
            {"file": n, "delay": 100}
            for n in sorted(nombres)
            if n.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ]

    imagenes: list = []
    retrasos: list[int] = []
    tamano: tuple[int, int] | None = None
    omitidos = 0

    for fotograma in orden[:limite]:
        if isinstance(fotograma, dict):
            nombre = str(fotograma.get("file") or "")
            retraso = int(fotograma.get("delay") or 100)
        else:
            nombre, retraso = str(fotograma), 100
        if not nombre or nombre not in nombres:
            omitidos += 1
            continue
        try:
            with archivo.open(nombre) as manejador:
                imagen = Image.open(io.BytesIO(manejador.read()))
                imagen.load()
                imagen = imagen.convert("RGBA" if "A" in imagen.getbands() else "RGB")
        except Exception:  # noqa: BLE001
            logger.warning("fotograma ilegible en la animación: %s", nombre, exc_info=True)
            omitidos += 1
            continue

        if tamano is None:
            tamano = imagen.size
        elif imagen.size != tamano:
            imagen = imagen.resize(tamano, Image.Resampling.LANCZOS)

        imagenes.append(imagen)
        retrasos.append(max(20, retraso))  # mínimo 20 ms por fotograma

    if len(imagenes) < 2:
        raise BlockedError(
            f"la animación no tiene fotogramas suficientes ({len(imagenes)} decodificados)"
        )

    destino.parent.mkdir(parents=True, exist_ok=True)
    imagenes[0].save(
        destino,
        "WEBP",
        save_all=True,
        append_images=imagenes[1:],
        duration=retrasos,
        loop=0,
        quality=calidad,
        method=6,
    )

    # Verificación: el archivo debe abrir y tener varios fotogramas
    try:
        with Image.open(destino) as comprobacion:
            comprobacion.load()
            fotogramas = int(getattr(comprobacion, "n_frames", 1))
    except Exception as exc:  # noqa: BLE001
        try:
            destino.unlink()
        except OSError:
            pass
        raise BlockedError(f"el WebP animado resultante no se pudo verificar: {exc}") from exc

    if fotogramas < 2:
        try:
            destino.unlink()
        except OSError:
            pass
        raise BlockedError("el WebP animado resultante no tiene varios fotogramas")

    meta = {
        "tipo": "ugoira (animación)",
        "fotogramas": fotogramas,
        "omitidos": omitidos,
        "duracion_ms": sum(retrasos),
        "calidad_webp": calidad,
        "resultado_px": f"{tamano[0]}x{tamano[1]}" if tamano else "",
        "transparencia": bool(imagenes[0].mode == "RGBA"),
    }
    logger.info(
        "animación convertida: %s (%d fotogramas, %.1f s)",
        destino.name, fotogramas, sum(retrasos) / 1000,
    )
    return destino, meta


# ------------------------------------------------------------------ entrada principal
def procesar(client: PoliteClient, art: Artwork, destino: Path,
             settings: dict) -> tuple[Path, dict]:
    """Descarga y convierte una animación ugoira al WebP animado final."""
    calidad = max(1, min(100, int(settings.get("calidad_webp")
                                   or config.WEBP_QUALITY_DEFAULT)))
    info = art.animacion or {}
    url_zip = info.get("zip_url") or art.url
    if not url_zip:
        raise BlockedError("la animación no trae URL de ZIP")
    datos = descargar_zip(client, url_zip)
    return convertir_a_webp_animado(datos, info.get("frames"), destino, calidad)
