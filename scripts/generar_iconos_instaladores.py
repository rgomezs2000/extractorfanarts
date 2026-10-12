"""Genera los iconos de los INSTALADORES (el símbolo típico de cada sistema).

  · Windows (.ico)  → la **caja con la flecha azul hacia dentro** de toda la vida
                      (el icono clásico de «instalar/agregar programa»).
  · macOS (.icns)   → el **disco plateado** de las imágenes de disco (.dmg).
  · Linux (.png)    → el **paquete de cartón** (la caja de los paquetes .deb/.rpm).

Además saca los tamaños pequeños del icono de la aplicación (48 y 128 px), que en Linux
hacen que se vea nítido en el menú y en el centro de software.

    python scripts\\generar_iconos_instaladores.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

AZUL = (30, 78, 140, 255)
AZUL_CLARO = (74, 158, 255, 255)
BLANCO = (255, 255, 255, 255)
GRIS_CAJA = (233, 236, 240, 255)
GRIS_LINEA = (150, 158, 168, 255)
PLATA = (222, 226, 232, 255)
PLATA_OSCURA = (168, 175, 185, 255)
CARTON = (206, 163, 105, 255)
CARTON_OSCURO = (170, 126, 72, 255)
LADO = 512


def _redondeado(dibujo, lado, relleno, margen_rel=0.04, radio_rel=0.22):
    margen = int(lado * margen_rel)
    dibujo.rounded_rectangle([margen, margen, lado - margen - 1, lado - margen - 1],
                             radius=int(lado * radio_rel), fill=relleno)


def _flecha_abajo(dibujo, lado, color, centro_x=None, arriba=0.20, abajo=0.52, ancho=0.13):
    """Flecha gruesa hacia abajo (el símbolo de «instalar»)."""
    cx = int(centro_x if centro_x is not None else lado / 2)
    y0, y1 = int(lado * arriba), int(lado * abajo)
    cuerpo = int(lado * ancho / 2)
    punta = int(lado * ancho * 1.5)
    dibujo.rounded_rectangle([cx - cuerpo, y0, cx + cuerpo, y1 - punta * 0.5],
                             radius=cuerpo, fill=color)
    dibujo.polygon([(cx - punta, y1 - punta), (cx + punta, y1 - punta), (cx, y1)], fill=color)


def icono_windows(lado: int = LADO) -> Image.Image:
    """Caja blanca con la flecha azul entrando: el icono clásico de instalación."""
    imagen = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(imagen)
    _redondeado(dibujo, lado, AZUL)
    # Caja (tapa + frente)
    x0, x1 = int(lado * 0.26), int(lado * 0.74)
    y_tapa, y_medio, y_base = int(lado * 0.56), int(lado * 0.66), int(lado * 0.82)
    dibujo.polygon([(x0, y_tapa), (int(lado * 0.5), int(lado * 0.50)),
                    (x1, y_tapa), (int(lado * 0.5), int(lado * 0.62))], fill=GRIS_CAJA)
    dibujo.rectangle([x0, y_tapa, x1, y_base], fill=BLANCO)
    dibujo.line([(x0, y_tapa), (x1, y_tapa)], fill=GRIS_LINEA, width=max(2, lado // 90))
    dibujo.line([(int(lado * 0.5), int(lado * 0.62)), (int(lado * 0.5), y_base)],
                fill=GRIS_LINEA, width=max(2, lado // 110))
    # Flecha azul clara hacia la caja
    _flecha_abajo(dibujo, lado, AZUL_CLARO, arriba=0.16, abajo=0.50, ancho=0.17)
    return imagen


def icono_macos(lado: int = LADO) -> Image.Image:
    """Disco plateado (imagen de disco .dmg) con una flecha discreta."""
    imagen = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(imagen)
    _redondeado(dibujo, lado, (250, 250, 252, 255), radio_rel=0.20)
    # Disco
    centro, radio = lado // 2, int(lado * 0.30)
    dibujo.ellipse([centro - radio, centro - radio + int(lado * 0.06),
                    centro + radio, centro + radio + int(lado * 0.06)], fill=PLATA,
                   outline=PLATA_OSCURA, width=max(3, lado // 80))
    agujero = int(radio * 0.30)
    dibujo.ellipse([centro - agujero, centro - agujero + int(lado * 0.06),
                    centro + agujero, centro + agujero + int(lado * 0.06)],
                   fill=(246, 247, 249, 255), outline=PLATA_OSCURA, width=max(2, lado // 120))
    _flecha_abajo(dibujo, lado, AZUL_CLARO, arriba=0.08, abajo=0.26, ancho=0.10)
    return imagen


def icono_linux(lado: int = LADO) -> Image.Image:
    """Paquete de cartón atado: el icono típico de los paquetes de Linux."""
    imagen = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(imagen)
    _redondeado(dibujo, lado, (245, 246, 248, 255), radio_rel=0.20)
    x0, x1 = int(lado * 0.20), int(lado * 0.80)
    y_tapa, y_base = int(lado * 0.30), int(lado * 0.80)
    # Tapa en perspectiva
    dibujo.polygon([(x0, y_tapa), (int(lado * 0.30), int(lado * 0.20)),
                    (int(lado * 0.90), int(lado * 0.20)), (x1, y_tapa)], fill=CARTON)
    # Frente
    dibujo.rectangle([x0, y_tapa, x1, y_base], fill=CARTON)
    # Cinta central y laterales
    ancho = max(3, lado // 70)
    dibujo.line([(lado // 2, y_tapa), (lado // 2, y_base)], fill=CARTON_OSCURO, width=ancho)
    dibujo.line([(x0, y_tapa), (x1, y_tapa)], fill=CARTON_OSCURO, width=ancho)
    dibujo.line([(int(lado * 0.30), int(lado * 0.20)), (int(lado * 0.30), y_tapa)],
                fill=CARTON_OSCURO, width=ancho)
    dibujo.line([(x0, y_tapa), (x0, y_base)], fill=CARTON_OSCURO, width=ancho)
    dibujo.line([(x1, y_tapa), (x1, y_base)], fill=CARTON_OSCURO, width=ancho)
    dibujo.line([(x0, y_base), (x1, y_base)], fill=CARTON_OSCURO, width=ancho)
    return imagen


def main() -> int:
    hechos: list[Path] = []

    win = icono_windows()
    ruta = ASSETS / "instalador_windows.ico"
    # OJO: hasta 128 px. El icono de 256 px lo guarda Pillow comprimido en PNG y **Inno
    # Setup no lo acepta** («icon file ... contains an invalid image»), que es quien
    # construye el instalador de Windows. Con 16..128 va en formato clásico y entra bien.
    win.save(ruta, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128)])
    hechos += [ruta, ASSETS / "instalador_windows.png"]
    win.resize((256, 256), Image.LANCZOS).save(ASSETS / "instalador_windows.png")

    mac = icono_macos()
    ruta_icns = ASSETS / "instalador_macos.icns"
    try:
        mac.save(ruta_icns)                       # Pillow lo escribe en varios tamaños
        hechos.append(ruta_icns)
    except Exception as exc:  # noqa: BLE001
        print(f"[aviso] no se pudo crear el .icns ({exc}); se deja el .png")
    mac.resize((512, 512), Image.LANCZOS).save(ASSETS / "instalador_macos.png")
    hechos.append(ASSETS / "instalador_macos.png")

    linux = icono_linux()
    linux.resize((256, 256), Image.LANCZOS).save(ASSETS / "instalador_linux.png")
    hechos.append(ASSETS / "instalador_linux.png")

    # Tamaños pequeños del icono de la aplicación (para Linux)
    original = ASSETS / "icon.png"
    if original.is_file():
        with Image.open(original) as app:
            app = app.convert("RGBA")
            for tam in (48, 128):
                destino = ASSETS / f"icon_{tam}.png"
                app.resize((tam, tam), Image.LANCZOS).save(destino)
                hechos.append(destino)

    print("Iconos de instaladores generados:")
    for ruta in hechos:
        if ruta.is_file():
            print(f"  [ok] {ruta.name:<28} {ruta.stat().st_size / 1024:7.1f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
