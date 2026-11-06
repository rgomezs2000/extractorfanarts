"""Sugerencias de tags de los boorus (biblioteca real de cada sitio, con categoría).

Cada booru publica su lista de etiquetas y la categoría de cada una. Se usa para el
autocompletado del campo de tags:

  · Gelbooru / Rule34 / Safebooru (familia gelbooru): `page=dapi&s=tag&q=index`
    con `name_pattern=prefijo%`. Devuelve JSON (Gelbooru) o XML (los demás).
  · Danbooru (familia danbooru): `/tags.json?search[name_matches]=prefijo*`.

Categorías normalizadas: general, artist, copyright, character, meta.
"""
from __future__ import annotations

import logging
import urllib.parse
import xml.etree.ElementTree as ET

from .. import config

logger = logging.getLogger("imaginteca")

# Códigos de categoría que usan Danbooru y la familia Gelbooru
_CATEGORIAS = {
    0: "general",
    1: "artist",
    3: "copyright",
    4: "character",
    5: "meta",
    6: "meta",        # «deprecated» se muestra como meta
}

MAX_SUGERENCIAS = 12


def _categoria(valor) -> str:
    try:
        return _CATEGORIAS.get(int(valor), "general")
    except (TypeError, ValueError):
        return "general"


def sitio_de(plataforma: str) -> dict | None:
    for sitio in getattr(config, "BOORU_SITES", []):
        if str(sitio.get("name")) == str(plataforma):
            return sitio
    return None


def credenciales(sitio: dict) -> dict:
    """Parámetros de autenticación del sitio, si los tiene."""
    auth = sitio.get("auth")
    if not isinstance(auth, dict):
        return {}
    salida = {}
    for campo in ("api_key", "user_id", "login"):
        valor = str(auth.get(campo) or "").strip()
        if valor:
            salida[campo] = valor
    return salida


def _familias(sitio: dict) -> tuple[str, str]:
    return str(sitio.get("base") or "").rstrip("/"), str(sitio.get("family") or "").lower()


def _limpiar(nombre) -> str:
    return str(nombre or "").strip().lower()


# ------------------------------------------------------------------ familias con API
FAMILIAS_CON_API = ("gelbooru", "danbooru", "moebooru", "philomena")


def soporta(plataforma: str) -> bool:
    """¿Este booru publica su lista de etiquetas? (Shimmie no, por ejemplo)."""
    sitio = sitio_de(plataforma)
    if sitio is None:
        return False
    return str(sitio.get("family") or "").lower() in FAMILIAS_CON_API


def url_para(plataforma: str, prefijo: str, limite: int = MAX_SUGERENCIAS) -> str:
    """URL de consulta de etiquetas para esa plataforma ("" si no hay API)."""
    import urllib.parse

    sitio = sitio_de(plataforma)
    if sitio is None:
        return ""
    base = str(sitio.get("base") or "").rstrip("/")
    familia = str(sitio.get("family") or "").lower()
    credenciales = credenciales_de(sitio)
    prefijo = _limpiar(prefijo).replace(" ", "_")
    if familia == "danbooru":
        consulta = {
            "search[name_matches]": f"{prefijo}*",
            "search[order]": "count",
            "limit": str(limite),
            **credenciales,
        }
        return f"{base}/tags.json?" + urllib.parse.urlencode(consulta)
    if familia == "moebooru":
        consulta = {"name": prefijo, "limit": str(limite), **credenciales}
        return f"{base}/tag.json?" + urllib.parse.urlencode(consulta)
    if familia == "philomena":
        consulta = {"q": prefijo, "limit": str(limite), **credenciales}
        return f"{base}/api/v1/json/search/tags?" + urllib.parse.urlencode(consulta)
    if familia == "gelbooru":
        consulta = {
            "page": "dapi", "s": "tag", "q": "index", "json": "1",
            "name_pattern": f"{prefijo}%", "limit": str(limite),
            **credenciales,
        }
        return f"{base}/index.php?" + urllib.parse.urlencode(consulta)
    return ""


def credenciales_de(sitio: dict) -> dict:
    """Alias público de las credenciales del sitio."""
    return credenciales(sitio)


def interpretar(texto: str, plataforma: str = "", limite: int = MAX_SUGERENCIAS) -> list[dict]:
    """Lee la respuesta (JSON de cualquier familia o XML de los clones de Gelbooru)."""
    familia = ""
    sitio = sitio_de(plataforma) if plataforma else None
    if sitio is not None:
        familia = str(sitio.get("family") or "").lower()
    if familia == "philomena":
        filas = _desde_philomena(texto, limite)
        if filas:
            return filas
    filas = desde_json(texto, limite)
    if filas:
        return filas
    return desde_xml(texto, limite)


