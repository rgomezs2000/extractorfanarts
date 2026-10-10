"""Genera el icono del asistente de Pixiv (azul Pixiv con la «p»).

El asistente `pixiv-token` tenía el MISMO icono que Imaginteca; ahora lleva el suyo,
para que se distinga en el escritorio y en la barra de tareas.

**Aviso de marcas:** «Pixiv» y su logotipo son marcas de Pixiv Inc. Este icono es una
**imitación reconocible** (cuadro redondeado azul con la «p» blanca) para identificar
que la herramienta sirve a esa plataforma; si el proyecto se distribuye ampliamente,
conviene pedir permiso o sustituirlo por uno propio.

    python scripts\\generar_icono_pixiv.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
AZUL = (0, 150, 250, 255)          # azul de la marca de Pixiv
BLANCO = (255, 255, 255, 255)
LADO = 512


def _fuente(tamano: int):
    """Fuente en negrita del sistema (la «p» de Pixiv es gruesa y redondeada)."""
    for nombre in ("arialbd.ttf", "seguisb.ttf", "DejaVuSans-Bold.ttf",
                   "arial.ttf", "DejaVuSans.ttf"):
        for carpeta in (r"C:\Windows\Fonts",
                        "/usr/share/fonts/truetype/dejavu",
                        "/Library/Fonts", "/System/Library/Fonts"):
            ruta = Path(carpeta) / nombre
            if ruta.is_file():
                try:
                    return ImageFont.truetype(str(ruta), tamano)
                except OSError:
                    continue
    return ImageFont.load_default()


def dibujar(lado: int) -> Image.Image:
    """Cuadro redondeado azul con una «p» blanca, al estilo de la marca."""
    imagen = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(imagen)
    margen = int(lado * 0.045)
    radio = int(lado * 0.22)
    dibujo.rounded_rectangle([margen, margen, lado - margen - 1, lado - margen - 1],
                             radius=radio, fill=AZUL)
    # La «p»: se dibuja la letra y se recorta el trazo para que quede gruesa y centrada.
    fuente = _fuente(int(lado * 0.78))
    caja = dibujo.textbbox((0, 0), "p", font=fuente)
    ancho, alto = caja[2] - caja[0], caja[3] - caja[1]
    posicion = ((lado - ancho) / 2 - caja[0], (lado - alto) / 2 - caja[1] - lado * 0.02)
    dibujo.text(posicion, "p", font=fuente, fill=BLANCO)
    return imagen


def main() -> int:
    destino_ico = ROOT / "assets" / "icon_pixiv.ico"
    destino_png = ROOT / "assets" / "icon_pixiv.png"
    destino_256 = ROOT / "assets" / "icon_pixiv_256.png"

    grande = dibujar(LADO)
    destino_png.parent.mkdir(parents=True, exist_ok=True)
    grande.save(destino_png)
    grande.resize((256, 256), Image.LANCZOS).save(destino_256)
    # Varios tamaños dentro del .ico (el que usa Windows en cada sitio)
    grande.save(destino_ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                                    (64, 64), (128, 128), (256, 256)])
    for ruta in (destino_ico, destino_png, destino_256):
        print(f"[ok] {ruta} ({ruta.stat().st_size / 1024:.1f} KB)")
    print()
    print("Se usa en el asistente de Pixiv (scripts/build_token_exe.py).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
