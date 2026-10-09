"""Crea un certificado de firma de código AUTOFIRMADO (gratis) para tus pruebas.

Uso:
    python scripts\\hacer_certificado.py --simular     # solo muestra los comandos
    python scripts\\hacer_certificado.py               # crea el certificado y el .pfx
    python scripts\\hacer_certificado.py --confiar     # además lo marca de confianza aquí
    python scripts\\hacer_certificado.py --clave "MiClave123" --nombre "Mi Editor"

Qué hace:
  1. Crea un certificado de firma de código en Cert:\\CurrentUser\\My (sin admin).
  2. Exporta  certs\\codigo.pfx  (con clave)  y  certs\\codigo.cer
  3. Con --confiar, lo añade a "Editores de confianza" y "Raíz de confianza" del
     usuario, para que TU equipo lo acepte como editor conocido.
  4. Muestra cómo firmar el ejecutable con scripts\\build_exe.py --firmar

⚠️  IMPORTANTE
    Un certificado autofirmado sirve para TU equipo y para probar el flujo de firma.
    NO elimina el aviso de SmartScreen en los equipos de otras personas: para eso
    hace falta un certificado emitido por una CA (OV/EV) o Azure Trusted Signing.
    Ver el README (§ Windows: SmartScreen, antivirus y firma).

🔐  El archivo .pfx contiene la clave privada: certs\\ está en .gitignore, no lo subas.
"""
from __future__ import annotations

import secrets
import string
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CERTS = ROOT / "certs"


def _clave_aleatoria(largo: int = 20) -> str:
    alfabeto = string.ascii_letters + string.digits
    return "".join(secrets.choice(alfabeto) for _ in range(largo))


def comandos_crear(nombre: str, pfx: Path, cer: Path, clave: str, anios: int) -> list[str]:
    return [
        # Certificado de firma de código (EKU 1.3.6.1.5.5.7.3.3)
        "$cert = New-SelfSignedCertificate -Type CodeSigningCert "
        f'-Subject "CN={nombre}" -FriendlyName "{nombre}" '
        "-KeyUsage DigitalSignature -KeyExportPolicy Exportable "
        f"-CertStoreLocation Cert:\\CurrentUser\\My -NotAfter (Get-Date).AddYears({anios}) "
        '-TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3")',
        f'$clave = ConvertTo-SecureString -String "{clave}" -Force -AsPlainText',
        f'Export-PfxCertificate -Cert $cert -FilePath "{pfx}" -Password $clave | Out-Null',
        f'Export-Certificate -Cert $cert -FilePath "{cer}" | Out-Null',
        'Write-Host "Huella:" $cert.Thumbprint',
    ]


def comandos_confiar(cer: Path) -> list[str]:
    return [
        f'Import-Certificate -FilePath "{cer}" '
        "-CertStoreLocation Cert:\\CurrentUser\\TrustedPublisher | Out-Null",
        f'Import-Certificate -FilePath "{cer}" '
        "-CertStoreLocation Cert:\\CurrentUser\\Root | Out-Null",
        'Write-Host "Certificado marcado como de confianza para este usuario."',
    ]


def _powershell(bloque: str) -> int:
    ejecutable = "powershell" if sys.platform.startswith("win") else "pwsh"
    return subprocess.call([ejecutable, "-NoProfile", "-Command", bloque], cwd=str(ROOT))


def _modo_restringido() -> bool:
    """Pista: consolas muy restringidas no permiten el proveedor Cert:\\."""
    if not sys.platform.startswith("win"):
        return False
    marca = CERTS / "_modo_ps.txt"
    try:
        CERTS.mkdir(exist_ok=True)
        subprocess.call([
            "powershell", "-NoProfile", "-Command",
            "Test-Path Cert:\\CurrentUser\\My | "
            f"Out-File -Encoding ascii '{marca}'",
        ])
        return "False" in marca.read_text(encoding="ascii", errors="ignore")
    except Exception:  # noqa: BLE001
        return False
    finally:
        try:
            marca.unlink()
        except OSError:
            pass


