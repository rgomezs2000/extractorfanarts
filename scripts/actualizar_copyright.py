"""Deja el aviso de copyright al año en curso en todos los documentos.

Formato del aviso:

  - Si el año actual es el de creación:  «© 2026 InfoArte»
  - Si el año ya ha cambiado:            «© 2026-2027 InfoArte»

Los archivos que deben ser ASCII puro (`LEEME-PRIMERO.txt`, que se muestra en la
consola) usan «(c)» en lugar de «©», porque el símbolo no se ve bien en consolas
con juegos de caracteres antiguos.

Uso (cada vez que cambie el año, o antes de publicar):

    python scripts\\actualizar_copyright.py             # actualiza los archivos
    python scripts\\actualizar_copyright.py --comprobar # solo dice qué cambiaría

El programa NO depende de esto: `app/config.py` calcula el aviso en cada arranque
(«Acerca de», la ventana de licencia y la ayuda siempre muestran el año correcto).
Este script es para que la documentación y los textos legales también lo estén.
"""
from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import config  # noqa: E402

# Avisos ya escritos en cualquiera de sus formas conocidas. El orden importa:
# primero las formas más largas, para no dejar restos («Copyright © …»).
PATRONES = (
    re.compile(r"\(\s*Copyright\s*\(c\)\s*20\d\d(?:\s*[-–]\s*20\d\d)?\s*InfoArte\s*\)",
               re.IGNORECASE),
    re.compile(r"Copyright\s+(?:\(c\)\s*)?(?:©\s*)?20\d\d(?:\s*[-–]\s*20\d\d)?\s*InfoArte",
               re.IGNORECASE),
    re.compile(r"Copyright\s+InfoArte\s+20\d\d(?:\s*[-–]\s*20\d\d)?", re.IGNORECASE),
    re.compile(r"©\s*20\d\d(?:\s*[-–]\s*20\d\d)?\s*InfoArte", re.IGNORECASE),
    re.compile(r"\(c\)\s*20\d\d(?:\s*[-–]\s*20\d\d)?\s*InfoArte", re.IGNORECASE),
)

# Archivos que deben seguir siendo ASCII puro.
ASCII = {"LEEME-PRIMERO.txt", "publicar_wiki.bat", "compilar.bat", "ejecutar.bat",
         "firmar.bat"}

# `app/config.py` DEFINE el aviso (y su comentario lleva ejemplos): no se toca.
EXCLUIDOS = {"app/config.py", "scripts/actualizar_copyright.py"}


def aviso(ascii_only: bool) -> str:
    texto = config.AUTOR_COPYRIGHT
    return texto.replace("©", "(c)") if ascii_only else texto


def archivos() -> list[str]:
    salida = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                            text=True, check=True).stdout.split()
    if "LICENSE" not in salida:      # no tiene extensión, pero sí aviso
        salida.append("LICENSE")
    return salida


def main() -> int:
    analizador = argparse.ArgumentParser(
        description="Actualiza el aviso de copyright al año en curso.")
    analizador.add_argument("--comprobar", action="store_true",
                            help="no escribe nada: solo dice qué cambiaría")
    argumentos = analizador.parse_args()

    print(f"[info] aviso que corresponde: {config.AUTOR_COPYRIGHT!r} "
          f"(año en curso {datetime.date.today().year}, "
          f"creación {config.ANIO_INICIAL})")
    print()

    tocados = 0
    for rel in archivos():
        if rel in EXCLUIDOS:
            continue
        if not rel.endswith((".md", ".txt", ".py", ".yml", ".bat", ".ps1")) and rel != "LICENSE":
            continue
        ruta = ROOT / rel
        if not ruta.is_file():
            continue
        try:
            texto = ruta.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        nuevo = texto
        for patron in PATRONES:
            nuevo = patron.sub(aviso(ruta.name in ASCII), nuevo)
        if nuevo == texto:
            continue
        tocados += 1
        print(f"  [{'aviso' if argumentos.comprobar else 'ok'}] {rel}")
        for viejo, actual in zip(texto.splitlines(), nuevo.splitlines()):
            if viejo != actual:
                print(f"        antes: {viejo.strip()}")
                print(f"        ahora: {actual.strip()}")
        if not argumentos.comprobar:
            ruta.write_text(nuevo, encoding="utf-8")

    print()
    if argumentos.comprobar:
        print(f"[ok] {tocados} archivo(s) cambiarían (no se ha escrito nada)")
    else:
        print(f"[ok] {tocados} archivo(s) actualizados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
