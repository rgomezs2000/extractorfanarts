"""Diagnóstico de conexión y credenciales por plataforma.

Uso:
    python scripts\\diag_conexion.py                 # Rule34.xxx por defecto
    python scripts\\diag_conexion.py Safebooru
    python scripts\\diag_conexion.py Gelbooru

Muestra: longitud de las credenciales (enmascaradas), cada petición HTTP con su
respuesta, y un veredicto claro. Todo queda también en .log_diag/app-<fecha>.log.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
_VENDOR = _ROOT / "vendor"
if _VENDOR.is_dir() and str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

from app import config  # noqa: E402
from app.logging_setup import setup_logging  # noqa: E402
from app.models.artwork import SearchQuery  # noqa: E402
from app.services.adapters import (  # noqa: E402
    BOORU_ADAPTERS,
    SOCIAL_ADAPTERS,
    WIKI_ADAPTERS,
    adapter_for,
)
from app.services.http_client import PoliteClient  # noqa: E402

setup_logging(_ROOT / ".diag_logs")


def _estado_credenciales(plataforma: str) -> None:
    print(f"[credenciales] plataforma: {plataforma}")

    # --- redes sociales ---
    if plataforma.startswith("X (Twitter)"):
        bearer, key, secret = config.X_BEARER_TOKEN, config.X_API_KEY, config.X_API_SECRET
        print(f"  X_BEARER_TOKEN : {'(vacío)' if not bearer else f'{len(bearer)} caracteres'}")
        print(f"  X_API_KEY      : {'(vacío)' if not key else f'{len(key)} caracteres'}")
        print(f"  X_API_SECRET   : {'(vacío)' if not secret else f'{len(secret)} caracteres'}")
        if bearer or (key and secret):
            print("  → configuración suficiente (la app usará el Bearer, o lo pedirá con key+secret)")
        else:
            print("  ← falta configurar: pon X_BEARER_TOKEN, o X_API_KEY + X_API_SECRET")
        print("  Nota: la API de X es de pago por uso (app de desarrollador con facturación).")
        return

    if plataforma == "DeviantArt":
        cid, csec = config.DEVIANTART_CLIENT_ID, config.DEVIANTART_CLIENT_SECRET
        print(f"  DEVIANTART_CLIENT_ID     : {'(vacío)' if not cid else f'{len(cid)} caracteres'}")
        print(f"  DEVIANTART_CLIENT_SECRET : {'(vacío)' if not csec else f'{len(csec)} caracteres'}")
        return

    if plataforma == "Tumblr":
        print(f"  TUMBLR_API_KEY : {'(vacío)' if not config.TUMBLR_API_KEY else 'configurada'}")
        return

    if plataforma == "Pinterest":
        tok = config.PINTEREST_ACCESS_TOKEN
        print(f"  PINTEREST_ACCESS_TOKEN : {'(vacío)' if not tok else f'{len(tok)} caracteres'}")
        print(f"  PINTEREST_COUNTRY_CODE : {config.PINTEREST_COUNTRY_CODE or '(vacío → sin búsqueda global)'}")
        return

    if plataforma == "Pixiv":
        token = getattr(config, "PIXIV_REFRESH_TOKEN", "")
        print(f"  PIXIV_REFRESH_TOKEN : {'(vacío)' if not token else f'{len(token)} caracteres'}")
        if token:
            print("  → configuración presente (la app pedirá un access token con él)")
        else:
            print("  ← falta: ejecuta  python scripts\\pixiv_token.py")
        print("  Nota: Pixiv no tiene API anónima; requiere tu cuenta (refresh token).")
        return

    if plataforma == "Newgrounds":
        print("  (Newgrounds no tiene API pública de arte; el adaptador lo explica)")
        return

    # --- boorus con claves ---
    if plataforma == "Rule34.xxx":
        clave, uid = config.RULE34_API_KEY, config.RULE34_USER_ID
    elif plataforma == "Gelbooru":
        clave, uid = config.GELBOORU_API_KEY, config.GELBOORU_USER_ID
    else:
        print("  (esta plataforma no usa claves)")
        return
    largo = len(clave)
    print(f"  api_key   : {'(vacía)' if not clave else f'{largo} caracteres'} "
          f"{'OK (~128)' if 120 <= largo <= 136 else '← revisa: debe tener ~128' if clave else ''}")
    print(f"  user_id   : {uid or '(vacío)'} "
          f"{'OK (7 dígitos)' if uid.isdigit() and len(uid) == 7 else '← revisa: debe tener 7 dígitos'}")
    if clave and (clave != clave.strip() or " " in clave):
        print("  ⚠ la clave tiene espacios al inicio/final: quítalos")
    if plataforma == "Rule34.xxx":
        tiene_cf = bool(config.CF_CLEARANCE and config.CF_USER_AGENT)
        print(f"  cf_clearance: {'configurado' if tiene_cf else 'NO configurado (necesario si hay CAPTCHA)'}")
        if tiene_cf:
            print(f"    (cookie de {len(config.CF_CLEARANCE)} caracteres, UA de "
                  f"{len(config.CF_USER_AGENT)} caracteres)")


def _buscar_adapter(plataforma: str):
    """Localiza la plataforma en cualquiera de los registros (booru, social, wiki)."""
    for tipo in ("booru", "social", "wiki"):
        adapter = adapter_for(tipo, plataforma)
        if adapter is not None:
            return tipo, adapter
    return None, None


def main() -> int:
    plataforma = sys.argv[1] if len(sys.argv) > 1 else "Rule34.xxx"
    termino = sys.argv[2] if len(sys.argv) > 2 else ""
    _estado_credenciales(plataforma)

    tipo, adapter = _buscar_adapter(plataforma)
    if adapter is None:
        print(f"[FALLO] plataforma desconocida: {plataforma}")
        print("        disponibles: " + ", ".join(
            list(BOORU_ADAPTERS) + list(SOCIAL_ADAPTERS) + list(WIKI_ADAPTERS)
        ))
        return 1

    # término de prueba por defecto según el tipo de plataforma
    if not termino:
        termino = {"booru": "hatsune_miku", "social": "fanart", "wiki": "naruto"}.get(tipo, "art")
    consulta = SearchQuery(kind=tipo, platform=plataforma, limit=2)
    if tipo == "booru":
        consulta.tags = termino
    elif tipo == "social":
        consulta.keyword = termino
    else:
        consulta.fandom = termino
        consulta.wiki_url = "https://naruto.fandom.com/" if termino == "naruto" else ""

    print(f"\n[prueba] buscando 2 resultados de '{termino}' en {plataforma} ({tipo}) …")
    client = PoliteClient(min_interval=0.5, block_pause=5.0, max_retries=1)
    try:
        arts = adapter.search(client, consulta)
        print(f"\n[RESULTADO] OK: {len(arts)} resultados recibidos")
        for art in arts[:2]:
            print(f"  - {art.summary()} | rating={art.rating}")
        if not arts:
            print("  (la conexión funcionó, pero no devolvió resultados con ese término)")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"\n[RESULTADO] FALLO: {exc}")
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
