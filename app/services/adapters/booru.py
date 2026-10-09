"""Adaptador de boorus: familias Gelbooru (dapi), Danbooru, Moebooru, Philomena y Shimmie.

Plantilla replicable: cada sitio es una entrada de configuración (BOORU_SITES
en app/config.py); el mismo código sirve para Gelbooru, Rule34.xxx, Safebooru,
Danbooru, Yande.re, Konachan, Derpibooru, rule34.paheal.net y cualquier booru de
esas familias.

**N tags por búsqueda**: el campo de tags admite los que quieras
(`lori_loud 1girl solo blonde_hair`), se separan por espacios o comas y se buscan
**todos** a la vez (intersección, como hace el propio booru). Además se **verifican
en local** uno a uno sobre los tags del resultado (por si la familia no los combina
como esperamos) y, si la instancia limita cuántos tags acepta una consulta (Danbooru
anónimo admite 2), se consulta con los permitidos y **los demás se exigen en local**,
avisando en la línea de conexión.

**Shimmie** (rule34.paheal.net y compañía): estos tableros suelen traer la API pública
desactivada (en rule34.paheal.net, `/api/…` devuelve el HTML del sitio), así que se lee
su **listado público** (`/post/list/<tags>/<página>`), el mismo HTML que recibe el
navegador; de cada resultado se extraen las etiquetas, el id, el tipo MIME y el enlace
del archivo completo.
"""
from __future__ import annotations

import html as _html
import logging
import re
from urllib.parse import quote

from ... import config
from ...models.artwork import Artwork, SearchQuery
from ..http_client import BlockedError, ConfigError, PoliteClient, SinResultados
from .base import SearchAdapter, split_tags

logger = logging.getLogger("imaginteca")

# Señales de que el servidor rechazó la consulta por llevar demasiados tags
_LIMITE_TAGS_RE = re.compile(
    r"tag[s]?[^.]{0,60}(limit|more than|maximum|max\.?|too many|at a time)", re.IGNORECASE
)
# Cuántos tags se envían cuando la instancia limita la consulta (Danbooru anónimo: 2)
TAGS_SI_HAY_LIMITE = 2

# Credenciales que pide cada familia de software (ver _auth_params). Si una entrada de
# BOORU_SITES las declara y están vacías, se avisa diciendo cuál falta.
_CREDENCIALES_POR_FAMILIA = {
    "gelbooru": ("api_key", "user_id"),
    "danbooru": ("api_key", "login"),
    "moebooru": ("login", "password_hash"),
    "philomena": (),          # la api_key es opcional (solo sube el límite de peticiones)
}

_RATING_MAP = {
    "s": "general", "safe": "general", "g": "general",
    "sensitive": "sensitive", "q": "questionable", "questionable": "questionable",
    "e": "explicit", "explicit": "explicit",
}

# Extractor de imágenes: los posts de video/webm/zip se descartan en el adaptador.
_NON_IMAGE_EXTS = {".webm", ".mp4", ".zip", ".swf", ".mov", ".avi", ".mkv"}


def _is_video_name(name: str | None) -> bool:
    if not name:
        return False
    lowered = name.lower()
    return any(lowered.endswith(ext) for ext in _NON_IMAGE_EXTS)


def _norm_tag(tag: str) -> str:
    """Normaliza un tag para comparar (minúsculas y espacios como guiones bajos)."""
    return re.sub(r"\s+", "_", (tag or "").strip().lower().lstrip("#"))


def _es_tag_simple(tag: str) -> bool:
    """¿Es un tag normal (comprobable en los tags del resultado)?

    Los boorus admiten además *operadores*: exclusión (`-1girl`), metadatos
    (`rating:general`, `user:foo`, `score:>100`), comodines (`*hair`)… Esos no aparecen
    en la lista de tags del resultado, así que no se pueden verificar en local.
    """
    return not (not tag or tag.startswith("-") or re.search(r"[:<>=*~()|!]", tag))


def _tiene_todos(tags_del_post: list[str], pedidos: list[str]) -> bool:
    """¿El resultado lleva TODOS los tags simples pedidos? (se comprueba en local)"""
    simples = [p for p in pedidos if _es_tag_simple(p)]
    if not simples:
        return True
    presentes = {_norm_tag(t) for t in tags_del_post or []}
    return all(_norm_tag(p) in presentes for p in simples)


