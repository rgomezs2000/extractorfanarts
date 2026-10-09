"""Instalador local de dependencias sin pip: descarga los wheels desde PyPI y
los extrae en ./vendor. Funciona en Windows, macOS y Linux (elige los wheels y
los motores IA de la plataforma en la que se ejecuta).

Uso:
    python scripts/setup_vendor.py [carpeta_destino] [--ai] [--solo-ia] [--only=pkg1,pkg2]

  --ai              instala también los motores de IA (Real-ESRGAN / waifu2x)
  --solo-ia         instala SOLO los motores de IA (ningún paquete de Python)
  --only=a,b        instala solo esos paquetes (para añadir uno nuevo sin tocar
                    lo ya instalado)

Sin carpeta de destino usa ./vendor2 (útil para reconstruir); lo normal es:
    python scripts/setup_vendor.py vendor

En el CI (GitHub Actions) conviene definir GITHUB_TOKEN: la API de GitHub limita a
60 peticiones/hora por IP sin autenticar y los runners comparten IP, así que sin
token la lista de releases puede fallar y los motores IA quedarse fuera.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WHEEL_DIR = ROOT / ".wheels"

# Versiones compatibles (resueltas con pip; se ajustan por plataforma al elegir)
PACKAGES: dict[str, str | None] = {
    "shiboken6": "6.11.2",
    "PySide6": "6.11.2",
    "PySide6_Essentials": "6.11.2",
    "PySide6_Addons": "6.11.2",
    "httpx": "0.28.1",
    "httpcore": "1.0.9",
    "h11": "0.16.0",
    "anyio": "4.15.1",
    "idna": "3.20",
    "sniffio": None,
    "certifi": None,
    "typing_extensions": None,
    "pillow": None,        # mejora de calidad (Lanczos/WebP)
    "curl_cffi": None,     # transporte con huella de navegador (Cloudflare)
    "cffi": None,          # dependencia de curl_cffi (extensión _cffi_backend)
    "pycparser": None,     # dependencia de cffi
    # Solo para empaquetar (scripts/build_exe.py)
    "pyinstaller": None,
    "pyinstaller-hooks-contrib": None,
    "altgraph": None,
    "packaging": None,
    "pefile": None,          # Windows
    "pywin32-ctypes": None,  # Windows
}

# Motores IA opcionales (binarios oficiales, autónomos: ejecutable + modelos).
AI_GITHUB: dict[str, str] = {
    "realesrgan-ncnn-vulkan": "xinntao/Real-ESRGAN",
    "waifu2x-ncnn-vulkan": "nihui/waifu2x-ncnn-vulkan",
}


# ------------------------------------------------------------------ plataforma
def _etiquetas_sistema() -> tuple[list[str], list[str]]:
    """(marcadores de sistema en el nombre del wheel, arquitecturas preferidas)."""
    maquina = platform.machine().lower()
    if sys.platform.startswith("win"):
        return ["win_amd64", "win32"], ["amd64"]
    if sys.platform == "darwin":
        if maquina in ("arm64", "aarch64"):
            return ["macosx"], ["universal2", "arm64", "x86_64"]
        return ["macosx"], ["universal2", "x86_64", "arm64"]
    return (["manylinux", "linux_x86_64", "linux_aarch64"],
            [maquina or "x86_64"])


def _etiquetas_ia() -> tuple[str, ...]:
    """Palabras clave del ZIP de motores IA según la plataforma."""
    if sys.platform.startswith("win"):
        return ("windows",)
    if sys.platform == "darwin":
        return ("macos",)
    return ("ubuntu", "linux")


def _puntuar_wheel(nombre: str) -> int:
    if not nombre.endswith(".whl"):
        return -1
    bajo = nombre.lower()
    tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
    sistema, arquitecturas = _etiquetas_sistema()

    es_any = "py3-none-any" in bajo
    tiene_plataforma = any(s in bajo for s in sistema)
    if not (es_any or tiene_plataforma):
        return -1

    puntos = 0
    if tag in bajo:
        puntos += 8
    elif "abi3" in bajo:
        puntos += 6
    elif es_any or "py3-none-" in bajo:
        # Puro para cualquier Python; puede llevar etiqueta de plataforma
        # (p. ej. pyinstaller-6.x-py3-none-win_amd64.whl)
        puntos += 4
    else:
        return -1
    for indice, arquitectura in enumerate(arquitecturas):
        if arquitectura in bajo:
            puntos += len(arquitecturas) - indice
    return puntos


def pick_wheel(files: list[dict]) -> dict | None:
    """Elige el mejor wheel para ESTA plataforma y versión de Python."""
    mejores = [f for f in files if _puntuar_wheel(f["filename"]) > 0]
    if not mejores:
        return None
    return max(mejores, key=lambda f: _puntuar_wheel(f["filename"]))


# ------------------------------------------------------------------ utilidades
def _json(url: str) -> dict:
    """GET JSON con User-Agent propio y token de GitHub si está disponible."""
    peticion = urllib.request.Request(
        url, headers={"User-Agent": "Imaginteca-setup_vendor"})
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and "api.github.com" in url:
        peticion.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(peticion, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _marcar_ejecutables(directorio: Path) -> None:
    """En macOS/Linux los binarios extraídos necesitan permiso de ejecución."""
    if sys.platform.startswith("win"):
        return
    nombres = tuple(AI_GITHUB)
    for ruta in directorio.rglob("*"):
        if not ruta.is_file():
            continue
        if not ruta.name.startswith(nombres):
            continue
        if ruta.suffix.lower() in (".param", ".bin", ".md", ".txt"):
            continue
        try:
            ruta.chmod(ruta.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            print(f"[ok] permiso de ejecución: {ruta.name}")
        except OSError as exc:
            print(f"[aviso] no se pudo marcar {ruta}: {exc}")


def install_ai_engines(target: Path) -> None:
    """Descarga y extrae los motores IA de ESTA plataforma desde GitHub."""
    etiquetas = _etiquetas_ia()
    for nombre, repo in AI_GITHUB.items():
        try:
            releases = _json(f"https://api.github.com/repos/{repo}/releases?per_page=15")
            asset = None
            for release in releases:
                for candidato in release.get("assets", []):
                    archivo = (candidato.get("name") or "").lower()
                    if archivo.endswith(".zip") and any(e in archivo for e in etiquetas):
                        asset = candidato
                        break
                if asset is not None:
                    break
            if asset is None:
                print(f"[omitido] {nombre}: sin binario para {sys.platform} ({etiquetas})")
                continue
            paquete = WHEEL_DIR / asset["name"]
            if not paquete.exists():
                print(f"[descargando] {nombre}: {asset['name']} …")
                urllib.request.urlretrieve(asset["browser_download_url"], paquete)
            else:
                print(f"[cache] {paquete.name}")
            with zipfile.ZipFile(paquete) as zf:
                zf.extractall(target)
            print(f"[ok] {nombre}")
        except Exception as exc:  # noqa: BLE001
            print(f"[omitido] {nombre}: {exc}")
    _marcar_ejecutables(target)
    _etiqueta_integridad_media(target)


def _etiqueta_integridad_media(directorio: Path) -> None:
    """Windows: devuelve a «Media» la etiqueta de integridad de los motores IA.

    Si la extracción ocurre dentro de un entorno restringido (sandbox de un agente,
    CI en contenedor…), los `.exe` heredan la etiqueta de integridad **baja** y
    Windows los lanza en modo restringido: arrancan (detectan la GPU) pero **no
    pueden escribir su salida** — «encode image … failed» —, así que el modo IA se
    queda en Lanczos sin explicar el motivo. Es exactamente la misma corrección que
    `build_exe.py` aplica al paquete compilado.
    """
    if not sys.platform.startswith("win"):
        return
    icacls = shutil.which("icacls")
    if not icacls:
        return
    try:
        resultado = subprocess.run(
            [icacls, str(directorio), "/setintegritylevel", "Medium", "/T", "/C"],
            capture_output=True, text=True,
        )
    except OSError:
        return
    if resultado.returncode == 0:
        print("[ok] etiqueta de integridad de los motores IA: Media")
    else:
        print("[aviso] no se pudo ajustar la etiqueta de integridad de los motores IA")


# ------------------------------------------------------------------ principal
def main() -> int:
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    target = Path(argumentos[0]) if argumentos else ROOT / "vendor2"
    solo: set[str] | None = None
    for arg in sys.argv[1:]:
        if arg.startswith("--only="):
            solo = {p.strip() for p in arg.split("=", 1)[1].split(",") if p.strip()}

    target.mkdir(parents=True, exist_ok=True)
    WHEEL_DIR.mkdir(exist_ok=True)
    print(f"[info] plataforma: {sys.platform} / {platform.machine()} · "
          f"python {sys.version_info.major}.{sys.version_info.minor}")

    instalados = 0
    solo_ia = "--solo-ia" in sys.argv
    for paquete, version in PACKAGES.items():
        if solo_ia:
            break
        if solo and paquete not in solo:
            continue
        try:
            info = _json(f"https://pypi.org/pypi/{paquete}/json")
        except Exception as exc:  # noqa: BLE001
            print(f"[omitido] {paquete}: {exc}")
            continue
        ver = version or info["info"]["version"]
        wheel = pick_wheel(info["releases"].get(ver, []))
        if wheel is None:
            print(f"[omitido] {paquete} {ver}: sin wheel para esta plataforma")
            continue
        ruta_wheel = WHEEL_DIR / wheel["filename"]
        if not ruta_wheel.exists():
            print(f"[descargando] {wheel['filename']} …")
            urllib.request.urlretrieve(wheel["url"], ruta_wheel)
        else:
            print(f"[cache] {ruta_wheel.name}")
        with zipfile.ZipFile(ruta_wheel) as zf:
            zf.extractall(target)
        print(f"[ok] {paquete} {ver}")
        instalados += 1

    # OJO: `--solo-ia` TAMBIÉN instala los motores. Antes solo lo hacía `--ai`, así
    # que `setup_vendor.py vendor --solo-ia` (lo que usa el CI) no instalaba NADA y
    # el paso terminaba con éxito: el paquete publicado salía sin motores de IA.
    if "--ai" in sys.argv or solo_ia:
        install_ai_engines(target)
        motores = sorted({ruta.name for ruta in target.rglob("*")
                          if ruta.is_file()
                          and ruta.name.startswith(tuple(AI_GITHUB))})
        if motores:
            print(f"[ok] motores IA instalados: {', '.join(motores)}")
        else:
            print("[AVISO] no se instaló ningún motor de IA (¿sin red o sin binario "
                  "para esta plataforma?): la aplicación seguirá funcionando con "
                  "Lanczos + afilado.")

    print(f"\nInstalado en {target} ({instalados} paquetes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
