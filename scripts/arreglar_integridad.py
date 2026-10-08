"""Arregla la etiqueta de integridad de un paquete ya compilado (Windows).

Síntoma que arregla: abres el `.exe` y la app **no puede guardar** en Imágenes,
Descargas ni en `~` («Permiso denegado»), aunque los permisos de esas carpetas sean
correctos — y aunque la abras con doble clic desde el Explorador. Ocurre cuando el
paquete se compiló desde una consola restringida (sandbox de un agente/IDE): los
archivos heredan la etiqueta de integridad **baja** y Windows lanza el proceso en
modo restringido. La etiqueta viaja con los archivos, por eso el problema persiste.

Uso:
    python scripts\\arreglar_integridad.py                      # dist\\ExtractorFanarts
    python scripts\\arreglar_integridad.py "ruta\\del\\paquete"  # otra carpeta

No necesita permisos de administrador y es idempotente (se puede ejecutar siempre).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def arreglar(carpeta: Path) -> int:
    if not sys.platform.startswith("win"):
        print("[aviso] esto solo aplica a Windows")
        return 1
    if not carpeta.is_dir():
        print(f"[error] no existe la carpeta: {carpeta}")
        return 1
    icacls = shutil.which("icacls")
    if not icacls:
        print("[error] no se encontró icacls en el sistema")
        return 1
    print(f"[info] poniendo la etiqueta de integridad en «Media» a:\n       {carpeta}")
    resultado = subprocess.run(
        [icacls, str(carpeta), "/setintegritylevel", "Medium", "/T"],
        capture_output=True, text=True,
    )
    salida = (resultado.stdout or "").strip().splitlines()
    print(f"       {salida[-1] if salida else 'sin salida'}")
    if resultado.returncode != 0:
        print(f"[error] icacls terminó con código {resultado.returncode}")
        print((resultado.stderr or "").strip()[-500:])
        return resultado.returncode
    print("[ok] listo: el ejecutable se abrirá con permisos normales.\n"
          "     Vuelve a abrir ExtractorFanarts (el proceso anterior mantiene la etiqueta).")
    return 0


def main() -> int:
    destino = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else \
        ROOT / "dist" / "ExtractorFanarts"
    return arreglar(destino.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
