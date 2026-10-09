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
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .. import config
from .http_client import ConfigError

logger = logging.getLogger("imaginteca")


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


def factor_for(longest: int) -> int:
    """Factor de upscaling según el lado mayor (reglas de UPSCALE_BUCKETS)."""
    for low, high, factor in config.UPSCALE_BUCKETS:
        if low <= longest <= high:
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
    return salida


def _ai_upscale(path: Path, factor: int, tamano: tuple[int, int]) -> Path | None:
    """Upscaling IA con motor Vulkan. Devuelve la ruta del PNG o None si falla.

    `realesrgan-x4plus*` es x4 nativo: usarlo con -s 2/3 corrompe la imagen, así
    que para 2x/3x se usa el modelo multiescala `realesr-animevideov3`, con
    respaldo "x4 → reducir". Cada intento se valida antes de aceptarse.
    """
    exe = _find_ai_exe()
    if exe is None:
        return None
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
def _guardar_webp(origen: Path, destino: Path, calidad: int, tenia_alfa: bool) -> tuple[int, int]:
    """Convierte a WebP respetando la transparencia. Devuelve el tamaño guardado."""
    Image, _ = _pillow()
    with Image.open(origen) as im:
        if _tiene_alfa(im):
            final = im.convert("RGBA")
            final.save(destino, "WEBP", quality=calidad, method=6, exact=True)
        else:
            final = im.convert("RGB")
            final.save(destino, "WEBP", quality=calidad, method=6)
        return final.width, final.height


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

    # 1) Validación del archivo descargado (detecta truncados/corruptos)
    try:
        with _abrir_verificada(path) as im:
            w, h = im.size
            tiene_alfa = _tiene_alfa(im)
    except ImagenCorruptaError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ImagenCorruptaError(f"no se pudo leer la imagen descargada: {exc}") from exc

    longest = max(w, h)
    factor = factor_for(longest) if mejorar else 1
    ancho_obj, alto_obj, escala_real = _tamano_objetivo(w, h, factor)
    tamano = (ancho_obj, alto_obj)
    meta: dict = {
        "original_px": f"{w}x{h}",
        "factor": factor,
        "escala_real": round(escala_real, 3),
        "modo": "",
        "calidad_webp": calidad,
        "transparencia": tiene_alfa,
    }

    out = path.with_suffix(".webp")
    dir_tmp = path.parent / ".tmp_upscale"
    temporales: list[Path] = []
    esperado = (w, h)
    mejorada: Path | None = None

    try:
        if factor > 1:
            dir_tmp.mkdir(exist_ok=True)
            base_upscale, alfa_path = _preparar_para_upscale(path, dir_tmp)
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

        if mejorada is not None:
            esperado = _guardar_webp(mejorada, out, calidad, tiene_alfa)
        else:
            esperado = _guardar_webp(path, out, calidad, tiene_alfa)
    except Exception:  # noqa: BLE001
        # Cualquier fallo en la mejora → conversión directa (segura, sin artefactos)
        logger.exception("mejora fallida; se aplica conversión directa a WebP")
        meta["factor"] = 1
        meta["escala_real"] = 1.0
        meta["modo"] = "WebP directo (mejora fallida; se conserva la calidad original)"
        try:
            esperado = _guardar_webp(path, out, calidad, tiene_alfa)
        except Exception:  # noqa: BLE001
            logger.exception("tampoco se pudo convertir a WebP; se conserva el original")
            meta["modo"] += " | ERROR: no se pudo generar el WebP"
            return path, meta
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
            esperado2 = _guardar_webp(path, out, calidad, tiene_alfa)
            if not _webp_valido(out, esperado2):
                raise ValueError("WebP inválido tras el reintento")
        except Exception:  # noqa: BLE001
            logger.error("no se pudo generar un WebP válido; se conserva el original")
            try:
                out.unlink()
            except OSError:
                pass
            meta["modo"] += " | ERROR: WebP no válido (se conserva el original)"
            return path, meta

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
        lado = max(int(valor) for valor in origen.lower().split("x"))
    except (ValueError, AttributeError):
        lado = 0
    if lado and lado < getattr(config, "AVISO_ORIGEN_PEQUENO", 300):
        texto += f" · ⚠ origen pequeño ({lado} px, poco detalle real)"
    return texto
