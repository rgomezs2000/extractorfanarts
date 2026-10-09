"""Genera los manifiestos de los gestores de paquetes: Scoop, Chocolatey y winget.

Los tres sirven para lo mismo: que el usuario instale **con una orden** y que, en
Windows, **no le salga el aviso azul** (los gestores descargan sin la marca de internet
que dispara SmartScreen). Van **dentro del repositorio y del release**: no hay que
mantener ningún repositorio aparte para Scoop.

    # desde el paquete ya construido (lo que hace el flujo de publicación)
    python scripts\\empaquetadores\\generar_manifiestos.py \\
        --instalador dist\\instaladores\\Imaginteca-0.1.5-beta.7-windows-installer.exe \\
        --zip dist\\Imaginteca-Windows.zip --version 0.1.5-beta.7

    # desde la última release publicada
    python scripts\\empaquetadores\\generar_manifiestos.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app import config  # noqa: E402

API = "https://api.github.com"
CABECERAS = {"User-Agent": f"{config.APP_NAME}-manifiestos",
             "Accept": "application/vnd.github+json"}
REPOS = [r for r in (getattr(config, "REPO_GITHUB", ""),
                     getattr(config, "UPDATE_REPO_ALTERNATIVO", ""),
                     getattr(config, "UPDATE_REPO", "")) if r]
SCOOP = ROOT / "scripts" / "scoop" / "generar_manifiesto.py"
DESCRIPCION = (f"{config.APP_NAME}: reúne, ordena y prepara colecciones de imágenes "
               "listas como datasets (LoRA, LyCORIS, checkpoints) o como galería")


def _hash(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def _descargar(url: str) -> bytes:
    peticion = urllib.request.Request(url, headers=CABECERAS)
    with urllib.request.urlopen(peticion, timeout=120) as respuesta:
        return respuesta.read()


def _release(etiqueta: str) -> tuple[dict, str]:
    for repo in REPOS:
        try:
            if etiqueta:
                peticion = urllib.request.Request(
                    f"{API}/repos/{repo}/releases/tags/{etiqueta}", headers=CABECERAS)
                with urllib.request.urlopen(peticion, timeout=45) as r:
                    return json.loads(r.read().decode("utf-8")), repo
            peticion = urllib.request.Request(f"{API}/repos/{repo}/releases",
                                              headers=CABECERAS)
            with urllib.request.urlopen(peticion, timeout=45) as r:
                for datos in json.loads(r.read().decode("utf-8")):
                    if not datos.get("prerelease") and not datos.get("draft"):
                        return datos, repo
        except Exception:  # noqa: BLE001
            continue
    raise SystemExit("[error] no se pudo consultar ninguna release")


def datos_de_release(etiqueta: str) -> dict:
    """Todo lo que necesitan los manifiestos, tomado de una release publicada."""
    release, repo = _release(etiqueta)
    version = str(release.get("tag_name") or "").lstrip("vV")
    activos = {a["name"]: a["browser_download_url"] for a in release.get("assets") or []}
    instalador = [n for n in activos
                  if n.startswith(f"{config.APP_NAME}-{version}") and n.endswith(".exe")]
    if not instalador:
        raise SystemExit(f"[error] la release {version} no trae instalador de Windows")
    nombre_instalador = instalador[0]
    sha_instalador = _descargar(activos[f"{nombre_instalador}.sha256"]
                                ).decode("utf-8", "replace").split()[0].lower()
    zip_nombre = f"{config.APP_NAME}-Windows.zip"
    sha_zip = _descargar(activos[f"{zip_nombre}.sha256"]
                         ).decode("utf-8", "replace").split()[0].lower()
    return {
        "version": version, "repo": repo,
        "instalador": nombre_instalador, "sha_instalador": sha_instalador,
        "zip": zip_nombre, "sha_zip": sha_zip,
    }


def datos_locales(instalador: Path, zip_ruta: Path, version: str, repo: str) -> dict:
    """Todo lo que necesitan los manifiestos, calculado de los archivos recién creados."""
    if not instalador.is_file():
        raise SystemExit(f"[error] no existe el instalador: {instalador}")
    datos = {
        "version": version, "repo": repo,
        "instalador": instalador.name, "sha_instalador": _hash(instalador),
        "zip": zip_ruta.name if zip_ruta.is_file() else f"{config.APP_NAME}-Windows.zip",
        "sha_zip": _hash(zip_ruta) if zip_ruta.is_file() else "",
    }
    return datos


def escribir_chocolatey(datos: dict, salida: Path) -> None:
    version, repo = datos["version"], datos["repo"]
    url = (f"https://github.com/{repo}/releases/download/v{version}/"
           f"{datos['instalador']}")
    (salida / "tools").mkdir(parents=True, exist_ok=True)
    (salida / f"{config.APP_NAME}.nuspec").write_text(f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>{config.APP_NAME.lower()}</id>
    <version>{version}</version>
    <title>{config.APP_NAME}</title>
    <authors>{config.AUTOR}</authors>
    <owners>{config.AUTOR}</owners>
    <projectUrl>https://github.com/{repo}</projectUrl>
    <packageSourceUrl>https://github.com/{repo}/tree/main/chocolatey</packageSourceUrl>
    <license type="expression">LicenseRef-Proprietary</license>
    <requireLicenseAcceptance>true</requireLicenseAcceptance>
    <projectSourceUrl>https://github.com/{repo}</projectSourceUrl>
    <docsUrl>https://github.com/{repo}/wiki</docsUrl>
    <summary>{DESCRIPCION}</summary>
    <description>{DESCRIPCION}</description>
    <tags>imagenes datasets fanart lora galeria imaginteca</tags>
  </metadata>
  <files>
    <file src="tools\\**" target="tools" />
  </files>
</package>
""", encoding="utf-8")
    (salida / "tools" / "chocolateyinstall.ps1").write_text(f"""$ErrorActionPreference = 'Stop'

# Instalador con asistente, en modo silencioso. La comprobación del hash evita que se
# instale un archivo manipulado.
$url      = '{url}'
$checksum = '{datos['sha_instalador']}'

Install-ChocolateyPackage `
  -PackageName   '{config.APP_NAME.lower()}' `
  -FileType      'exe' `
  -SilentArgs    '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-' `
  -Url           $url `
  -Checksum      $checksum `
  -ChecksumType  'sha256' `
  -ValidExitCodes @(0)
""", encoding="utf-8")
    (salida / "tools" / "chocolateyuninstall.ps1").write_text(f"""$ErrorActionPreference = 'Stop'

Uninstall-ChocolateyPackage `
  -PackageName  '{config.APP_NAME.lower()}' `
  -FileType     'exe' `
  -SilentArgs   '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' `
  -ValidExitCodes @(0)
""", encoding="utf-8")
    print(f"  [ok] Chocolatey: {salida}")


