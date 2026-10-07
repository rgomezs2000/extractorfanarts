"""Obtiene el refresh token de Pixiv (flujo OAuth PKCE) y lo guarda.

Uso:
    python scripts\\pixiv_token.py                    # interactivo (recomendado)
    python scripts\\pixiv_token.py --code=XXXX        # si ya tienes el código
    python scripts\\pixiv_token.py --code=XXXX --save # guarda sin preguntar

Qué hace:
  1. Genera el código PKCE y te muestra el enlace de inicio de sesión de Pixiv.
  2. Inicias sesión con TU cuenta en el navegador.
  3. El navegador acaba en una URL con `?code=...` (la página puede fallar: es normal).
  4. Pegas esa URL (o solo el código) y el script obtiene el refresh token.
  5. Puede escribirlo automáticamente en app/config_local.py (ignorado por git).

Tu contraseña nunca pasa por este script ni por la app: solo el refresh token,
que puedes revocar cerrando sesión en Pixiv.

Importante: el código de autorización caduca en ~1 minuto; si el canje falla con
"invalid_request", vuelve a ejecutar el script y usa un código nuevo.
"""
from __future__ import annotations

import base64
import hashlib
import re
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
_VENDOR = _ROOT / "vendor"
if _VENDOR.is_dir() and str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

import httpx  # noqa: E402

from app import config  # noqa: E402

TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"
REDIRECT_URI = "https://app-api.pixiv.net/web/v1/users/auth/pixiv/callback"
LOGIN_URL = "https://app-api.pixiv.net/web/v1/login"
HASH_SECRET = "28c1fdd170a5204386cb1313c7077b34f83e4aaf4aa829ce78c231e05b0bae2c"
APP_UA = "PixivAndroidApp/5.0.234 (Android 10; Pixel 3)"
CONFIG_LOCAL = _ROOT / "app" / "config_local.py"


def _cabeceras() -> dict:
    ahora = datetime.now(timezone.utc).isoformat()
    return {
        "User-Agent": APP_UA,
        "App-OS": "android",
        "App-OS-Version": "10",
        "App-Version": "5.0.234",
        "X-Client-Time": ahora,
        "X-Client-Hash": hashlib.md5((ahora + HASH_SECRET).encode()).hexdigest(),
    }


def _limpiar_entrada(entrada: str) -> str:
    """Quita comillas y decodifica SOLO si toda la cadena viene percent-encoded.

    Ojo: decodificar una URL completa antes de parsearla rompería sus parámetros
    (los '&' internos se confundirían con separadores de la URL externa).
    """
    texto = entrada.strip().strip('"').strip("'")
    if texto.lower().startswith(("http%3a", "https%3a")):
        texto = unquote(texto)
    return texto.strip()


def _clasificar(entrada: str) -> tuple[str, str]:
    """Devuelve (codigo, url_de_continuacion).

    - URL del callback (con ?code=...) o código suelto → (codigo, "")
    - URL intermedia post-redirect?return_to=...      → ("", enlace interno)
    - Enlace /start o /login con code_challenge       → ("", ese enlace)
    - Cualquier otra cosa                             → ("", "")
    """
    texto = _limpiar_entrada(entrada)
    if not texto:
        return "", ""

    if "code=" in texto:
        consulta = parse_qs(urlparse(texto).query)
        return (consulta.get("code") or [""])[0], ""

    if "return_to=" in texto:
        consulta = parse_qs(urlparse(texto).query)
        interno = (consulta.get("return_to") or [""])[0]
        return "", unquote(interno) if interno else ""

    if texto.startswith("http") and "code_challenge=" in texto:
        return "", texto  # ya es el enlace de continuación

    if "://" not in texto and " " not in texto and 10 < len(texto) < 300:
        return texto, ""  # código suelto

    return "", ""


def _extraer_code(entrada: str) -> str:
    """Compatibilidad: solo el código (o "" si lo pegado no lo es)."""
    return _clasificar(entrada)[0]


def _continuacion_desde_intermedia(entrada: str) -> str | None:
    """Compatibilidad: extrae el enlace interno de una URL post-redirect."""
    texto = _limpiar_entrada(entrada)
    if "return_to=" not in texto:
        return None
    consulta = parse_qs(urlparse(texto).query)
    interno = (consulta.get("return_to") or [""])[0]
    return unquote(interno) if interno else None


