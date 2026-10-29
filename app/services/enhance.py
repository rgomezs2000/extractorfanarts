"""Mejora de calidad post-descarga: upscaling (Lanczos o IA), definición y WebP.

Reglas (configurables en app/config.py, UPSCALE_BUCKETS):
  - Hasta 699 px: 4x · 700-799 px: 3x · 800 px en adelante: 2x
  - Tope MAX_OUTPUT_SIDE (7680 px = 8K); por encima de 7679 px no se reescala.
  - `resumen_mejora()` devuelve el texto que ve el usuario («153x153 → 612x612 ·
    Lanczos 4x») y avisa si el origen era diminuto (poco detalle real).
El resultado se guarda SIEMPRE en .webp con la calidad configurada.

CONTROL DE INTEGRIDAD (anti-corrupción / anti-artefactos):
  1. El archivo descargado se decodifica completo antes de tocarlo: si está
     truncado o corrupto → ImagenCorruptaError (el controlador lo descarta).
  2. Cada salida de IA se valida contra el original (diferencia media, MAE):
     una salida corrupta tipo "mosaico" se descarta y se prueba el siguiente
     método. Nunca se guarda una imagen corrupta.
  3. Si cualquier paso falla, se aplica una conversión DIRECTA a WebP (segura).
  4. El .webp final se vuelve a abrir y verificar (decodifica + tamaño).
     Si no pasa, se conserva el archivo original en lugar de guardar algo roto.

DEFINICIÓN: afilado (UnsharpMask) con intensidad configurable; en IA es suave
para no crear halos.
TRANSPARENCIA: el alfa se separa, se reescala aparte y se recompone (sin halos).
"""
from __future__ import annotations

import logging
import re
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .. import config
from . import calidad as control_calidad
from .http_client import ConfigError

logger = logging.getLogger("imaginteca")
_GPUS_CACHE: list[str] | None = None
_ULTIMO_MOTOR = ""


class ImagenCorruptaError(Exception):
    """El archivo descargado no es una imagen válida (truncado o dañado)."""


def _pillow():
    try:
        from PIL import Image, ImageFilter
        return Image, ImageFilter
    except ImportError:
        raise ConfigError(
            "Falta la librería Pillow en ./vendor: ejecuta python scripts\\setup_vendor.py"
        )


def gpus_detectadas() -> list[str]:
    """Nombres de las tarjetas gráficas del equipo (informativo).

    El motor usa Vulkan y elige la tarjeta él solo; esto sirve para dejar en el registro
    y en el autoexamen QUÉ tarjeta hay (NVIDIA, AMD/ATI, Intel…) y que se pueda comprobar.
    """
    global _GPUS_CACHE
    if _GPUS_CACHE is not None:
        return _GPUS_CACHE
    nombres: list[str] = []
    try:
        if os.name == "nt":
            banderas = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            salida = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"],
                capture_output=True, text=True, timeout=10, creationflags=banderas,
            )
            nombres = [l.strip() for l in (salida.stdout or "").splitlines() if l.strip()]
        elif sys.platform == "darwin":
            salida = subprocess.run(["system_profiler", "SPDisplaysDataType"],
                                    capture_output=True, text=True, timeout=10)
            nombres = [l.split(":", 1)[1].strip() for l in (salida.stdout or "").splitlines()
                       if "Chipset Model" in l]
    except Exception:  # noqa: BLE001
        nombres = []
    _GPUS_CACHE = nombres
    return nombres


def factor_for(ancho: int) -> int:
    """Factor de ampliación según el ANCHO de la imagen (reglas de UPSCALE_BUCKETS).

    El mínimo de 1600 px se mide sobre el ancho: el factor se aplica luego a los dos
    lados, así una imagen vertical también gana ancho de verdad.

    Suelo de calidad: por DEBAJO de `UPSCALE_MIN_SOURCE` no se amplía. Estas imágenes
    diminutas (stickers de Bluesky de 256 px, iconos, emojis) no ganan detalle al
    ampliarlas 8x o 32x: solo se convierten en manchas borrosas. Con el suelo en 0 se
    recupera la tabla estricta.
    """
    if ancho < int(getattr(config, "UPSCALE_MIN_SOURCE", 0) or 0):
        return 1
    for low, high, factor in config.UPSCALE_BUCKETS:
        if low <= ancho <= high:
            return factor
    return 1


def _tamano_objetivo(w: int, h: int, factor: int) -> tuple[int, int, float]:
    """Tamaño final aplicando el tope de 8K. Nunca reduce por debajo del original."""
    escala = float(factor)
    tope = getattr(config, "MAX_OUTPUT_SIDE", 7680)
    longest = max(w, h)
    if factor > 1 and longest * escala > tope:
        escala = max(1.0, tope / longest)
    return max(1, round(w * escala)), max(1, round(h * escala)), escala


def _tiene_alfa(im) -> bool:
    return im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)


def _afilar(im, porcentaje: int, radio: float = 2.0, umbral: int = 3):
    """UnsharpMask sobre RGB; la intensidad se limita para no dañar la imagen."""
    porcentaje = max(0, min(150, int(porcentaje or 0)))
    if not porcentaje:
        return im
    _, ImageFilter = _pillow()
    return im.filter(ImageFilter.UnsharpMask(radius=radio, percent=porcentaje, threshold=umbral))


def _abrir_verificada(ruta: Path):
    """Abre y decodifica por completo un archivo, o lanza ImagenCorruptaError."""
    Image, _ = _pillow()
    try:
        im = Image.open(ruta)
        im.load()  # fuerza la decodificación completa (detecta truncados)
        return im
    except Exception as exc:  # noqa: BLE001
        raise ImagenCorruptaError(
            f"el archivo no es una imagen válida (corrupto o incompleto): {exc}"
        ) from exc


