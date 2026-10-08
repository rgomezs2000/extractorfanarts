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
    """Separa tags por espacios y/o comas, sin repetir y quitando el '#' y las comillas.

    Admite **N tags** (los que quieras), que es lo natural en un booru:
    `lori_loud 1girl solo blonde_hair` → 4 tags que se buscan todos a la vez.
    """
    if not tags_text:
        return []
    out: list[str] = []
    for part in tags_text.replace(",", " ").split():
        limpio = part.strip().strip('"').lstrip("#").strip()
        if limpio and limpio.lower() not in [v.lower() for v in out]:
            out.append(limpio)
    return out
