"""Prueba de humo de los helpers de red (sin GUI ni PySide6).

Ejecuta búsquedas mínimas (3 resultados por fuente) contra:
  - Safebooru (API abierta)
  - Mastodon (mastodon.social, hashtag público)
  - Bluesky (búsqueda pública)

Uso:
    python scripts/smoke_services.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
_VENDOR = _ROOT / "vendor"
if _VENDOR.is_dir() and str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

from app import config  # noqa: E402
from app.models.artwork import SearchQuery  # noqa: E402
from app.services import filters  # noqa: E402
from app.services.adapters import adapter_for  # noqa: E402
from app.services.http_client import PoliteClient  # noqa: E402


def main() -> int:
    resultados = {}
    # pausas cortas para que la prueba sea rápida (producción usa 300 s)
    client = PoliteClient(min_interval=0.5, block_pause=5.0)
    try:
        # 1) Safebooru: búsqueda por tags
        try:
            q = SearchQuery(kind="booru", platform="Safebooru", tags="hatsune_miku", limit=3)
            arts = adapter_for("booru", "Safebooru").search(client, q)
            kept, rejected = filters.apply_filters(arts, limit=3)
            resultados["safebooru"] = {
                "ok": True,
                "obras": [a.summary() for a in kept],
                "descartados": rejected,
            }
        except Exception as exc:
            resultados["safebooru"] = {"ok": False, "error": str(exc)}

        # 2) Mastodon: timeline de hashtag público
        try:
            q = SearchQuery(kind="social", platform=f"Mastodon · {config.MASTODON_INSTANCES[0]}",
                            hashtag="art", limit=3)
            arts = adapter_for("social", q.platform).search(client, q)
            kept, rejected = filters.apply_filters(arts, limit=3)
            resultados["mastodon"] = {
                "ok": True,
                "obras": [a.summary() for a in kept],
                "descartados": rejected,
            }
        except Exception as exc:
            resultados["mastodon"] = {"ok": False, "error": str(exc)}

        # 3) Bluesky: búsqueda pública por palabra clave
        try:
            q = SearchQuery(kind="social", platform="Bluesky", keyword="fanart", limit=3)
            arts = adapter_for("social", "Bluesky").search(client, q)
            kept, rejected = filters.apply_filters(arts, limit=3)
            resultados["bluesky"] = {
                "ok": True,
                "obras": [a.summary() for a in kept],
                "descartados": rejected,
            }
        except Exception as exc:
            resultados["bluesky"] = {"ok": False, "error": str(exc)}

        # 4) Filtros: verificación de la lista negra (sin red)
        from app.models.artwork import Artwork
        malo = Artwork(site="test", site_id="1", url="http://x/img.jpg", tags=["loli"])
        bueno = Artwork(site="test", site_id="2", url="http://x/img2.jpg", tags=["safe"],
                        md5="abc")
        kept, rejected = filters.apply_filters([malo, bueno], limit=10)
        resultados["filtros"] = {
            "aceptados": [a.site_id for a in kept],
            "descartados": rejected,
            "lista_negra_ok": "1" not in [a.site_id for a in kept],
        }
    finally:
        client.close()

    print(json.dumps(resultados, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
