"""Retira de un Release de GitHub los adjuntos que NO son de esta versión.

Se usa desde el flujo de publicación DESPUÉS de subir los paquetes: quita los
restos de publicaciones anteriores de la misma etiqueta (o con un nombre antiguo
del proyecto) sin tocar los archivos actuales. Así el Release nunca se queda sin
publicar aunque la limpieza falle: el trabajo avisa y sigue.

    # conservar solo los archivos que hay en una carpeta (lo que hace el CI)
    python scripts\\limpiar_release.py --repo usuario/repo --tag v0.1.5-beta.3 \\
        --carpeta paquetes

    # conservar una lista explícita de nombres
    python scripts\\limpiar_release.py --conservar "A.zip,A.zip.sha256"

    # borrar TODOS los adjuntos del Release (limpieza total)
    python scripts\\limpiar_release.py --todo

Solo usa la biblioteca estándar: no depende de `gh`, que en el CI fallaba sin
dejar rastro. Los fallos se imprimen además como anotación (`::error::`) para que
se vean en la página del flujo aunque no se puedan leer los registros.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

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
        return 0, f"{type(exc).__name__}: {exc}"


def _aviso(texto: str) -> None:
    """Fallo visible en la página del flujo (anotación) y en el registro."""
    print(f"[error] {texto}")
    print(f"::error::{texto}")


def main() -> int:
    argumentos = sys.argv[1:]
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    etiqueta = os.environ.get("ETIQUETA") or os.environ.get("GITHUB_REF_NAME", "")
    carpeta = ""
    conservar: set[str] = set()
    borrar_todo = False
    comprobar = 0
    for indice, argumento in enumerate(argumentos):
        if argumento == "--repo" and indice + 1 < len(argumentos):
            repo = argumentos[indice + 1]
        elif argumento == "--tag" and indice + 1 < len(argumentos):
            etiqueta = argumentos[indice + 1]
        elif argumento == "--carpeta" and indice + 1 < len(argumentos):
            carpeta = argumentos[indice + 1]
        elif argumento == "--conservar" and indice + 1 < len(argumentos):
            conservar = {n.strip() for n in argumentos[indice + 1].split(",") if n.strip()}
        elif argumento == "--comprobar" and indice + 1 < len(argumentos):
            comprobar = int(argumentos[indice + 1])
        elif argumento == "--todo":
            borrar_todo = True

    if carpeta:
        ruta = Path(carpeta)
        if not ruta.is_dir():
            _aviso(f"no existe la carpeta de paquetes: {ruta}")
            return 1
        conservar = {archivo.name for archivo in ruta.iterdir() if archivo.is_file()}

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if not repo or not etiqueta:
        _aviso("faltan datos: usa --repo usuario/repo --tag vX.Y.Z")
        return 1
    print(f"[info] repositorio: {repo} · etiqueta: {etiqueta} · "
          f"token: {'sí' if token else 'NO'} · "
          f"conservar: {sorted(conservar) if conservar else 'nada (se borra todo)'}")

    estado, datos = _peticion(f"{API}/repos/{repo}/releases/tags/{etiqueta}", token)
    if estado == 404:
        _aviso(f"no hay ningún Release con la etiqueta {etiqueta}")
        return 1
    if estado != 200 or not isinstance(datos, dict):
        _aviso(f"no se pudo consultar el Release (HTTP {estado}): {datos}")
        return 1

    adjuntos = datos.get("assets") or []
    print(f"[info] Release id={datos.get('id')} · adjuntos: {len(adjuntos)}")
    for adjunto in adjuntos:
        print(f"       {adjunto['id']:>12}  {adjunto['name']}")

    if comprobar:
        if len(adjuntos) != comprobar:
            _aviso(f"el Release tiene {len(adjuntos)} adjuntos y se esperan {comprobar}: "
                   f"{[a['name'] for a in adjuntos]}")
            return 1
        print(f"[ok] el Release tiene exactamente {comprobar} adjuntos, todos de esta versión")
        return 0

    sobrantes = [a for a in adjuntos if borrar_todo or a["name"] not in conservar]
    if not sobrantes:
        print("[ok] no hay adjuntos sobrantes: el Release está limpio")
        return 0
    if not token:
        _aviso("sin token no se puede borrar nada")
        return 1

    print(f"[info] se van a retirar {len(sobrantes)} adjunto(s) que no son de esta versión")
    fallos = 0
    for adjunto in sobrantes:
        estado, respuesta = _peticion(
            f"{API}/repos/{repo}/releases/assets/{adjunto['id']}", token, "DELETE")
        if estado in (200, 204):
            print(f"[ok] retirado: {adjunto['name']}")
        else:
            fallos += 1
            _aviso(f"no se pudo retirar {adjunto['name']} (HTTP {estado}): {respuesta}")
    print(f"[fin] retirados {len(sobrantes) - fallos}/{len(sobrantes)}")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