def _pasos_siguientes(pfx: Path, clave: str) -> None:
    print()
    print("=" * 74)
    print("  CÓMO FIRMAR EL EJECUTABLE")
    print("=" * 74)
    print()
    print("  PowerShell:")
    print(f'    $env:EF_CERT_PFX = "{pfx}"')
    print(f'    $env:EF_CERT_PASSWORD = "{clave}"')
    print("    python scripts\\build_exe.py --firmar")
    print()
    print("  O directamente con signtool:")
    signtool = (r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe")
    print(f'    "{signtool}" sign /f "{pfx}" /p "{clave}" /fd sha256 `')
    print('        /tr http://timestamp.digicert.com /td sha256 `')
    print('        "dist\\Imaginteca\\Imaginteca.exe"')
    print()
    print("  Comprobar la firma:")
    print(f'    "{signtool}" verify /pa /v "dist\\Imaginteca\\Imaginteca.exe"')
    print()
    print("  Para quitar el certificado de tu equipo:")
    print('    Get-ChildItem Cert:\\CurrentUser\\My -CodeSigningCert | Remove-Item')
    print("=" * 74)


def main() -> int:
    argumentos = sys.argv[1:]
    simular = "--simular" in argumentos
    confiar = "--confiar" in argumentos

    nombre = "Imaginteca (pruebas)"
    clave = _clave_aleatoria()
    for indice, argumento in enumerate(argumentos):
        if argumento == "--nombre" and indice + 1 < len(argumentos):
            nombre = argumentos[indice + 1]
        if argumento == "--clave" and indice + 1 < len(argumentos):
            clave = argumentos[indice + 1]

    CERTS.mkdir(exist_ok=True)
    pfx = CERTS / "codigo.pfx"
    cer = CERTS / "codigo.cer"

    if not sys.platform.startswith("win"):
        print("[aviso] este script está pensado para Windows (usa openssl en macOS/Linux)")
        return 1

    comandos = comandos_crear(nombre, pfx, cer, clave, anios=3)
    if confiar:
        comandos += comandos_confiar(cer)

    if simular:
        print("Comandos que se ejecutarían (PowerShell):\n")
        for linea in comandos:
            print("  " + linea)
        print(f"\n  Certificado: {pfx}")
        print(f"  Clave del .pfx: {clave}")
        return 0

    print(f"[info] creando certificado autofirmado «{nombre}» …")
    _powershell(" ; ".join(comandos))

    # La prueba de verdad: ¿se creó el .pfx?
    if not pfx.is_file():
        print()
        print("[error] no se pudo crear el certificado desde este Python.")
        print()
        print("  Causa habitual: el Python de la MICROSOFT STORE ejecuta sus procesos")
        print("  hijos dentro de un contenedor (MSIX) que no puede leer el registro de")
        print("  certificados ni el almacen de claves -> el modulo")
        print("  Microsoft.PowerShell.Security no carga, desaparece 'Cert:\\' y la")
        print("  creacion de la clave falla con 'Acceso denegado (NTE_PERM)'.")
        print()
        print("  Solucion (sin pasar por Python):")
        print("     A) Doble clic en:  crear_certificado.bat")
        print("     B) O en una consola normal:")
        print("        powershell -NoProfile -ExecutionPolicy Bypass \\")
        print("            -File scripts\\hacer_certificado.ps1")
        print("     C) O con --abrir (lanza el .bat a traves del Explorador):")
        print("        python scripts\\hacer_certificado.py --abrir")
        print()
        print("     Comprueba antes:  Test-Path Cert:\\CurrentUser\\My   (debe dar True)")
        print()

        if "--abrir" in sys.argv:
            lanzador = ROOT / "crear_certificado.bat"
            if lanzador.is_file():
                try:
                    print(f"[info] abriendo {lanzador.name} (se ejecutara con permisos normales) …")
                    subprocess.Popen(["explorer.exe", str(lanzador)])
                    print("       Sigue las instrucciones de la ventana que se abrio.")
                    return 1
                except OSError as exc:
                    print(f"[aviso] no se pudo abrir automáticamente: {exc}")

        print("  Equivalentes de PowerShell por si prefieres pegarlos a mano:")
        print()
        for linea in comandos:
            print("    " + linea)
        return 1

    try:
        (CERTS / "clave.txt").write_text(clave + "\n", encoding="utf-8")
        print(f"[ok] clave guardada en {CERTS / 'clave.txt'} (ignorado por git)")
    except OSError as exc:
        print(f"[aviso] no se pudo guardar la clave: {exc}")

    print(f"[ok] {pfx}")
    print(f"[ok] {cer}")
    _pasos_siguientes(pfx, clave)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
