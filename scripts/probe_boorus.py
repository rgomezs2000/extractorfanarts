"""Sondeo de boorus candidatos: comprueba si responden con JSON válido de su
familia (gelbooru/danbooru/moebooru) sin autenticación, para decidir cuáles
agregar a app/config.py.

Uso:
    python scripts/probe_boorus.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
_VENDOR = _ROOT / "vendor"
if _VENDOR.is_dir() and str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

import httpx  # noqa: E402

CANDIDATES = [
    # (nombre, familia, url de prueba)
    ("The Big ImageBoard (TBIB)", "gelbooru",
     "https://tbib.org/index.php?page=dapi&s=post&q=index&json=1&limit=1&pid=0"),
    ("Xbooru", "gelbooru",
     "https://xbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit=1&pid=0"),
    ("Realbooru", "gelbooru",
     "https://realbooru.com/index.php?page=dapi&s=post&q=index&json=1&limit=1&pid=0"),
    ("Hypnohub", "gelbooru",
     "https://hypnohub.net/index.php?page=dapi&s=post&q=index&json=1&limit=1&pid=0"),
    ("Rule34.us", "gelbooru",
     "https://rule34.us/index.php?page=dapi&s=post&q=index&json=1&limit=1&pid=0"),
    ("Safebooru (Donmai)", "danbooru",
     "https://safebooru.donmai.us/posts.json?limit=1"),
    ("Konachan (SFW)", "moebooru",
     "https://konachan.net/post.json?limit=1"),
    ("Derpibooru", "philomena",
     "https://derpibooru.org/api/v1/json/search/images?q=*&per_page=1"),
    ("ATF Booru", "danbooru",
     "https://derpibooru.org/api/v1/json/search/images?q=*&per_page=1"),
]


def main() -> int:
    with httpx.Client(follow_redirects=True, timeout=20.0,
                      headers={"User-Agent": "ExtractorFanarts/0.1 (sondeo de compatibilidad)"}) as c:
        for name, family, url in CANDIDATES:
            t0 = time.monotonic()
            try:
                resp = c.get(url)
                ok = False
                detalle = ""
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        if isinstance(data, list) and data and "file_url" in data[0]:
                            ok, detalle = True, "lista con file_url"
                        elif isinstance(data, dict) and "posts" in data and data["posts"]:
                            ok, detalle = True, "objeto con posts"
                        elif isinstance(data, list):
                            ok, detalle = False, f"lista sin file_url ({list(data[0])[:5]})"
                        else:
                            ok, detalle = False, str(data)[:80]
                    except Exception:
                        detalle = "JSON invalido"
                print(f"[{family:9}] {name:28} HTTP {resp.status_code} "
                      f"{time.monotonic()-t0:5.1f}s -> {'OK ' if ok else 'NO '} {detalle}", flush=True)
            except Exception as exc:
                print(f"[{family:9}] {name:28} ERROR {time.monotonic()-t0:5.1f}s: {exc!r}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
