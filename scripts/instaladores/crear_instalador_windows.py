"""Crea el instalador de Windows (con asistente) usando Inno Setup.

Genera el archivo `.iss` con los datos de la versión del proyecto y llama a
`ISCC.exe` (Inno Setup 6). El instalador:

  - tiene asistente (Idioma → Licencia → Carpeta → Accesos directos → Instalar),
  - se instala **por usuario** (no pide administrador) en
    `%LOCALAPPDATA%\\Programs\\Imaginteca` — o en Archivos de programa si el
    usuario elige instalarlo para todos,
  - crea accesos directos en el menú Inicio (y opcionalmente en el escritorio),
  - deja desinstalador en «Aplicaciones instaladas»,
  - conserva **tu `config_local.py`** al actualizar (ver [Components]/[Files]).

Uso (lo llama el flujo de compilación en Windows):

    python scripts\\instaladores\\crear_instalador_windows.py \\
        --dist dist\\Imaginteca --salida dist\\instaladores
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app import config  # noqa: E402

RUTAS_ISCC = (
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
)


def localizar_iscc() -> Path | None:
    """Busca el compilador de Inno Setup (o lo toma de INNO_SETUP_ISCC)."""
    variable = os.environ.get("INNO_SETUP_ISCC", "").strip()
    if variable and Path(variable).is_file():
        return Path(variable)
    en_path = shutil.which("iscc") or shutil.which("ISCC")
    if en_path:
        return Path(en_path)
    for ruta in RUTAS_ISCC:
        if Path(ruta).is_file():
            return Path(ruta)
    return None


def escribir_iss(dist: Path, salida: Path) -> Path:
    """Escribe el archivo de Inno Setup con los datos de esta versión."""
    version = config.APP_VERSION
    iss = salida / "imaginteca.iss"
    iss.write_text(
        f"""; Instalador de {config.APP_NAME} para Windows (generado automáticamente)
; Compilar con: ISCC.exe imaginteca.iss
#define MiVersion "{version}"
#define MiDist "{dist}"
#define MiIcono "{ROOT / 'assets' / 'icon.ico'}"
#define MiLicencia "{ROOT / 'LICENSE'}"
#define MiLeeme "{ROOT / 'LEEME-PRIMERO.txt'}"

[Setup]
AppId={{{{8D2A6E5C-1F47-4A9B-9C3E-{version.replace('.', '').replace('-', '')[:12]:0<12}}}}}
AppName={config.APP_NAME}
AppVersion={{#MiVersion}}
AppVerName={config.APP_NAME} {{#MiVersion}}
AppPublisher={config.AUTOR}
VersionInfoVersion={version.split('-')[0]}
VersionInfoCompany={config.AUTOR}
VersionInfoDescription={config.APP_NAME} - tu coleccion de imagenes y datasets para IA
VersionInfoCopyright={config.AUTOR_COPYRIGHT} · Todos los derechos reservados.
DefaultDirName={{autopf}}\\{config.APP_NAME}
DefaultGroupName={config.APP_NAME}
DisableProgramGroupPage=yes
DisableWelcomePage=no
LicenseFile={{#MiLicencia}}
InfoBeforeFile={{#MiLeeme}}
OutputDir={salida}
OutputBaseFilename={config.APP_NAME}-{version}-windows-installer
SetupIconFile={{#MiIcono}}
UninstallDisplayIcon={{app}}\\{config.APP_NAME}.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el Escritorio"; \\
    GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
; Todo el paquete. `onlyifdoesntexist` en la configuración del usuario: al
; actualizar por encima NO se pisa lo que el usuario haya puesto en sus claves.
Source: "{{#MiDist}}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs \\
    createallsubdirs; Excludes: "config_local.py"
Source: "{{#MiDist}}\\config_local.py"; DestDir: "{{app}}"; \\
    Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{{group}}\\{config.APP_NAME}"; Filename: "{{app}}\\{config.APP_NAME}.exe"
Name: "{{group}}\\Leer primero"; Filename: "{{app}}\\LEEME-PRIMERO.txt"
Name: "{{group}}\\Desinstalar {config.APP_NAME}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{config.APP_NAME}"; Filename: "{{app}}\\{config.APP_NAME}.exe"; \\
    Tasks: desktopicon

[Run]
Filename: "{{app}}\\{config.APP_NAME}.exe"; Description: "Abrir {config.APP_NAME}"; \\
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{{app}}\\_internal"
Type: files; Name: "{{app}}\\*.pyc"
""",
        encoding="utf-8",
    )
    return iss


def main() -> int:
    analizador = argparse.ArgumentParser(description="Crea el instalador de Windows.")
    analizador.add_argument("--dist", default=str(ROOT / "dist" / config.APP_NAME))
    analizador.add_argument("--salida", default=str(ROOT / "dist" / "instaladores"))
    argumentos = analizador.parse_args()

    dist = Path(argumentos.dist).resolve()
    salida = Path(argumentos.salida).resolve()
    salida.mkdir(parents=True, exist_ok=True)
    if not dist.is_dir():
        print(f"[error] no existe el paquete: {dist}")
        return 1

    iscc = localizar_iscc()
    if iscc is None:
        print("[error] no se encontró Inno Setup (ISCC.exe).")
        print("        Instálalo desde https://jrsoftware.org/isdl.php o define")
        print("        INNO_SETUP_ISCC con la ruta del compilador.")
        return 1

    iss = escribir_iss(dist, salida)
    print(f"[ok] guion de Inno Setup: {iss}")
    codigo = subprocess.call([str(iscc), str(iss)])
    if codigo != 0:
        print(f"[error] Inno Setup terminó con código {codigo}")
        return codigo
    instaladores = sorted(salida.glob("*.exe"))
    for instalador in instaladores:
        print(f"[ok] instalador: {instalador} "
              f"({instalador.stat().st_size / 1024 / 1024:.1f} MB)")
    return 0 if instaladores else 1


if __name__ == "__main__":
    raise SystemExit(main())