def _guardar_en_config(token: str) -> bool:
    if not CONFIG_LOCAL.exists():
        print(f"[aviso] no existe {CONFIG_LOCAL}; crea el archivo y añade la línea a mano")
        return False
    contenido = CONFIG_LOCAL.read_text(encoding="utf-8")
    linea = f'PIXIV_REFRESH_TOKEN = "{token}"'
    if re.search(r"^#?\s*PIXIV_REFRESH_TOKEN\s*=", contenido, flags=re.MULTILINE):
        contenido = re.sub(r"^#?\s*PIXIV_REFRESH_TOKEN\s*=.*$", linea, contenido,
                           flags=re.MULTILINE)
    else:
        contenido = contenido.rstrip() + "\n\n# --------------------------------------------------- Pixiv\n" + linea + "\n"
    CONFIG_LOCAL.write_text(contenido, encoding="utf-8")
    return True


def main() -> int:
    # Modo no interactivo:  --code=XXXX  (y opcional --save)
    code_arg = ""
    guardar_auto = "--save" in sys.argv
    for argumento in sys.argv[1:]:
        if argumento.startswith("--code="):
            code_arg = argumento.split("=", 1)[1].strip()

    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip("=")
    url = (f"{LOGIN_URL}?code_challenge={challenge}&code_challenge_method=S256"
           f"&client=pixiv-android")

    if not code_arg:
        print("=" * 78)
        print("PASO 1 — Abre este enlace e inicia sesión con TU cuenta de Pixiv:")
        print()
        print("   " + url)
        print()
        print("PASO 2 — Al final el navegador muestra una página de error de Pixiv (normal).")
        print("         Copia la URL COMPLETA de la barra de direcciones: debe contener")
        print("         'code=...'.")
        print()
        print("⚠️  NO CIERRES ESTA CONSOLA hasta pegar el código: el enlace de arriba")
        print("    solo es válido con ESTA ejecución del script (si lo reinicias, cambia).")
        print("=" * 78)

        code = ""
        while not code:
            entrada = input("\nPega la URL final (con code=...) o el código: ").strip()
            code, continuacion = _clasificar(entrada)
            if code:
                break
            if continuacion:
                print()
                print("[aviso] Eso no es el final: es un enlace INTERMEDIO del login.")
                print("        Ábrelo en el navegador (ya con tu sesión de Pixiv iniciada):")
                print()
                print("   " + continuacion)
                print()
                print("        Luego copia la URL FINAL (la que contiene 'code=...') y pégala aquí.")
            else:
                print("[aviso] No se detectó 'code=' en lo pegado.")
                print("        Copia la URL completa de la barra de direcciones tras iniciar sesión.")
    else:
        code = _extraer_code(code_arg)

    if not code:
        print("[error] no se detectó ningún código")
        return 1

    print("\n[info] canjeando el código por un refresh token …")
    try:
        respuesta = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "code_verifier": verifier,
                "client_id": config.PIXIV_CLIENT_ID,
                "client_secret": config.PIXIV_CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "include_policy": "true",
            },
            headers=_cabeceras(),
            timeout=30,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[error] no se pudo contactar con Pixiv: {exc}")
        return 1

    if respuesta.status_code != 200:
        print(f"[error] Pixiv respondió HTTP {respuesta.status_code}: {respuesta.text[:200]}")
        return 1

    datos = respuesta.json()
    refresh = datos.get("refresh_token")
    if not refresh:
        print(f"[error] respuesta sin refresh_token: {str(datos)[:200]}")
        return 1

    print("\n" + "=" * 78)
    print("REFRESH TOKEN:")
    print()
    print("   " + refresh)
    print("=" * 78)

    try:
        respuesta_guardar = "s" if guardar_auto else input(
            "\n¿Guardarlo en app/config_local.py? (s/n): "
        ).strip().lower()
    except EOFError:
        respuesta_guardar = "n"
    if respuesta_guardar.startswith("s"):
        if _guardar_en_config(refresh):
            print("[ok] guardado en app/config_local.py — reinicia la app")
        else:
            print("[aviso] no se pudo guardar automáticamente")
    else:
        print("[info] copia el token en PIXIV_REFRESH_TOKEN de app/config_local.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
