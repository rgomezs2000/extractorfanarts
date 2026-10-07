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
LOG_DIR = Path.home() / ".extractorfanarts" / "logs"

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

# Pixiv: la API oficial de la app EXIGE cuenta (no hay acceso anónimo).
# Se usa con TU cuenta mediante un refresh token (no se guarda tu contraseña).
# Obtén el token con:  python scripts\pixiv_token.py
# Los dos valores siguientes son las constantes públicas de la app oficial
# (las mismas que usan los clientes conocidos); no son secretos tuyos.
PIXIV_CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
PIXIV_CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"
PIXIV_REFRESH_TOKEN = ""     # <- pega aquí tu refresh token (en config_local.py)

# Límites para las animaciones "ugoira" de Pixiv (ZIP de fotogramas → WebP animado)
UGOIRA_MAX_FRAMES = 400      # fotogramas máximos a componer
UGOIRA_MAX_ZIP_MB = 200      # tamaño máximo del ZIP descargado

# Cabecera Referer obligatoria en algunos CDN: el de Pixiv (i.pximg.net) responde
# 403 sin ella. Se aplica por sufijo de dominio.
REFERER_DOMAINS = {
    "pximg.net": "https://www.pixiv.net/",
    "pixiv.net": "https://www.pixiv.net/",
}

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

# ------------------------------------------------------------------ Cloudflare (opcional)
# Algunos boorus (p. ej. Rule34.xxx) activan defensas Cloudflare que responden
# un CAPTCHA en lugar de datos. El procedimiento RESPETUOSO y documentado es:
#   1) abrir el sitio en TU navegador y resolver el CAPTCHA manualmente,
#   2) copiar la cookie `cf_clearance` y el User-Agent exacto de ese navegador,
#   3) pegarlos aquí (o mejor en app/config_local.py) y reiniciar la app.
# La autorización es tuya y del navegador que resolvió el reto; caduca como en
# el navegador. No se resuelve ni evade ningún CAPTCHA automáticamente.
CF_CLEARANCE = ""      # valor de la cookie cf_clearance (~450-520 caracteres)
CF_USER_AGENT = ""     # User-Agent exacto del navegador que resolvió el CAPTCHA
CF_DOMAINS = ["rule34.xxx"]   # dominios (y subdominios) donde se usarán

# Transporte con huella de navegador para los dominios de CF_DOMAINS.
# "" = automático: se activa solo si hay CF_CLEARANCE y curl_cffi está instalado
# (python scripts\setup_vendor.py --ai). Valores válidos de curl_cffi:
# "chrome", "chrome124", "edge101", "firefox133", "safari18_0", etc.
BROWSER_IMPERSONATE = ""

# Dominios que exigen "aspecto de navegador" (bot-check de Cloudflare):
# se les aplica el transporte con huella de Chrome + un User-Agent de navegador.
# - rule34.xxx: además lleva la cookie cf_clearance (CF_DOMAINS).
# - fandom.com / nocookie.net: el CDN de imágenes de Fandom bloquea a clientes
#   que no parecen un navegador (verificado: "Just a moment..." → 403 sin UA real).
BROWSER_DOMAINS = ["rule34.xxx", "fandom.com", "nocookie.net", "wikia.com", "booru.allthefallen.moe"]

# User-Agent de navegador usado en BROWSER_DOMAINS cuando no hay CF_USER_AGENT.
# Se puede sobreescribir en app/config_local.py (por ejemplo con el UA real de tu
# navegador, que es lo que funciona mejor contra Cloudflare).
DEFAULT_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36"
)

# Instancias del fediverso: solo son los valores POR DEFECTO que propone la UI.
# La app puede leer CUALQUIER instancia de Mastodon/Misskey/CherryPick:
#   - escribe la instancia en el campo "Instancia" de la UI, o
#   - usa @usuario@instancia (se consulta la instancia de ese usuario).
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
     {"name": "ATF Booru", "family": "danbooru", "base": "https://booru.allthefallen.moe/",
      "auth": None,
      "view_tpl": "https://booru.allthefallen.moe/posts/{id}"},
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

