"""Adaptador de Mastodon (API pública, sin login) — cualquier instancia.

Soporta:
  - `@usuario`          → se busca en la instancia seleccionada (campo Instancia).
  - `@usuario@host.tld` → se consulta **la instancia de ese usuario** directamente
    (funciona con cualquier servidor del fediverso sin límites de una sola instancia).
  - `#hashtag` / palabra clave → timeline pública / búsqueda en la instancia elegida.

**Filtros combinados:** los tres campos (usuario, palabras clave y hashtags) se aplican
a la vez; y se admiten **varios** valores en palabras clave y hashtags
(`#lola_loud #the_loud_house`, `"lola loud", the loud house`). Como la API de Mastodon no
sabe combinarlos, se piden candidatos (con paginación) y se filtran en local con
`social_filtros.Criterios`: un artista + un hashtag devuelve *solo* lo que cumple ambos.

Todo con endpoints públicos: **no se envía autenticación** (el parámetro
`resolve=true`, que sí exige token, ya no se usa).

Respaldo para instancias restrictivas: algunas (p. ej. baraag.net) responden
`422 {"error":"This method requires an authenticated user"}` en las timelines por
hashtag. En ese caso se usa el **RSS público** de la etiqueta
(`/tags/<tag>.rss`), que sí es abierto, y como último recurso la timeline pública.
Con varios hashtags se piden sus RSS y se cruzan (intersección) para no perder
publicaciones que sí llevan los dos.
"""
from __future__ import annotations

import html as _html
import logging
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote, urlparse

from ... import config
from ...models.artwork import Artwork, SearchQuery
from ..http_client import BlockedError, ConfigError, PoliteClient, SinResultados
from .base import SearchAdapter
from .social_filtros import Criterios, etiquetas_de

logger = logging.getLogger("extractorfanarts")

_HASHTAG_RE = re.compile(r"#([\w]+)")
_IMG_SRC_RE = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)
_RSS_MEDIA = {"media": "http://search.yahoo.com/mrss/"}
_TEXTO_RE = re.compile(r"<[^>]+>")


def normalizar_instancia(valor: str) -> str:
    """Acepta 'baraag.net', 'https://baraag.net' o 'https://baraag.net/'."""
    texto = (valor or "").strip().rstrip("/")
    if not texto:
        return ""
    if not texto.startswith(("http://", "https://")):
        texto = "https://" + texto
    return texto


def host_de_handle(usuario: str) -> str | None:
    """Extrae el host de '@usuario@host.tld' (o None si no lo lleva)."""
    limpio = (usuario or "").strip().lstrip("@")
    if "@" in limpio:
        host = limpio.split("@", 1)[1].strip()
        return host or None
    return None