# Cada resultado de un tablero Shimmie viene en un bloque así (rule34.paheal.net):
#   <div class='shm-thumb thumb' data-mime='image/png' data-tags='1girl cute youtube'
#        data-post-id='7451852'>… <img id='thumb_7451852' … src='https://r34t…' />
#        … <a href='https://r34i.paheal-cdn.net/89/e1/89e1…'>File Only</a>
_INICIO_POST_SHIMMIE = re.compile(r"<div class=['\"]shm-thumb thumb['\"]", re.IGNORECASE)
_SHIMMIE_MIME = re.compile(r"data-mime='([^']*)'")
_SHIMMIE_TAGS = re.compile(r"data-tags='([^']*)'")
_SHIMMIE_ID = re.compile(r"data-post-id='(\d+)'")
_SHIMMIE_MINIATURA = re.compile(r"<img id='thumb_\d+'[^>]*?src='([^']+)'")
_SHIMMIE_ARCHIVO = re.compile(r"<a href='(https?://[^']+)'>File Only</a>")
_SHIMMIE_FECHA = re.compile(r"title='[^']*?(\d{4}-\d{2}-\d{2}T[\d:+\-]+)'")


def _parsear_shimmie(html: str) -> list[dict]:
    """Extrae los resultados del listado HTML de un tablero Shimmie.

    Devuelve diccionarios con id, etiquetas, tipo MIME, miniatura y archivo completo
    (los mismos datos que el navegador recibe en esa página). Cada resultado se delimita
    por el inicio de su bloque (`<div class='shm-thumb thumb' …>`), porque el nombre
    `shm-thumb` se repite dentro de un mismo resultado (`shm-thumb-link`).
    """
    if not html:
        return []
    marcas = [encontrado.start() for encontrado in _INICIO_POST_SHIMMIE.finditer(html)]
    salida: list[dict] = []
    for indice, inicio in enumerate(marcas):
        fin = marcas[indice + 1] if indice + 1 < len(marcas) else len(html)
        trozo = html[inicio:fin]
        identificador = _SHIMMIE_ID.search(trozo)
        archivo = _SHIMMIE_ARCHIVO.search(trozo)
        if not identificador or not archivo:
            continue            # sin id o sin enlace al archivo: no se puede descargar
        mime = _SHIMMIE_MIME.search(trozo)
        etiquetas = _SHIMMIE_TAGS.search(trozo)
        miniatura = _SHIMMIE_MINIATURA.search(trozo)
        fecha = _SHIMMIE_FECHA.search(trozo)
        salida.append({
            "id": identificador.group(1),
            "tags": _html.unescape(etiquetas.group(1)) if etiquetas else "",
            "mime": mime.group(1) if mime else "",
            "thumb_url": _html.unescape(miniatura.group(1)) if miniatura else "",
            "file_url": _html.unescape(archivo.group(1)),
            "created_at": fecha.group(1) if fecha else None,
        })
    return salida


def _auth_params(site_cfg: dict) -> dict:
    """Credenciales del sitio: los **tokens de su propia entrada** de BOORU_SITES.

    Se admiten dos formas en `auth` (ver app/config.py → BOORU_SITES):
      • un diccionario con los tokens, que es lo normal y lo que se documenta:
            {"api_key": "…", "user_id": "…"}      (Gelbooru / Rule34)
            {"api_key": "…", "login": "…"}        (Danbooru y familia, p. ej. FBooru)
            {"login": "…", "password_hash": "…"}  (Moebooru)
            {"api_key": "…"}                      (Philomena, opcional)
      • la forma abreviada ("GELBOORU",) / ("RULE34",), que lee las claves de las
        constantes de app/config.py (se mantiene por compatibilidad).
    Si el sitio pide credenciales y están vacías, se avisa con un ConfigError que dice
    exactamente qué campo falta.
    """
    tipo = site_cfg.get("auth")
    if not tipo:
        return {}

    if isinstance(tipo, dict):
        familia = str(site_cfg.get("family") or "").lower()
        necesarios = _CREDENCIALES_POR_FAMILIA.get(familia, tuple(tipo))
        tokens = {k: str(v or "").strip() for k, v in tipo.items()}
        usados = {k: v for k, v in tokens.items() if v}
        faltan = [k for k in necesarios if not tokens.get(k)]
        if faltan and (necesarios or not usados):
            raise ConfigError(
                f"{site_cfg.get('name', 'el sitio')} necesita "
                f"{', '.join(faltan)}: rellénalo en su entrada de BOORU_SITES "
                "(app/config.py) o en app/config_local.py"
            )
        return usados

    kind = tipo[0] if isinstance(tipo, (list, tuple)) else str(tipo)
    if kind == "GELBOORU":
        if not config.GELBOORU_API_KEY or not config.GELBOORU_USER_ID:
            raise ConfigError(
                "Gelbooru requiere API key y user ID: escríbelos en app/config_local.py "
                "(https://gelbooru.com/index.php?page=account&s=options)"
            )
        return {"api_key": config.GELBOORU_API_KEY, "user_id": config.GELBOORU_USER_ID}
    if kind == "RULE34":
        if not config.RULE34_API_KEY or not config.RULE34_USER_ID:
            raise ConfigError(
                "Rule34.xxx requiere API key y user ID: escríbelos en app/config_local.py "
                "(https://rule34.xxx/index.php?page=account&s=options)"
            )
        return {"api_key": config.RULE34_API_KEY, "user_id": config.RULE34_USER_ID}
    raise ConfigError(f"tipo de autenticación desconocido: {kind}")


