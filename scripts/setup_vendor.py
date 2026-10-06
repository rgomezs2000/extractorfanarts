"""Instalador local de dependencias sin pip: descarga los wheels desde PyPI y
los extrae en ./vendor. Útil cuando pip no está disponible o falla.

Uso:
    python scripts/setup_vendor.py [carpeta_destino]   # por defecto: vendor2

Después de ejecutarlo, la aplicación usa ./vendor (ver main.py). Si usas otro
destino, renombra la carpeta a `vendor` o ajusta main.py.
"""
from __future__ import annotations

import json
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WHEEL_DIR = ROOT / ".wheels"

# Versiones compatibles (resueltas por pip el 2026-10-06, Python 3.12 / win_amd64)
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
    "sniffio": None,  # última versión
    "certifi": None,  # última versión
    "typing_extensions": None,  # última versión
    "pillow": None,  # mejora de calidad (Lanczos/WebP)
}

# Motores IA opcionales (modo IA del upscaling). Se instalan con: --ai
# Descarga los binarios oficiales autónomos (exe + modelos) desde GitHub Releases.
AI_GITHUB: dict[str, str] = {
    "realesrgan-ncnn-vulkan": "xinntao/Real-ESRGAN",
    "waifu2x-ncnn-vulkan": "nihui/waifu2x-ncnn-vulkan",
}


def _json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def pick_wheel(files: list[dict]) -> dict | None:
    tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
    for f in files:
        name = f["filename"]
        if name.endswith(".whl") and "win_amd64" in name and tag in name:
            return f
    for f in files:
        name = f["filename"]
        if name.endswith(".whl") and "win_amd64" in name and "abi3" in name:
            return f
    for f in files:
        name = f["filename"]
        if name.endswith(".whl") and ("win_amd64" in name or "py3-none-any" in name):
            return f
    return None


def install_ai_engines(target: Path) -> None:
    """Descarga y extrae los motores IA (Real-ESRGAN / waifu2x) desde GitHub."""
    for name, repo in AI_GITHUB.items():
        try:
            rels = _json(f"https://api.github.com/repos/{repo}/releases?per_page=15")
            asset = None
            for rel in rels:
                for a in rel.get("assets", []):
                    n = (a.get("name") or "").lower()
                    if "windows" in n and n.endswith(".zip"):
                        asset = a
                        break
                if asset is not None:
                    break
            if asset is None:
                print(f"[omitido] {name}: sin asset windows en los releases")
                continue
            zp = WHEEL_DIR / asset["name"]
            if not zp.exists():
                print(f"[descargando] {name}: {asset['name']} …")
                urllib.request.urlretrieve(asset["browser_download_url"], zp)
            else:
                print(f"[cache] {zp.name}")
            with zipfile.ZipFile(zp) as zf:
                zf.extractall(target)
            print(f"[ok] {name}")
        except Exception as exc:
            print(f"[omitido] {name}: {exc}")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    target = Path(args[0]) if args else ROOT / "vendor2"
    target.mkdir(parents=True, exist_ok=True)
    WHEEL_DIR.mkdir(exist_ok=True)

    for package, version in PACKAGES.items():
        try:
            info = _json(f"https://pypi.org/pypi/{package}/json")
        except Exception as exc:
            print(f"[omitido] {package}: {exc}")
            continue
        ver = version or info["info"]["version"]
        files = info["releases"].get(ver, [])
        wheel = pick_wheel(files)
        if wheel is None:
            print(f"[ERROR] sin wheel para {package} {ver}")
            return 1
        wheel_path = WHEEL_DIR / wheel["filename"]
        if not wheel_path.exists():
            print(f"[descargando] {wheel['filename']} …")
            urllib.request.urlretrieve(wheel["url"], wheel_path)
        else:
            print(f"[cache] {wheel_path.name}")
        with zipfile.ZipFile(wheel_path) as zf:
            zf.extractall(target)
        print(f"[ok] {package} {ver}")

    if "--ai" in sys.argv:
        install_ai_engines(target)

    print(f"\nInstalado en {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