# ------------------------------------------------------------------ validación IA
def _mae_contra_original(original: Path, candidato: Path, w: int, h: int) -> float | None:
    """Diferencia media (0-255) entre el original y el candidato reducido a su tamaño."""
    try:
        from PIL import Image, ImageChops
        with Image.open(original) as im_o, Image.open(candidato) as im_c:
            im_c.load()
            referencia = im_o.convert("RGB")
            reducido = im_c.convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
        histograma = ImageChops.difference(referencia, reducido).convert("L").histogram()
        total = sum(histograma)
        if not total:
            return None
        return sum(i * n for i, n in enumerate(histograma)) / total
    except Exception:  # noqa: BLE001
        return None


def _corregir_paleta(original: Path, salida: Path) -> list[int] | None:
    """Devuelve la paleta de una salida IA a la del original (limpieza de color).

    Los modelos Real-ESRGAN desplazan ligeramente los canales (medido en el modelo de
    anime: +1,4 en el verde). Se calcula el desplazamiento medio por canal comparando
    el original con la salida reducida a su tamaño, y se resta en la imagen completa:
    el resultado conserva la definición de la IA pero con la MISMA paleta, sin
    cambiar el color de la obra. Devuelve los desfases aplicados (o None si no hacía
    falta tocar nada).
    """
    try:
        Image, _ = _pillow()
        with Image.open(original) as im_o, Image.open(salida) as im_s:
            referencia = im_o.convert("RGB")
            imagen = im_s.convert("RGB")
        reducida = imagen.resize(referencia.size, Image.Resampling.LANCZOS)
        desfases: list[int] = []
        for canal in range(3):
            a = referencia.getchannel(canal).tobytes()
            b = reducida.getchannel(canal).tobytes()
            desfases.append(round(sum(x - y for x, y in zip(a, b)) / len(a)))
        if all(abs(desfase) <= getattr(config, "AI_PALETA_TOLERANCIA", 1)
               for desfase in desfases):
            return None                      # ya coincide: no se toca nada
        canales = []
        for canal, desfase in enumerate(desfases):
            banda = imagen.getchannel(canal)
            if desfase:
                banda = banda.point(lambda v, d=desfase: max(0, min(255, v + d)))
            canales.append(banda)
        Image.merge("RGB", canales).save(salida, "PNG")
        return desfases
    except Exception:  # noqa: BLE001
        logger.warning("no se pudo corregir la paleta de la salida IA", exc_info=True)
        return None


def _validar_ia(original: Path, candidato: Path, w: int, h: int) -> bool:
    """Descarta salidas de IA que no se parezcan al original (mosaicos/desplazamientos)."""
    mae = _mae_contra_original(original, candidato, w, h)
    umbral = getattr(config, "AI_MAX_MAE", 12)
    if mae is None:
        logger.warning("no se pudo validar la salida IA (%s): se descarta", candidato.name)
        return False
    if mae > umbral:
        logger.warning(
            "salida IA descartada por posible corrupción: MAE %.1f > umbral %s (%s)",
            mae, umbral, candidato.name,
        )
        return False
    return True


# ------------------------------------------------------------------ transparencia
def _preparar_para_upscale(path: Path, dir_tmp: Path) -> tuple[Path, Path | None]:
    """Separa la transparencia antes de reescalar (RGB aplanado sobre blanco)."""
    Image, _ = _pillow()
    with Image.open(path) as im:
        if not _tiene_alfa(im):
            return path, None
        rgba = im.convert("RGBA")
        alfa_path = dir_tmp / f"{path.stem}.alpha.png"
        rgba.getchannel("A").save(alfa_path, "PNG")
        fondo = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        plano = Image.alpha_composite(fondo, rgba).convert("RGB")
        rgb_path = dir_tmp / f"{path.stem}.rgb.png"
        plano.save(rgb_path, "PNG")
        return rgb_path, alfa_path


def _recomponer_alfa(rgb_path: Path, alfa_path: Path, salida: Path) -> Path:
    """Vuelve a aplicar el canal alfa (reescalado al tamaño final)."""
    Image, _ = _pillow()
    with Image.open(rgb_path) as im_rgb, Image.open(alfa_path) as im_alfa:
        rgb = im_rgb.convert("RGB")
        alfa = im_alfa.convert("L").resize(rgb.size, Image.Resampling.LANCZOS)
        combinada = rgb.convert("RGBA")
        combinada.putalpha(alfa)
        combinada.save(salida, "PNG")
    return salida


# ------------------------------------------------------------------ Lanczos
def _lanczos_upscale(path: Path, tamano: tuple[int, int]) -> Path:
    """Reescalado clásico al tamaño objetivo + afilado (SHARPEN_LANCZOS)."""
    Image, _ = _pillow()
    tmp = path.with_name(path.stem + ".up.png")
    with Image.open(path) as im:
        rgb = im.convert("RGB")
        if rgb.size != tamano:
            rgb = rgb.resize(tamano, Image.Resampling.LANCZOS)
        rgb = _afilar(rgb, config.SHARPEN_LANCZOS,
                      radio=getattr(config, "SHARPEN_LANCZOS_RADIO", 1.5))
        rgb.save(tmp, "PNG")
    return tmp


def _ultimas_lineas(ruta: Path, cuantas: int = 3) -> str:
    """Últimas líneas del registro de un motor, para explicar un fallo."""
    try:
        texto = ruta.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    except OSError:
        return ""
    return " | ".join(linea.strip() for linea in texto[-cuantas:] if linea.strip())


