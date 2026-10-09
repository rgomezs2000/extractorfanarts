"""Arregla la etiqueta de integridad de un paquete compilado y de los motores IA.

Síntoma 1 (paquete): abres el `.exe` y la app **no puede guardar** en Imágenes,
Descargas ni en `~` («Permiso denegado»), aunque los permisos de esas carpetas sean
correctos — y aunque la abras con doble clic desde el Explorador.

Síntoma 2 (motores IA): marcas «Modo IA» y la app sigue usando Lanczos; en el
registro aparece `encode image … failed`. Los motores `realesrgan-ncnn-vulkan.exe`
y `waifu2x-ncnn-vulkan.exe` arrastran la etiqueta de integridad **baja**, Windows
los lanza en modo restringido y **no pueden escribir su imagen de salida**.

Las dos cosas se arreglan igual: devolviendo los archivos al nivel «Media». Pasa
cuando se compila o se descarga desde una consola restringida (sandbox de un
agente/IDE), porque la etiqueta **viaja con los archivos**.

Uso:
    python scripts\\arreglar_integridad.py                  # paquete + motores IA
    python scripts\\arreglar_integridad.py "ruta\\paquete"   # otro paquete
    python scripts\\arreglar_integridad.py --motores         # solo los motores IA

No necesita permisos de administrador y es idempotente (se puede ejecutar siempre).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOTORES = ("realesrgan-ncnn-vulkan", "waifu2x-ncnn-vulkan")


def _medio(ruta: Path) -> bool:
    """Pone la etiqueta de integridad «Media» a un archivo o carpeta (recursivo)."""
    icacls = shutil.which("icacls")
    if not icacls:
        print("[error] no se encontró icacls en el sistema")
        return False
    orden = [icacls, str(ruta), "/setintegritylevel", "Medium"]
    if ruta.is_dir():
        orden += ["/T", "/C"]
    resultado = subprocess.run(orden, capture_output=True, text=True)
    salida = (resultado.stdout or "").strip().splitlines()
    print(f"       {ruta.name}: {salida[-1] if salida else 'sin salida'}")
    if resultado.returncode != 0:
        detalle = (resultado.stderr or "").strip()
        if detalle:
            print(f"       {detalle[-300:]}")
        return False
    return True


def arreglar(carpeta: Path) -> int:
    """Arregla la etiqueta del paquete compilado (incluye los motores que lleva)."""
    if not sys.platform.startswith("win"):
        print("[aviso] esto solo aplica a Windows")
        return 1
    if not carpeta.is_dir():
        print(f"[error] no existe la carpeta: {carpeta}")
        return 1
    print(f"[info] poniendo la etiqueta de integridad en «Media» a:\n       {carpeta}")
    if not _medio(carpeta):
        print("[error] no se pudo arreglar el paquete")
        return 1
    print("[ok] listo: el ejecutable se abrirá con permisos normales.\n"
          "     Vuelve a abrir Imaginteca (el proceso anterior mantiene la etiqueta).")
    return 0


def arreglar_motores() -> int:
    """Devuelve a «Media» los motores IA de ./vendor (modo IA que no mejora)."""
    if not sys.platform.startswith("win"):
        return 0
    vendor = ROOT / "vendor"
    if not vendor.is_dir():
        print("[aviso] no hay carpeta vendor: no hay motores que revisar")
        return 0
    print(f"[info] revisando los motores IA de:\n       {vendor}")
    encontrados = 0
    for elemento in sorted(vendor.iterdir()):
        if not elemento.name.startswith(MOTORES):
            continue
        encontrados += 1
        _medio(elemento)
    if not encontrados:
        print("[aviso] no se encontraron motores IA en vendor. Para instalarlos:\n"
              "        python scripts\\setup_vendor.py vendor --solo-ia")
        return 0
    print("[ok] motores IA revisados. Prueba otra vez el modo IA: si la etiqueta era "
          "el problema, ahora sí mejorará.")
    return 0


def main() -> int:
    if "--motores" in sys.argv:
        return arreglar_motores()
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    destino = (Path(argumentos[0]).expanduser() if argumentos
               else ROOT / "dist" / "Imaginteca")
    codigo = arreglar(destino.resolve())
    return arreglar_motores() or codigo


if __name__ == "__main__":
    raise SystemExit(main())
