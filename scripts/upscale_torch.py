"""Motor de IA opcional por PyTorch: usa TU Python y hereda CUDA/DirectML/TensorRT/CPU.

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
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def dispositivo(torch, pedido: str):
    """Devuelve (dispositivo, nombre legible) según lo pedido y lo disponible."""
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
    """RRDBNet de Real-ESRGAN (paquete `realesrgan`)."""
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
