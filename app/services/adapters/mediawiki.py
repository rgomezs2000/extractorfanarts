"""Adaptador de wikis de fandom (MediaWiki: Fandom.com y otras wikis).

Busca el fandom (franquicia) y/o personaje/concepto en el repositorio de la
wiki usando la API pública api.php, sin login.

Detalles:
  - Usa `prop=imageinfo` para obtener la **URL directa** del archivo, el
    **autor** (uploader) y la **licencia** (extmetadata), además de descartar
    videos/audio (solo imágenes).
  - La descarga usa esa URL directa; la miniatura de ejemplo usa
    Special:FilePath con ?width=640.
"""
from __future__ import annotations

import logging
import re
from urllib.parse import quote, urlparse

from ...models.artwork import Artwork, SearchQuery
from ..http_client import ConfigError, PoliteClient
from .base import SearchAdapter

logger = logging.getLogger("imaginteca")

_HTML_RE = re.compile(r"<[^>]+>")


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _norm_titulo(nombre: str) -> str:
    return nombre.replace("_", " ").strip()


_PALABRAS_VACIAS = {
    "the", "of", "and", "a", "an", "de", "del", "la", "el", "los", "las", "y", "o",
    "en", "con", "para", "por", "un", "una", "unos", "unas", "al", "es", "su", "sus",
    "gallery", "galeria", "galería", "costumes", "atuendos", "images", "imagenes",
}


def _terminos(texto: str | None) -> list[str]:
    """Uno o varios términos separados por comas (o punto y coma).

    Las **comillas** marcan búsqueda **exacta** en la wiki: `"traje de gala"` busca esa
    frase tal cual; sin comillas, la wiki busca por palabras (inexacta).
    """
    if not texto:
        return []
    partes = re.split(r"[,;]+", str(texto))
    return [p.strip() for p in partes if p.strip()]


def _tokens(texto: str) -> list[str]:
    """Palabras significativas (para comparar nombres de archivo y títulos)."""
    palabras = re.findall(r"[0-9a-záéíóúüñ]+", str(texto).lower())
    return [p for p in palabras if len(p) >= 4 and p not in _PALABRAS_VACIAS]


def _relacionado(nombre_archivo: str, terminos: list[str]) -> bool:
    """¿El nombre del archivo menciona algo del término buscado?

    Es el filtro de relevancia: de las páginas **ajenas** al término (resultados de la
    búsqueda que hablan de otros personajes) solo se aceptan los archivos que nombran
    al personaje o concepto buscado; los de **sus propias páginas** (personaje y sus
    pestañas: Galería, Atuendos…) se aceptan siempre, porque son suyos.
    """
    if not terminos:
        return True
    archivo = str(nombre_archivo).lower()
    for termino in terminos:
        limpio = termino.strip('"').strip()
        palabras = _tokens(limpio)
        if not palabras:
            if limpio.lower() in archivo:
                return True
            continue
        if any(palabra in archivo for palabra in palabras):
            return True
    return False


def _es_pestaña_de_atuendos(titulo: str) -> bool:
    """¿Es una pestaña de atuendos/galería? (Ahí están los conjuntos del personaje)."""
    return bool(re.search(r"/(atuendos|costumes|outfits|vestuario|galer[íi]a|gallery)\b",
                          str(titulo), re.IGNORECASE))


def _texto_plano(valor: str | None) -> str | None:
    if not valor:
        return None
    limpio = _HTML_RE.sub("", str(valor)).strip()
    return limpio or None