class MastodonAdapter(SearchAdapter):
    def __init__(self, instance: str = "mastodon.social"):
        self.base_default = normalizar_instancia(instance) or "https://mastodon.social"
        self.name = f"Mastodon · {self._host(self.base_default)}"

    @staticmethod
    def _host(base: str) -> str:
        return urlparse(base).netloc or base

    def _base(self, query: SearchQuery) -> str:
        """Instancia a usar: la del @usuario@host, o la elegida en la UI."""
        host = host_de_handle(query.usuario)
        if host:
            return normalizar_instancia(host)
        if query.instance:
            return normalizar_instancia(query.instance)
        return self.base_default

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        base = self._base(query)
        criterios = Criterios.desde_query(query)
        if criterios.vacio:
            return []
        aviso = getattr(client, "aviso", None)
        if aviso is not None:
            aviso(f"filtros de búsqueda → {criterios.detalle()}")
        logger.info("Mastodon %s: %s", self._host(base), criterios.descripcion())

        estados, criterios = self._candidatos(client, criterios, base, query.limit)
        descartados = 0
        out: list[Artwork] = []
        for st in estados:
            texto = f"{st.get('content') or ''} {st.get('spoiler_text') or ''}"
            etiquetas = etiquetas_de([t.get("name", "") for t in st.get("tags", [])],
                                     _HASHTAG_RE.findall(texto))
            autor = (st.get("account") or {}).get("acct") \
                or (st.get("account") or {}).get("username") or ""
            if not criterios.cumple(texto=texto, etiquetas=etiquetas, autor=autor):
                descartados += 1
                logger.debug("descartada %s: %s", st.get("id"),
                             criterios.explica(texto=texto, etiquetas=etiquetas, autor=autor))
                continue
            for media in st.get("media_attachments", []):
                if media.get("type") not in ("image", "unknown"):
                    continue
                art = self._normalize(st, media, base)
                if art is not None:
                    out.append(art)
                    if len(out) >= query.limit:
                        return out
        logger.info("Mastodon %s: %d publicaciones revisadas, %d descartadas por los filtros, "
                    "%d imágenes", self._host(base), len(estados), descartados, len(out))
        return out

    # ------------------------------------------------------------------ candidatos
    def _candidatos(self, client: PoliteClient, criterios: Criterios, base: str,
                    limite: int) -> tuple[list[dict], Criterios]:
        """Publicaciones candidatas y los criterios aplicables a ellas.

        Normalmente los criterios son los mismos que pidió el usuario; con la búsqueda
        por texto pueden cambiar (se buscan las palabras clave como etiquetas), así que
        se devuelven junto a los candidatos.
        """
        fuente = criterios.fuente
        if fuente == "usuario":
            estados = self._ampliar(client, self._por_usuario(client, criterios, base, limite),
                                    criterios, base)
            return estados, criterios
        if fuente == "hashtag":
            return self._por_hashtags(client, base, criterios), criterios
        return self._por_palabra(client, base, criterios)

    def _por_palabra(self, client: PoliteClient, base: str,
                     criterios: Criterios) -> tuple[list[dict], Criterios]:
        """Búsqueda por texto: se prueban **todas** las palabras clave indicadas.

        La búsqueda de texto de Mastodon suele exigir token; si no está disponible se
        intenta la timeline pública y, como último recurso, se interpretan las palabras
        clave como etiquetas («Lola Loud» → `#lola_loud`), que sí son públicas. En ese
        caso se devuelven unos criterios ajustados (`como_etiquetas`) para que el filtro
        local exija esas etiquetas en lugar del texto.
        """
        terminos = list(criterios.palabras) or ([criterios.consulta] if criterios.consulta
                                                else [])
        estados: list[dict] = []
        vistos: set[str] = set()
        for termino in terminos:
            try:
                for st in self._buscar_texto(client, base, termino):
                    clave = str(st.get("id"))
                    if clave not in vistos:
                        vistos.add(clave)
                        estados.append(st)
            except (BlockedError, ConfigError) as exc:
                logger.info("búsqueda por texto «%s» no disponible en %s (%s)",
                            termino, self._host(base), exc)
                break
        if estados:
            return estados, criterios

        # 2) Timeline pública (los filtros se aplican después en local)
        try:
            publica = client.get_json(
                f"{base}/api/v1/timelines/public",
                params={"limit": str(config.SOCIAL_PAGINA), "only_media": "true"},
            )
            if publica:
                return publica, criterios
        except (BlockedError, ConfigError) as exc:
            logger.info("timeline pública no disponible en %s (%s)", self._host(base), exc)

        # 3) Las palabras clave como etiquetas (Lola Loud → #lola_loud)
        etiquetas = criterios.etiquetas_derivadas()
        if not etiquetas:
            raise BlockedError(
                f"{self._host(base)} no permite buscar por texto sin iniciar sesión. "
                "Prueba con un hashtag (#…) o con un @usuario, que sí funcionan sin cuenta."
            )
        logger.info("%s: sin búsqueda de texto; se interpretan las palabras clave como "
                    "etiquetas -> %s", self._host(base), ", ".join(f"#{e}" for e in etiquetas))
        aviso = getattr(client, "aviso", None)
        if aviso is not None:
            aviso("sin búsqueda de texto en esta instancia; se usan las etiquetas "
                  + ", ".join(f"#{e}" for e in etiquetas))
        estados = []
        vistos = set()
        for etiqueta in etiquetas:
            try:
                for st in self._por_hashtag(client, base, etiqueta):
                    clave = str(st.get("id"))
                    if clave not in vistos:
                        vistos.add(clave)
                        estados.append(st)
            except Exception:  # noqa: BLE001
                logger.debug("no se pudo buscar la etiqueta #%s", etiqueta, exc_info=True)
        return estados, criterios.como_etiquetas()

    def _ampliar(self, client: PoliteClient, estados: list[dict], criterios: Criterios,
                 base: str) -> list[dict]:
        """Suma candidatos de las etiquetas/texto buscados (mejora el alcance).

        La timeline de un artista puede no traer ya (por antigüedad) la publicación que
        lleva el hashtag buscado, mientras que la timeline/RSS de la etiqueta sí. Se unen
        ambas fuentes y el filtro local se queda solo con lo que cumple los criterios.
        """
        ids = {str(st.get("id")) for st in estados}
        for tag in criterios.hashtags:
            try:
                for st in self._por_hashtag(client, base, tag):
                    clave = str(st.get("id"))
                    if clave not in ids:
                        ids.add(clave)
                        estados.append(st)
            except Exception:  # noqa: BLE001
                logger.debug("no se pudo ampliar la búsqueda con #%s", tag, exc_info=True)
        if criterios.palabras and not criterios.hashtags:
            for palabra in criterios.palabras:
                try:
                    for st in self._buscar_texto(client, base, palabra):
                        clave = str(st.get("id"))
                        if clave not in ids:
                            ids.add(clave)
                            estados.append(st)
                except Exception:  # noqa: BLE001
                    logger.debug("no se pudo ampliar la búsqueda de «%s»", palabra,
                                 exc_info=True)
        return estados

    def _paginas(self) -> int:
        return max(1, int(getattr(config, "SOCIAL_PAGINAS", 6)))

    def _por_usuario(self, client: PoliteClient, criterios: Criterios, base: str,
                     limite: int) -> list[dict]:
        """Timeline del usuario, paginando hasta reunir coincidencias suficientes."""
        cuenta = self._cuenta(client, criterios.usuario, base)
        estados: list[dict] = []
        max_id: str | None = None
        for _ in range(self._paginas()):
            params = {"limit": str(config.SOCIAL_PAGINA), "only_media": "true",
                      "exclude_replies": "true", "exclude_reblogs": "true"}
            if max_id:
                params["max_id"] = max_id
            pagina = client.get_json(
                f"{base}/api/v1/accounts/{cuenta['id']}/statuses", params=params
            )
            if not pagina:
                break
            estados.extend(pagina)
            encontradas = 0
            for st in estados:
                texto = f"{st.get('content') or ''} {st.get('spoiler_text') or ''}"
                etiquetas = etiquetas_de([t.get("name", "") for t in st.get("tags", [])],
                                         _HASHTAG_RE.findall(texto))
                autor = (st.get("account") or {}).get("acct") or ""
                if criterios.cumple(texto=texto, etiquetas=etiquetas, autor=autor):
                    encontradas += len(st.get("media_attachments") or []) or 1
            if encontradas >= limite or len(estados) >= config.SOCIAL_MAX_CANDIDATOS:
                break
            if criterios.vacio:
                break
            if not (criterios.palabras or criterios.hashtags):
                break                      # sin filtros extra, una página basta
            max_id = str(pagina[-1].get("id") or "")
            if not max_id:
                break
        return estados

    def _por_hashtags(self, client: PoliteClient, base: str,
                      criterios: Criterios) -> list[dict]:
        """Timeline(s) por hashtag.

        Con un valor, su timeline/RSS. Con **N valores**: si se exigen todos, se
        **cruzan** las publicaciones (intersección); si vale cualquiera, se **unen**
        (unión), así no se pierde ninguna de las etiquetas indicadas. Cada etiqueta
        cuesta una petición (espaciada por el intervalo de cortesía).
        """
        hashtags = criterios.hashtags
        if len(hashtags) == 1:
            return self._por_hashtag(client, base, hashtags[0])
        listas: list[dict[str, dict]] = []
        for tag in hashtags:
            listas.append({str(st.get("id")): st
                           for st in self._por_hashtag(client, base, tag)})
        if not listas:
            return []
        if criterios.exigir_todos:
            comunes = set(listas[0])
            for lista in listas[1:]:
                comunes &= set(lista)
            return [listas[0][i] for i in listas[0] if i in comunes]
        # Unión, conservando el orden de la primera lista
        union: dict[str, dict] = {}
        for lista in listas:
            for clave, estado in lista.items():
                union.setdefault(clave, estado)
        return list(union.values())

    def _por_hashtag(self, client: PoliteClient, base: str, tag: str) -> list[dict]:
        try:
            return client.get_json(
                f"{base}/api/v1/timelines/tag/{quote(tag)}",
                params={"limit": str(config.SOCIAL_PAGINA), "only_media": "true"},
            )
        except (BlockedError, ConfigError) as exc:
            # Instancias como baraag.net exigen token para esta timeline:
            # se usa el RSS público de la etiqueta (abierto, sin login).
            logger.info(
                "timeline por hashtag no disponible en %s (%s); se intenta el RSS público",
                self._host(base), exc,
            )
        return self._hashtag_por_rss(client, base, tag)

    def _buscar_texto(self, client: PoliteClient, base: str, termino: str) -> list[dict]:
        """Búsqueda de publicaciones por texto (puede no estar disponible sin token)."""
        datos = client.get_json(
            f"{base}/api/v2/search",
            params={"q": termino, "type": "statuses", "limit": str(config.SOCIAL_PAGINA)},
        )
        return datos.get("statuses", []) if isinstance(datos, dict) else []

    def _cuenta(self, client: PoliteClient, usuario: str, base: str) -> dict:
        """Cuenta del usuario indicado (lookup público con respaldo de búsqueda)."""
        acct = (usuario or "").strip().lstrip("@")
        nombre = acct.split("@", 1)[0]
        try:
            # Endpoint público de Mastodon 3.4+ (no requiere autenticación)
            cuenta = client.get_json(
                f"{base}/api/v1/accounts/lookup", params={"acct": nombre}
            )
        except Exception:  # noqa: BLE001
            cuenta = None
        if cuenta and cuenta.get("id"):
            return cuenta
        # Respaldo: búsqueda SIN `resolve` (resolve=true exige token → HTTP 401)
        datos = client.get_json(
            f"{base}/api/v2/search",
            params={"q": acct, "type": "accounts", "limit": "5"},
        )
        cuentas = datos.get("accounts", [])
        if not cuentas:
            raise SinResultados(f"no se encontró el usuario '{acct}' en {self._host(base)}")
        return cuentas[0]

    def _hashtag_por_rss(self, client: PoliteClient, base: str, tag: str) -> list[dict]:
        """Respaldo: RSS público de la etiqueta (/tags/<tag>.rss)."""
        xml = client.get_text(f"{base}/tags/{quote(tag)}.rss")
        try:
            raiz = ET.fromstring(xml.encode("utf-8"))
        except ET.ParseError as exc:
            raise BlockedError(
                f"no se pudo leer el RSS del hashtag en {self._host(base)}: {exc}"
            ) from exc

        estados: list[dict] = []
        for item in raiz.iter("item"):
            enlace = item.findtext("link") or ""
            medios: list[dict] = []
            for nodo in item.findall("media:content", _RSS_MEDIA):
                url = nodo.get("url")
                medio = (nodo.get("medium") or "").lower()
                tipo = (nodo.get("type") or "").lower()
                if not url or medio == "video" or tipo.startswith(("video/", "audio/")):
                    continue
                medios.append({"type": "image", "url": url, "preview_url": url})
            if not medios:
                descripcion = _html.unescape(item.findtext("description") or "")
                medios = [{"type": "image", "url": u, "preview_url": u}
                          for u in _IMG_SRC_RE.findall(descripcion)]
            if not medios:
                continue
            autor = ""
            if "/@" in enlace:
                autor = enlace.split("/@", 1)[1].split("/", 1)[0]
            categorias = [c.text or "" for c in item.findall("category")]
            descripcion = item.findtext("description") or ""
            estados.append({
                "id": enlace.rstrip("/").rsplit("/", 1)[-1],
                "url": enlace,
                "created_at": item.findtext("pubDate"),
                "content": f"{descripcion} {' '.join('#' + c for c in categorias)}",
                "tags": [{"name": c} for c in categorias if c] or [{"name": tag}],
                "account": {"acct": autor},
                "media_attachments": medios,
                # El RSS no expone el flag "sensitive": se marca como sensible
                # (la app no lo descarga si el usuario restringe el contenido adulto)
                "sensitive": True,
            })
        return estados

    # ------------------------------------------------------------------ normalización
    def _normalize(self, st: dict, media: dict, base: str) -> Artwork | None:
        url = media.get("url")
        if not url:
            return None
        text = st.get("content") or ""
        tags = [t.get("name", "") for t in st.get("tags", [])]
        tags += _HASHTAG_RE.findall(text)
        account = st.get("account", {})
        author = account.get("acct") or account.get("username")
        return Artwork(
            site=f"Mastodon · {self._host(base)}",
            site_id=str(st.get("id", "")),
            url=url,
            preview_url=media.get("preview_url") or url,
            page_url=st.get("url") or st.get("uri"),
            tags=list(dict.fromkeys(t for t in tags if t)),
            rating="sensitive" if st.get("sensitive") else "general",
            md5=None,
            author=author,
            license=None,
            created_at=st.get("created_at"),
            content_text=_TEXTO_RE.sub(" ", text)[:2000],
            source_field=None,
            raw=st,
        )