def _desde_philomena(texto: str, limite: int) -> list[dict]:
    import json

    try:
        datos = json.loads(texto)
    except (ValueError, TypeError):
        return []
    filas = datos.get("tags") if isinstance(datos, dict) else datos
    if not isinstance(filas, list):
        return []
    salida = []
    for fila in filas[:limite]:
        if not isinstance(fila, dict):
            continue
        nombre = _limpiar(fila.get("name"))
        if not nombre:
            continue
        categoria = str(fila.get("category") or "").strip().lower()
        categorias = {"general", "artist", "copyright", "character", "meta", "oc"}
        if categoria not in categorias:
            categoria = "general"
        if categoria == "oc":
            categoria = "meta"
        salida.append({"tag": nombre, "categoria": categoria})
    return salida


def sugerir(cliente, plataforma: str, prefijo: str,
            limite: int = MAX_SUGERENCIAS) -> list[dict]:
    """Etiquetas que empiezan por `prefijo` en la biblioteca de ese booru."""
    prefijo = _limpiar(prefijo).replace(" ", "_")
    if len(prefijo) < 2:
        return []
    url = url_para(plataforma, prefijo, limite)
    if not url:
        logger.info("autocompletado: %s no publica lista de etiquetas", plataforma)
        return []
    try:
        try:
            texto = cliente.get_text(url)
        except AttributeError:
            datos = cliente.get_json(url)
            texto = __import__("json").dumps(datos)
        return interpretar(texto, plataforma, limite)
    except Exception as exc:  # noqa: BLE001
        logger.info("autocompletado: %s no respondió (%s)", plataforma, exc)
        return []


# ------------------------------------------------------------------ familia gelbooru
def _gelbooru(cliente, base: str, sitio: dict, prefijo: str, limite: int) -> list[dict]:
    """Familia Gelbooru: unos responden JSON (Gelbooru) y otros XML (Rule34, Safebooru)."""
    params = {
        "page": "dapi", "s": "tag", "q": "index", "json": "1",
        "name_pattern": f"{prefijo}%", "limit": str(limite),
        **credenciales(sitio),
    }
    url = f"{base}/index.php"
    try:
        datos = cliente.get_json(url, params=params)
    except Exception:  # noqa: BLE001
        datos = None
    if isinstance(datos, dict):
        filas = datos.get("tag") or datos.get("tags") or []
        if isinstance(filas, dict):
            filas = [filas]
        salida = [
            {"tag": _limpiar(f.get("name")), "categoria": _categoria(f.get("type"))}
            for f in filas if isinstance(f, dict) and f.get("name")
        ]
        if salida:
            return salida[:limite]
    # Los clones devuelven XML aunque se pida JSON: se lee tal cual.
    try:
        texto = cliente.get_text(url, params=params)
        return desde_xml(texto, limite)
    except Exception as exc:  # noqa: BLE001
        logger.info("autocompletado: XML no disponible en %s (%s)", base, exc)
        return []


# ------------------------------------------------------------------ familia danbooru
def _danbooru(cliente, base: str, sitio: dict, prefijo: str, limite: int) -> list[dict]:
    params = {
        "search[name_matches]": f"{prefijo}*",
        "search[order]": "count",
        "limit": str(limite),
        **credenciales(sitio),
    }
    datos = cliente.get_json(f"{base}/tags.json", params=params)
    if isinstance(datos, list):
        return [
            {"tag": _limpiar(f.get("name")), "categoria": _categoria(f.get("category"))}
            for f in datos if isinstance(f, dict) and f.get("name")
        ][:limite]
    return []


# ------------------------------------------------------------------ XML (algunos clones)
def desde_xml(texto: str, limite: int = MAX_SUGERENCIAS) -> list[dict]:
    """Lee la respuesta XML de los clones de Gelbooru (`<tag name= type=>`)."""
    try:
        raiz = ET.fromstring(texto)
    except ET.ParseError:
        return []
    salida = []
    for nodo in raiz.findall("tag")[:limite]:
        nombre = _limpiar(nodo.get("name"))
        if nombre:
            salida.append({"tag": nombre, "categoria": _categoria(nodo.get("type"))})
    return salida


def url_de_consulta(plataforma: str, prefijo: str) -> str:
    """URL que se consulta (para el registro/diagnóstico)."""
    sitio = sitio_de(plataforma)
    if sitio is None:
        return ""
    base, familia = _familias(sitio)
    if familia == "danbooru":
        return f"{base}/tags.json?search[name_matches]={urllib.parse.quote(prefijo)}*"
    return f"{base}/index.php?page=dapi&s=tag&q=index&name_pattern={urllib.parse.quote(prefijo)}%"

def desde_json(texto: str, limite: int = MAX_SUGERENCIAS) -> list[dict]:
    """Lee la respuesta JSON: Gelbooru ({"tag": [...]}) o Danbooru (lista)."""
    import json

    try:
        datos = json.loads(texto)
    except (ValueError, TypeError):
        return []
    filas = datos
    if isinstance(datos, dict):
        filas = datos.get("tag") or datos.get("tags") or []
        if isinstance(filas, dict):
            filas = [filas]
    if not isinstance(filas, list):
        return []
    salida = []
    for fila in filas[:limite]:
        if not isinstance(fila, dict):
            continue
        nombre = _limpiar(fila.get("name"))
        if nombre:
            categoria = fila.get("type", fila.get("category"))
            salida.append({"tag": nombre, "categoria": _categoria(categoria)})
    return salida
