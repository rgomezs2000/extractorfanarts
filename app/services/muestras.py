"""Muestras de la galería: imagen original → WebP nítida y ligera para la vista previa.

La tira de miniaturas, la imagen grande del carrusel y el visor ampliado **no**
muestran la miniatura que devuelve la API (pequeña y borrosa al ampliarla): se
construye una **muestra** a partir de la imagen original con las mismas reglas de
calidad del proyecto, pero acotada al tamaño de pantalla para que sea ligera:

  - se aplica el factor de `UPSCALE_BUCKETS` (si "Mejorar calidad" está marcada) para
    que una imagen pequeña no se vea borrosa, con **Lanczos + afilado** (el motor IA
    se reserva para los archivos que se guardan: hacerlo en cada muestra sería
    muchísimo más lento y no aporta nada a tamaño de pantalla);
  - el resultado se limita a `MUESTRA_LADO_MAX` (o `MUESTRA_ICONO_LADO_MAX` para la
    tira de miniaturas): nunca se guarda ni se mantiene en memoria una muestra enorme;
  - se entrega SIEMPRE en **WebP** con `MUESTRA_CALIDAD_WEBP`, con lo que cada
    muestra ocupa unos pocos KB;
  - la transparencia se respeta.

Nunca lanza excepción por datos inválidos: si los bytes no son una imagen legible
devuelve `b""` (la galería lo marca como casilla no disponible).
"""
from __future__ import annotations

import io
import logging

from .. import config
from . import enhance

logger = logging.getLogger("extractorfanarts")


def _pillow():
    from PIL import Image
    return Image


def preparar_muestra(
    datos: bytes,
    settings: dict | None = None,
    *,
    lado_max: int | None = None,
    calidad: int | None = None,
    mejorar: bool | None = None,
) -> bytes:
    """Devuelve los bytes .webp de la muestra correspondiente a `datos`.

    `datos` son los bytes de la imagen original descargada. `lado_max` acota el lado
    mayor (por defecto el de la muestra grande); `mejorar` permite forzar o desactivar
    el upscaling (por defecto, el de la ventana y `MUESTRA_MEJORAR`).
    """
    if not datos:
        return b""
    Image = _pillow()
    lado_max = int(lado_max or getattr(config, "MUESTRA_LADO_MAX", 1600))
    calidad = int(calidad or getattr(config, "MUESTRA_CALIDAD_WEBP", 80))
    calidad = max(1, min(100, calidad))
    ajustes = settings or {}
    if mejorar is None:
        mejorar = bool(ajustes.get("mejorar")) and bool(
            getattr(config, "MUESTRA_MEJORAR", True))

    try:
        with Image.open(io.BytesIO(datos)) as abierta:
            ancho, alto = abierta.size
            tiene_alfa = enhance._tiene_alfa(abierta)
            factor = enhance.factor_for(max(ancho, alto)) if mejorar else 1

            # Tamaño objetivo: el factor de mejora, pero SIEMPRE acotado al tope de la
            # muestra (una vista previa no necesita 4000 px, y guardarla en memoria sí
            # se nota). Con imágenes grandes el tope reduce, no agranda.
            escala = float(factor)
            lado_mayor = max(ancho, alto)
            if escala * lado_mayor > lado_max:
                escala = lado_max / lado_mayor
            objetivo = (max(1, round(ancho * escala)), max(1, round(alto * escala)))

            # En JPEG se decodifica ya a escala reducida (draft): así una imagen enorme
            # no consume cientos de MB solo para hacer una muestra de pantalla.
            try:
                abierta.draft("RGBA" if tiene_alfa else "RGB", objetivo)
            except Exception:  # noqa: BLE001
                pass            # PNG y otros formatos no admiten draft
            abierta.load()      # decodifica completo (detecta truncados)

            imagen = abierta.convert("RGBA" if tiene_alfa else "RGB")
            if imagen.size != objetivo:
                imagen = imagen.resize(objetivo, Image.Resampling.LANCZOS)
                if escala > 1:
                    # afilado suave: compensa el suavizado del reescalado
                    imagen = enhance._afilar(imagen, max(20, config.SHARPEN_LANCZOS // 2))

            salida = io.BytesIO()
            if tiene_alfa:
                imagen.save(salida, "WEBP", quality=calidad, method=6, exact=True)
            else:
                imagen.save(salida, "WEBP", quality=calidad, method=6)
            return salida.getvalue()
    except Exception:  # noqa: BLE001
        logger.debug("no se pudo preparar la muestra (%d bytes)", len(datos), exc_info=True)
        return b""
