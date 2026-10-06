"""Interfaz común de los adaptadores de búsqueda."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ...models.artwork import Artwork, SearchQuery
from ..http_client import PoliteClient


class SearchAdapter(ABC):
    """Todo adaptador convierte una SearchQuery en una lista de Artwork."""

    name = "base"

    @abstractmethod
    def search(self, client: PoliteClient, query: SearchQuery) -> list[Artwork]:
        """Ejecuta la búsqueda nativa de la plataforma (su algoritmo público)."""


def split_tags(tags_text: str) -> list[str]:
    """Separa tags por espacios y/o comas, quitando el '#' si viene."""
    if not tags_text:
        return []
    out = []
    for part in tags_text.replace(",", " ").split():
        part = part.strip().lstrip("#").strip()
        if part:
            out.append(part)
    return out
