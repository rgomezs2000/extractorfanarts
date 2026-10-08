"""Verificación de los boorus nuevos agregados en app/config.py.

Para cada sitio nuevo ejecuta una búsqueda de 2 resultados (solo metadatos,
sin descargar imágenes) y comprueba que la URL del archivo responde como
imagen. Uso: python scripts/verify_new_boorus.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
_VENDOR = _ROOT / "vendor"
if _VENDOR.is_dir() and str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

import httpx  # noqa: E402

from app.models.artwork import SearchQuery  # noqa: E402
from app.services.adapters import adapter_for  # noqa: E402
from app.services.http_client import PoliteClient  # noqa: E402

CASOS = [
    ("The Big ImageBoard", "solo"),
    ("Xbooru", "solo"),
    ("Hypnohub", "solo"),
    ("Safebooru (Donmai)", "hatsune_miku"),
    ("Konachan (SFW)", "hatsune_miku"),
    ("Derpibooru", "fluttershy"),
    ("ATF Booru", "solo"),
]


def main() -> int:
    client = PoliteClient(min_interval=0.5, block_pause=5.0)
    checker = httpx.Client(follow_redirects=True, timeout=20.0,
                           headers={"User-Agent": "ExtractorFanarts/0.1 (verificacion)"})
    try:
        for name, tag in CASOS:
            print(f"[{name}] tag={tag}", flush=True)
            adapter = adapter_for("booru", name)
            if adapter is None:
                print("   NO EXISTE en el registro", flush=True)
                continue
            try:
                arts = adapter.search(client, SearchQuery(kind="booru", platform=name, tags=tag, limit=2))
                print(f"   resultados: {len(arts)}", flush=True)
                for a in arts[:2]:
                    ctype = "?"
                    try:
                        with checker.stream("GET", a.url) as resp:
                            ctype = resp.headers.get("content-type", "?")
                            next(resp.iter_bytes(256), b"")
                    except Exception as exc:
                        ctype = f"error: {exc!r}"
                    print(f"   - {a.summary()} | rating={a.rating} | archivo={ctype}", flush=True)
            except Exception as exc:
                print(f"   ERROR: {exc!r}", flush=True)
    finally:
        checker.close()
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
