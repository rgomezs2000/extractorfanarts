"""Adaptador de Mastodon (API pública, sin login) — cualquier instancia.

Soporta:
  - `@usuario`          → se busca en la instancia seleccionada (campo Instancia).
  - `@usuario@host.tld` → se consulta **la instancia de ese usuario** directamente
    (funciona con cualquier servidor del fediverso sin límites de una sola instancia).
  - `#hashtag` / palabra clave → timeline pública / búsqueda en la instancia elegida.

Todo con endpoints públicos: **no se envía autenticación** (el parámetro
`resolve=true`, que sí exige token, ya no se usa).

Respaldo para instancias restrictivas: algunas (p. ej. baraag.net) responden
`422 {"error":"This method requires an authenticated user"}` en las timelines por
hashtag. En ese caso se usa el **RSS público** de la etiqueta
(`/tags/<tag>.rss`), que sí es abierto, y como último recurso la timeline pública.
"""
from __future__ import annotations

import html as _html
import logging
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote, urlparse

from ...models.artwork import Artwork, SearchQuery
from ..http_client import BlockedError, ConfigError, PoliteClient
from .base import SearchAdapter

logger = logging.getLogger("extractorfanarts")

_HASHTAG_RE = re.compile(r"#([\w]+)")
_IMG_SRC_RE = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)
_RSS_MEDIA = {"media": "http://search.yahoo.com/mrss/"}


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
        if query.usuario:
            statuses = self._by_user(client, query, base)
        elif query.hashtag:
            statuses = self._by_hashtag(client, query, base)
        else:
            statuses = self._by_keyword(client, query, base)

        out: list[Artwork] = []
        for st in statuses:
            for media in st.get("media_attachments", []):
                if media.get("type") not in ("image", "unknown"):
                    continue
                art = self._normalize(st, media, base)
                if art is not None:
                    out.append(art)
                    if len(out) >= query.limit:
                        return out
        return out

    def _by_user(self, client: PoliteClient, query: SearchQuery, base: str) -> list[dict]:
        acct = query.usuario.strip().lstrip("@")
        nombre = acct.split("@", 1)[0]
        try:
            # Endpoint público de Mastodon 3.4+ (no requiere autenticación)
            cuenta = client.get_json(
                f"{base}/api/v1/accounts/lookup", params={"acct": nombre}
            )
        except Exception:  # noqa: BLE001
            cuenta = None
        if not cuenta or not cuenta.get("id"):
            # Respaldo: búsqueda SIN `resolve` (resolve=true exige token → HTTP 401)
            datos = client.get_json(
                f"{base}/api/v2/search",
                params={"q": acct, "type": "accounts", "limit": "5"},
            )
            cuentas = datos.get("accounts", [])
            if not cuentas:
                raise BlockedError(
                    f"no se encontró el usuario '{acct}' en {self._host(base)}"
                )
            cuenta = cuentas[0]
        return client.get_json(
            f"{base}/api/v1/accounts/{cuenta['id']}/statuses",
            params={"limit": "40", "only_media": "true"},
        )

    def _by_hashtag(self, client: PoliteClient, query: SearchQuery, base: str) -> list[dict]:
        tag = query.hashtag.strip().lstrip("#")
        try:
            return client.get_json(
                f"{base}/api/v1/timelines/tag/{tag}",
                params={"limit": "40", "only_media": "true"},
            )
        except (BlockedError, ConfigError) as exc:
            # Instancias como baraag.net exigen token para esta timeline:
            # se usa el RSS público de la etiqueta (abierto, sin login).
            logger.info(
                "timeline por hashtag no disponible en %s (%s); se intenta el RSS público",
                self._host(base), exc,
            )
        return self._hashtag_por_rss(client, base, tag)

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
            estados.append({
                "id": enlace.rstrip("/").rsplit("/", 1)[-1],
                "url": enlace,
                "created_at": item.findtext("pubDate"),
                "content": item.findtext("description") or "",
                "tags": [{"name": c} for c in categorias if c] or [{"name": tag}],
                "account": {"acct": autor},
                "media_attachments": medios,
                # El RSS no expone el flag "sensitive": se marca como sensible
                # (la app no lo descarga si el usuario restringe el contenido adulto)
                "sensitive": True,
            })
        return estados

    def _by_keyword(self, client: PoliteClient, query: SearchQuery, base: str) -> list[dict]:
        try:
            datos = client.get_json(
                f"{base}/api/v2/search",
                params={"q": query.keyword, "type": "statuses", "limit": "40"},
            )
            return datos.get("statuses", [])
        except (BlockedError, ConfigError) as exc:
            logger.info("búsqueda por texto no disponible en %s (%s); se usa la timeline pública",
                        self._host(base), exc)
        # Respaldo: timeline pública filtrada localmente por la palabra clave
        estados = client.get_json(
            f"{base}/api/v1/timelines/public",
            params={"limit": "40", "only_media": "true"},
        )
        aguja = query.keyword.strip().lower()
        return [
            e for e in estados
            if aguja in (e.get("content") or "").lower()
            or aguja in (e.get("spoiler_text") or "").lower()
        ]

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
            content_text=re.sub(r"<[^>]+>", " ", text)[:2000],
            source_field=None,
            raw=st,
        )