class MediaWikiAdapter(SearchAdapter):
    name = "Fandom (MediaWiki)"

    # ------------------------------------------------------------------ resolución de la wiki
    def _resolve_base(self, client: PoliteClient, query: SearchQuery) -> str:
        if query.wiki_url:
            base = query.wiki_url.rstrip("/")
        elif query.fandom:
            base = f"https://{_slug(query.fandom)}.fandom.com"
        else:
            base = None
        if not base:
            raise ConfigError(
                "Indica el nombre del fandom (ej. naruto) o la URL completa de la wiki"
            )
        try:
            client.get_json(f"{base}/api.php", params={
                "action": "query", "meta": "siteinfo", "format": "json",
            })
        except Exception as exc:  # noqa: BLE001
            raise ConfigError(
                f"No se pudo conectar con la wiki '{base}'. "
                "Escribe la URL completa de la wiki (ej. https://naruto.fandom.com). "
                f"({exc})"
            )
        return base

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        """Busca en la wiki: la página del personaje, **sus pestañas** y conceptos.

        - **Personaje**: se miran su página principal **y sus subpáginas** (Galería,
          Atuendos, Momentos, Relaciones…) que son las pestañas de la wiki, más los
          archivos cuyo nombre empieza por el personaje. De las páginas ajenas solo se
          aceptan archivos que **mencionen** al personaje (filtro de relevancia).
        - **Concepto** (`traje de gala`, `ropa interior`, `pijama`, `traje de baño`,
          `poses`…): la búsqueda de la wiki devuelve las **páginas que lo tienen**
          (normalmente los «Atuendos/Costumes» de los personajes) y de ahí salen sus
          imágenes. Con **comillas** la búsqueda es **exacta**; sin ellas, por palabras.
        """
        base = self._resolve_base(client, query)
        terminos = _terminos(query.character) or _terminos(query.fandom)
        if not terminos:
            return []

        # 1) páginas de cada término (la suya, sus pestañas y lo que devuelva la wiki)
        propias: list[str] = []          # la página del término (se filtra por nombre)
        pestañas: list[str] = []         # sus pestañas (Galería, Atuendos…): son suyas
        ajenas: list[str] = []           # páginas de la búsqueda que hablan del término
        for termino in terminos:
            tabs, de_busqueda = self._paginas(client, base, termino)
            propias.append(termino)
            pestañas.extend(tabs)
            ajenas.extend(de_busqueda)

        def _unico(lista: list[str]) -> list[str]:
            vistos: set[str] = set()
            return [t for t in lista if t and not (t in vistos or vistos.add(t))]

        propias = _unico(propias)
        pestañas = [p for p in _unico(pestañas) if p not in set(propias)]
        ajenas = [p for p in _unico(ajenas)
                  if p not in set(propias) and p not in set(pestañas)]

        # 2) archivos: las pestañas enteras (su galería y sus atuendos son suyos), la
        #    página principal y las ajenas solo con los que **mencionan** el término.
        archivos: list[str] = []
        archivos.extend(self._imagenes_de(client, base, pestañas))
        for pagina, nombres in self._imagenes_por_pagina(
                client, base, propias + ajenas).items():
            relacionados = [n for n in nombres if _relacionado(n, terminos)]
            if relacionados:
                archivos.extend(relacionados)
            elif _es_pestaña_de_atuendos(pagina):
                # Las pestañas de atuendos/galería que ha devuelto la búsqueda del
                # concepto son justo lo que se busca (aunque el archivo no se llame
                # igual que el concepto): se aceptan enteras.
                archivos.extend(nombres)
        archivos.extend(self._archivos_por_prefijo(client, base, terminos))

        archivos = _unico(archivos)
        if not archivos:
            return []

        seleccion = archivos[: query.limit]
        infos = self._imageinfo(client, base, seleccion)
        needle = terminos[0]

        out: list[Artwork] = []
        for nombre in seleccion:
            art = self._normalize(base, nombre, needle, infos.get(_norm_titulo(nombre)))
            if art is not None:
                out.append(art)
        return out

    def _paginas(self, client: PoliteClient, base: str,
                 termino: str) -> tuple[list[str], list[str]]:
        """(subpáginas o pestañas del término, páginas que devuelve la búsqueda).

        Las pestañas se piden con `list=allpages` y el prefijo `<término>/`: así salen
        Galería, Galería/Temporada 1, Atuendos, Momentos… sin tener que adivinarlas.
        """
        pestañas: list[str] = []
        try:
            data = client.get_json(f"{base}/api.php", params={
                "action": "query", "list": "allpages", "apprefix": f"{termino}/",
                "aplimit": "100", "apnamespace": "0", "format": "json",
            })
            pestañas = [p.get("title", "") for p in
                        data.get("query", {}).get("allpages", []) or []]
        except Exception:  # noqa: BLE001
            pestañas = []

        encontradas: list[str] = []
        try:
            data = client.get_json(f"{base}/api.php", params={
                "action": "query", "list": "search", "srsearch": termino,
                "srlimit": "15", "format": "json",
            })
            encontradas = [h.get("title", "") for h in
                           data.get("query", {}).get("search", []) or []]
        except Exception:  # noqa: BLE001
            encontradas = []
        return [p for p in pestañas if p], [p for p in encontradas if p]

    def _imagenes_de(self, client: PoliteClient, base: str,
                     paginas: list[str]) -> list[str]:
        """Archivos usados en esas páginas (en lotes de 10 títulos)."""
        archivos: list[str] = []
        for nombres in self._imagenes_por_pagina(client, base, paginas).values():
            archivos.extend(nombres)
        return archivos

    def _imagenes_por_pagina(self, client: PoliteClient, base: str,
                             paginas: list[str]) -> dict[str, list[str]]:
        """{título de la página: [archivos]} (en lotes de 10 títulos)."""
        resultado: dict[str, list[str]] = {}
        for i in range(0, len(paginas), 10):
            lote = paginas[i:i + 10]
            try:
                data = client.get_json(f"{base}/api.php", params={
                    "action": "query", "prop": "images", "imlimit": "500",
                    "titles": "|".join(lote), "format": "json",
                })
            except Exception:  # noqa: BLE001
                continue
            for pagina in data.get("query", {}).get("pages", {}).values():
                titulo = str(pagina.get("title", ""))
                for img in pagina.get("images") or []:
                    if not isinstance(img, dict):
                        continue
                    # El espacio de nombres 6 es «archivos», pero se llama distinto en
                    # cada idioma: File: (inglés), Archivo: (español), Datei:, Fichier…
                    # Por eso se comprueba el número y se quita lo que haya antes de «:».
                    if img.get("ns") != 6 and not str(img.get("title", "")).startswith("File:"):
                        continue
                    nombre = str(img.get("title", "")).split(":", 1)[-1].strip()
                    if nombre:
                        resultado.setdefault(titulo, []).append(nombre)
        return resultado

    def _archivos_por_prefijo(self, client: PoliteClient, base: str,
                              terminos: list[str]) -> list[str]:
        """Archivos cuyo nombre empieza por el término (personaje o concepto)."""
        archivos: list[str] = []
        for termino in terminos:
            limpio = termino.strip('"').strip()
            if not limpio:
                continue
            try:
                data = client.get_json(f"{base}/api.php", params={
                    "action": "query", "list": "allimages", "aiprefix": limpio,
                    "ailimit": "100", "aiprop": "url", "format": "json",
                })
                for img in data.get("query", {}).get("allimages", []) or []:
                    archivos.append(img.get("name", ""))
            except Exception:  # noqa: BLE001
                continue
        return archivos

    # ------------------------------------------------------------------ imageinfo (por lotes)
    def _imageinfo(self, client: PoliteClient, base: str, nombres: list[str]) -> dict[str, dict]:
        """Devuelve {titulo_normalizado: imageinfo} en lotes de 50 títulos."""
        infos: dict[str, dict] = {}
        for i in range(0, len(nombres), 50):
            lote = nombres[i:i + 50]
            try:
                data = client.get_json(f"{base}/api.php", params={
                    "action": "query", "prop": "imageinfo",
                    "iiprop": "url|user|size|mime|extmetadata",
                    "titles": "|".join(f"File:{n}" for n in lote),
                    "format": "json",
                })
            except Exception:  # noqa: BLE001
                continue
            for page in data.get("query", {}).get("pages", {}).values():
                info = (page.get("imageinfo") or [{}])[0]
                titulo = str(page.get("title", "")).replace("File:", "", 1)
                if not titulo:
                    continue
                # La página puede enlazar un archivo BORRADO o que nunca se subió («red
                # link»): MediaWiki lo devuelve con «missing». Se marca para no ofrecerlo
                # y no acabar con descargas que dan 404.
                if not info or "missing" in page or page.get("missing") is not None:
                    if not info:
                        info = {"missing": True}
                infos[_norm_titulo(titulo)] = info
        return infos

    # ------------------------------------------------------------------ normalización
    def _normalize(self, base: str, nombre: str, needle: str,
                   info: dict | None) -> Artwork | None:
        info = info or {}
        if info.get("missing"):
            # Archivo que la página enlaza pero que no existe en el wiki: no se ofrece.
            logger.info("wiki: se omite «%s» porque el archivo no existe en el wiki", nombre)
            return None
        mime = str(info.get("mime") or "")
        if mime and not mime.startswith("image/"):
            return None  # la app es un extractor de imágenes: se ignora video/audio/pdf

        host = urlparse(base).netloc
        url = info.get("url") or f"{base}/wiki/Special:FilePath/{quote(nombre)}"
        preview = f"{base}/wiki/Special:FilePath/{quote(nombre)}?width=640"
        meta = info.get("extmetadata") or {}
        licencia = _texto_plano((meta.get("LicenseShortName") or {}).get("value"))
        autor = info.get("user") or None
        tags = [t for t in ([needle] if needle else []) if t]

        return Artwork(
            site=f"Wiki: {host}",
            site_id=nombre,
            url=url,
            preview_url=preview,
            page_url=info.get("descriptionurl") or f"{base}/wiki/File:{quote(nombre)}",
            tags=tags,
            rating="general",
            md5=None,
            author=autor,
            license=licencia,  # las wikis mezclan libre con fair use → confirmación manual
            created_at=None,
            content_text=None,
            source_field=None,
            raw={"wiki": base, "file": nombre, "info": info},
        )
