"""Registro de adaptadores: redes sociales, boorus y wikis de fandom."""
from __future__ import annotations

from ... import config
from .base import SearchAdapter, split_tags
from .booru import BooruAdapter
from .fediverso import FediversoAdapter
from .mastodon import MastodonAdapter
from .misskey import MisskeyAdapter
from .bluesky import BlueskyAdapter
from .deviantart import DeviantArtAdapter
from .tumblr import TumblrAdapter
from .twitter import XAdapter
from .pinterest import PinterestAdapter
from .pixiv import PixivAdapter
from .newgrounds import NewgroundsAdapter
from .mediawiki import MediaWikiAdapter

# Boorus (plantilla replicable: una entrada de configuración por sitio)
BOORU_ADAPTERS: dict[str, SearchAdapter] = {
    site["name"]: BooruAdapter(site) for site in config.BOORU_SITES
}

# Redes sociales
# El fediverso es una sola entrada que sirve para CUALQUIER instancia de
# Mastodon/Misskey/CherryPick (la instancia se elige en la UI o se deduce del
# propio handle @usuario@instancia).
SOCIAL_ADAPTERS: dict[str, SearchAdapter] = {
    "Fediverso (Mastodon/Misskey/CherryPick)": FediversoAdapter(),
    "Bluesky": BlueskyAdapter(),
    "DeviantArt": DeviantArtAdapter(),
    "Tumblr": TumblrAdapter(),
    "X (Twitter)": XAdapter(),
    "Pinterest": PinterestAdapter(),
    "Pixiv": PixivAdapter(),
    "Newgrounds": NewgroundsAdapter(),
}

# Wikis de fandom
WIKI_ADAPTERS: dict[str, SearchAdapter] = {
    "Fandom (MediaWiki)": MediaWikiAdapter(),
}

_REGISTRY = {
    "social": SOCIAL_ADAPTERS,
    "booru": BOORU_ADAPTERS,
    "wiki": WIKI_ADAPTERS,
}


def adapter_for(kind: str, platform: str) -> SearchAdapter | None:
    """Devuelve el adaptador para la combinación tipo/plataforma elegida."""
    return _REGISTRY.get(kind, {}).get(platform)


__all__ = [
    "SearchAdapter", "split_tags",
    "BOORU_ADAPTERS", "SOCIAL_ADAPTERS", "WIKI_ADAPTERS", "adapter_for",
    "FediversoAdapter", "MastodonAdapter", "MisskeyAdapter",
]