class BooruAdapter(SearchAdapter):
    def __init__(self, site_cfg: dict):
        self.cfg = site_cfg
        self.name = site_cfg["name"]
        self.family = site_cfg["family"]
        self.base = site_cfg["base"].rstrip("/")
        self.view_tpl = site_cfg.get("view_tpl", "")

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        """Busca con **todos** los tags indicados (los que quieras)."""
        tags = [_norm_tag(t) for t in split_tags(query.tags)]
        tags = [t for t in tags if t]
        if not tags:
            return []

        # Se consultan todos; si la instancia los limita, se reintenta con los permitidos
        para_consulta, resto = self._reparto_de_tags(client, tags)

        out: list[Artwork] = []
        descartados = 0
        page = 0
        while len(out) < query.limit:
            try:
                raw = self._fetch_page(client, para_consulta, page)
            except (BlockedError, ConfigError) as exc:
                if page == 0 and not resto and _LIMITE_TAGS_RE.search(str(exc)) \
                        and len(para_consulta) > TAGS_SI_HAY_LIMITE:
                    # El sitio rechaza tantos tags: se consulta con los permitidos y el
                    # resto se exige en local (así N tags siguen funcionando).
                    resto = para_consulta[TAGS_SI_HAY_LIMITE:]
                    para_consulta = para_consulta[:TAGS_SI_HAY_LIMITE]
                    self._avisar(client, f"solo admite {len(para_consulta)} tags por "
                                         f"consulta; los otros {len(resto)} se comprueban "
                                         "en local")
                    raw = self._fetch_page(client, para_consulta, page)
                else:
                    raise
            if not raw:
                break
            for item in raw:
                art = self._normalize(item)
                if art is None:
                    continue
                if not _tiene_todos(art.tags, tags):
                    descartados += 1
                    continue
                out.append(art)
                if len(out) >= query.limit:
                    return out
            if len(raw) < self._page_size():
                break
            page += 1

        if descartados:
            logger.info("%s: %d resultados descartados por no llevar todos los tags %s",
                        self.name, descartados, tags)
        return out

    def _reparto_de_tags(self, client: PoliteClient,
                         tags: list[str]) -> tuple[list[str], list[str]]:
        """(tags que se consultan, tags que se exigen en local).

        Danbooru sin credenciales admite 2 tags por búsqueda (límite documentado): en
        lugar de fallar, se consulta con esos 2 y el resto se comprueba en local.
        Se prefieren los **tags simples** para la consulta, porque los operadores
        (`-tag`, `rating:x`, `score:>10`) no se pueden verificar en local.
        """
        if self.family != "danbooru" or len(tags) <= TAGS_SI_HAY_LIMITE:
            return tags, []
        try:
            con_clave = bool(_auth_params(self.cfg))
        except ConfigError:
            con_clave = False
        if con_clave:
            return tags, []
        simples = [t for t in tags if _es_tag_simple(t)]
        operadores = [t for t in tags if not _es_tag_simple(t)]
        # Los operadores van primero (no se pueden comprobar después); el resto de la
        # consulta se completa con tags simples, que sí se verifican en local.
        consulta = operadores[:TAGS_SI_HAY_LIMITE]
        consulta += simples[:max(0, TAGS_SI_HAY_LIMITE - len(consulta))]
        resto = [t for t in tags if t not in consulta]
        no_verificables = [t for t in resto if not _es_tag_simple(t)]
        self._avisar(client, f"sin clave admite {TAGS_SI_HAY_LIMITE} tags por consulta; "
                             f"los otros {len(resto)} se comprueban en local"
                             + (f" (no se pueden comprobar: {', '.join(no_verificables)})"
                                if no_verificables else ""))
        return consulta, resto

    def _avisar(self, client: PoliteClient, mensaje: str) -> None:
        texto = f"{self.name}: {mensaje}"
        logger.info(texto)
        aviso = getattr(client, "aviso", None)
        if aviso is not None:
            aviso(texto)

    def _page_size(self) -> int:
        if self.family == "danbooru":
            return 200
        if self.family == "philomena":
            return 50
        if self.family == "shimmie":
            return 70          # el listado HTML de Shimmie muestra 70 por página
        return 100

    def _fetch_page(self, client: PoliteClient, tags: list[str], page: int) -> list[dict]:
        joined = " ".join(tags)
        auth = _auth_params(self.cfg)
        if self.family == "gelbooru":
            params = {
                "page": "dapi", "s": "post", "q": "index", "json": "1",
                "tags": joined, "limit": "100", "pid": str(page),
                **auth,
            }
            data = client.get_json(f"{self.base}/index.php", params=params)
            return data if isinstance(data, list) else []
        if self.family == "danbooru":
            params = {"tags": joined, "limit": "200", "page": str(page + 1)}
            params.update(auth)
            data = client.get_json(f"{self.base}/posts.json", params=params)
            return data if isinstance(data, list) else []
        if self.family == "moebooru":
            params = {"tags": joined, "limit": "100", "page": str(page + 1)}
            data = client.get_json(f"{self.base}/post.json", params=params)
            return data if isinstance(data, list) else []
        if self.family == "philomena":
            # Philomena (Derpibooru): la coma es «Y» (los espacios serían «O»)
            params = {"q": ", ".join(tags), "per_page": "50", "page": str(page + 1)}
            data = client.get_json(f"{self.base}/api/v1/json/search/images", params=params)
            return data.get("images", []) if isinstance(data, dict) else []
        if self.family == "shimmie":
            return self._fetch_shimmie(client, joined, page)
        raise ConfigError(f"familia de booru desconocida: {self.family}")

    # ------------------------------------------------------------------ Shimmie (HTML)
    def _fetch_shimmie(self, client: PoliteClient, joined: str, page: int) -> list[dict]:
        """Listado de un tablero **Shimmie** (p. ej. rule34.paheal.net).

        Shimmie trae su API pública desactivada en muchos sitios (rule34.paheal.net
        responde HTML en `/api/…`), así que se lee el **listado público** que el propio
        navegador recibe: `GET /post/list/<tags>/<página>` con `tags` separados por
        espacios (en la URL, `%20`; con `+` devuelve 404) y 70 resultados por página.
        De cada resultado se toman los `data-tags` (lista completa de etiquetas), el id,
        el tipo MIME (para saltar vídeos) y el enlace del **archivo completo**.
        Al pasarse de la última página, Shimmie responde 404: se trata como fin de lista.
        """
        url = f"{self.base}/post/list/{quote(joined, safe='')}/{page + 1}"
        cabeceras = dict(self.cfg.get("headers") or {})
        try:
            html = client.get_text(url, headers=cabeceras or None)
        except SinResultados:
            logger.debug("%s: fin de resultados en la página %d", self.name, page + 1)
            return []
        return _parsear_shimmie(html)


    # ------------------------------------------------------------------ normalización
    def _normalize(self, raw: dict) -> Artwork | None:
        try:
            if self.family == "gelbooru":
                return self._normalize_gelbooru(raw)
            if self.family == "danbooru":
                return self._normalize_danbooru(raw)
            if self.family == "moebooru":
                return self._normalize_moebooru(raw)
            if self.family == "philomena":
                return self._normalize_philomena(raw)
            if self.family == "shimmie":
                return self._normalize_shimmie(raw)
        except (KeyError, TypeError):
            return None
        return None

    def _normalize_shimmie(self, raw: dict) -> Artwork | None:
        """Resultado de un tablero Shimmie (lo que ya viene parseado del listado)."""
        sid = str(raw.get("id", "")).strip()
        url = (raw.get("file_url") or "").strip()
        tags = [t for t in (raw.get("tags") or "").split() if t]
        if not sid or not url:
            return None
        mime = (raw.get("mime") or "").lower()
        if mime and not mime.startswith("image/"):
            return None            # vídeos, animaciones flash, zips…
        # El nombre del archivo en estos CDN es su md5: sirve para deduplicar.
        md5 = url.rstrip("/").rpartition("/")[2] or None
        if md5 and not re.fullmatch(r"[0-9a-fA-F]{32}", md5):
            md5 = None
        return Artwork(
            site=self.name,
            site_id=sid,
            url=url,
            preview_url=raw.get("thumb_url") or url,
            page_url=self.view_tpl.format(id=sid),
            tags=tags,
            # Rule34 Paheal es un tablero adulto: pasa el filtro de rating solo si el
            # usuario marcó «Contenido adulto» (como cualquier resultado explicit).
            rating="explicit",
            md5=md5,
            author=raw.get("author") or None,
            license=None,
            created_at=raw.get("created_at"),
            content_text=raw.get("title") or None,
            source_field=None,
            raw=raw,
        )

    def _normalize_gelbooru(self, raw: dict) -> Artwork | None:
        sid = str(raw.get("id", ""))
        tags = re.split(r"\s+", (raw.get("tags") or "").strip())
        directory = raw.get("directory") or ""
        image = raw.get("image") or ""
        if _is_video_name(image):
            return None
        # Algunos sitios de esta familia no incluyen file_url: se construye
        # desde directory+image (p. ej. The Big ImageBoard).
        url = raw.get("file_url")
        if not url and directory and image:
            url = f"{self.base}/images/{directory}/{image}"
        if not url:
            return None
        preview = raw.get("sample_url") or raw.get("preview_url")
        if not preview and directory and image:
            preview = f"{self.base}/thumbnails/{directory}/thumbnail_{image}"
        return Artwork(
            site=self.name,
            site_id=sid,
            url=url,
            preview_url=preview,
            page_url=self.view_tpl.format(id=sid),
            tags=[t for t in tags if t],
            rating=_RATING_MAP.get(str(raw.get("rating", "")).lower(), "general"),
            md5=raw.get("md5"),
            author=raw.get("owner"),
            license=None,
            created_at=raw.get("created_at"),
            content_text=None,
            source_field=raw.get("source") or "",
            raw=raw,
        )

    def _normalize_danbooru(self, raw: dict) -> Artwork:
        sid = str(raw.get("id", ""))
        if _is_video_name(raw.get("file_ext")):
            return None
        tags = re.split(r"\s+", (raw.get("tag_string") or "").strip())
        artist = (raw.get("tag_string_artist") or "").strip().split(" ")[0] or None
        return Artwork(
            site=self.name,
            site_id=sid,
            url=raw.get("file_url") or raw.get("large_file_url", ""),
            preview_url=raw.get("preview_file_url"),
            page_url=self.view_tpl.format(id=sid),
            tags=[t for t in tags if t],
            rating=_RATING_MAP.get(str(raw.get("rating", "")).lower(), "general"),
            md5=raw.get("md5"),
            author=artist,
            license=None,
            created_at=raw.get("created_at"),
            content_text=None,
            source_field=raw.get("source") or "",
            raw=raw,
        )

    def _normalize_moebooru(self, raw: dict) -> Artwork:
        sid = str(raw.get("id", ""))
        if _is_video_name(raw.get("file_url")):
            return None
        tags = re.split(r"\s+", (raw.get("tags") or "").strip())
        return Artwork(
            site=self.name,
            site_id=sid,
            url=raw["file_url"],
            preview_url=raw.get("sample_url") or raw.get("preview_url"),
            page_url=self.view_tpl.format(id=sid),
            tags=[t for t in tags if t],
            rating=_RATING_MAP.get(str(raw.get("rating", "")).lower(), "general"),
            md5=raw.get("md5"),
            author=raw.get("author") or None,
            license=None,
            created_at=str(raw.get("created_at", "")) or None,
            content_text=None,
            source_field=raw.get("source") or "",
            raw=raw,
        )

    def _normalize_philomena(self, raw: dict) -> Artwork | None:
        """Familia Philomena (p. ej. Derpibooru)."""
        sid = str(raw.get("id", ""))
        if _is_video_name(raw.get("format")):
            return None
        rep = raw.get("representations") or {}
        url = rep.get("full")
        if not url:
            return None
        preview = rep.get("medium") or rep.get("large") or rep.get("small") or url
        tags = raw.get("tags") or []
        low = [t.lower() for t in tags]
        if any("explicit" in t or "grimdark" in t for t in low):
            rating = "explicit"
        elif any("questionable" in t for t in low):
            rating = "questionable"
        elif any("suggestive" in t for t in low):
            rating = "sensitive"
        else:
            rating = "general"
        return Artwork(
            site=self.name,
            site_id=sid,
            url=url,
            preview_url=preview,
            page_url=self.view_tpl.format(id=sid),
            tags=tags,
            rating=rating,
            md5=None,
            author=raw.get("uploader") or None,
            license=None,
            created_at=raw.get("created_at"),
            content_text=(raw.get("description") or "")[:2000],
            source_field=raw.get("source_url") or "",
            raw=raw,
        )