# Guardar un archivo .json de metadatos junto a cada imagen (autoría, origen,
# licencia, tags). DESACTIVADO por defecto: solo se descarga la imagen.
# Se puede activar con la casilla "Guardar metadatos .json" en la UI.
WRITE_SIDECAR_JSON = False

# ------------------------------------------------------------------ mejora de calidad (upscaling + WebP)
# REQUISITO: todo lo descargado se convierte SIEMPRE a .webp y el original no
# se conserva (services/enhance.py). ENHANCE_DEFAULT_ON controla SOLO el upscaling.
WEBP_ALWAYS = True             # conversión a WebP obligatoria (nunca se guarda el original)
ENHANCE_DEFAULT_ON = True
NO_UPSCALE_ABOVE = 1600        # (histórico) umbral antiguo; ahora lo gobiernan UPSCALE_BUCKETS
UPSCALE_BUCKETS = [
    (0, 699, 4),       # hasta 699 px      -> 4x
    (700, 799, 3),     # de 700 a 799 px   -> 3x
    (800, 1500, 2),    # de 800 a 1500 px  -> 2x
    (1501, 1599, 1),   # de 1501 a 1599 px -> 1x (solo WebP)
    (1600, 7679, 2),   # de 1600 px en adelante -> 2x, con tope de 8K
]

# Tope de resolución de salida: ninguna imagen mejorada supera este lado mayor
# (7680 px = 8K UHD). Si el factor la excediera, se reduce al tope (nunca se
# reduce por debajo del tamaño original).
MAX_OUTPUT_SIDE = 7680
# Límite de píxeles para usar IA (evita trabajos desmesurados que la GPU no
# terminaría en un tiempo razonable); por encima se usa Lanczos al tamaño objetivo.
AI_MAX_PIXELS = 50_000_000

WEBP_QUALITY_DEFAULT = 90     # calidad WebP configurable en la UI (1-100)
AI_EXE_OVERRIDE = ""          # ruta manual al exe IA si no está en vendor/PATH
AI_MODEL = "realesrgan-x4plus-anime"   # modelo x4 (fanart); "realesrgan-x4plus" para realista
# Modelo multiescala (variantes x2/x3/x4 incluidas). Se usa para 2x y 3x porque
# los modelos x4 con -s 2/3 producen imágenes corruptas en realesrgan-ncnn-vulkan.
AI_MODEL_ESCALA = "realesr-animevideov3"

# Definición (afilado): porcentaje de UnsharpMask aplicado tras el upscaling.
SHARPEN_LANCZOS = 65   # Lanczos: afilado notable (compensa el suavizado del reescalado)
SHARPEN_AI = 25        # IA: toque suave (el modelo ya aporta nitidez; evita halos)

# ------------------------------------------------------------------ control de integridad (anti-artefactos)
# Validación de la salida IA comparándola con el original (diferencia media, 0-255).
# Medido: salidas válidas ≈ 1-2; salida corrupta (mosaico) ≈ 46. Si se supera el
# umbral, la salida IA se descarta y se usa el siguiente método (nunca se guarda).
AI_MAX_MAE = 12
# Verificar que el .webp final abre correctamente y tiene el tamaño esperado.
VERIFY_OUTPUT = True

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
    "childporn", "child_porn",
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

# ------------------------------------------------------------------ overrides locales (credenciales)
# Si existe app/config_local.py (IGNORADO por git), sus constantes en MAYÚSCULAS
# sobreescriben las de este archivo. Es la forma recomendada de poner tus claves
# sin riesgo de subirlas al repositorio: edita solo app/config_local.py.
try:
    from . import config_local as _config_local
except ImportError:
    _config_local = None

if _config_local is not None:
    for _nombre in dir(_config_local):
        if _nombre.isupper():
            globals()[_nombre] = getattr(_config_local, _nombre)
    del _nombre
