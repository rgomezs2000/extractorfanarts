"""Filtros legales y éticos del núcleo.

Se aplican SIEMPRE antes de mostrar o descargar cualquier resultado:
  1. lista negra de tags (config: `PROHIBITED_TAG_TOKENS`, `PROHIBITED_TAG_PREFIXES`),
  2. exclusión de plataformas de pago / contenido exclusivo (`BLOCKED_PAID_DOMAINS`),
  3. tu lista de exclusión (`EXCLUDED_TAG_TOKENS`, `EXCLUDED_DOMAINS`,
     `EXCLUDED_TEXT_TOKENS`),
  4. gate de rating adulto (activación explícita del usuario),
  5. política de "solo material liberado" (licencia permisiva),
  6. deduplicación por hash.

**Toda la lista negra vive en `app/config.py` como arrays** (o en `config_local.py`, que
los sobreescribe): este módulo no guarda ningún valor, solo los lee, así que para
ajustarla basta con editar el config y reiniciar. Con `describir_filtros()` se muestra al
usuario lo que hay configurado (la app lo hace con el botón «¿Qué se filtra?»).
"""
from __future__ import annotations

import re

from .. import config
from ..models.artwork import Artwork

_TOKEN_RE = re.compile(r"[a-z0-9_]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _lista(valor) -> list[str]:
    """Normaliza una lista del config (admite lista, tupla, conjunto o texto suelto)."""
    if not valor:
        return []
    if isinstance(valor, str):
        valor = [valor]
    return [str(v).strip().lower() for v in valor if str(v).strip()]


def tags_prohibidos() -> set[str]:
    """Tags exactos de la lista negra (leídos del config, nunca incrustados aquí)."""
    return set(_lista(getattr(config, "PROHIBITED_TAG_TOKENS", ())))


def prefijos_prohibidos() -> tuple[str, ...]:
    """Prefijos de tags de la lista negra (leídos del config)."""
    return tuple(_lista(getattr(config, "PROHIBITED_TAG_PREFIXES", ())))


def dominios_de_pago() -> list[str]:
    """Dominios de plataformas de pago excluidas (leídos del config)."""
    return _lista(getattr(config, "BLOCKED_PAID_DOMAINS", ()))


def _casa_lista(texto: str, lista: list[str]) -> str | None:
    """¿El texto contiene alguna entrada de la lista? («algo*» = empieza por).

    Devuelve la entrada que casó (para poder decirte cuál fue), o None.
    """
    if not texto or not lista:
        return None
    bajo = texto.lower()
    tokens = _tokens(texto)
    for entrada in lista:
        if entrada.endswith("*"):
            prefijo = entrada[:-1]
            if prefijo and any(t.startswith(prefijo) for t in tokens):
                return entrada
        elif entrada in tokens or entrada in bajo:
            return entrada
    return None


def motivo_exclusion_propia(artwork: Artwork) -> str | None:
    """Motivo por el que TU lista de exclusión descarta este resultado (o None).

    Es independiente de la lista negra del núcleo: solo mira tus `EXCLUDED_TAG_TOKENS`,
    `EXCLUDED_DOMAINS` y `EXCLUDED_TEXT_TOKENS` (arrays de app/config.py, o de
    app/config_local.py / ~/.imaginteca/config_local.py para que no se pierdan
    al actualizar la app).
    """
    entrada = _casa_lista(" ".join(artwork.tags or []), _lista(config.EXCLUDED_TAG_TOKENS))
    if entrada:
        return f"excluido por tu lista (tag {entrada})"
    haystack = " ".join((artwork.content_text or "", artwork.source_field or "",
                         artwork.page_url or "", artwork.url or "")).lower()
    for dominio in _lista(config.EXCLUDED_DOMAINS):
        if dominio and dominio in haystack:
            return f"excluido por tu lista (dominio {dominio})"
    texto = " ".join([artwork.content_text or ""] + list(artwork.tags or []))
    entrada = _casa_lista(texto, _lista(config.EXCLUDED_TEXT_TOKENS))
    if entrada:
        return f"excluido por tu lista (texto «{entrada}»)"
    return None


def has_prohibited_tags(artwork: Artwork) -> bool:
    """¿La obra lleva algún tag de la lista negra? (tags exactos y prefijos del config)."""
    text = " ".join(artwork.tags)
    if not text:
        return False
    toks = _tokens(text)
    if toks & tags_prohibidos():
        return True
    prefijos = prefijos_prohibidos()
    return bool(prefijos) and any(t.startswith(prefijos) for t in toks)


def links_to_paid_platform(artwork: Artwork) -> bool:
    """Detecta enlaces hacia plataformas de pago en el contenido del resultado."""
    haystack = " ".join(
        (artwork.content_text or "", artwork.source_field or "", artwork.page_url or "")
    ).lower()
    if not haystack:
        return False
    return any(dom in haystack for dom in dominios_de_pago())


def is_free_license(license_text: str | None) -> bool:
    if not license_text:
        return False
    low = license_text.lower()
    return any(hint in low for hint in config.FREE_LICENSE_HINTS)


def describir_filtros(allow_adult_ratings: list[str] | None = None,
                      require_free_license: bool | None = None,
                      limit: int | None = None) -> str:
    """Texto (para mostrar al usuario) con la lista negra y los filtros activos."""
    permitidos = allow_adult_ratings or config.ALLOW_ADULT_RATINGS
    licencia = config.REQUIRE_FREE_LICENSE if require_free_license is None else require_free_license
    tope = limit or config.MAX_RESULTS_PER_SOURCE

    lineas = [
        "Estos filtros se aplican SIEMPRE, antes de mostrar o descargar un resultado.",
        "Viven en el núcleo (app/config.py y app/services/filters.py) y la interfaz no",
        "puede desactivarlos.",
        "",
        "1) LISTA NEGRA de tags → se descarta el resultado",
        f"   • tags exactos (PROHIBITED_TAG_TOKENS): "
        f"{', '.join(sorted(tags_prohibidos())) or '(vacía)'}",
        f"   • prefijos (PROHIBITED_TAG_PREFIXES): "
        f"{', '.join(p + '*' for p in prefijos_prohibidos()) or '(vacía)'}",
        "",
        "2) PLATAFORMAS DE PAGO / CONTENIDO EXCLUSIVO → se descarta el resultado cuyo",
        "   enlace, texto o página apunte a (BLOCKED_PAID_DOMAINS):",
        f"   • {', '.join(dominios_de_pago()) or '(vacía)'}",
        "",
        "3) RATING ADULTO (casilla «Contenido adulto» en Opciones)",
        f"   • permitidos ahora: {', '.join(sorted(permitidos))}",
        "   • sin la casilla solo pasan los ratings general/sensitive.",
        "",
        "4) LICENCIA (casilla «Solo licencia liberada»)",
        f"   • {'ACTIVADA: solo licencias permisivas' if licencia else 'desactivada: no se exige licencia'}",
        f"   • se consideran liberadas: {', '.join(config.FREE_LICENSE_HINTS)}",
        "",
        "5) DUPLICADOS por hash (md5): un mismo archivo no se repite.",
        "",
        f"6) TOPE de resultados por fuente: {tope} (MAX_RESULTS_PER_SOURCE).",
        "",
        "TU LISTA DE EXCLUSIÓN (la ajustas tú, se suma a lo anterior)",
        f"   • se lee de: {config.CONFIG_LOCAL_USADO or '(sin config_local.py: usa app/config.py)'}",
        f"   • EXCLUDED_TAG_TOKENS: {', '.join(_lista(config.EXCLUDED_TAG_TOKENS)) or '(vacía)'}",
        f"   • EXCLUDED_DOMAINS: {', '.join(_lista(config.EXCLUDED_DOMAINS)) or '(vacía)'}",
        f"   • EXCLUDED_TEXT_TOKENS: {', '.join(_lista(config.EXCLUDED_TEXT_TOKENS)) or '(vacía)'}",
        "   • «algo*» significa «empieza por». Ejemplos para pegar en config_local.py:",
        '        EXCLUDED_TAG_TOKENS = {"gore", "vore", "scat", "guroli*"}',
        '        EXCLUDED_DOMAINS = ["deviantart.com"]',
        '        EXCLUDED_TEXT_TOKENS = ["commission open", "adopt"]',
        "",
        "Qué verás cuando algo se descarte: en los resultados, el motivo y el número",
        "(«Descartados por: contenido prohibido (lista negra): 3»), y en el registro",
        "(app-AAAA-MM-DD.log) la línea «resultados filtrados: … descartados → …».",
    ]
    return "\n".join(lineas)


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
        motivo = motivo_exclusion_propia(art)
        if motivo:
            _reject(motivo)
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
