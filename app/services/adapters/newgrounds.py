"""Adaptador de Newgrounds — limitación documentada.

Newgrounds NO expone una API pública de arte:
  - newgrounds.io (API oficial) cubre juegos, medallas y guardado en la nube;
    su lista de componentes no incluye galerías de arte.
  - Las páginas de arte del sitio están protegidas (NG Guard) y el scraping
    queda fuera del alcance ético del proyecto (ver informe §4).

Este adaptador existe para que la plataforma aparezca documentada en la lista
de redes; al usarla explica el motivo. No se implementa scraping ni evasión.
"""
from __future__ import annotations

from ...models.artwork import Artwork, SearchQuery
from ..http_client import ConfigError, PoliteClient
from .base import SearchAdapter


class NewgroundsAdapter(SearchAdapter):
    name = "Newgrounds"

    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        raise ConfigError(
            "Newgrounds no tiene API pública de arte: newgrounds.io solo cubre "
            "juegos/medallas y el sitio protege sus páginas de arte (NG Guard). "
            "El scraping y la evasión de protecciones están fuera del alcance "
            "ético de este proyecto (informe §4). Opciones: descargar el arte "
            "manualmente desde newgrounds.com/art o usar otra plataforma."
        )
