"""Configuración central de ExtractorFanarts.

Por ahora NO hay autenticación interna ni gestión de usuarios: las claves de
las APIs se colocan aquí (ver README). Los datos sensibles deberían migrarse
a variables de entorno o un archivo externo en una versión futura.
"""
from pathlib import Path

APP_NAME = "ExtractorFanarts"
APP_VERSION = "0.1.0"

# User-Agent identificado (cortesía / transparencia con los sitios)
# Nota: debe ser ASCII puro (los headers HTTP no admiten acentos).
USER_AGENT = (
    f"{APP_NAME}/{APP_VERSION} (herramienta personal de archivo de fanarts; "
    "respeta los limites y terminos de cada API; contacto: usuario-local)"
)

# ------------------------------------------------------------------ carpetas
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "ExtractorFanarts"
DB_PATH = Path.home() / ".extractorfanarts" / "history.db"

# ------------------------------------------------------------------ credenciales (por ahora en el código)
# Gelbooru: https://gelbooru.com/index.php?page=account&s=options
GELBOORU_API_KEY = ""
GELBOORU_USER_ID = ""

# Rule34.xxx: https://rule34.xxx/index.php?page=account&s=options
RULE34_API_KEY = ""
RULE34_USER_ID = ""

# DeviantArt: https://www.deviantart.com/developers/ (OAuth2 client credentials)
DEVIANTART_CLIENT_ID = ""
DEVIANTART_CLIENT_SECRET = ""

# Tumblr: https://www.tumblr.com/oauth/apps (consumer key, OAuth 1.0a)
TUMBLR_API_KEY = ""

# X / Twitter: API v2 oficial, DE PAGO por uso desde 2026 (app de desarrollador
# con facturación activa). https://developer.x.com/
# Opción A: Bearer token ya emitido (app-only).
X_BEARER_TOKEN = ""
# Opción B: consumer key/secret (OAuth2 client credentials → se obtiene el Bearer solo).
X_API_KEY = ""
X_API_SECRET = ""

# Pinterest: API v5 oficial (app aprobada + token OAuth del usuario).
# https://developers.pinterest.com/
PINTEREST_ACCESS_TOKEN = ""
# Necesario para la búsqueda GLOBAL (/v5/search/partner/pins, beta para apps
# asociadas); código ISO 3166-1 alpha-2 (ej. "US"). Sin esto se busca sobre
# los pins de la cuenta conectada (/v5/search/pins).
PINTEREST_COUNTRY_CODE = ""

# Newgrounds: newgrounds.io no expone arte (solo juegos/medallas) y el sitio
# protege sus páginas de arte. El adaptador informa el motivo al usarse;
# no se implementa scraping. Se dejan los campos por documentación.
NEWGROUNDS_APP_ID = ""
NEWGROUNDS_SESSION_ID = ""

# Instancias del fediverso (sin claves; se pueden agregar más aquí).
# CherryPick usa la misma API que Misskey: basta agregar su instancia.
MASTODON_INSTANCES = ["mastodon.social"]
MISSKEY_INSTANCES = ["misskey.io"]

# ------------------------------------------------------------------ boorus soportados
# Plantilla replicable: cada entrada usa una de las familias ya implementadas
# ("gelbooru" | "danbooru" | "moebooru" | "philomena"). "auth" indica claves
# obligatorias del sitio (ver _auth_params en services/adapters/booru.py).
BOORU_SITES = [
    {"name": "Safebooru",  "family": "gelbooru", "base": "https://safebooru.org",
     "auth": None,
     "view_tpl": "https://safebooru.org/index.php?page=post&s=view&id={id}"},
    {"name": "Gelbooru",   "family": "gelbooru", "base": "https://gelbooru.com",
     "auth": ("GELBOORU",),
     "view_tpl": "https://gelbooru.com/index.php?page=post&s=view&id={id}"},
    {"name": "Rule34.xxx", "family": "gelbooru", "base": "https://api.rule34.xxx",
     "auth": ("RULE34",),
     "view_tpl": "https://rule34.xxx/index.php?page=post&s=view&id={id}"},
    {"name": "The Big ImageBoard", "family": "gelbooru", "base": "https://tbib.org",
     "auth": None,
     "view_tpl": "https://tbib.org/index.php?page=post&s=view&id={id}"},
    {"name": "Xbooru",     "family": "gelbooru", "base": "https://xbooru.com",
     "auth": None,
     "view_tpl": "https://xbooru.com/index.php?page=post&s=view&id={id}"},
    {"name": "Hypnohub",   "family": "gelbooru", "base": "https://hypnohub.net",
     "auth": None,
     "view_tpl": "https://hypnohub.net/index.php?page=post&s=view&id={id}"},
    {"name": "Danbooru",   "family": "danbooru", "base": "https://danbooru.donmai.us",
     "auth": None,
     "view_tpl": "https://danbooru.donmai.us/posts/{id}"},
    {"name": "Safebooru (Donmai)", "family": "danbooru", "base": "https://safebooru.donmai.us",
     "auth": None,
     "view_tpl": "https://safebooru.donmai.us/posts/{id}"},
    {"name": "Yande.re",   "family": "moebooru", "base": "https://yande.re",
     "auth": None,
     "view_tpl": "https://yande.re/post/show/{id}"},
    {"name": "Konachan",   "family": "moebooru", "base": "https://konachan.com",
     "auth": None,
     "view_tpl": "https://konachan.com/post/show/{id}"},
    {"name": "Konachan (SFW)", "family": "moebooru", "base": "https://konachan.net",
     "auth": None,
     "view_tpl": "https://konachan.net/post/show/{id}"},
    {"name": "Derpibooru", "family": "philomena", "base": "https://derpibooru.org",
     "auth": None,
     "view_tpl": "https://derpibooru.org/images/{id}"},
]

