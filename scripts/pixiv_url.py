"""Convierte URLs intermedias de Pixiv en el enlace limpio que hay que abrir.

Pixiv encadena varias redirecciones al iniciar sesión:

    /web/v1/login?...            (el enlace que da pixiv_token.py)
      → accounts.pixiv.net/post-redirect?return_to=<ENLACE CODIFICADO>
      → /web/v1/users/auth/pixiv/start?code_challenge=...      ← "enlace limpio"
      → /web/v1/users/auth/pixiv/callback?state=...&code=...   ← aquí está el CODE

Este script no adivina: decodifica lo que le pegues y te muestra el enlace listo
para abrir en el navegador (o el `code` si ya lo tienes).

Uso:
    python scripts\\pixiv_url.py "<URL que copiaste del navegador>"
    python scripts\\pixiv_url.py "<URL>" --abrir          # lo abre en el navegador
    python scripts\\pixiv_url.py --pegar                  # te pide pegar la URL

Ejemplos de entradas que acepta:
    https://accounts.pixiv.net/post-redirect?return_to=https%3A%2F%2Fapp-api...
    https%3A%2F%2Fapp-api.pixiv.net%2Fweb%2Fv1%2F...      (percent-encoded)
    https://app-api.pixiv.net/web/v1/users/auth/pixiv/start?code_challenge=...
    https://app-api.pixiv.net/web/v1/users/auth/pixiv/callback?...&code=XXXX
"""
from __future__ import annotations

import sys
import webbrowser
from urllib.parse import parse_qs, unquote, urlparse


def analizar(entrada: str) -> dict:
    """Decodifica y clasifica la entrada. Devuelve {tipo, url, code}.

    tipo: "callback" (ya tiene código) | "continuacion" (enlace a abrir) | "desconocido"
    """
    texto = (entrada or "").strip().strip('"').strip("'")
    for _ in range(6):  # desanida codificaciones y return_to anidados
        # 1) Solo si TODA la cadena está percent-encoded (copiada de return_to).
        #    Decodificar una URL completa antes de parsearla rompería sus parámetros.
        if texto.lower().startswith(("http%3a", "https%3a")):
            texto = unquote(texto)
            continue
        # 2) URL con return_to=...: se extrae el valor y se decodifica aparte
        if "return_to=" in texto:
            interno = (parse_qs(urlparse(texto).query).get("return_to") or [""])[0]
            if interno:
                texto = unquote(interno)
                continue
        break

    resultado = {"tipo": "desconocido", "url": texto, "code": ""}
    if not texto:
        return resultado

    if "code=" in texto:
        resultado["code"] = (parse_qs(urlparse(texto).query).get("code") or [""])[0]
        if resultado["code"]:
            resultado["tipo"] = "callback"
            return resultado

    if texto.startswith("http") and ("code_challenge=" in texto or "/start" in texto):
        resultado["tipo"] = "continuacion"
    elif "://" not in texto and " " not in texto:
        resultado["tipo"] = "codigo_suelto"
        resultado["code"] = texto
    return resultado


def _pedir_entrada() -> str:
    print("Pega la URL que copiaste del navegador y pulsa Enter:")
    return input("> ").strip()


def main() -> int:
    argumentos = sys.argv[1:]
    abrir = "--abrir" in argumentos
    pegar = "--pegar" in argumentos or not [a for a in argumentos if not a.startswith("--")]

    if pegar:
        entrada = _pedir_entrada()
    else:
        entrada = next(a for a in argumentos if not a.startswith("--"))

    datos = analizar(entrada)
    print()
    if datos["tipo"] == "callback":
        print("✅ Esa URL YA contiene el código.")
        print()
        print("   CODE: " + datos["code"])
        print()
        print("   Pégalo (o la URL completa) en:  python scripts\\pixiv_token.py")
        print("   ⚠️  Hazlo en la MISMA ejecución del script que generó el enlace.")
        return 0

    if datos["tipo"] == "continuacion":
        print("👉 Ese no es el final: es un enlace INTERMEDIO del login.")
        print("   Abre ESTE enlace limpio en el navegador (con tu sesión de Pixiv iniciada):")
        print()
        print("   " + datos["url"])
        print()
        print("   Después copia la URL FINAL (la que contiene 'code=...') y pásala por")
        print("   este mismo script o por  python scripts\\pixiv_token.py")
        if abrir:
            try:
                webbrowser.open(datos["url"])
                print("\n   [abriendo en el navegador…]")
            except Exception as exc:  # noqa: BLE001
                print(f"\n   [aviso] no se pudo abrir automáticamente: {exc}")
        else:
            print("\n   (añade --abrir para que se abra solo en el navegador)")
        return 0

    if datos["tipo"] == "codigo_suelto":
        print("✅ Parece un código suelto:")
        print()
        print("   " + datos["code"])
        print()
        print("   Úsalo con:  python scripts\\pixiv_token.py --code=" + datos["code"] + " --save")
        return 0

    print("❓ No se reconoció la entrada. Debería ser una de estas:")
    print("   - la URL del navegador tras iniciar sesión (contiene code=...)")
    print("   - la URL post-redirect de Pixiv")
    print("   - el enlace /start?code_challenge=...")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
