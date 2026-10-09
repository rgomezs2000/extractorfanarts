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


def localizar_signtool() -> Path | None:
    """Busca signtool.exe (Windows SDK)."""
    en_path = shutil.which("signtool")
    if en_path:
        return Path(en_path)
    for base in (Path(r"C:\Program Files (x86)\Windows Kits\10\bin"),
                 Path(r"C:\Program Files\Windows Kits\10\bin")):
        if base.is_dir():
            candidatos = sorted(base.glob("*/x64/signtool.exe"))
            if candidatos:
                return candidatos[-1]
    return None


def firma_configurada() -> tuple[Path, list[str]] | None:
    """(signtool, argumentos del certificado) si hay firma configurada, o None.

    Sin certificado, el instalador sale **sin firmar** y el aviso azul de SmartScreen
    seguirá apareciendo (un certificado autofirmado tampoco lo quita).
    """
    tiene = any(os.environ.get(v) for v in (
        "WINDOWS_CERT_PFX_BASE64", "WINDOWS_CERT_THUMBPRINT", "TRUSTED_SIGNING_DLIB"))
    if not tiene:
        return None
    signtool = localizar_signtool()
    if signtool is None:
        print("[aviso] hay certificado configurado, pero no se encontró signtool.exe")
        return None
    if os.environ.get("WINDOWS_CERT_PFX_BASE64"):
        pfx = Path(os.environ.get("RUNNER_TEMP") or os.environ.get("TEMP") or ".")
        pfx = pfx / "certificado.pfx"
        import base64
        pfx.write_bytes(base64.b64decode(os.environ["WINDOWS_CERT_PFX_BASE64"]))
        extra = ["/f", str(pfx)]
        if os.environ.get("WINDOWS_CERT_PASSWORD"):
            extra += ["/p", os.environ["WINDOWS_CERT_PASSWORD"]]
        return signtool, extra
    if os.environ.get("WINDOWS_CERT_THUMBPRINT"):
        return signtool, ["/sha1", os.environ["WINDOWS_CERT_THUMBPRINT"]]
    return signtool, ["/dlib", os.environ["TRUSTED_SIGNING_DLIB"],
                      "/dmdf", os.environ.get("TRUSTED_SIGNING_METADATA", "")]


def escribir_iss(dist: Path, salida: Path, firmar: bool = False) -> Path:
    """Escribe el archivo de Inno Setup con los datos de esta versión."""
    version = config.APP_VERSION
    linea_firma = "SignTool=imagintecafirma\n" if firmar else ""
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
{linea_firma}

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

[Code]
{{ Quita la marca de internet de los ejecutables instalados: Windows avisa al abrir
   un programa descargado del navegador, y esa marca la heredan los archivos
   extraídos. Al instalarlo con el asistente, el programa queda SIN ese aviso. }}
procedure CurStepChanged(CurStep: TSetupStep);
var
  Ruta: String;
begin
  if CurStep = ssPostInstall then
  begin
    Ruta := ExpandConstant('{{app}}\\{config.APP_NAME}.exe');
    if FileExists(Ruta) then
      DeleteFile(Ruta + ':Zone.Identifier');
    Ruta := ExpandConstant('{{app}}\\pixiv-token.exe');
    if FileExists(Ruta) then
      DeleteFile(Ruta + ':Zone.Identifier');
  end;
end;
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

    firma = firma_configurada()
    iss = escribir_iss(dist, salida, firmar=firma is not None)
    print(f"[ok] guion de Inno Setup: {iss}")
    comando = [str(iscc), str(iss)]
    if firma is not None:
        signtool, extra = firma
        orden_firma = '"{}" sign /fd sha256 /td sha256 /tr http://timestamp.digicert.com {} $f'.format(
            signtool, " ".join(f'"{a}"' if " " in a else a for a in extra))
        comando.append(f"/Simagintecafirma={orden_firma}")
        print("[ok] el instalador se firmará con el certificado configurado")
    else:
        print("[aviso] sin certificado: el instalador saldrá SIN FIRMAR y SmartScreen")
        print("        seguirá mostrando el aviso azul (un certificado autofirmado no lo quita)")
    codigo = subprocess.call(comando)
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
