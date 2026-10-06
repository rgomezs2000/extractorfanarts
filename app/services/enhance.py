"""Mejora de calidad post-descarga: upscaling (Lanczos o IA) y WebP.

Reglas (configurables en app/config.py):
  - Lado mayor >= NO_UPSCALE_ABOVE (1600 px): SIN upscale, solo WebP (mantiene calidad).
  - Hasta 699 px: 4x. De 700 a 799 px: 3x. De 800 a 1500 px: 2x. De 1501 a 1599 px: 1x.
El resultado se guarda SIEMPRE en .webp con la calidad configurada.

Modo IA: usa realesrgan-ncnn-vulkan / waifu2x-ncnn-vulkan si están disponibles
(modelo anime por defecto); si no, cae a Lanczos + afilado suave y lo informa.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .. import config
from .http_client import ConfigError


def _pillow():
    try:
        from PIL import Image, ImageFilter
        return Image, ImageFilter
    except ImportError:
        raise ConfigError(
            "Falta la librería Pillow en ./vendor: ejecuta python scripts\\setup_vendor.py"
        )


def factor_for(longest: int) -> int:
    """Factor de upscaling según el lado mayor de la imagen (reglas del usuario)."""
    if longest >= config.NO_UPSCALE_ABOVE:
        return 1
    for low, high, factor in config.UPSCALE_BUCKETS:
        if low <= longest <= high:
            return factor
    return 1


# ------------------------------------------------------------------ Lanczos
def _lanczos_upscale(path: Path, factor: int) -> Path:
    Image, ImageFilter = _pillow()
    tmp = path.with_name(path.stem + ".up.png")
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        out = im.resize((w * factor, h * factor), Image.Resampling.LANCZOS)
        out = out.filter(ImageFilter.UnsharpMask(radius=2, percent=50, threshold=3))
        out.save(tmp, "PNG")
    return tmp


# ------------------------------------------------------------------ IA (opcional)
def _find_ai_exe() -> Path | None:
    names = ("realesrgan-ncnn-vulkan", "waifu2x-ncnn-vulkan")
    if config.AI_EXE_OVERRIDE:
        p = Path(config.AI_EXE_OVERRIDE)
        if p.exists():
            return p
    for name in names:
        found = shutil.which(name + ".exe") or shutil.which(name)
        if found:
            return Path(found)
    root = Path(__file__).resolve().parents[2]  # app/services -> raíz del proyecto
    vendor = root / "vendor"
    if vendor.is_dir():
        for name in names:
            for p in vendor.rglob(f"{name}*.exe"):
                return p
    return None


def _ai_upscale(path: Path, factor: int) -> Path | None:
    """Upscaling IA con motor Vulkan. Devuelve la ruta del PNG o None si falla."""
    exe = _find_ai_exe()
    if exe is None:
        return None
    out_dir = path.parent / ".ai_tmp"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / (path.stem + "_ai.png")
    # Nota: estos exes esperan -o como RUTA DE ARCHIVO con extensión, no carpeta.
    base_cmd = [str(exe), "-i", str(path), "-o", str(out_file),
                "-s", str(factor), "-f", "png"]
    intentos = []
    if "realesrgan" in exe.name.lower():
        intentos.append(base_cmd + ["-n", config.AI_MODEL])
    intentos.append(base_cmd)
    for cmd in intentos:
        try:
            # Los exes ncnn buscan ./models relativo al directorio de trabajo:
            # se ejecutan con cwd = carpeta del ejecutable.
            # stdio a DEVNULL (no pipes): compatible con sandbox y con la app.
            subprocess.run(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=1800, check=True, cwd=str(exe.parent),
            )
            if out_file.exists() and out_file.stat().st_size > 0:
                return out_file
        except Exception:
            continue
    return None


# ------------------------------------------------------------------ entrada principal
def postprocess(path: Path, settings: dict) -> tuple[Path, dict]:
    """Aplica la política de calidad a un archivo descargado.

    - SIEMPRE convierte a .webp (requisito: nunca se conserva el original).
    - El flag "mejorar" controla SOLO el upscaling (IA o Lanczos); si está
      desactivado, se hace conversión directa a WebP con la calidad configurada.

    Devuelve (ruta_final_en_webp, metadata_de_mejora).
    """
    Image, _ = _pillow()
    calidad = int(settings.get("calidad_webp") or config.WEBP_QUALITY_DEFAULT)
    mejorar = bool(settings.get("mejorar"))
    modo_ia = bool(settings.get("modo_ia"))

    with Image.open(path) as im:
        w, h = im.size
    longest = max(w, h)
    factor = factor_for(longest) if mejorar else 1
    meta: dict = {"original_px": f"{w}x{h}", "factor": factor, "modo": "", "calidad_webp": calidad}

    src = path
    if factor > 1:
        if modo_ia:
            ai_out = _ai_upscale(path, factor)
            if ai_out is not None:
                src = ai_out
                meta["modo"] = f"IA {factor}x"
            else:
                src = _lanczos_upscale(path, factor)
                meta["modo"] = f"Lanczos {factor}x (IA no disponible)"
        else:
            src = _lanczos_upscale(path, factor)
            meta["modo"] = f"Lanczos {factor}x"
    elif mejorar:
        meta["modo"] = "solo WebP (sin upscale)"
    else:
        meta["modo"] = "WebP directo (mejora desactivada)"

    out = path.with_suffix(".webp")
    with Image.open(src) as im:
        rgb = im.convert("RGB")
        meta["resultado_px"] = f"{rgb.width}x{rgb.height}"
        rgb.save(out, "WEBP", quality=calidad, method=6)

    # REQUISITO: el original nunca se conserva; se elimina tras la conversión.
    if src != path:
        try:
            src.unlink()
        except OSError:
            pass
    if out != path:
        try:
            path.unlink()
        except OSError:
            pass
    return out, meta
