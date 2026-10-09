"""Obtiene el refresh token de Pixiv (flujo OAuth PKCE) y lo guarda en config_local.py.

Uso como script (desarrollo, dentro del repositorio):
    python scripts\\pixiv_token.py                    # interactivo (recomendado)
    python scripts\\pixiv_token.py --code=XXXX        # si ya tienes el código
    python scripts\\pixiv_token.py --code=XXXX --save # guarda sin preguntar

Uso como ejecutable (el que viaja DENTRO del paquete del release):
    pixiv-token.exe                                   # doble clic; no necesita Python

Qué hace:
  1. Genera el código PKCE y muestra el enlace de inicio de sesión de Pixiv.
  2. Inicias sesión con TU cuenta en el navegador.
  3. El navegador acaba en una URL con `?code=...` (la página puede dar error: es normal).
  4. Pegas esa URL (o solo el código) y se obtiene el refresh token.
  5. Lo escribe en el MISMO `config_local.py` que lee la aplicación, así que basta con
     reiniciar Imaginteca.

Tu contraseña nunca pasa por este asistente ni por la aplicación: solo el refresh token,
que puedes revocar cerrando sesión en Pixiv.

Importante: el código de autorización caduca en ~1 minuto. Si el canje falla con
"invalid_request", vuelve a ejecutarlo y usa un código nuevo.
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
if str(_ROOT) not in sys.path:
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


def _congelado() -> bool:
    """True cuando corremos como ejecutable compilado (PyInstaller)."""
    return bool(getattr(sys, "frozen", False))


def _destino_config() -> Path:
    """El `config_local.py` que lee la aplicación: en ese mismo se escribe el token.

    La app lo busca, por este orden: junto al ejecutable, dentro del paquete y en
    `~/.imaginteca/config_local.py`. `config.CONFIG_LOCAL_USADO` ya contiene la
    ruta del que encontró, así que escribir ahí garantiza que la app lo verá.
    """
    usado = str(getattr(config, "CONFIG_LOCAL_USADO", "") or "")
    if usado:
        return Path(usado)
    if _congelado():
        return Path(sys.executable).resolve().parent / "config_local.py"
    return _ROOT / "app" / "config_local.py"


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


def _guardar_en_config(token: str) -> Path | None:
    """Escribe (o reemplaza) PIXIV_REFRESH_TOKEN en el config_local.py de la app."""
    destino = _destino_config()
    linea = f'PIXIV_REFRESH_TOKEN = "{token}"'
    try:
        if destino.is_file():
            contenido = destino.read_text(encoding="utf-8")
        else:
            destino.parent.mkdir(parents=True, exist_ok=True)
            contenido = (
                '"""Ajustes y credenciales locales de Imaginteca.\n\n'
                "Cualquier constante en MAYUSCULAS de aqui sobreescribe app/config.py.\n"
                '"""\n'
            )
        if re.search(r"^#?\s*PIXIV_REFRESH_TOKEN\s*=", contenido, flags=re.MULTILINE):
            contenido = re.sub(r"^#?\s*PIXIV_REFRESH_TOKEN\s*=.*$", linea, contenido,
                               flags=re.MULTILINE)
        else:
            contenido = (contenido.rstrip()
                         + "\n\n# --------------------------------------------------- Pixiv\n"
                         + linea + "\n")
        destino.write_text(contenido, encoding="utf-8")
        return destino
    except OSError as exc:
        print(f"[aviso] no se pudo escribir en {destino}: {exc}")
        return None


def _pedir(mensaje: str) -> str | None:
    """`input()` que no revienta si la consola se cierra o no hay entrada."""
    try:
        return input(mensaje)
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def _pausa_final() -> None:
    """En el ejecutable, la ventana de consola se cierra al terminar: esperamos.

    Solo cuando hay una consola interactiva de verdad (doble clic). Si se lanza desde
    otra terminal o con la entrada redirigida, no se detiene. Se puede desactivar con
    `--sin-pausa`.
    """
    if not _congelado() or "--sin-pausa" in sys.argv:
        return
    if any(opcion in sys.argv for opcion in ("--ayuda", "-h", "--help", "--donde")):
        return
    try:
        if sys.stdin is None or not sys.stdin.isatty():
            return
    except Exception:  # noqa: BLE001
        return
    _pedir("\nPulse Intro para cerrar…")


def _ayuda() -> None:
    print(__doc__.strip())
    print("\nOpciones:")
    print("  --code=XXXX    canjea directamente un código que ya tengas")
    print("  --save         guarda el token sin preguntar")
    print("  --donde        muestra en qué config_local.py se guardará y sale")
    print("  --sin-pausa    no espera al final (al lanzarlo desde otra consola)")
    print("  --ayuda        muestra esta ayuda")


def main() -> int:
    if "--ayuda" in sys.argv or "-h" in sys.argv or "--help" in sys.argv:
        _ayuda()
        return 0

    if "--donde" in sys.argv:
        destino = _destino_config()
        print(f"config_local.py que usa la aplicación: {destino}")
        print(f"existe: {'sí' if destino.is_file() else 'no (se creará al guardar el token)'}")
        print(f"ejecutable: {Path(sys.executable).resolve()}")
        return 0

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
        print("ASISTENTE DE PIXIV — Imaginteca")
        print("=" * 78)
        print("PASO 1 — Abre este enlace e inicia sesión con TU cuenta de Pixiv:")
        print()
        print("   " + url)
        print()
        print("PASO 2 — Al final el navegador muestra una página de error de Pixiv (normal).")
        print("         Copia la URL COMPLETA de la barra de direcciones: debe contener")
        print("         'code=...'.")
        print()
        print("⚠️  NO CIERRES ESTA VENTANA hasta pegar el código: el enlace de arriba")
        print("    solo es válido con ESTA ejecución (si la reinicias, cambia).")
        print("=" * 78)

        code = ""
        while not code:
            entrada = _pedir("\nPega la URL final (con code=...) o el código: ")
            if entrada is None:
                print("[error] no se recibió ningún dato (¿se cerró la entrada?).")
                return 1
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
    print("TU REFRESH TOKEN DE PIXIV (cópialo por si acaso):")
    print()
    print("   " + refresh)
    print("=" * 78)

    destino = _destino_config()
    respuesta_guardar = "s" if guardar_auto else _pedir(
        f"\n¿Guardarlo en {destino}? (s/n): "
    )
    if respuesta_guardar is None:
        print(f"[info] no se guardó nada. Añade a mano en {destino}:")
        print(f'      PIXIV_REFRESH_TOKEN = "{refresh}"')
        return 0
    if respuesta_guardar.strip().lower().startswith("s"):
        guardado = _guardar_en_config(refresh)
        if guardado is not None:
            print(f"[ok] guardado en {guardado}")
            print("[ok] reinicia Imaginteca y Pixiv quedará activado")
        else:
            print("[aviso] no se pudo guardar automáticamente; copia el token a mano")
            print(f'      PIXIV_REFRESH_TOKEN = "{refresh}"')
    else:
        print(f"[info] copia el token en PIXIV_REFRESH_TOKEN dentro de {destino}")
    return 0


if __name__ == "__main__":
    try:
        _codigo = main()
    except Exception as exc:  # noqa: BLE001
        print(f"\n[error] algo falló: {exc}")
        _codigo = 1
    finally:
        _pausa_final()
    raise SystemExit(_codigo)
