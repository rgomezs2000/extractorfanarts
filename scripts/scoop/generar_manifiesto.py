"""Genera el manifiesto de Scoop para la última versión publicada.

**Por qué esto quita la ventana azul sin certificado:** SmartScreen avisa de los
archivos descargados del navegador porque Windows les pone la *marca de internet*
(Zona.Identifier). Scoop descarga los paquetes con su propio descargador, **sin esa
marca**, así que al abrir el programa no aparece el aviso azul. Es gratis y no
necesita certificado.

Lo que hace falta: un repositorio de *bucket* (por ejemplo `scoop-bucket`) con este
manifiesto dentro. Los usuarios instalan con:

    scoop bucket add rgomezs2000 https://github.com/rgomezs2000/scoop-bucket
    scoop install imaginteca

Uso (lo puede ejecutar el flujo de publicación o tú a mano):

    python scripts\\scoop\\generar_manifiesto.py                    # última release
    python scripts\\scoop\\generar_manifiesto.py --etiqueta v0.1.5-beta.5
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app import config  # noqa: E402

API = "https://api.github.com"
CABECERAS = {"User-Agent": f"{config.APP_NAME}-scoop",
             "Accept": "application/vnd.github+json"}
DESTINO = ROOT / "scoop" / "imaginteca.json"

# Dónde están de verdad las releases: el repositorio del proyecto (y, si el nombre
# cambia en el futuro, el alternativo que ya usa el actualizador).
REPOS = [r for r in (getattr(config, "REPO_GITHUB", ""),
                     getattr(config, "UPDATE_REPO_ALTERNATIVO", ""),
                     getattr(config, "UPDATE_REPO", "")) if r]


def _leer(url: str, timeout: int) -> bytes:
    peticion = urllib.request.Request(url, headers=CABECERAS)
    with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
        return respuesta.read()


def _api(ruta: str, timeout: int = 45) -> bytes:
    """Pide una ruta de la API probando los repositorios candidatos."""
    ultimo: Exception | None = None
    for repo in REPOS:
        try:
            return _leer(f"{API}/repos/{repo}/{ruta}", timeout)
        except Exception as exc:  # noqa: BLE001
            ultimo = exc
            continue
    raise SystemExit(f"[error] no se pudo consultar GitHub ({ruta}): {ultimo}")


def _json(ruta: str) -> dict:
    return json.loads(_api(ruta).decode("utf-8"))


def release(etiqueta: str) -> tuple[dict, str]:
    """(datos de la release, repositorio usado)."""
    if etiqueta:
        for repo in REPOS:
            try:
                return json.loads(_api(f"releases/tags/{etiqueta}").decode("utf-8")), repo
            except SystemExit:
                continue
        raise SystemExit(f"[error] no encontré la release {etiqueta}")
    for repo in REPOS:
        try:
            releases = json.loads(_api("releases").decode("utf-8"))
        except SystemExit:
            continue
        for release in releases:
            if not release.get("prerelease") and not release.get("draft"):
                return release, repo
    raise SystemExit("[error] no hay ninguna release oficial publicada")


def main() -> int:
    analizador = argparse.ArgumentParser(description="Manifiesto de Scoop.")
    analizador.add_argument("--etiqueta", default="",
                            help="etiqueta concreta (v0.1.5-beta.5); por defecto, la última oficial")
    argumentos = analizador.parse_args()

    datos, repo = release(argumentos.etiqueta)
    version = str(datos.get("tag_name") or "").lstrip("vV")
    activos = {a["name"]: a["browser_download_url"] for a in datos.get("assets") or []}
    paquete = "Imaginteca-Windows.zip"
    if paquete not in activos:
        raise SystemExit(f"[error] la release {version} no trae {paquete}")
    huella = activos.get(f"{paquete}.sha256")
    if not huella:
        raise SystemExit(f"[error] falta {paquete}.sha256: no puedo calcular el hash")
    # El .sha256 publicado es «<hash>  <archivo>»
    hash_sha = _leer(huella, 90).decode("utf-8", "replace").split()[0].strip().lower()
    print(f"[info] versión {version} · repositorio {repo} · sha256 {hash_sha[:16]}…")

    manifiesto = {
        "version": version,
        "description": f"{config.APP_NAME}: colecciones de imágenes listas como datasets "
                       f"(LoRA, LyCORIS, checkpoints) o como galería",
        "homepage": f"https://github.com/{repo}",
        "license": "Proprietary",
        "architecture": {
            "64bit": {
                "url": activos[paquete],
                "hash": f"sha256:{hash_sha}",
            }
        },
        "extract_dir": config.APP_NAME,
        "bin": f"{config.APP_NAME}.exe",
        "shortcuts": [[f"{config.APP_NAME}.exe", config.APP_NAME]],
        "checkver": {"github": f"https://github.com/{repo}"},
        "autoupdate": {
            "architecture": {
                "64bit": {
                    "url": f"https://github.com/{repo}/releases/download/"
                           f"v$version/{paquete}"
                }
            }
        },
    }
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=4) + "\n",
                       encoding="utf-8")
    print(f"[ok] manifiesto escrito: {DESTINO}")
    print()
    print("Para publicarlo (una sola vez):")
    print("  1. Crea un repositorio llamado «scoop-bucket» en tu cuenta.")
    print(f"  2. Sube la carpeta {DESTINO.parent.name}/ con este archivo.")
    print("  3. Los usuarios instalan sin ventana azul:")
    print(f"     scoop bucket add {config.UPDATE_REPO.split('/')[0]} "
          f"https://github.com/{config.UPDATE_REPO.split('/')[0]}/scoop-bucket")
    print(f"     scoop install {DESTINO.stem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