# ------------------------------------------------------------------ políticas de descarga
# Ratings permitidos por defecto. Los ratings "questionable"/"explicit" exigen
# activación explícita en la UI (verificación de mayoría de edad del usuario).
ALLOW_ADULT_RATINGS = ["general", "sensitive"]

# Si es True (o se marca "Solo material liberado" en la UI) únicamente se
# descargan obras con licencia permisiva explícita.
REQUIRE_FREE_LICENSE = False

MAX_RESULTS_PER_SOURCE = 100
MAX_PREVIEW_BYTES = 8 * 1024 * 1024  # tope para la imagen de ejemplo

# Requisito: si el archivo destino ya existe, se sobreescribe.
OVERWRITE_EXISTING = True

# ------------------------------------------------------------------ mejora de calidad (upscaling + WebP)
# REQUISITO: todo lo descargado se convierte SIEMPRE a .webp y el original no
# se conserva (services/enhance.py). ENHANCE_DEFAULT_ON controla SOLO el upscaling.
WEBP_ALWAYS = True             # conversión a WebP obligatoria (nunca se guarda el original)
ENHANCE_DEFAULT_ON = True
NO_UPSCALE_ABOVE = 1600        # lado mayor >= 1600 px: sin upscale, solo WebP
UPSCALE_BUCKETS = [
    (0, 699, 4),       # hasta 699 px     -> 4x
    (700, 799, 3),     # de 700 a 799 px  -> 3x
    (800, 1500, 2),    # de 800 a 1500 px -> 2x
    (1501, 1599, 1),   # de 1501 a 1599 px -> 1x (solo WebP)
]
WEBP_QUALITY_DEFAULT = 90     # calidad WebP configurable en la UI (1-100)
AI_EXE_OVERRIDE = ""          # ruta manual al exe IA si no está en vendor/PATH
AI_MODEL = "realesrgan-x4plus-anime"   # modelo anime (fanart); "realesrgan-x4plus" para realista

# ------------------------------------------------------------------ anti-bloqueo (pausas prudentes, sin evasión)
MIN_REQUEST_INTERVAL = 1.5     # segundos mínimos entre peticiones a un mismo dominio
BACKOFF_BASE = 30.0            # pausa inicial ante 429/5xx (crece exponencialmente)
BACKOFF_MAX = 600.0            # tope de pausa
BLOCK_PAUSE = 300.0            # pausa ante posible bloqueo (403/401)
MAX_RETRIES = 3                # reintentos máximos por petición

# ------------------------------------------------------------------ legal / ético
# Lista negra DURA de tokens de tags (contenido de menores y afines).
# Vive en el núcleo y no puede desactivarse desde la UI.
PROHIBITED_TAG_TOKENS = {
    "loli", "lolicon", "shota", "shotacon", "cub", "toddlercon",
    "underage", "under_age", "childporn", "child_porn",
}

# Plataformas de pago y contenido exclusivo: se descartan resultados cuyos
# enlaces/textos apunten a estos dominios (ver informe §4.5).
BLOCKED_PAID_DOMAINS = [
    "patreon.com", "fanbox.cc", "onlyfans.com", "fansly.com",
    "unifans.io", "fansky.social", "fansky.app", "subscribestar.adult",
    "gumroad.com",
]

# Indicadores de licencia considerados "material liberado" (archivo personal).
FREE_LICENSE_HINTS = (
    "cc0", "public domain", "cc-by", "cc by", "creative commons",
)