# ------------------------------------------------------------------ IA (opcional)
def _find_ai_exe() -> Path | None:
    """Localiza el motor IA (Windows .exe o binario de macOS/Linux)."""
    names = ("realesrgan-ncnn-vulkan", "waifu2x-ncnn-vulkan")
    if config.AI_EXE_OVERRIDE:
        p = Path(config.AI_EXE_OVERRIDE)
        if p.exists():
            return p
    for name in names:
        for candidato in (name, name + ".exe"):
            encontrado = shutil.which(candidato)
            if encontrado:
                return Path(encontrado)
    root = Path(__file__).resolve().parents[2]  # app/services -> raíz del proyecto
    candidatos_raiz = [root / "vendor"]
    if getattr(sys, "frozen", False):
        candidatos_raiz.append(Path(sys.executable).resolve().parent / "vendor")
        interior = getattr(sys, "_MEIPASS", None)
        if interior:
            candidatos_raiz.append(Path(interior) / "vendor")
    for base in candidatos_raiz:
        if not base.is_dir():
            continue
        for name in names:
            for p in base.rglob(f"{name}*"):
                if not p.is_file() or p.suffix.lower() in (".param", ".bin", ".txt", ".md"):
                    continue
                if p.suffix.lower() == ".exe" or os.access(p, os.X_OK):
                    return p
    return None


def _ejecutar_ia(exe: Path, entrada: Path, salida: Path, escala: int,
                 modelo: str | None, w: int, h: int) -> Path | None:
    """Ejecuta el motor IA y valida tamaño y contenido de la salida."""
    cmd = [str(exe), "-i", str(entrada), "-o", str(salida), "-s", str(escala), "-f", "png"]
    gpu = str(getattr(config, "AI_GPU", "") or "").strip()
    if gpu:
        cmd += ["-g", gpu]   # forzar tarjeta gráfica concreta (Vulkan)
    if modelo and "realesrgan" in exe.name.lower():
        cmd += ["-n", modelo]

    # La salida del motor se guarda en un ARCHIVO, no en una tubería: las tuberías
    # fallan en entornos con sandbox y, sobre todo, aquí hacen falta las palabras del
    # motor para saber POR QUÉ no mejoró (p. ej. «encode image … failed» cuando el
    # .exe arrastra la etiqueta de integridad baja y Windows lo lanza en modo
    # restringido: arranca, pero no puede escribir su salida).
    # El registro es SOLO para diagnosticar: se lee y se borra en la misma llamada,
    # así no queda ni un archivo suelto (ni en la salida ni en el temporal).
    registro = Path(tempfile.gettempdir()) / f"imaginteca-ia-{os.getpid()}.log"
    error_ejecucion = ""
    motivo_motor = ""
    try:
        # Los exes ncnn buscan ./models relativo al directorio de trabajo:
        # se ejecutan con cwd = carpeta del ejecutable.
        with open(registro, "wb") as manejador:
            subprocess.run(
                cmd, stdout=manejador, stderr=subprocess.STDOUT,
                timeout=1800, check=True, cwd=str(exe.parent),
            )
    except Exception as exc:  # noqa: BLE001
        error_ejecucion = str(exc)
    finally:
        motivo_motor = _ultimas_lineas(registro)
        try:
            registro.unlink()
        except OSError:
            pass

    if error_ejecucion or not salida.exists() or salida.stat().st_size == 0:
        logger.warning("el motor IA (%s) no mejoró la imagen: %s · %s",
                       exe.name, error_ejecucion or "no generó ninguna imagen",
                       motivo_motor)
        return None
    try:
        Image, _ = _pillow()
        with Image.open(salida) as im:
            im.load()
            if im.size != (w * escala, h * escala):
                # tamaño inesperado → resultado no fiable
                logger.warning("salida IA con tamaño inesperado: %s (se descarta)", im.size)
                return None
    except Exception:  # noqa: BLE001
        return None
    # Validación de contenido: descarta mosaicos/desplazamientos
    if not _validar_ia(entrada, salida, w, h):
        return None
    global _ULTIMO_MOTOR
    _ULTIMO_MOTOR = "Real-ESRGAN"
    return salida