def escribir_winget(datos: dict, salida: Path) -> None:
    version, repo = datos["version"], datos["repo"]
    url = (f"https://github.com/{repo}/releases/download/v{version}/"
           f"{datos['instalador']}")
    salida.mkdir(parents=True, exist_ok=True)
    ident = f"{config.AUTOR}.{config.APP_NAME}"          # InfoArte.Imaginteca
    (salida / f"{ident}.yaml").write_text(f"""# Manifiesto de versión (winget)
PackageIdentifier: {ident}
PackageVersion: {version}
DefaultLocale: es-ES
ManifestType: version
ManifestVersion: 1.6.0
""", encoding="utf-8")
    (salida / f"{ident}.installer.yaml").write_text(f"""# Manifiesto del instalador (winget)
PackageIdentifier: {ident}
PackageVersion: {version}
InstallerType: inno
Scope: user
InstallModes:
  - interactive
  - silent
  - silentWithProgress
UpgradeBehavior: install
ReleaseDate: {datos.get('fecha', '') or '2026-10-09'}
Installers:
  - Architecture: x64
    InstallerUrl: {url}
    InstallerSha256: {datos['sha_instalador'].upper()}
    InstallerSwitches:
      Silent: /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
      SilentWithProgress: /SILENT /SUPPRESSMSGBOXES /NORESTART
ManifestType: installer
ManifestVersion: 1.6.0
""", encoding="utf-8")
    (salida / f"{ident}.locale.es-ES.yaml").write_text(f"""# Textos en español (winget)
PackageIdentifier: {ident}
PackageVersion: {version}
PackageLocale: es-ES
Publisher: {config.AUTOR}
PublisherUrl: https://github.com/{repo}
PublisherSupportUrl: https://github.com/{repo}/wiki/Foro
PackageName: {config.APP_NAME}
PackageUrl: https://github.com/{repo}
License: Propietaria (todos los derechos reservados)
LicenseUrl: https://github.com/{repo}/blob/main/LICENSE
Copyright: {config.AUTOR_COPYRIGHT}
ShortDescription: {DESCRIPCION}
Description: {DESCRIPCION}
Tags:
  - imagenes
  - datasets
  - fanart
  - galeria
ReleaseNotesUrl: https://github.com/{repo}/releases/tag/v{version}
ManifestType: defaultLocale
ManifestVersion: 1.6.0
""", encoding="utf-8")
    print(f"  [ok] winget: {salida} ({ident} {version})")


