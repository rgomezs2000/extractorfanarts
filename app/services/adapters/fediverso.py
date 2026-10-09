"""Adaptador del fediverso: cualquier instancia de Mastodon / Misskey / CherryPick.

Detecta automáticamente el software de la instancia y delega en el adaptador
correspondiente, de modo que no hay que limitarse a una sola instancia:

  - `@usuario@baraag.net`      → consulta esa instancia directamente.
  - `@usuario` + campo "Instancia" → usa la instancia indicada en la UI.
  - `#hashtag` / palabra clave → busca en la instancia elegida.

Detección (todo con endpoints públicos, sin login):
  - Mastodon → GET  {base}/api/v1/instance   (respuesta con "uri"/"title")
  - Misskey/CherryPick → POST {base}/api/meta (respuesta con "version"/"name")
El resultado se guarda en caché por host para no repetir la comprobación.
"""
from __future__ import annotations

import logging
from urllib.parse import urlparse

from ... import config
from ...models.artwork import Artwork, SearchQuery
from ..http_client import BlockedError, PoliteClient
from .base import SearchAdapter
from .mastodon import MastodonAdapter, host_de_handle, normalizar_instancia
from .misskey import MisskeyAdapter

logger = logging.getLogger("imaginteca")


class FediversoAdapter(SearchAdapter):
    name = "Fediverso"

    _tipos: dict[str, str] = {}  # host -> "mastodon" | "misskey"

    # ------------------------------------------------------------------ instancia
    def _base(self, query: SearchQuery) -> str:
        host = host_de_handle(query.usuario)
        if host:
            return normalizar_instancia(host)
        if query.instance:
            return normalizar_instancia(query.instance)
        por_defecto = (config.MASTODON_INSTANCES or ["mastodon.social"])[0]
        return normalizar_instancia(por_defecto)

    def _detectar(self, client: PoliteClient, base: str) -> str:
        host = urlparse(base).netloc or base
        if host in self._tipos:
            return self._tipos[host]

        tipo: str | None = None
        try:
            datos = client.get_json(f"{base}/api/v1/instance")
            if isinstance(datos, dict) and ("uri" in datos or "title" in datos) \
                    and "maintainerName" not in datos:
                tipo = "mastodon"
        except Exception:  # noqa: BLE001
            tipo = None

        if tipo is None:
            try:
                datos = client.post_json(f"{base}/api/meta", {})
                if isinstance(datos, dict) and (
                    "version" in datos or "maintainerName" in datos or "name" in datos
                ):
                    tipo = "misskey"
            except Exception:  # noqa: BLE001
                tipo = None

        if tipo is None:
            raise BlockedError(
                f"No se pudo detectar el software de '{host}'. Comprueba que sea una "
                "instancia de Mastodon, Misskey o CherryPick (y que su API sea pública)."
            )

        self._tipos[host] = tipo
        logger.info("fediverso: %s detectado como %s", host, tipo)
        return tipo

    # ------------------------------------------------------------------ búsqueda
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        base = self._base(query)
        tipo = self._detectar(client, base)
        adaptador: SearchAdapter = (
            MisskeyAdapter(base) if tipo == "misskey" else MastodonAdapter(base)
        )
        return adaptador.search(client, query)
