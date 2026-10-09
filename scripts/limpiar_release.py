"""Borra los adjuntos de un Release de GitHub (para re-publicar la misma versión).

Se usa desde el flujo de publicación, ANTES de crear el Release: así una etiqueta
re-publicada no arrastra los paquetes de la vez anterior ni los de un nombre antiguo
del proyecto. También funciona a mano:

    # PowerShell
    $env:GITHUB_TOKEN = "ghp_…"
    python scripts\\limpiar_release.py --repo usuario/repo --tag v0.1.0-beta.1

    # sin token solo consulta (el borrado necesita permiso de escritura)
    python scripts\\limpiar_release.py --repo usuario/repo --tag v0.1.0-beta.1

Solo usa la biblioteca estándar: no depende de `gh`, que en el CI fallaba sin decir
por qué y dejaba el Release acumulando adjuntos de versiones anteriores.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"


def _peticion(url: str, token: str, metodo: str = "GET") -> tuple[int, object]:
    cabeceras = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Imaginteca-limpieza-release",
    }
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    peticion = urllib.request.Request(url, method=metodo, headers=cabeceras)
    try:
        with urllib.request.urlopen(peticion, timeout=60) as respuesta:
            cuerpo = respuesta.read().decode("utf-8")
            return respuesta.status, (json.loads(cuerpo) if cuerpo.strip() else {})
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")[:400]
    except Exception as exc:  # noqa: BLE001
        return 0, str(exc)


def main() -> int:
    argumentos = sys.argv[1:]
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    etiqueta = os.environ.get("ETIQUETA") or os.environ.get("GITHUB_REF_NAME", "")
    for indice, argumento in enumerate(argumentos):
        if argumento == "--repo" and indice + 1 < len(argumentos):
            repo = argumentos[indice + 1]
        elif argumento == "--tag" and indice + 1 < len(argumentos):
            etiqueta = argumentos[indice + 1]

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if not repo or not etiqueta:
        print("[error] faltan datos: usa --repo usuario/repo --tag vX.Y.Z "
              "(o define GITHUB_REPOSITORY y GITHUB_REF_NAME)")
        return 1
    print(f"[info] repositorio: {repo} · etiqueta: {etiqueta} · "
          f"token: {'sí' if token else 'NO (solo se podrá consultar)'}")

    estado, datos = _peticion(f"{API}/repos/{repo}/releases/tags/{etiqueta}", token)
    if estado == 404:
        print("[ok] no hay ningún Release con esa etiqueta: nada que limpiar")
        return 0
    if estado != 200 or not isinstance(datos, dict):
        print(f"[error] no se pudo consultar el Release (HTTP {estado}): {datos}")
        return 1

    adjuntos = datos.get("assets") or []
    print(f"[info] Release id={datos.get('id')} · adjuntos actuales: {len(adjuntos)}")
    for adjunto in adjuntos:
        print(f"       {adjunto['id']:>12}  {adjunto['name']}")
    if not adjuntos:
        print("[ok] el Release no tiene adjuntos: nada que borrar")
        return 0
    if not token:
        print("[aviso] sin token no se puede borrar (solo se ha consultado)")
        return 0

    fallos = 0
    for adjunto in adjuntos:
        estado, respuesta = _peticion(
            f"{API}/repos/{repo}/releases/assets/{adjunto['id']}", token, "DELETE")
        if estado in (200, 204):
            print(f"[ok] borrado: {adjunto['name']}")
        else:
            fallos += 1
            print(f"[error] no se pudo borrar {adjunto['name']} (HTTP {estado}): {respuesta}")
    print(f"[fin] borrados {len(adjuntos) - fallos}/{len(adjuntos)} adjuntos")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
