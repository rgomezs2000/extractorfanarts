"""Filtros legales y éticos del núcleo (no desactivables por la UI).

Se aplican SIEMPRE antes de mostrar o descargar cualquier resultado:
  1. lista negra dura de tags (contenido de menores y afines),
  2. exclusión de plataformas de pago / contenido exclusivo,
  3. gate de rating adulto (activación explícita del usuario),
  4. política de "solo material liberado" (licencia permisiva),
  5. deduplicación por hash.
"""
from __future__ import annotations

import re

from .. import config
from ..models.artwork import Artwork

_TOKEN_RE = re.compile(r"[a-z0-9_]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def has_prohibited_tags(artwork: Artwork) -> bool:
    text = " ".join(artwork.tags)
    if not text:
        return False
    toks = _tokens(text)
    if toks & config.PROHIBITED_TAG_TOKENS:
        return True
    for tok in toks:
        if tok.startswith("pedo") or tok.startswith("loli") or tok.startswith("shota"):
            return True
    return False


def links_to_paid_platform(artwork: Artwork) -> bool:
    """Detecta enlaces hacia plataformas de pago en el contenido del resultado."""
    haystack = " ".join(
        (artwork.content_text or "", artwork.source_field or "", artwork.page_url or "")
    ).lower()
    if not haystack:
        return False
    return any(dom in haystack for dom in config.BLOCKED_PAID_DOMAINS)


def is_free_license(license_text: str | None) -> bool:
    if not license_text:
        return False
    low = license_text.lower()
    return any(hint in low for hint in config.FREE_LICENSE_HINTS)


def apply_filters(
    artworks: list[Artwork],
    allow_adult_ratings: list[str] | None = None,
    require_free_license: bool | None = None,
    seen_hashes: set[str] | None = None,
    limit: int | None = None,
) -> tuple[list[Artwork], dict[str, int]]:
    """Devuelve (obras admitidas, contador de motivos de descarte)."""
    allow = allow_adult_ratings or config.ALLOW_ADULT_RATINGS
    require_license = config.REQUIRE_FREE_LICENSE if require_free_license is None else require_free_license
    seen = seen_hashes if seen_hashes is not None else set()
    limit = limit or config.MAX_RESULTS_PER_SOURCE

    kept: list[Artwork] = []
    rejected: dict[str, int] = {}
    seen_in_run: set[str] = set()

    def _reject(reason: str) -> None:
        rejected[reason] = rejected.get(reason, 0) + 1

    for art in artworks:
        if has_prohibited_tags(art):
            _reject("contenido prohibido (lista negra)")
            continue
        if links_to_paid_platform(art):
            _reject("enlace a plataforma de pago")
            continue
        if art.rating not in allow:
            _reject(f"rating no permitido ({art.rating})")
            continue
        if require_license and not is_free_license(art.license):
            _reject("sin licencia liberada")
            continue
        if art.md5:
            if art.md5 in seen or art.md5 in seen_in_run:
                _reject("duplicado (hash)")
                continue
            seen_in_run.add(art.md5)
        kept.append(art)
        if len(kept) >= limit:
            break

    return kept, rejected
