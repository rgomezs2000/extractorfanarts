"""Advertencias de contenido (content warnings) y si una imagen es NSFW.

Cada plataforma lo cuenta a su manera, así que aquí se reunen las señales conocidas de
los **fediversos** (Mastodon: `sensitive` + `spoiler_text`), los **boorus** (rating
`questionable`/`explicit`, `is_flagged`, `flagged`…), **Pixiv** (`x_restrict`, `sexual`),
**X/Twitter** (`possibly_sensitive`) y similares.

Se distinguen dos cosas:

  · **NSFW / adulto**: la clasificación lo es (`questionable`/`explicit`) o la plataforma lo
    marca así (Pixiv `x_restrict`, `sexual`, `is_mature`…). Las imágenes **SFW no se
    marcan**: ni adulto ni advertencia.
  · **Advertencias**: lo que la persona o la plataforma añaden **encima** de eso —
    el aviso de contenido (`spoiler_text`), «marcada como sensible», «oculta por la
    plataforma» o «marcada por moderación».

Con eso, en **Propiedades** se añaden dos apartados propios (cuando amerita) y en la
búsqueda/descarga se puede pedir que **se omitan las que traen advertencias**.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("imaginteca")

# Valores de `rating` que ya son adultos
RATINGS_ADULTOS = ("questionable", "explicit")

# Campos de texto que llevan un aviso de contenido
_CAMPOS_AVISO = ("spoiler_text", "content_warning", "contentwarnings", "warning",
                 "warnings", "advisory", "advisories", "notice")

# Campos que marcan la imagen como sensible/oculta/moderada (advertencia)
_CAMPOS_FLAG_AVISO = ("is_flagged", "flagged", "is_banned", "is_masked", "masked",
                      "hidden", "deprecated", "moderation", "is_sensitive")

# Campos que indican adulto (además del rating)
_CAMPOS_FLAG_ADULTO = ("is_mature", "mature", "nsfw", "adult", "is_adult",
                       "possibly_sensitive", "sexual", "sensitive")


def _datos(obra) -> dict:
    return obra.raw if isinstance(obra.raw, dict) else {}


def _texto(valor) -> str:
    if isinstance(valor, (list, tuple)):
        return "; ".join(str(v).strip() for v in valor if str(v).strip())
    return str(valor).strip() if valor not in (None, "") else ""


def es_adulto(obra) -> bool:
    """¿La imagen es NSFW? (por clasificación o por las marcas de la plataforma)."""
    if str(getattr(obra, "rating", "") or "").lower() in RATINGS_ADULTOS:
        return True
    datos = _datos(obra)
    for campo in _CAMPOS_FLAG_ADULTO:
        if campo not in datos:
            continue
        valor = datos.get(campo)
        if campo == "sensitive" and valor in (False, None, ""):
            continue
        if campo == "x_restrict":
            try:
                if int(valor) > 0:
                    return True
            except (TypeError, ValueError):
                continue
            continue
        if valor and valor not in ("0", "false", "False", 0, False):
            return True
    if datos.get("x_restrict"):
        try:
            return int(datos["x_restrict"]) > 0
        except (TypeError, ValueError):
            pass
    return False


def advertencias(obra) -> list[tuple[str, str]]:
    """[(título del aviso, detalle), …] tal como se muestran en Propiedades."""
    datos = _datos(obra)
    avisos: list[tuple[str, str]] = []

    texto_aviso = ""
    for campo in _CAMPOS_AVISO:
        if datos.get(campo):
            texto_aviso = _texto(datos[campo])
            if texto_aviso:
                break
    if texto_aviso:
        avisos.append(("Aviso de contenido", texto_aviso))

    if datos.get("sensitive") and str(getattr(obra, "rating", "")).lower() not in ("explicit",):
        avisos.append(("Marcada como sensible", "sí"))

    for campo, etiqueta in (("is_flagged", "Marcada por moderación"),
                            ("flagged", "Marcada por moderación"),
                            ("is_banned", "Retirada por la plataforma"),
                            ("is_masked", "Oculta por la plataforma"),
                            ("masked", "Oculta por la plataforma")):
        if datos.get(campo):
            avisos.append((etiqueta, "sí"))
            break

    return avisos


def tiene_advertencias(obra) -> bool:
    """¿Trae alguna advertencia? (para el filtro de búsqueda/descarga)."""
    return bool(advertencias(obra))


def resumen(obra) -> str:
    """Frase corta para la cabecera: «adulto (NSFW)» o vacío si es SFW."""
    if not es_adulto(obra):
        return ""
    motivo = str(getattr(obra, "rating", "") or "").strip()
    avisos = advertencias(obra)
    extra = f" · {len(avisos)} advertencia(s)" if avisos else ""
    return f"adulto (NSFW){f' · clasificación: {motivo}' if motivo else ''}{extra}"
