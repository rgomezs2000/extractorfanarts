"""Análisis de calidad de una imagen (ideas del inspector forense de 29a.ch).

No «adivina»: **mide** los defectos que hacen que una imagen se vea sucia o fea, y con esas
medidas decide dos cosas:

  1. **Si conviene ampliarla.** Ampliar una imagen con bloques de compresión o borrosa solo
     multiplica los defectos: es mejor no ampliarla y decirlo.
  2. **Con qué parámetros guardarla en WebP.** Calidad mínima, esfuerzo máximo y, cuando la
     imagen es «plana» (capturas, dibujos de línea, fondos lisos), **sin pérdida**: ahí la
     compresión con pérdida se nota muchísimo.

Lo que se mide (sobre una miniatura de ~320 px, para que sea rápido aunque el original sea 8K):

  · **nitidez**  — varianza del filtro de bordes. Muy baja = borrosa.
  · **ruido**    — diferencia media frente a un filtro de mediana. Alto = ruidosa/grano.
  · **bloques**  — energía de los bordes cada 8 píxeles (la rejilla del JPEG). Alto = está
                    re-comprimida y se ven cuadritos.
  · **recortes** — porcentaje de píxeles quemados (≥250) o empastados (≤5).
  · **colores**  — pocos colores = imagen plana → WebP sin pérdida.

Con esos números se emite un **veredicto** (`limpia`, `aceptable`, `con defectos`) y una
lista de motivos legible, que va al registro y a la barra de estado.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("imaginteca")

LADO_ANALISIS = 320          # se analiza una miniatura: rápido y representativo
UMBRAL_NITIDEZ = 200.0       # por debajo, se considera borrosa
UMBRAL_RUIDO = 6.0           # por encima, se considera ruidosa
UMBRAL_BLOQUES = 12.0         # por encima, se ven los bloques del JPEG
UMBRAL_RECORTES = 0.06       # más del 6 % de píxeles quemados/empastados
UMBRAL_CUANTIZACION = 22.0   # media de la tabla de cuantización del JPEG: más = comprimida
UMBRAL_BPP = 0.55            # bits por píxel: por debajo, el JPEG está muy machacado
COLORES_PLANA = 512          # menos colores que esto: dibujo de línea o captura → sin pérdida


@dataclass
class Analisis:
    """Resultado de mirar una imagen con lupa."""

    valida: bool = False
    motivo: str = ""                 # por qué no es válida (si lo es, vacío)
    formato: str = ""
    modo: str = ""
    ancho: int = 0
    alto: int = 0
    nitidez: float = 0.0
    ruido: float = 0.0
    bloques: float = 0.0
    cuantizacion: float = 0.0        # media de la tabla de cuantización (si es JPEG)
    bpp: float = 0.0                 # bits por píxel del archivo (compresión real)
    recortes: float = 0.0
    colores: int = 0
    veredicto: str = "desconocido"   # limpia / aceptable / con defectos
    problemas: list[str] = field(default_factory=list)

    @property
    def limpia(self) -> bool:
        return self.veredicto == "limpia"

    @property
    def con_defectos(self) -> bool:
        return self.veredicto == "con defectos"

    @property
    def plana(self) -> bool:
        """¿Pocos colores? (captura, dibujo de línea, fondo liso) → WebP sin pérdida."""
        return 0 < self.colores <= COLORES_PLANA

    def como_texto(self) -> str:
        if not self.valida:
            return f"imagen no válida ({self.motivo})"
        partes = [
            f"{self.ancho}×{self.alto}",
            f"nitidez {self.nitidez:.0f}",
            f"ruido {self.ruido:.1f}",
            f"bloques {self.bloques:.1f}",
        ]
        if self.recortes:
            partes.append(f"recortes {self.recortes * 100:.1f}%")
        if self.plana:
            partes.append(f"plana ({self.colores} colores)")
        texto = ", ".join(partes) + f" → {self.veredicto}"
        if self.problemas:
            texto += ": " + "; ".join(self.problemas)
        return texto


# ---------------------------------------------------------------------- lectura
def _a_imagen(datos):
    """Pillow desde bytes o ruta, verificando que decodifica (no corrupta)."""
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Falta Pillow") from exc
    origen = io.BytesIO(datos) if isinstance(datos, (bytes, bytearray)) else str(datos)
    imagen = Image.open(origen)
    imagen.load()                     # decodifica todo: aquí saltan las corruptas
    return imagen


def analizar(datos) -> Analisis:
    """Mide la imagen. `datos` puede ser bytes o una ruta."""
    analisis = Analisis()
    try:
        imagen = _a_imagen(datos)
    except Exception as exc:  # noqa: BLE001
        analisis.valida = False
        analisis.motivo = f"{type(exc).__name__}: {str(exc)[:90]}"
        return analisis

    try:
        from PIL import Image, ImageChops, ImageFilter, ImageStat
    except ImportError:               # pragma: no cover
        return analisis

    analisis.valida = True
    analisis.formato = (imagen.format or "").upper()
    analisis.modo = imagen.mode
    analisis.ancho, analisis.alto = imagen.size

    # Miniatura en gris para medir rápido
    copia = imagen.convert("L")
    if max(copia.size) > LADO_ANALISIS:
        copia.thumbnail((LADO_ANALISIS, LADO_ANALISIS))

    # Nitidez: varianza de los bordes
    try:
        bordes = copia.filter(ImageFilter.FIND_EDGES)
        analisis.nitidez = float(ImageStat.Stat(bordes).var[0])
    except Exception:  # noqa: BLE001
        analisis.nitidez = 0.0

    # Ruido: diferencia media frente a la mediana
    try:
        suave = copia.filter(ImageFilter.MedianFilter(3))
        diferencia = ImageChops.difference(copia, suave)
        analisis.ruido = float(ImageStat.Stat(diferencia).mean[0])
    except Exception:  # noqa: BLE001
        analisis.ruido = 0.0

    # Bloques: en JPEG se lee la tabla de cuantización (la medida directa de cuánto se
    # comprimió); en otros formatos se mide la rejilla 8×8 del propio píxel.
    try:
        if analisis.formato == "JPEG":
            tablas = getattr(imagen, "quantization", None) or {}
            valores = [v for tabla in tablas.values() for v in tabla]
            if valores:
                analisis.cuantizacion = sum(valores) / len(valores)
        analisis.bloques = _bloques(copia)
    except Exception:  # noqa: BLE001
        analisis.bloques = 0.0

    # Bits por píxel del archivo: la medida más fiable de cuánto se comprimió un JPEG
    # (un q=12 baja de 0,3 bpp; un q=90 ronda 1-2 bpp).
    try:
        if analisis.formato == "JPEG" and analisis.ancho and analisis.alto:
            if isinstance(datos, (bytes, bytearray)):
                tamano = len(datos)
            else:
                tamano = Path(str(datos)).stat().st_size
            analisis.bpp = (tamano * 8) / float(analisis.ancho * analisis.alto)
    except Exception:  # noqa: BLE001
        analisis.bpp = 0.0

    # Recortes: píxeles quemados o empastados
    try:
        histograma = copia.histogram()
        total = max(1, copia.size[0] * copia.size[1])
        quemados = sum(histograma[250:])
        empastados = sum(histograma[:6])
        analisis.recortes = (quemados + empastados) / total
    except Exception:  # noqa: BLE001
        analisis.recortes = 0.0

    # Colores: para saber si es «plana» (captura o dibujo)
    try:
        recuento = imagen.convert("RGB")
        if max(recuento.size) > LADO_ANALISIS:
            recuento.thumbnail((LADO_ANALISIS, LADO_ANALISIS))
        colores = recuento.getcolors(maxcolors=1_000_000) or []
        analisis.colores = len(colores)
    except Exception:  # noqa: BLE001
        analisis.colores = 0

    _juzgar(analisis)
    return analisis


def _bloques(imagen) -> float:
    """Energía de los bordes en la rejilla 8×8 (el rastro típico de un JPEG recomprimido).

    Si la imagen es casi lisa no hay rejilla que medir: se devuelve 0 (evita falsos
    positivos en capturas, dibujos de línea y fondos planos).
    """
    ancho, alto = imagen.size
    datos = list(imagen.getdata())
    if ancho < 16 or alto < 16:
        return 0.0

    frontera: list[float] = []
    interior: list[float] = []
    for y in range(1, alto):
        fila = datos[y * ancho:(y + 1) * ancho]
        for x in range(8, ancho, 8):
            frontera.append(abs(fila[x] - fila[x - 1]))
        for x in range(4, ancho, 8):
            interior.append(abs(fila[x] - fila[x - 1]))
    for x in range(1, ancho):
        columna = [datos[y * ancho + x] for y in range(alto)]
        for y in range(8, alto, 8):
            frontera.append(abs(columna[y] - columna[y - 1]))
        for y in range(4, alto, 8):
            interior.append(abs(columna[y] - columna[y - 1]))
    if not frontera or not interior:
        return 0.0
    media_frontera = sum(frontera) / len(frontera)
    media_interior = sum(interior) / len(interior)
    # Con muy poco contraste no hay nada que medir (imagen plana): no es un defecto.
    if media_interior < 0.8:
        return 0.0
    return min(60.0, max(0.0, (media_frontera / media_interior - 1.0) * 20.0))


def _juzgar(analisis: Analisis) -> None:
    """Decide el veredicto y anota los motivos en lenguaje claro.

    Los defectos **graves** (borrosa, ruidosa, comprimida) hacen que no convenga ampliar;
    los **leves** (solo zonas quemadas) se aceptan con aviso. Una imagen **plana**
    (captura, dibujo de línea, fondo liso) se considera limpia por naturaleza: sus
    «bloques» y sus zonas blancas son su contenido, no defectos.
    """
    graves: list[str] = []
    leves: list[str] = []
    # Los «recortes» (píxeles a 255) solo cuentan si NO son un fondo liso: el blanco de un
    # sticker o de un dibujo es su diseño, no información pérdida.
    fondo_liso = analisis.colores <= 4000
    if not analisis.plana:
        if analisis.nitidez < UMBRAL_NITIDEZ:
            graves.append("poca nitidez (borrosa o desenfocada)")
        if analisis.ruido > UMBRAL_RUIDO:
            graves.append("ruido o grano visible")
        comprimida = ("artefactos de compresión (bloques del JPEG)")
        if analisis.bpp and analisis.formato == "JPEG" and analisis.bpp < UMBRAL_BPP:
            graves.append(comprimida)
        elif analisis.cuantizacion > UMBRAL_CUANTIZACION:
            graves.append(comprimida)
        elif analisis.bloques > UMBRAL_BLOQUES:
            graves.append(comprimida)
        # Las zonas quemadas NO se tratan como defecto: en dibujos, stickers y capturas el
        # «blanco» es el fondo, y en una foto no se puede recuperar. Se miden y se muestran
        # en la ficha, pero no convierten la imagen en «defectuosa» ni generan avisos.
    analisis.problemas = graves + leves
    if graves:
        analisis.veredicto = "con defectos"
    elif leves:
        analisis.veredicto = "aceptable"
    else:
        analisis.veredicto = "limpia"


# ---------------------------------------------------------------------- decisiones
def factor_recomendado(lado_mayor: int, factor_base: int,
                       analisis: Analisis | None) -> tuple[int, str]:
    """Factor de ampliación que conviene, y por qué.

    Se parte del tramo configurado (4x/3x/2x). Si la imagen trae defectos serios, **no se
    amplía**: ampliarla solo haría más grandes los bloques y el ruido. Se sigue guardando
    en WebP con la mejor calidad posible.
    """
    if factor_base <= 1:
        return 1, ""
    if analisis is None or not analisis.valida:
        return factor_base, ""
    if analisis.con_defectos:
        return 1, ("no se amplía: " + "; ".join(analisis.problemas)
                   + " (ampliar solo agrandaría los defectos)")
    if analisis.ruido > UMBRAL_RUIDO * 0.6 and factor_base > 2:
        return 2, "se amplía la mitad: el grano no gana nada con más ampliación"
    return factor_base, ""


def parametros_webp(analisis: Analisis | None, calidad: int) -> dict:
    """Parámetros de guardado en WebP que no añaden defectos.

    · calidad mínima 90 (configurable por `WEBP_CALIDAD_MINIMA`);
    · esfuerzo máximo (`method=6`), que es lo que más apura la compresión sin perder;
    · **sin pérdida** cuando la imagen es plana (capturas, dibujos de línea, fondos lisos),
      donde la compresión con pérdida se nota en forma de manchas y bordes sucios.
    """
    from .. import config as _config

    minima = int(getattr(_config, "WEBP_CALIDAD_MINIMA", 90) or 90)
    base = max(1, min(100, int(calidad or 90)))
    parametros = {
        "quality": max(base, minima),
        "method": 6,
        "lossless": bool(analisis is not None and analisis.valida and analisis.plana),
    }
    if parametros["lossless"]:
        parametros["quality"] = 100
    return parametros


def analizar_ruta(ruta: Path) -> Analisis:
    """Atajo para analizar un archivo."""
    return analizar(Path(ruta))


# ---------------------------------------------------------------------- reparación
def reparar(imagen, analisis: Analisis) -> tuple[object, list[str]]:
    """Arregla lo que se pueda: ruido, bloques de compresión y falta de nitidez.

    Se aplica **siempre antes** de ampliar y guardar: no se entrega una imagen en mal
    estado. Devuelve la imagen arreglada y la lista de lo que se hizo (para el registro).
    """
    from PIL import ImageFilter

    hechos: list[str] = []
    if analisis is None or not analisis.valida:
        return imagen, hechos

    pixeles = max(1, imagen.size[0] * imagen.size[1])
    # 1) Ruido / grano: un filtro de mediana quita el grano sin destrozar los bordes.
    if analisis.ruido > UMBRAL_RUIDO and pixeles <= 25_000_000:
        imagen = imagen.filter(ImageFilter.MedianFilter(3))
        hechos.append("reducido el ruido")
    # 2) Bloques de compresión: un desenfoque mínimo rompe la rejilla del JPEG y luego
    #    se recupera la definición; así los cuadritos dejan de verse.
    comprimida = (
        analisis.bloques > UMBRAL_BLOQUES
        or analisis.cuantizacion > UMBRAL_CUANTIZACION
        or (analisis.formato == "JPEG" and analisis.bpp and analisis.bpp < UMBRAL_BPP)
    )
    if comprimida:
        imagen = imagen.filter(ImageFilter.GaussianBlur(0.6))
        hechos.append("alisados los bloques de compresión")
    # 3) Nitidez: reenfoque suave (sin halos) si estaba borrosa o si se acaba de alisar.
    if analisis.nitidez < UMBRAL_NITIDEZ or comprimida:
        imagen = imagen.filter(ImageFilter.UnsharpMask(radius=2, percent=160, threshold=2))
        hechos.append("recuperada la nitidez")
    return imagen, hechos


def recuperar_danada(datos) -> object | None:
    """Intenta abrir una imagen dañada o truncada (recupera lo que haya), o None.

    Muchos archivos «corruptos» solo están **cortados**: Pillow puede leer lo que llegó
    y reconstruir la imagen. Así no se descarga otra vez lo que ya tenemos.
    """
    try:
        from PIL import Image, ImageFile
    except ImportError:  # pragma: no cover
        return None
    anterior = ImageFile.LOAD_TRUNCATED_IMAGES
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    try:
        origen = io.BytesIO(datos) if isinstance(datos, (bytes, bytearray)) else str(datos)
        imagen = Image.open(origen)
        imagen.load()
        return imagen
    except Exception:  # noqa: BLE001
        return None
    finally:
        ImageFile.LOAD_TRUNCATED_IMAGES = anterior
