"""Prepara y publica un release de Imaginteca en GitHub.

Uso:
    python scripts\\release.py                 # crea el .zip del compilado y muestra los pasos
    python scripts\\release.py --tag           # crea y sube la etiqueta vX.Y.Z
                                               # → GitHub Actions compila los 3 sistemas
                                               #   y publica el Release automáticamente
    python scripts\\release.py --gh            # publica el Release desde aquí con gh
                                               #   (sube el .zip ya compilado en este equipo)
    python scripts\\release.py --version 0.2.0 # usa otra versión para la etiqueta

Requisitos para --gh:  winget install --id GitHub.cli   &&   gh auth login
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
for _ruta in (ROOT, VENDOR):
    if _ruta.is_dir() and str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

from app import config  # noqa: E402

DIST = ROOT / "dist"
PAQUETE = DIST / "Imaginteca"
LICENCIA = ROOT / "LICENSE"
NOTICIAS = ROOT / "THIRD-PARTY-NOTICES.txt"
LEEME = ROOT / "LEEME-PRIMERO.txt"

SISTEMAS = {"win32": "windows", "darwin": "macos", "linux": "linux"}


def version() -> str:
    argumentos = sys.argv[1:]
    for indice, argumento in enumerate(argumentos):
        if argumento.startswith("--version="):
            return argumento.split("=", 1)[1].strip()
        if argumento == "--version" and indice + 1 < len(argumentos):
            return argumentos[indice + 1].strip()
    return config.APP_VERSION


def _copiar_avisos() -> None:
    for origen in (LICENCIA, NOTICIAS, LEEME):
        if not origen.is_file():
            continue
        try:
            shutil.copy2(origen, PAQUETE / origen.name)
            print(f"[ok] incluido en el paquete: {origen.name}")
        except OSError as exc:
            print(f"[aviso] no se pudo copiar {origen.name}: {exc}")

    # La guía del USUARIO viaja como README.md; el README técnico (arquitectura,
    # scripts, cómo compilar) se queda en el repositorio y no se distribuye.
    manual = ROOT / "README-USUARIO.md"
    if manual.is_file():
        try:
            shutil.copy2(manual, PAQUETE / "README.md")
            print("[ok] incluido en el paquete: README.md (guía del usuario)")
        except OSError as exc:
            print(f"[aviso] no se pudo copiar {manual.name}: {exc}")


def _hash_sha256(archivo: Path) -> str:
    import hashlib

    resumen = hashlib.sha256()
    with archivo.open("rb") as manejador:
        for bloque in iter(lambda: manejador.read(1024 * 1024), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def _plantilla_limpia() -> str:
    """Plantilla de config_local.py sin claves (la que va en el paquete)."""
    try:
        import importlib.util as _util

        especificacion = _util.spec_from_file_location(
            "build_exe", ROOT / "scripts" / "build_exe.py")
        if especificacion is not None and especificacion.loader is not None:
            modulo = _util.module_from_spec(especificacion)
            especificacion.loader.exec_module(modulo)
            return modulo.PLANTILLA_CONFIG
    except Exception as exc:  # noqa: BLE001
        print(f"[aviso] no se pudo leer la plantilla de build_exe: {exc}")
    return ("# PLANTILLA-VACIA\n"
            '"""Tus credenciales aqui (RULE34_API_KEY, PIXIV_REFRESH_TOKEN, ...)."""\n')


def _contiene_claves(texto: str) -> bool:
    import re

    return bool(re.search(r'^\s*[A-Z][A-Z0-9_]*\s*=\s*"[^"]{4,}"', texto, re.MULTILINE))


def _verificar_sin_claves(archivo: Path) -> bool:
    """Comprueba que el .zip no lleve credenciales dentro."""
    try:
        with zipfile.ZipFile(archivo) as zf:
            for nombre in zf.namelist():
                if nombre.endswith("config_local.py"):
                    if _contiene_claves(zf.read(nombre).decode("utf-8", "ignore")):
                        print("[ERROR] el paquete contiene CLAVES en config_local.py; no lo publiques")
                        return False
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[aviso] no se pudo verificar el paquete: {exc}")
        return True


def crear_zip(etiqueta: str) -> Path | None:
    if not PAQUETE.is_dir():
        print(f"[error] no existe {PAQUETE}. Compila primero:  python scripts\\build_exe.py")
        return None
    _copiar_avisos()

    # Tus claves viven junto al ejecutable para probarlo, pero NO deben salir en el
    # release: se sustituye el archivo por la plantilla durante el empaquetado y se
    # restaura al terminar.
    ruta_config = PAQUETE / "config_local.py"
    original = ruta_config.read_bytes() if ruta_config.is_file() else None
    if original is not None:
        if _contiene_claves(original.decode("utf-8", "ignore")):
            ruta_config.write_text(_plantilla_limpia(), encoding="utf-8")
            print("[ok] config_local.py del paquete sustituido por la plantilla vacía")
        else:
            print("[info] config_local.py ya era la plantilla (sin claves)")

    sufijo = SISTEMAS.get(sys.platform, sys.platform)
    destino = DIST / f"Imaginteca-{etiqueta}-{sufijo}.zip"
    print(f"[info] comprimiendo {PAQUETE.name} …")
    try:
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for ruta in sorted(PAQUETE.rglob("*")):
                if ruta.is_file():
                    zf.write(ruta, ruta.relative_to(DIST))
    finally:
        if original is not None:          # deja tus claves donde estaban
            ruta_config.write_bytes(original)
    mb = destino.stat().st_size / (1024 * 1024)
    print(f"[ok] {destino}  ({mb:.0f} MB)")

    if not _verificar_sin_claves(destino):
        print("[aviso] revisa el paquete antes de subirlo a un release")
        return None

    # Huella SHA-256 para que los usuarios puedan verificar la descarga
    huella = _hash_sha256(destino)
    firmas = destino.with_suffix(destino.suffix + ".sha256")
    firmas.write_text(f"{huella}  {destino.name}\n", encoding="utf-8")
    print(f"[ok] {firmas.name}")
    print(f"     SHA-256: {huella}")
    return destino


def _ejecutar(comando: list[str], descripcion: str) -> bool:
    print(f"[ejecutando] {descripcion}\n             {' '.join(comando)}")
    try:
        return subprocess.call(comando, cwd=str(ROOT)) == 0
    except OSError as exc:
        print(f"[error] {exc}")
        return False


def subir_etiqueta(etiqueta: str) -> int:
    """Crea y sube la etiqueta: GitHub Actions publica el Release con los 3 sistemas."""
    estado = subprocess.run(["git", "status", "--porcelain"], cwd=str(ROOT),
                            capture_output=True, text=True)
    if estado.stdout.strip():
        print("[aviso] tienes cambios sin confirmar; el Release se construirá desde el")
        print("        ÚLTIMO commit subido, no desde el estado actual del disco.")
        print("        Confirma y sube primero:  git add -A && git commit -m '...' && git push")
        print()

    if not _ejecutar(["git", "tag", "-a", etiqueta, "-m", f"Imaginteca {etiqueta}"],
                     f"crear la etiqueta {etiqueta}"):
        print("[error] no se pudo crear la etiqueta (¿ya existe?)")
        return 1
    if not _ejecutar(["git", "push", "origin", etiqueta], "subir la etiqueta"):
        print("[error] no se pudo subir la etiqueta")
        return 1

    print()
    print("=" * 70)
    print(f"  Etiqueta {etiqueta} subida.")
    print("  GitHub Actions está compilando Windows, macOS y Linux.")
    print("  El Release aparecerá aquí en unos minutos:")
    print("    https://github.com/rgomezs2000/imaginteca/releases")
    print("  (pestaña Actions para ver el progreso)")
    print("=" * 70)
    return 0


def publicar_con_gh(etiqueta: str, paquete: Path) -> int:
    """Publica el Release desde este equipo subiendo el .zip ya compilado."""
    if shutil.which("gh") is None:
        print("[error] no tienes GitHub CLI (gh). Instálalo con:")
        print("        winget install --id GitHub.cli")
        print("        y luego:  gh auth login")
        print("        (o usa --tag para que lo haga GitHub Actions)")
        return 1
    return 0 if _ejecutar(
        ["gh", "release", "create", etiqueta, str(paquete),
         "--title", f"Imaginteca {etiqueta}",
         "--generate-notes"],
        f"publicar el Release {etiqueta}",
    ) else 1


def pasos(etiqueta: str, paquete: Path | None) -> None:
    print()
    print("=" * 70)
    print("  CÓMO PUBLICAR EL RELEASE")
    print("=" * 70)
    print()
    print("  OPCIÓN A — automática (recomendada): compila los 3 sistemas en GitHub")
    print("    python scripts\\release.py --tag")
    print("    (equivale a:  git tag -a %s -m \"...\"  &&  git push origin %s)" % (etiqueta, etiqueta))
    print()
    print("  OPCIÓN B — desde este equipo con GitHub CLI (solo el .zip local)")
    if paquete is not None:
        print(f"    gh release create {etiqueta} \"{paquete}\" --title \"Imaginteca {etiqueta}\" --generate-notes")
    print("    (si no tienes gh:  winget install --id GitHub.cli  &&  gh auth login)")
    print()
    print("  OPCIÓN C — a mano desde la web")
    print("    1. https://github.com/rgomezs2000/imaginteca/releases/new")
    print(f"    2. Etiqueta nueva: {etiqueta}  (crear al publicar)")
    if paquete is not None:
        print(f"    3. Adjunta el archivo: {paquete}")
    print()
    print("  Nota: las etiquetas con formato v* disparan el flujo automático,")
    print("        que además adjunta los paquetes de macOS y Linux.")
    print("=" * 70)


def main() -> int:
    etiqueta = version()
    if not etiqueta.startswith("v"):
        etiqueta = "v" + etiqueta

    print(f"Imaginteca · release {etiqueta}")
    print(f"  paquete local: {PAQUETE}")

    quiere_todo = "--gh" in sys.argv
    crear = PAQUETE.is_dir() and "--tag" not in sys.argv
    paquete = crear_zip(etiqueta) if crear else None

    if "--tag" in sys.argv:
        return subir_etiqueta(etiqueta)
    if quiere_todo:
        if paquete is None:
            print("[error] no hay paquete que subir; compila primero")
            return 1
        return publicar_con_gh(etiqueta, paquete)

    pasos(etiqueta, paquete)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
