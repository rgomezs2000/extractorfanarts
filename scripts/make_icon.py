"""Genera el icono de la aplicación: una paleta de pintura con pincel.

Se dibuja por código (no depende de archivos ni fuentes externas) y se guarda en:
    assets/icon.png        1024x1024 (Linux, macOS, vistas previas)
    assets/icon.ico        multi-tamaño 16/24/32/48/64/128/256 (Windows, .exe)
    assets/icon_256.png    para el icono de ventana en cualquier sistema

Uso:
    python scripts/make_icon.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_VENDOR = ROOT / "vendor"
if _VENDOR.is_dir() and str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

LIENZO = 2048          # se dibuja en grande y se reduce (bordes suaves)
SALIDA = ROOT / "assets"

CREMA = (255, 249, 240, 255)
CREMA_SOMBRA = (238, 226, 210, 255)
BORDE = (58, 44, 36, 255)
MADERA = (150, 92, 48, 255)
MADERA_OSCURA = (110, 64, 30, 255)
METAL = (188, 195, 202, 255)
CERDA = (70, 60, 55, 255)

PINTURAS = [
    (231, 76, 60),    # rojo
    (243, 156, 18),   # naranja
    (241, 196, 15),   # amarillo
    (39, 174, 96),    # verde
    (41, 128, 185),   # azul
    (142, 68, 173),   # violeta
]
TAMANOS_ICO = [16, 24, 32, 48, 64, 128, 256]


def _punto(d: ImageDraw.ImageDraw, centro: tuple[float, float], radio: float,
           color: tuple[int, ...]) -> None:
    x, y = centro
    d.ellipse([x - radio, y - radio, x + radio, y + radio], fill=color)


def _pincel(capa: Image.Image) -> None:
    """Pincel diagonal dibujado DETRÁS de la paleta."""
    d = ImageDraw.Draw(capa)
    inicio = (240.0, 1860.0)
    fin = (1840.0, 250.0)
    dx, dy = fin[0] - inicio[0], fin[1] - inicio[1]
    largo = math.hypot(dx, dy)
    ux, uy = dx / largo, dy / largo

    def punto_en(t: float, radio: float, color) -> None:
        x = inicio[0] + ux * t
        y = inicio[1] + uy * t
        _punto(d, (x, y), radio, color)

    # mango de madera (con extremo redondeado) hasta el 78 % del recorrido
    t_mango = largo * 0.78
    d.line([inicio, (inicio[0] + ux * t_mango, inicio[1] + uy * t_mango)],
           fill=MADERA, width=104)
    d.line([inicio, (inicio[0] + ux * t_mango, inicio[1] + uy * t_mango)],
           fill=MADERA_OSCURA, width=30)
    punto_en(0, 52, MADERA)
    # virola metálica
    t_virola = largo * 0.86
    d.line([(inicio[0] + ux * t_mango, inicio[1] + uy * t_mango),
            (inicio[0] + ux * t_virola, inicio[1] + uy * t_virola)],
           fill=METAL, width=118)
    # cerdas + punta de pintura
    d.line([(inicio[0] + ux * t_virola, inicio[1] + uy * t_virola), fin],
           fill=CERDA, width=112)
    punto_en(largo, 56, PINTURAS[0])
    punto_en(largo * 0.995, 34, (255, 255, 255, 230))


def crear_icono() -> Image.Image:
    base = Image.new("RGBA", (LIENZO, LIENZO), (0, 0, 0, 0))

    # 1) pincel al fondo
    _pincel(base)

    # 2) silueta de la paleta (con hueco para el pulgar) como máscara
    margen = 210
    forma = Image.new("L", (LIENZO, LIENZO), 0)
    fm = ImageDraw.Draw(forma)
    fm.ellipse([margen, margen, LIENZO - margen, LIENZO - margen], fill=255)
    # hueco del pulgar (abajo a la derecha)
    fm.ellipse([1420, 1340, 1740, 1660], fill=0)
    # muesca lateral derecha (da el aspecto de paleta)
    fm.ellipse([LIENZO - margen - 160, 900, LIENZO - margen + 260, 1190], fill=0)

    # contorno: dilatar la silueta con desenfoque + umbral
    contorno = forma.filter(ImageFilter.GaussianBlur(26)).point(lambda v: 255 if v > 70 else 0)
    base.paste(BORDE, mask=contorno)
    # cuerpo crema con un degradado suave (sombra abajo)
    sombra = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sombra)
    sd.ellipse([margen + 90, margen + 150, LIENZO - margen, LIENZO - margen + 40],
               fill=CREMA_SOMBRA)
    cuerpo = Image.new("RGBA", base.size, CREMA)
    cuerpo = Image.composite(cuerpo, sombra, forma)
    base.paste(cuerpo, mask=forma)

    # 3) gotas de pintura repartidas por el arco (de abajo-izquierda a arriba-derecha)
    d = ImageDraw.Draw(base)
    centro = (LIENZO / 2, LIENZO / 2)
    radio_arco = 610.0
    angulos = (152, 186, 220, 254, 288, 324)
    for angulo, color in zip(angulos, PINTURAS):
        rad = math.radians(angulo)
        x = centro[0] + math.cos(rad) * radio_arco
        y = centro[1] + math.sin(rad) * radio_arco
        _punto(d, (x, y), 152, BORDE)          # aro oscuro (contraste a 16 px)
        _punto(d, (x, y), 128, color + (255,))
        _punto(d, (x - 42, y - 46), 40, (255, 255, 255, 190))  # brillo

    # 4) brillo superior del cuerpo de la paleta
    brillo = Image.new("RGBA", base.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(brillo)
    bd.ellipse([margen + 120, margen + 90, LIENZO - margen - 320, margen + 430],
               fill=(255, 255, 255, 90))
    brillo = brillo.filter(ImageFilter.GaussianBlur(40))
    base = Image.alpha_composite(base, Image.composite(
        brillo, Image.new("RGBA", base.size, (0, 0, 0, 0)), forma))
    return base


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    grande = crear_icono()
    icono = grande.resize((1024, 1024), Image.Resampling.LANCZOS)

    png = SALIDA / "icon.png"
    icono.save(png)
    print(f"[ok] {png}")

    png256 = SALIDA / "icon_256.png"
    icono.resize((256, 256), Image.Resampling.LANCZOS).save(png256)
    print(f"[ok] {png256}")

    ico = SALIDA / "icon.ico"
    icono.save(ico, format="ICO", sizes=[(t, t) for t in TAMANOS_ICO])
    print(f"[ok] {ico}  (tamaños: {', '.join(str(t) for t in TAMANOS_ICO)})")

    # Vista previa en una tira para comprobar cómo se ve en pequeño
    tira = Image.new("RGBA", (sum(TAMANOS_ICO) + 20 * len(TAMANOS_ICO), 256),
                     (245, 245, 245, 255))
    x = 10
    for tamano in TAMANOS_ICO:
        mini = icono.resize((tamano, tamano), Image.Resampling.LANCZOS)
        tira.paste(mini, (x, 128 - tamano // 2), mini)
        x += tamano + 20
    vista = SALIDA / "icon_preview.png"
    tira.save(vista)
    print(f"[ok] {vista} (vista previa de todos los tamaños)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
