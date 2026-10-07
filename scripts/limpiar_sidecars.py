"""Borra los archivos de metadatos (.json) generados junto a las imágenes.

Uso:
    python scripts\\limpiar_sidecars.py "C:\\Users\\usuario\\Documents\\ExtractorFanarts"
    python scripts\\limpiar_sidecars.py "C:\\...\\ExtractorFanarts" --borrar

Sin `--borrar` solo muestra qué se eliminaría (modo seguro).
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 1
    carpeta = Path(args[0])
    if not carpeta.is_dir():
        print(f"[error] no existe la carpeta: {carpeta}")
        return 1

    archivos = sorted(carpeta.rglob("*.json"))
    total_bytes = sum(p.stat().st_size for p in archivos)
    print(f"[info] {len(archivos)} archivos .json ({total_bytes / 1024:.0f} KB) en {carpeta}")

    if "--borrar" not in sys.argv:
        for p in archivos[:15]:
            print(f"   - {p.relative_to(carpeta)}")
        if len(archivos) > 15:
            print(f"   … y {len(archivos) - 15} más")
        print("\n(modo seguro) Para borrarlos de verdad, repite el comando añadiendo --borrar")
        return 0

    borrados = 0
    for p in archivos:
        try:
            p.unlink()
            borrados += 1
        except OSError as exc:
            print(f"[aviso] no se pudo borrar {p}: {exc}")
    print(f"[ok] borrados {borrados} de {len(archivos)} archivos .json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
