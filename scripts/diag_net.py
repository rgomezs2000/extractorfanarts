"""Diagnóstico fuente por fuente con salida inmediata y tiempos cortos."""
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


def probe(name: str, url: str, params: dict | None = None) -> None:
    print(f"[{name}] iniciando…", flush=True)
    t0 = time.monotonic()
    try:
        with httpx.Client(follow_redirects=True, timeout=20.0) as c:
            resp = c.get(url, params=params)
            print(f"[{name}] HTTP {resp.status_code} en {time.monotonic()-t0:.1f}s "
                  f"({len(resp.content)} bytes)", flush=True)
    except Exception as exc:
        print(f"[{name}] ERROR en {time.monotonic()-t0:.1f}s: {exc!r}", flush=True)


probe("safebooru", "https://safebooru.org/index.php", {
    "page": "dapi", "s": "post", "q": "index", "json": "1",
    "tags": "hatsune_miku", "limit": "3", "pid": "0",
})
probe("mastodon", "https://mastodon.social/api/v1/timelines/tag/art",
      {"limit": "3", "only_media": "true"})
probe("bluesky", "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts",
      {"q": "fanart", "limit": "3"})


def probe_post(name: str, url: str, payload: dict) -> None:
    print(f"[{name}] iniciando…", flush=True)
    t0 = time.monotonic()
    try:
        with httpx.Client(follow_redirects=True, timeout=20.0) as c:
            resp = c.post(url, json=payload)
            print(f"[{name}] HTTP {resp.status_code} en {time.monotonic()-t0:.1f}s "
                  f"({len(resp.content)} bytes)", flush=True)
    except Exception as exc:
        print(f"[{name}] ERROR en {time.monotonic()-t0:.1f}s: {exc!r}", flush=True)


probe_post("misskey", "https://misskey.io/api/notes/local-timeline",
           {"limit": 3, "withFiles": True})
probe("fandom", "https://naruto.fandom.com/api.php", {
    "action": "query", "list": "search", "srsearch": "naruto_uzumaki",
    "srlimit": "3", "format": "json",
})
print("fin", flush=True)
