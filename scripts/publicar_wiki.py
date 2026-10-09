"""Publica las páginas de `docs/wiki/` en la Wiki de GitHub del repositorio.

La wiki de GitHub es un repositorio git APARTE (`<repo>.wiki.git`). Este script
evita mantener dos copias del mismo texto: las páginas viven **dentro** del
repositorio principal (`docs/wiki/`) y desde ahí se publican en la wiki.

    python scripts\\publicar_wiki.py                 # publica (usa config.REPO_GITHUB)
    python scripts\\publicar_wiki.py --comprobar     # solo muestra qué haría
    python scripts\\publicar_wiki.py --repo usuario/repo

Necesita `git` instalado y permiso de escritura en la wiki. **La primera vez** hay
que activar la wiki y crear una página desde la web (GitHub crea el repositorio de
la wiki con esa primera página); el script lo detecta y lo explica.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from app import config
except Exception:  # noqa: BLE001
    config = None

ORIGEN = ROOT / "docs" / "wiki"


def _git(argumentos: list[str], carpeta: Path | None = None,
         permitir_fallo: bool = False) -> tuple[int, str]:
    entorno = dict(os.environ)
    entorno["GIT_TERMINAL_PROMPT"] = "0"     # sin preguntas interactivas
    orden = ["git"] + argumentos
    resultado = subprocess.run(orden, cwd=str(carpeta) if carpeta else str(ROOT),
                               capture_output=True, text=True, env=entorno)
    salida = f"{resultado.stdout}{resultado.stderr}".strip()
    if resultado.returncode != 0 and not permitir_fallo:
        print(f"  [error] {' '.join(orden)}\n{salida}")
        raise SystemExit(1)
    return resultado.returncode, salida


def _repositorio_por_defecto() -> str:
    if config is not None:
        return str(getattr(config, "REPO_GITHUB", "") or "")
    return ""


def main() -> int:
    analizador = argparse.ArgumentParser(
        description="Publica docs/wiki/ en la Wiki de GitHub del repositorio.")
    analizador.add_argument("--repo", default=_repositorio_por_defecto(),
                            help="usuario/repositorio (por defecto, config.REPO_GITHUB)")
    analizador.add_argument("--comprobar", action="store_true",
                            help="no publica: solo dice qué haría")
    analizador.add_argument("--esperar", action="store_true",
                            help="espera a que exista la wiki (tras guardar la primera "
                                 "página desde la web) y publica sola")
    analizador.add_argument("--esperar-segundos", type=int, default=1800,
                            help="cuánto esperar con --esperar (por defecto 1800 = 30 min)")
    analizador.add_argument("--forzar", action="store_true",
                            help="sobrescribe TAMBIÉN las páginas del foro (¡puede borrar "
                                 "mensajes de usuarios!)")
    analizador.add_argument("--limpiar-sobrantes", action="store_true",
                            help="retira de la wiki las páginas que ya no están en docs/wiki")
    argumentos = analizador.parse_args()

    if not argumentos.repo:
        print("[error] falta el repositorio: usa --repo usuario/repo")
        return 1
    if not ORIGEN.is_dir():
        print(f"[error] no existe la carpeta de páginas: {ORIGEN}")
        return 1

    paginas = sorted(ORIGEN.glob("*.md"))
    if not paginas:
        print(f"[error] no hay páginas .md en {ORIGEN}")
        return 1
    print(f"[info] repositorio : {argumentos.repo}")
    print(f"[info] páginas     : {len(paginas)} en {ORIGEN}")
    for pagina in paginas:
        print(f"          - {pagina.name}")

    if argumentos.comprobar:
        print("[ok] comprobación hecha: no se ha publicado nada (--comprobar)")
        return 0

    url_wiki = f"https://github.com/{argumentos.repo}.wiki.git"
    temporal = Path(tempfile.mkdtemp(prefix="imaginteca-wiki-"))
    try:
        limite = time.time() + max(0, argumentos.esperar_segundos)
        avisado = False
        while True:
            print(f"[info] clonando la wiki en {temporal} …")
            codigo, salida = _git(["clone", "--depth", "1", url_wiki, str(temporal)],
                                  permitir_fallo=True)
            if codigo == 0:
                break
            if not argumentos.esperar or time.time() >= limite:
                print("  [aviso] no se pudo clonar la wiki.")
                print("  GitHub NO crea el repositorio de la wiki hasta que se guarda la")
                print("  PRIMERA página desde la web (no se puede hacer por git):")
                print(f"    1) Abre https://github.com/{argumentos.repo}/wiki")
                print("    2) Pulsa «Create the first page» y guarda cualquier título")
                print("       (por ejemplo «Inicio»); el contenido se reemplazará.")
                print("    3) Vuelve a ejecutar este script (o usa --esperar).")
                print(f"  Detalle de git: {salida}")
                return 1
            if not avisado:
                print("  [espera] la wiki todavía no existe. Ve a")
                print(f"           https://github.com/{argumentos.repo}/wiki")
                print("           pulsa «Create the first page» y guarda cualquier título:")
                print(f"           publicaré solo (espero {argumentos.esperar_segundos // 60} min).")
                avisado = True
            time.sleep(10)

        # ── Sincronización con protección del foro ────────────────────────────────
        # La documentación manda desde `docs/wiki/` (se sobrescribe), pero las
        # páginas del FORO pueden tener mensajes de usuarios: si ya existen, NO se
        # tocan. Así se puede actualizar la wiki sin borrar lo que ha escrito nadie.
        existentes = {p.name for p in temporal.glob("*.md")}
        nombres_repo = {p.name for p in paginas}

        def es_foro(nombre: str) -> bool:
            return nombre.startswith("Foro")

        escritas, conservadas = [], []
        for pagina in paginas:
            if pagina.name in existentes and es_foro(pagina.name) and not argumentos.forzar:
                conservadas.append(pagina.name)
                continue
            shutil.copy2(pagina, temporal / pagina.name)
            escritas.append(pagina.name)
        print(f"[ok] {len(escritas)} páginas escritas desde docs/wiki")
        if conservadas:
            print(f"[ok] {len(conservadas)} páginas del foro se conservan tal cual "
                  f"(pueden tener mensajes de usuarios):")
            for nombre in sorted(conservadas):
                print(f"          - {nombre}")

        sobrantes = sorted(n for n in existentes if n not in nombres_repo)
        for nombre in sobrantes:
            if argumentos.limpiar_sobrantes:
                (temporal / nombre).unlink()
                print(f"[ok] retirada la página sobrante: {nombre}")
            else:
                print(f"[aviso] la wiki tiene una página que no está en docs/wiki: "
                      f"{nombre}  (usa --limpiar-sobrantes para retirarla)")

        _git(["add", "-A"], temporal)
        codigo, estado = _git(["status", "--porcelain"], temporal)
        if not estado.strip():
            print("[ok] la wiki ya estaba al día: no hay cambios que publicar")
            return 0

        print("[info] cambios a publicar:")
        for linea in estado.splitlines():
            print(f"          {linea}")

        _git(["-c", "user.name=Imaginteca", "-c", "user.email=imaginteca@users.noreply.github.com",
              "commit", "-m", "wiki: actualiza las páginas desde docs/wiki"], temporal)
        _git(["push", "origin", "HEAD"], temporal)
        print("[ok] wiki publicada")
        print(f"     https://github.com/{argumentos.repo}/wiki")
        return 0
    finally:
        shutil.rmtree(temporal, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