def main() -> int:
    analizador = argparse.ArgumentParser(description="Manifiestos de los gestores de paquetes.")
    analizador.add_argument("--version", default="")
    analizador.add_argument("--repo", default="")
    analizador.add_argument("--instalador", default="", help="instalador .exe ya construido")
    analizador.add_argument("--zip", default="", help="paquete .zip ya construido")
    analizador.add_argument("--etiqueta", default="", help="release concreta (si no, la última)")
    analizador.add_argument("--salida", default="", help="carpeta donde escribirlos")
    argumentos = analizador.parse_args()

    if argumentos.instalador:
        datos = datos_locales(Path(argumentos.instalador).resolve(),
                              Path(argumentos.zip).resolve() if argumentos.zip else Path(),
                              argumentos.version or config.APP_VERSION,
                              argumentos.repo or REPOS[0])
    else:
        datos = datos_de_release(argumentos.etiqueta)
    print(f"[info] versión {datos['version']} · {datos['repo']} · instalador "
          f"{datos['instalador']} · sha256 {datos['sha_instalador'][:16]}…")

    # Ruta ABSOLUTA: el manifiesto de Scoop se genera en otro proceso (con su propio
    # directorio de trabajo), así que una ruta relativa acabaría en el sitio equivocado.
    base = Path(argumentos.salida).resolve() if argumentos.salida else ROOT
    escribir_chocolatey(datos, base / "chocolatey")
    escribir_winget(datos, base / "winget")

    # El manifiesto de Scoop lo genera su propio script (una sola fuente de verdad).
    orden = [sys.executable, str(SCOOP), "--version", datos["version"],
             "--repo", datos["repo"], "--salida", str(base / "scoop" / "imaginteca.json")]
    if argumentos.zip and Path(argumentos.zip).is_file():
        orden += ["--zip", str(Path(argumentos.zip).resolve())]
    else:
        orden += ["--etiqueta", f"v{datos['version']}"]
    codigo = subprocess.call(orden, cwd=str(ROOT))
    if codigo != 0:
        print("[error] no se pudo generar el manifiesto de Scoop")
        return codigo

    print()
    print("Todos los manifiestos quedan en el repositorio y se publican en el release.")
    print("Para publicarlos en cada gestor, mira chocolatey\\README.md y winget\\README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
