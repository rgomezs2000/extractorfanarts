"""Modelo de datos: una obra de arte normalizada desde cualquier fuente."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Artwork:
    """Representación común de un fanart/arte/imagen, sea cual sea el origen."""

    site: str                  # nombre de la plataforma/instancia
    site_id: str               # id de la obra en su sitio
    url: str                   # URL del archivo completo
    preview_url: str | None = None   # miniatura / muestra
    page_url: str | None = None      # página de la obra en el sitio
    tags: list[str] = field(default_factory=list)
    rating: str = "general"    # general | sensitive | questionable | explicit
    md5: str | None = None
    author: str | None = None
    license: str | None = None
    created_at: str | None = None
    content_text: str | None = None   # texto del post/descripción (para filtros)
    source_field: str | None = None   # campo "source" de los boorus
    raw: dict = field(default_factory=dict)

    def summary(self) -> str:
        author = self.author or "desconocido"
        ntags = len(self.tags)
        return f"{author} — {self.site} ({ntags} tags)"


@dataclass
class SearchQuery:
    """Filtro de búsqueda introducido por el usuario en la UI."""

    kind: str = "social"       # "social" | "booru" | "wiki"
    platform: str = ""         # clave de la plataforma en el registro de adaptadores
    usuario: str = ""          # @usuario (redes sociales)
    keyword: str = ""          # palabra clave (redes sociales)
    hashtag: str = ""          # #hashtag (redes sociales)
    tags: str = ""             # tags separadas por espacio/comas (boorus)
    fandom: str = ""           # nombre del fandom / franquicia (wikis)
    character: str = ""        # personaje y/o concepto (wikis)
    wiki_url: str = ""         # URL completa de la wiki (opcional)
    limit: int = 100