_SCRIPT_TORCH = """\"\"\"Motor de IA opcional por PyTorch: usa TU Python y hereda CUDA/DirectML/TensorRT/CPU.

El programa no puede traer PyTorch (cientos de MB), pero sí puede **usar el tuyo**:
lanza este script con el intérprete que tenga torch y le pasa la imagen. Según lo que
tengas instalado, el dispositivo será:

  · CUDA          -> tarjetas NVIDIA (torch con CUDA)
  · DirectML      -> cualquier GPU DX12 en Windows (paquete torch-directml)
  · TensorRT      -> NVIDIA con torch-tensorrt instalado
  · MPS           -> Apple Silicon
  · CPU           -> siempre, como último recurso

Uso:
    python upscale_torch.py -i entrada.png -o salida.png -s 4 [--device auto|cuda|dml|trt|mps|cpu]
\"\"\"
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def dispositivo(torch, pedido: str):
    \"\"\"Devuelve (dispositivo, nombre legible) según lo pedido y lo disponible.\"\"\"
    pedido = (pedido or "auto").lower()
    try:
        import torch_directml  # noqa: F401
        hay_dml = True
    except ImportError:
        hay_dml = False

    if pedido in ("cpu",):
        return torch.device("cpu"), "CPU"
    if pedido in ("cuda", "auto", "trt"):
        if torch.cuda.is_available():
            nombre = torch.cuda.get_device_name(0)
            return torch.device("cuda"), f"CUDA · {nombre}"
        if pedido == "cuda":
            raise SystemExit("pediste CUDA y no está disponible")
    if pedido in ("dml", "auto") and hay_dml:
        import torch_directml

        return torch_directml.device(), "DirectML"
    if pedido in ("mps", "auto") and getattr(torch.backends, "mps", None) \
            and torch.backends.mps.is_available():
        return torch.device("mps"), "MPS (Apple)"
    if pedido == "dml":
        raise SystemExit("pediste DirectML y torch-directml no está instalado")
    return torch.device("cpu"), "CPU"


def cargar_modelo(ruta_pesos: Path, escala_nativa: int = 4):
    \"\"\"RRDBNet de Real-ESRGAN (paquete `realesrgan`).\"\"\"
    from realesrgan import RRDBNet

    modelo = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6,
                     num_grow_ch=32, scale=escala_nativa)
    if not ruta_pesos.is_file():
        raise SystemExit(f"no encuentro los pesos: {ruta_pesos}")
    estado = __import__("torch").load(str(ruta_pesos), map_location="cpu")
    if isinstance(estado, dict) and "params_ema" in estado:
        estado = estado["params_ema"]
    modelo.load_state_dict(estado, strict=True)
    modelo.eval()
    return modelo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", required=True)
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("-s", "--scale", type=int, default=4)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--weights", default="")
    args = ap.parse_args()

    try:
        import torch
    except ImportError:
        print("PyTorch no está instalado en este Python", file=sys.stderr)
        return 3

    from PIL import Image

    entrada = Path(args.input)
    salida = Path(args.output)
    pesos = Path(args.weights) if args.weights else (
        Path.home() / ".imaginteca" / "ia" / "RealESRGAN_x4plus_anime_6B.pth")
    try:
        modelo = cargar_modelo(pesos)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 4

    equipo, nombre = dispositivo(torch, args.device)
    print(f"dispositivo: {nombre}")
    modelo = modelo.to(equipo)

    with Image.open(entrada) as im:
        original = im.convert("RGB")
    datos = torch.from_numpy(__import__("numpy").array(original)).permute(2, 0, 1)
    datos = datos.float().div(255).unsqueeze(0).to(equipo)
    with torch.no_grad():
        resultado = modelo(datos)
    resultado = resultado.squeeze(0).clamp(0, 1).mul(255).round().byte()
    resultado = resultado.permute(1, 2, 0).cpu().numpy()
    imagen = Image.fromarray(resultado, "RGB")
    if imagen.width != original.width * args.scale:
        objetivo = (original.width * args.scale, original.height * args.scale)
        imagen = imagen.resize(objetivo, Image.LANCZOS)
    salida.parent.mkdir(parents=True, exist_ok=True)
    imagen.save(salida, "PNG")
    print(f"guardado: {salida} ({imagen.width}x{imagen.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""
_PYTHON_TORCH: str | None = ""


def _python_con_torch() -> str | None:
    """Busca un intérprete de Python que tenga torch instalado (el del usuario)."""
    global _PYTHON_TORCH
    if _PYTHON_TORCH is not None:
        return _PYTHON_TORCH or None
    candidatos: list[list[str]] = []
    manual = str(getattr(config, "AI_PYTHON", "") or "").strip()
    if manual:
        candidatos.append([manual])
    if os.name == "nt":
        candidatos += [["py", "-3"], ["python"], ["python3"]]
    else:
        candidatos += [["python3"], ["python"]]
    for orden in candidatos:
        try:
            prueba = subprocess.run(
                orden + ["-c", "import torch; print(torch.__version__)"],
                capture_output=True, text=True, timeout=25,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if prueba.returncode == 0 and prueba.stdout.strip():
                _PYTHON_TORCH = " ".join(orden)
                logger.info("IA torch: intérprete %s (torch %s)", _PYTHON_TORCH,
                            prueba.stdout.strip().splitlines()[0])
                return _PYTHON_TORCH
        except Exception:  # noqa: BLE001
            continue
    _PYTHON_TORCH = ""
    return None


def _pesos_torch() -> Path:
    """Ruta de los pesos de Real-ESRGAN anime 6B; los descarga si faltan (~18 MB)."""
    indicada = str(getattr(config, "AI_TORCH_MODEL", "") or "").strip()
    if indicada:
        return Path(indicada)
    destino = Path.home() / ".imaginteca" / "ia" / "RealESRGAN_x4plus_anime_6B.pth"
    if destino.is_file() and destino.stat().st_size > 1_000_000:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    url = ("https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/"
           "RealESRGAN_x4plus_anime_6B.pth")
    logger.info("IA torch: descargando los pesos del modelo anime (~18 MB)…")
    try:
        cliente = PoliteClient()
        try:
            datos = cliente.get_bytes(url, max_bytes=60 * 1024 * 1024)
        finally:
            cliente.close()
        if datos and len(datos) > 1_000_000:
            destino.write_bytes(datos)
            logger.info("IA torch: pesos guardados en %s", destino)
            return destino
    except Exception as exc:  # noqa: BLE001
        logger.info("IA torch: no se pudieron descargar los pesos (%s)", exc)
    return destino

def _ai_torch(path: Path, factor: int, tamano: tuple[int, int]) -> Path | None:
    """Amplía con la instalación de PyTorch del usuario (CUDA/DirectML/TensorRT/CPU)."""
    interprete = _python_con_torch()
    if not interprete:
        logger.info("IA torch: no se encontró un Python con torch; se usa otro motor")
        return None
    Image, _ = _pillow()
    with Image.open(path) as im:
        w, h = im.size
    if (w * factor) * (h * factor) > getattr(config, "AI_MAX_PIXELS", 50_000_000):
        return None
    with Image.open(path) as im:
        w, h = im.size
    out_dir = path.parent / ".ai_tmp"
    out_dir.mkdir(exist_ok=True)
    script = out_dir / "upscale_torch.py"
    script.write_text(_SCRIPT_TORCH, encoding="utf-8")
    salida = out_dir / f"{path.stem}_torch_{factor}.png"
    orden = interprete.split() + [str(script), "-i", str(path), "-o", str(salida),
                                 "-s", str(min(factor, 4)),
                                 "--device", str(getattr(config, "AI_TORCH_DEVICE", "auto") or "auto")]
    pesos = str(_pesos_torch())
    if pesos:
        orden += ["--weights", pesos]
    try:
        proceso = subprocess.run(orden, capture_output=True, text=True, timeout=1800,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception as exc:  # noqa: BLE001
        logger.info("IA torch: no se pudo ejecutar (%s)", exc)
        return None
    if proceso.returncode != 0 or not salida.exists():
        detalle = (proceso.stderr or proceso.stdout or "").strip().splitlines()
        logger.info("IA torch falló: %s", detalle[-1] if detalle else proceso.returncode)
        return None
    try:
        with Image.open(salida) as im:
            im.load()
            if im.width < w:
                return None
        if salida.exists():
            global _ULTIMO_MOTOR
            detalle = (proceso.stdout or "").strip().splitlines()
            _ULTIMO_MOTOR = "torch" + (f" [{detalle[0]}]" if detalle else "")
        return salida
    except Exception:  # noqa: BLE001
        return None

def _find_waifu2x_exe() -> Path | None:
    """Localiza waifu2x-ncnn-vulkan (segundo motor, también Vulkan)."""
    manual = str(getattr(config, "AI_WAIFU2X_EXE", "") or "").strip()
    if manual:
        ruta = Path(manual)
        if ruta.is_file():
            return ruta
    base = Path(__file__).resolve().parent.parent.parent
    for carpeta in (base / "vendor", Path(getattr(sys, "_MEIPASS", base)) / "vendor",
                    Path(sys.executable).resolve().parent / "vendor"):
        if not carpeta.is_dir():
            continue
        directo = carpeta / "waifu2x-ncnn-vulkan.exe"
        if directo.is_file():
            return directo
        for sub in sorted(carpeta.glob("waifu2x-ncnn-vulkan*")):
            if sub.is_dir():
                exe = sub / "waifu2x-ncnn-vulkan.exe"
                if exe.is_file():
                    return exe
    return None


def _ai_waifu2x(path: Path, factor: int, tamano: tuple[int, int]) -> Path | None:
    """Amplía con waifu2x (modelo anime). Devuelve el PNG o None si no se puede.

    waifu2x escala de forma nativa 2, 4, 8, 16 y 32: encaja con los tramos grandes
    (8x, 16x, 32x) sin encadenar reescalados. Su modelo de anime está pensado para
    dibujo de línea, que es la mitad de lo que se descarga aquí.
    """
    exe = _find_waifu2x_exe()
    if exe is None:
        return None
    Image, _ = _pillow()
    with Image.open(path) as im:
        w, h = im.size
    objetivo = min([2, 4, 8, 16, 32], key=lambda e: (abs(e - factor), e))
    if (w * objetivo) * (h * objetivo) > getattr(config, "AI_MAX_PIXELS", 50_000_000):
        objetivo = max(2, objetivo // 2)
    out_dir = path.parent / ".ai_tmp"
    out_dir.mkdir(exist_ok=True)
    salida = out_dir / f"{path.stem}_w2x_{objetivo}.png"
    registro = Path(tempfile.gettempdir()) / f"imaginteca-w2x-{os.getpid()}.log"
    cmd = [str(exe), "-i", str(path), "-o", str(salida), "-s", str(objetivo),
           "-m", "models-upconv_7_anime_style_art_rgb", "-n", "1", "-f", "png"]
    gpu = str(getattr(config, "AI_GPU", "") or "").strip()
    # Sin GPU no se fuerza nada: este binario de waifu2x no admite -g -1 (crashea) y
    # Real-ESRGAN necesita Vulkan; si la IA no puede, se sigue con Lanczos.
    if gpu:
        cmd += ["-g", gpu]
    try:
        with open(registro, "wb") as manejador:
            subprocess.run(cmd, stdout=manejador, stderr=subprocess.STDOUT, timeout=1800,
                           check=True, cwd=str(exe.parent))
    except Exception as exc:  # noqa: BLE001
        logger.info("waifu2x no pudo ampliar la imagen: %s", exc)
        return None
    finally:
        try:
            registro.unlink()
        except OSError:
            pass
    try:
        with Image.open(salida) as im:
            im.load()
            if im.width < w or im.height < h:
                return None
        global _ULTIMO_MOTOR
        _ULTIMO_MOTOR = "waifu2x"
        return salida
    except Exception:  # noqa: BLE001
        return None


def fabricante_gpu() -> str:
    """Fabricante de la tarjeta principal (NVIDIA, AMD/ATI, Intel…) o vacío."""
    nombres = " ".join(gpus_detectadas()).lower()
    if "nvidia" in nombres:
        return "NVIDIA"
    if "amd" in nombres or "ati" in nombres or "radeon" in nombres:
        return "AMD/ATI"
    if "intel" in nombres:
        return "Intel"
    return ""

def _ai_upscale(path: Path, factor: int, tamano: tuple[int, int]) -> Path | None:
    """Upscaling IA con motor Vulkan. Devuelve la ruta del PNG o None si falla.

    `realesrgan-x4plus*` es x4 nativo: usarlo con -s 2/3 corrompe la imagen, así
    que para 2x/3x se usa el modelo multiescala `realesr-animevideov3`, con
    respaldo "x4 → reducir". Cada intento se valida antes de aceptarse.
    """
    motor = str(getattr(config, "AI_ENGINE", "auto") or "auto").lower()
    if motor in ("torch", "cuda", "dml", "tensorrt", "trt"):
        return _ai_torch(path, factor, tamano)
    # Cadena de motores: auto -> Real-ESRGAN y, si falla, waifu2x. Los dos son Vulkan.
    if motor in ("waifu2x", "auto"):
        if motor == "waifu2x":
            return _ai_waifu2x(path, factor, tamano)
    exe = _find_ai_exe()
    if exe is None:
        logger.info("IA: no se encontró Real-ESRGAN; se prueba waifu2x")
        return _ai_waifu2x(path, factor, tamano)
    Image, _ = _pillow()
    with Image.open(path) as im:
        w, h = im.size

    if (w * factor) * (h * factor) > getattr(config, "AI_MAX_PIXELS", 50_000_000):
        return None  # demasiado grande para la GPU: se usará Lanczos

    out_dir = path.parent / ".ai_tmp"
    out_dir.mkdir(exist_ok=True)

    modelo_escala = getattr(config, "AI_MODEL_ESCALA", "realesr-animevideov3")
    modelo_x4 = config.AI_MODEL
    intentos: list[tuple[int, str | None, bool]] = []
    if factor in (2, 3):
        intentos.append((factor, modelo_escala, False))
        intentos.append((4, modelo_x4, True))
        intentos.append((4, None, True))
    else:
        intentos.append((4, modelo_x4, False))
        intentos.append((4, modelo_escala, False))
        intentos.append((4, None, False))

    for escala, modelo, reducir in intentos:
        etiqueta = f"{escala}x" + (f"_{modelo}" if modelo else "")
        salida = out_dir / f"{path.stem}_ai_{etiqueta}.png"
        resultado = _ejecutar_ia(exe, path, salida, escala, modelo, w, h)
        if resultado is None:
            try:
                salida.unlink()
            except OSError:
                pass
            continue
        if reducir or resultado != tamano:
            # refinado final: tamaño objetivo + afilado suave de IA
            refinado = out_dir / f"{path.stem}_ai_final.png"
            with Image.open(resultado) as im:
                rgb = im.convert("RGB")
                if rgb.size != tamano:
                    rgb = rgb.resize(tamano, Image.Resampling.LANCZOS)
                rgb = _afilar(rgb, config.SHARPEN_AI, radio=1.5, umbral=2)
                rgb.save(refinado, "PNG")
            try:
                resultado.unlink()
            except OSError:
                pass
            final = refinado
        else:
            final = resultado

        # LIMPIEZA DE COLOR: el modelo desplaza un poco los canales; se devuelve la
        # paleta a la del original para que la mejora no cambie el color de la obra.
        desfases = _corregir_paleta(path, final)
        if desfases is not None:
            logger.info("paleta de la salida IA corregida al original (R%+d G%+d B%+d)",
                        desfases[0], desfases[1], desfases[2])
        return final
    return None


# ------------------------------------------------------------------ guardado y verificación
def _guardar_webp(origen: Path, destino: Path, calidad: int, tenia_alfa: bool,
                  sin_perdida: bool = False) -> tuple[int, int]:
    """Convierte a WebP respetando la transparencia. Devuelve el tamaño guardado.

    `sin_perdida` se usa cuando la imagen es plana (capturas, dibujos de línea, fondos
    lisos): ahí la compresión con pérdida deja manchas y bordes sucios, así que se guarda
    sin pérdida, que además suele ocupar menos en ese tipo de imágenes.
    """
    Image, _ = _pillow()
    with Image.open(origen) as im:
        opciones: dict = {"method": 6}
        if sin_perdida:
            opciones["lossless"] = True
            opciones["quality"] = 100
        else:
            opciones["quality"] = calidad
        if _tiene_alfa(im):
            final = im.convert("RGBA")
            _guardar_con_reintento(final, destino, exact=True, **opciones)
        else:
            final = im.convert("RGB")
            _guardar_con_reintento(final, destino, **opciones)
        return final.width, final.height


def _guardar_con_reintento(imagen, destino: Path, **opciones) -> None:
    """Guarda el .webp reintentando si el archivo está ocupado un instante.

    La galería abre la imagen en cuanto aparece y, con «Modo IA», el proceso tarda
    segundos: es fácil que Windows rechace la escritura justo entonces con
    «OSError [Errno 22] Invalid argument». Se reintenta con una pausa breve: al segundo
    intento el archivo ya está libre y se guarda la imagen mejorada de verdad.
    """
    ultimo: Exception | None = None
    for intento in range(1, 4):
        try:
            imagen.save(destino, "WEBP", **opciones)
            return
        except OSError as exc:
            ultimo = exc
            logger.info("no se pudo guardar %s (intento %d/3): %s",
                        Path(destino).name, intento, exc)
            time.sleep(0.35)
    raise ultimo if ultimo is not None else OSError("no se pudo guardar el WebP")


def _webp_valido(destino: Path, esperado: tuple[int, int]) -> bool:
    """Verifica que el .webp abre correctamente y tiene el tamaño esperado."""
    try:
        Image, _ = _pillow()
        with Image.open(destino) as im:
            im.load()
            return im.size == esperado
    except Exception:  # noqa: BLE001
        return False


# ------------------------------------------------------------------ entrada principal
def postprocess(path: Path, settings: dict) -> tuple[Path, dict]:
    """Aplica la política de calidad a un archivo descargado.

    - SIEMPRE acaba en .webp (o conserva el original si algo falla).
    - Respeta la transparencia y nunca deja corrupciones ni artefactos.
    - El flag "mejorar" controla el upscaling y la definición.

    Devuelve (ruta_final, metadata). Lanza ImagenCorruptaError si el archivo
    descargado no es una imagen válida.
    """
    Image, _ = _pillow()
    calidad = max(1, min(100, int(settings.get("calidad_webp") or config.WEBP_QUALITY_DEFAULT)))
    mejorar = bool(settings.get("mejorar"))
    modo_ia = bool(settings.get("modo_ia"))

    # El .webp conserva el nombre original aunque haya que recuperar el archivo
    ruta_original = path
    # 1) Validación del archivo descargado (detecta truncados/corruptos)
    meta_recuperada = False
    try:
        with _abrir_verificada(path) as im:
            w, h = im.size
            tiene_alfa = _tiene_alfa(im)
    except ImagenCorruptaError as exc:
        # Antes de descartarla, se intenta RECUPERAR lo que llegó (muchos «corruptos» son
        # archivos cortados a los que les falta el final). Si se recupera, se repara y se
        # guarda en WebP como cualquier otra: no se entrega nada en mal estado.
        recuperada = control_calidad.recuperar_danada(path.read_bytes())
        if recuperada is None:
            raise
        logger.warning("imagen dañada recuperada parcialmente: %s (%s)", path.name, exc)
        base_recuperada = path.parent / ".tmp_upscale" / f"{path.stem}.recuperada.png"
        base_recuperada.parent.mkdir(exist_ok=True)
        try:
            recuperada.save(base_recuperada, "PNG")
        except Exception:  # noqa: BLE001
            raise exc
        path = base_recuperada
        w, h = recuperada.size
        tiene_alfa = _tiene_alfa(recuperada)
        meta_recuperada = True
    except Exception as exc:  # noqa: BLE001
        raise ImagenCorruptaError(f"no se pudo leer la imagen descargada: {exc}") from exc

    # El factor se decide por el ANCHO (no por el alto): así una imagen vertical
    # también llega al ancho mínimo, que es lo que se nota en la calidad final.
    factor = factor_for(w) if mejorar else 1
    ancho_obj, alto_obj, escala_real = _tamano_objetivo(w, h, factor)
    tamano = (ancho_obj, alto_obj)
    # El análisis fino y la reparación se hacen DESPUÉS de reescalar (ver más abajo):
    # primero se amplía según la resolución y luego se mide y se arregla el resultado.
    parametros = control_calidad.parametros_webp(None, calidad)
    meta: dict = {
        "original_px": f"{w}x{h}",
        "factor": factor,
        "escala_real": round(escala_real, 3),
        "modo": "",
        "calidad_webp": parametros["quality"],
        "transparencia": tiene_alfa,
        "calidad": "",
        "calidad_detalle": "",
        "sin_perdida": parametros["lossless"],
        "reparacion": "",
    }
    if meta_recuperada:
        meta["reparacion"] = "archivo dañado recuperado"

    out = ruta_original.with_suffix(".webp")
    dir_tmp = path.parent / ".tmp_upscale"
    temporales: list[Path] = []
    esperado = (w, h)
    mejorada: Path | None = None
    origen = path

    try:
        if factor > 1:
            dir_tmp.mkdir(exist_ok=True)
            base_upscale, alfa_path = _preparar_para_upscale(origen, dir_tmp)
            if base_upscale != path:
                temporales.append(base_upscale)
            if alfa_path is not None:
                temporales.append(alfa_path)

            if modo_ia:
                ai_out = _ai_upscale(base_upscale, factor, tamano)
                if ai_out is not None:
                    temporales.append(ai_out)
                    mejorada = ai_out
                    meta["modo"] = f"IA {factor}x"
                    if _ULTIMO_MOTOR:
                        meta["modo"] += f" ({_ULTIMO_MOTOR})"
                    gpus = gpus_detectadas()
                    logger.info("IA: modelo %s · GPU detectada: %s", config.AI_MODEL,
                                ", ".join(gpus) if gpus else "(no detectada)")
                    meta["ia_gpu"] = ", ".join(gpus) if gpus else ""
                else:
                    demasiado_grande = (
                        (w * factor) * (h * factor)
                        > getattr(config, "AI_MAX_PIXELS", 50_000_000)
                    )
                    mejorada = _lanczos_upscale(base_upscale, tamano)
                    temporales.append(mejorada)
                    if demasiado_grande:
                        meta["modo"] = f"Lanczos {factor}x (IA omitida: imagen muy grande)"
                    else:
                        meta["modo"] = (f"Lanczos {factor}x "
                                        "(IA no disponible: mira el registro)")
                        meta["ia_fallida"] = True
            else:
                mejorada = _lanczos_upscale(base_upscale, tamano)
                temporales.append(mejorada)
                meta["modo"] = f"Lanczos {factor}x"

            # devolver el canal alfa reescalado a la imagen mejorada
            if alfa_path is not None:
                con_alfa = dir_tmp / f"{path.stem}.rgba.png"
                _recomponer_alfa(mejorada, alfa_path, con_alfa)
                temporales.append(con_alfa)
                mejorada = con_alfa
        elif mejorar:
            meta["modo"] = "solo WebP (sin upscale)"
        else:
            meta["modo"] = "WebP directo (mejora desactivada)"

        # 3) ANÁLISIS Y REPARACIÓN, ya DESPUÉS del reescalado.
        #    Primero se amplía según la resolución (IA o Lanczos) y luego se mide el
        #    resultado y se arregla: ruido, bloques de compresión y falta de nitidez.
        #    Así el reenfoque actúa sobre la imagen final (antes, al revés, el reescalado
        #    volvía a difuminar lo poco que se había arreglado).
        analisis = None
        if mejorada is not None:
            origen = mejorada
        # Reenfoque final: un reescalado grande (sobre todo Lanczos 8x-16x) deja la imagen
        # blanda. Se aplica un afilado suave proporcional al aumento, y más flojo si la IA
        # ya ha aportado detalle (para no crear halos).
        if mejorar and factor > 1 and getattr(config, "AFILAR_TRAS_ESCALAR", True):
            try:
                ImageA, _ = _pillow()
                with ImageA.open(origen) as abierta:
                    abierta.load()
                    imagen_afilada = abierta.convert(
                        "RGBA" if _tiene_alfa(abierta) else "RGB")
                intensidad = (max(20, min(60, 20 + 8 * factor)) if (modo_ia and mejorada)
                              else max(30, min(120, 20 + 8 * factor)))
                imagen_afilada = _afilar(imagen_afilada, intensidad, radio=1.4, umbral=2)
                dir_tmp.mkdir(exist_ok=True)
                afilada = dir_tmp / f"{path.stem}.afilada.png"
                imagen_afilada.save(afilada, "PNG")
                temporales.append(afilada)
                origen = afilada
                meta["reparacion"] = (meta["reparacion"] + "; " if meta["reparacion"]
                                      else "") + f"realfinado final ({intensidad}%)"
                logger.info("realfinado %s tras el reescalado (%d%%)", path.name, intensidad)
            except Exception:  # noqa: BLE001
                logger.debug("no se pudo afilar %s", path.name, exc_info=True)
        if getattr(config, "CALIDAD_ANALISIS", True):
            try:
                analisis = control_calidad.analizar(origen)
                logger.info("calidad tras el reescalado de %s: %s", path.name,
                            analisis.como_texto())
            except Exception:      # noqa: BLE001
                logger.debug("no se pudo analizar la calidad de %s", path.name, exc_info=True)
                analisis = None
        if analisis is not None and analisis.valida:
            parametros = control_calidad.parametros_webp(analisis, calidad)
            meta["calidad"] = analisis.veredicto
            meta["calidad_detalle"] = analisis.como_texto()
            meta["sin_perdida"] = parametros["lossless"]
            meta["calidad_webp"] = parametros["quality"]
            if analisis.problemas:
                try:
                    Image3, _ = _pillow()
                    with Image3.open(origen) as abierta:
                        abierta.load()
                        arreglada, hechos = control_calidad.reparar(abierta, analisis)
                    dir_tmp.mkdir(exist_ok=True)
                    reparada = dir_tmp / f"{path.stem}.reparada.png"
                    arreglada.save(reparada, "PNG")
                    temporales.append(reparada)
                    origen = reparada
                    meta["reparacion"] = ((meta["reparacion"] + "; ") if meta["reparacion"] else "") + "; ".join(hechos)
                    logger.info("reparada %s tras el reescalado: %s", path.name,
                                meta["reparacion"])
                except Exception:  # noqa: BLE001
                    logger.debug("no se pudo reparar %s", path.name, exc_info=True)

        esperado = _guardar_webp(origen, out, parametros["quality"], tiene_alfa,
                                 parametros["lossless"])
    except Exception:  # noqa: BLE001
        # Cualquier fallo en la mejora → conversión directa (segura, sin artefactos)
        logger.exception("mejora fallida; se aplica conversión directa a WebP")
        meta["factor"] = 1
        meta["escala_real"] = 1.0
        meta["modo"] = "WebP directo (mejora fallida; se conserva la calidad original)"
        try:
            esperado = _guardar_webp(origen, out, parametros["quality"], tiene_alfa, parametros["lossless"])
        except Exception:  # noqa: BLE001
            logger.exception("tampoco se pudo convertir a WebP: se descarta la imagen")
            raise ImagenCorruptaError("no se pudo convertir la imagen a WebP")
    finally:
        for tmp in temporales:
            try:
                tmp.unlink()
            except OSError:
                pass
        for extra in (dir_tmp, path.parent / ".ai_tmp"):
            try:
                if extra.is_dir() and not any(extra.iterdir()):
                    extra.rmdir()
            except OSError:
                pass

    # 3) Verificación final: el .webp debe abrir y tener el tamaño esperado
    if getattr(config, "VERIFY_OUTPUT", True) and not _webp_valido(out, esperado):
        logger.warning("el WebP resultante no pasó la verificación: %s", out)
        try:
            esperado2 = _guardar_webp(origen, out, parametros["quality"], tiene_alfa, parametros["lossless"])
            if not _webp_valido(out, esperado2):
                raise ValueError("WebP inválido tras el reintento")
        except Exception:  # noqa: BLE001
            logger.error("no se pudo generar un WebP válido: se descarta la imagen")
            try:
                out.unlink()
            except OSError:
                pass
            raise ImagenCorruptaError("el WebP resultante no es válido")

    meta["resultado_px"] = f"{esperado[0]}x{esperado[1]}"

    # 4) REQUISITO: el original nunca se conserva (solo tras verificar el .webp)
    if out != path:
        try:
            path.unlink()
        except OSError:
            pass
    return out, meta


def resumen_mejora(meta: dict | None) -> str:
    """Texto corto y VERIFICABLE de lo que se hizo con la imagen.

    Es lo que se muestra en la barra de estado y se registra en el .log, para que
    no haya que adivinar si la mejora se aplicó: deja ver el tamaño de partida, el
    resultado real y el método.

        «153x153 → 612x612 · Lanczos 4x · ⚠ origen pequeño (153 px)»

    Sin esto, un «Lanczos 4x» sobre una imagen diminuta parece un fallo cuando en
    realidad se aplicó la regla: lo que pasa es que el ORIGEN era muy pequeño.
    """
    meta = meta or {}
    origen = str(meta.get("original_px") or "").strip()
    destino = str(meta.get("resultado_px") or "").strip()
    modo = str(meta.get("modo") or "").strip()

    partes = []
    if origen and destino:
        partes.append(f"{origen} → {destino}")
    elif destino:
        partes.append(destino)
    if modo:
        partes.append(modo)
    texto = " · ".join(partes) if partes else "sin mejora"

    try:
        medidas = [int(valor) for valor in origen.lower().split("x")]
        lado = max(medidas)
        ancho_origen = medidas[0]      # la regla de reescalado se basa en el ANCHO
    except (ValueError, AttributeError, IndexError):
        lado = 0
        ancho_origen = 0
    # Aviso cuando el resultado es una AMPLIACIÓN de un original pequeño: da igual el
    # adaptador (DeviantArt, Bluesky, boorus…). Antes solo avisaba por debajo de 300 px y
    # un original de 426 px ampliado 4x salía blando sin ninguna explicación.
    umbral = int(getattr(config, "AVISO_ORIGEN_PEQUENO", 300) or 0)
    factor = 1
    coincidencia = re.search(r"(\d+)\s*x", modo.lower())
    if coincidencia:
        try:
            factor = int(coincidencia.group(1))
        except ValueError:
            factor = 1
    if ancho_origen and (ancho_origen < umbral or (factor >= 3 and ancho_origen < 700)):
        texto += (f" · ⚠ origen pequeño ({ancho_origen} px de ancho, ampliado {factor}x: "
                  "se verá más suave)" if factor > 1
                  else f" · ⚠ origen pequeño ({ancho_origen} px, poco detalle real)")
    return texto
