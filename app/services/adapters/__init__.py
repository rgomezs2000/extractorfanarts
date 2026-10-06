"""Registro de adaptadores: redes sociales, boorus y wikis de fandom."""
from __future__ import annotations

from ... import config
from .base import SearchAdapter, split_tags
from .booru import BooruAdapter
from .mastodon import MastodonAdapter
from .misskey import MisskeyAdapter
from .bluesky import BlueskyAdapter
from .deviantart import DeviantArtAdapter
from .tumblr import TumblrAdapter
from .twitter import XAdapter
from .pinterest import PinterestAdapter
from .newgrounds import NewgroundsAdapter
from .mediawiki import MediaWikiAdapter

# Boorus (plantilla replicable: una entrada de configuración por sitio)
BOORU_ADAPTERS: dict[str, SearchAdapter] = {
    site["name"]: BooruAdapter(site) for site in config.BOORU_SITES
}

# Redes sociales
SOCIAL_ADAPTERS: dict[str, SearchAdapter] = {}
for instance in config.MASTODON_INSTANCES:
    SOCIAL_ADAPTERS[f"Mastodon · {instance}"] = MastodonAdapter(instance)
for instance in config.MISSKEY_INSTANCES:
    SOCIAL_ADAPTERS[f"Misskey · {instance}"] = MisskeyAdapter(instance)
SOCIAL_ADAPTERS["Bluesky"] = BlueskyAdapter()
SOCIAL_ADAPTERS["DeviantArt"] = DeviantArtAdapter()
SOCIAL_ADAPTERS["Tumblr"] = TumblrAdapter()
SOCIAL_ADAPTERS["X (Twitter)"] = XAdapter()
SOCIAL_ADAPTERS["Pinterest"] = PinterestAdapter()
SOCIAL_ADAPTERS["Newgrounds"] = NewgroundsAdapter()

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
]
