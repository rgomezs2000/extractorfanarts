"""Configuración central de Imaginteca.

Por ahora NO hay autenticación interna ni gestión de usuarios: las claves de
las APIs se colocan aquí (ver README). Los datos sensibles deberían migrarse
a variables de entorno o un archivo externo en una versión futura.
"""
import datetime
import os
import sys
from pathlib import Path

APP_NAME = "Imaginteca"
APP_VERSION = "0.1.2-beta"

# ------------------------------------------------------------------ autoría
# Lo que se muestra al usuario como autor. NO se publica ningún dato personal:
# ni nombre propio, ni correo. El canal privado es Discord.
AUTOR = "InfoArte"
ANIO_INICIAL = 2026          # año de creación del proyecto


def aviso_copyright(anio_inicial: int = ANIO_INICIAL, autor: str = AUTOR) -> str:
    """Aviso de copyright con el año en curso.

      - Si el año actual es el de creación:  «© 2026 InfoArte»
      - Si ya ha cambiado el año:            «© 2026-2027 InfoArte»

    Se calcula en cada arranque, así que el programa nunca muestra un año viejo.
    """
    actual = datetime.date.today().year
    rango = f"{anio_inicial}-{actual}" if actual > anio_inicial else str(anio_inicial)
    return f"© {rango} {autor}"


AUTOR_COPYRIGHT = aviso_copyright()
CONTACTO_DISCORD = "rgomezs2010"

# ------------------------------------------------------------------ actualizaciones
# Repositorio del que se leen las versiones nuevas (Releases de GitHub). Si renombras
# el repositorio en GitHub, cambia esto para que el botón «Actualizaciones» siga
# encontrando los paquetes.
UPDATE_REPO = "rgomezs2000/imaginteca"
# Nombre anterior del repositorio. GitHub redirige las llamadas de un repositorio
# renombrado, así que tener los dos hace que la comprobación funcione tanto si el
# renombrado ya se hizo como si todavía no.
UPDATE_REPO_ALTERNATIVO = "rgomezs2000/extractorfanarts"
UPDATE_INCLUIR_BETAS = True    # el proyecto publica versiones beta: cuentan como versión
UPDATE_TIMEOUT = 15            # segundos de espera al consultar GitHub

# ------------------------------------------------------------------ comunidad
# Enlaces que muestra la aplicación (menú Ayuda y «Acerca de»). Se usa el nombre con
# el que el repositorio existe HOY: si se renombra, GitHub redirige automáticamente,
# así que estos enlaces siguen funcionando siempre.
REPO_GITHUB = "rgomezs2000/extractorfanarts"
URL_REPO = f"https://github.com/{REPO_GITHUB}"
URL_WIKI = f"{URL_REPO}/wiki"
# El FORO vive dentro de la wiki (no en el repositorio): es una página editable por
# cualquiera, con un tablero por tema.
URL_FORO = f"{URL_WIKI}/Foro"
URL_FORO_SOPORTE = f"{URL_WIKI}/Foro-Soporte-tecnico"
URL_FORO_FALLOS = f"{URL_WIKI}/Foro-Fallos"
URL_FORO_COMUNIDAD = f"{URL_WIKI}/Foro-y-comunidad"
URL_DESCARGAS = f"{URL_REPO}/releases"
URL_SOPORTE = f"{URL_WIKI}/Soporte-tecnico"   # qué incluir para pedir ayuda
URL_PROBLEMAS = f"{URL_WIKI}/Problemas-frecuentes"
CONTACTO_EMAIL = ""            # sin correo público: el canal es el foro de la wiki

# User-Agent identificado (cortesía / transparencia con los sitios)
# Nota: debe ser ASCII puro (los headers HTTP no admiten acentos).
USER_AGENT = (
    f"{APP_NAME}/{APP_VERSION} (archivo personal de imagenes; "
    "respeta los limites y terminos de cada API; contacto: usuario-local)"
)

# ------------------------------------------------------------------ carpetas
def carpeta_imagenes() -> Path:
    """Carpeta de IMÁGENES del sistema (Pictures), no Documentos.

    Se resuelve en este orden, para respetar la configuración real de cada sistema:
      1. Windows: valor del registro "My Pictures" (así funciona también si OneDrive
         redirige la carpeta) y, si no, ~/Pictures.
      2. Linux/BSD: XDG_PICTURES_DIR de ~/.config/user-dirs.dirs (puede estar en
         español, p. ej. ~/Imágenes) y, si no, ~/Pictures o ~/Imágenes.
      3. macOS: ~/Pictures.
      4. Último recurso: QStandardPaths de Qt (si está disponible).
    """
    hogar = Path.home()

    if sys.platform.startswith("win"):
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            ) as clave:
                valor, _ = winreg.QueryValueEx(clave, "My Pictures")
            ruta = Path(os.path.expandvars(valor))
            if ruta.is_dir():
                return ruta
        except Exception:  # noqa: BLE001
            pass
        candidatas = [hogar / "Pictures", hogar / "Imágenes", hogar / "Imagenes"]
    elif sys.platform == "darwin":
        candidatas = [hogar / "Pictures", hogar / "Imágenes"]
    else:
        candidatas = []
        try:  # XDG: la carpeta puede tener nombre localizado (~/Imágenes)
            archivo = hogar / ".config" / "user-dirs.dirs"
            for linea in archivo.read_text(encoding="utf-8", errors="ignore").splitlines():
                if linea.strip().startswith("XDG_PICTURES_DIR="):
                    valor = linea.split("=", 1)[1].strip().strip('"')
                    ruta = Path(os.path.expandvars(valor.replace("$HOME", str(hogar))))
                    if ruta.is_dir():
                        return ruta
        except Exception:  # noqa: BLE001
            pass
        candidatas = [hogar / "Pictures", hogar / "Imágenes", hogar / "Images"]

    for candidata in candidatas:
        if candidata.is_dir():
            return candidata

    try:  # último recurso: lo que diga Qt
        from PySide6.QtCore import QStandardPaths

        ruta_qt = QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
        if ruta_qt:
            return Path(ruta_qt)
    except Exception:  # noqa: BLE001
        pass
    return hogar / "Pictures"


# Las descargas van a la carpeta de IMÁGENES del sistema (Imágenes en Windows,
# ~/Imágenes (XDG) en Linux, ~/Pictures en macOS). Nunca a Documentos.
DEFAULT_OUTPUT_DIR = carpeta_imagenes() / "Imaginteca"
DB_PATH = Path.home() / ".imaginteca" / "history.db"
LOG_DIR = Path.home() / ".imaginteca" / "logs"

# Registros: la app escribe un archivo .log POR DÍA (app-AAAA-MM-DD.log) y muestra en
# la consola los mismos mensajes. En el .exe de Windows la consola se abre sola.
LOG_EN_CONSOLA = True          # abre/usa una consola con los registros (False = sin consola)
LOG_DIAS_A_CONSERVAR = 30      # días de .log que se conservan (0 = no borrar nunca)


def carpeta_junto_a_la_app() -> Path:
    """Carpeta de descargas junto a la aplicación (ÚLTIMO recurso de salida).

    Sirve cuando la app corre en un entorno restringido —por ejemplo lanzada desde
    la terminal de un agente/IDE con sandbox— que solo deja escribir junto al
    proyecto: en ese caso tus carpetas (Imágenes, Descargas, ~) están bloqueadas y
    esta es la única salida para no perder la descarga. En un arranque normal nunca
    se usa, porque antes funcionan las carpetas del usuario.
    """
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent      # carpeta del .exe
    else:
        base = Path(__file__).resolve().parent.parent     # raíz del proyecto
    return base / "descargas"

# ------------------------------------------------------------------ credenciales (por ahora en el código)
# Gelbooru: https://gelbooru.com/index.php?page=account&s=options
GELBOORU_API_KEY = ""
GELBOORU_USER_ID = ""

# Rule34.xxx: https://rule34.xxx/index.php?page=account&s=options
RULE34_API_KEY = ""
RULE34_USER_ID = ""

# FBooru (fbooru.net): credenciales propias del sitio, tal como las da su perfil de API
#   https://booru.fbooru.net/profile.json?api_key=…&login=…
# Ese api_key y ese login se envían en cada consulta de /posts.json.
FBOORU_API_KEY = "8UKW1QjmPnhdhd3ZLE1JRvuK"
FBOORU_LOGIN = "rgomezs2000"

# ------------------------------------------------------------------ siguientes credenciales
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
# TODOS los boorus viven en este array: **nombre**, **sitio** (`base`) y, si el sitio
# pide credenciales, **sus tokens dentro de la misma entrada** (`auth`). Para añadir,
# quitar o mover un booru solo se toca esta lista (el adaptador es una plantilla
# replicable; ver `_auth_params` en app/services/adapters/booru.py).
#
#   "name"     : nombre que aparece en la interfaz.
#   "family"   : software del sitio: "gelbooru" | "danbooru" | "moebooru" | "philomena"
#                | "shimmie" (tableros Shimmie, tipo rule34.paheal.net: su API pública
#                suele estar desactivada, así que se lee el listado público).
#   "base"     : URL base de la API (sin barra final).
#   "auth"     : None si es público, o un diccionario con los tokens del sitio:
#                  gelbooru : {"api_key": ..., "user_id": ...}
#                  danbooru : {"api_key": ..., "login": ...}
#                  moebooru : {"login": ..., "password_hash": ...}
#                  philomena: {"api_key": ...}   (opcional: sube el límite de peticiones)
#                También se admite la forma abreviada ("GELBOORU",) / ("RULE34",), que
#                lee las claves de las constantes de más abajo (compatibilidad).
#   "headers"  : cabeceras extra opcionales (p. ej. {"Cookie": "..."} en Shimmie).
#   "view_tpl" : plantilla de la página del resultado; {id} es el id del post.
BOORU_SITES = [
    {"name": "Safebooru",  "family": "gelbooru", "base": "https://safebooru.org",
     "auth": None,
     "view_tpl": "https://safebooru.org/index.php?page=post&s=view&id={id}"},
    {"name": "Gelbooru",   "family": "gelbooru", "base": "https://gelbooru.com",
     "auth": {"api_key": GELBOORU_API_KEY, "user_id": GELBOORU_USER_ID},
     "view_tpl": "https://gelbooru.com/index.php?page=post&s=view&id={id}"},
    {"name": "Rule34.xxx", "family": "gelbooru", "base": "https://api.rule34.xxx",
     "auth": {"api_key": RULE34_API_KEY, "user_id": RULE34_USER_ID},
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
    # FBooru: booru de la familia Danbooru con credenciales propias (api_key + login).
    # El perfil de la API es https://booru.allthefallen.moe/profile.json?api_key=…&login=…
    # (ese mismo api_key/login se envían en cada consulta de /posts.json).
    {"name": "ATF Booru", "family": "danbooru", "base": "https://booru.allthefallen.moe",
     "auth": {"api_key": FBOORU_API_KEY, "login": FBOORU_LOGIN},
     "view_tpl": "https://booru.allthefallen.moe/posts/{id}"},
    # Rule34 Paheal: tablero **Shimmie** (no Danbooru). Su API pública está desactivada
    # (/api/… devuelve el HTML del sitio), así que se lee el listado público
    # /post/list/<tags>/<página>, el mismo que recibe el navegador, con 70 por página.
    # Los tags se separan con espacios (en la URL, %20). Es un tablero adulto: los
    # resultados son rating "explicit", así que hace falta marcar «Contenido adulto».
    {"name": "Rule34 Paheal", "family": "shimmie", "base": "https://rule34.paheal.net",
     "auth": None,
     # Si algún día pidiera aceptar sus términos con una cookie, descomenta:
     # "headers": {"Cookie": "ui-tnc-agreed=true"},
     "view_tpl": "https://rule34.paheal.net/post/view/{id}"},
]

# ------------------------------------------------------------------ políticas de descarga
# Ratings permitidos por defecto. Los ratings "questionable"/"explicit" exigen
# activación explícita en la UI (verificación de mayoría de edad del usuario).
ALLOW_ADULT_RATINGS = ["general", "sensitive"]

# Si es True (o se marca "Solo material liberado" en la UI) únicamente se
# descargan obras con licencia permisiva explícita.
REQUIRE_FREE_LICENSE = False

MAX_RESULTS_PER_SOURCE = 100
MAX_PREVIEW_BYTES = 8 * 1024 * 1024  # tope para cada imagen de ejemplo

# Búsqueda social con filtros combinados (usuario + palabras clave + hashtags).
# Las APIs no saben combinar los tres campos, así que la app pide candidatos y aplica
# los filtros en local: más páginas = más probabilidad de encontrar coincidencias
# (p. ej. un hashtag concreto entre las publicaciones de un artista).
SOCIAL_PAGINA = 40             # publicaciones por petición
SOCIAL_PAGINAS = 6             # páginas máximas por búsqueda
SOCIAL_MAX_CANDIDATOS = 240    # publicaciones que se revisan como máximo
# Con VARIOS valores dentro de un mismo campo (varios hashtags o varias palabras clave):
#   "alguno"  → vale cualquiera de ellos (unión: más resultados)   ← por defecto
#               p. ej. «#lola_loud #the_loud_house» = arte con una u otra etiqueta
#   "todos"   → se exigen todos (intersección: más preciso)
#               p. ej. «#lola_loud #the_loud_house» = solo lo que lleva las dos
# Entre campos (usuario / palabras / hashtags) siempre se exigen todos los que rellenes.
SOCIAL_VARIOS_EN_CAMPO = "alguno"

# Galería (carrusel): cuántas miniaturas se cargan AL INSTANTE al terminar la búsqueda.
# Son miniaturas (preview_url), no las imágenes completas.
MUESTRAS_GALERIA = 8

# Si es True, al terminar la búsqueda se siguen cargando en segundo plano las
# miniaturas que faltan (respetando MIN_REQUEST_INTERVAL entre peticiones) hasta
# completar TODAS las casillas del carrusel. Con False, el resto se carga solo
# cuando el usuario navega hasta esa imagen.
CARGAR_GALERIA_COMPLETA = True

# Tope de imágenes del carrusel que se cargan en segundo plano de una vez (para
# no lanzar cientos de peticiones si una búsqueda devuelve muchísimos resultados).
GALERIA_MAX_SEGUNDO_PLANO = 120

# ------------------------------------------------------------------ muestras de la galería
# Las muestras que se ven en la galería (tira de miniaturas, imagen grande y visor
# ampliado) se construyen en el propio programa a partir de la imagen ORIGINAL y se
# entregan SIEMPRE en .webp (nítidas y ligeras), no como la miniatura de la API:
#   · tira de miniaturas  -> muestra pequeña (MUESTRA_ICONO_LADO_MAX)
#   · imagen grande/visor -> muestra mayor (MUESTRA_LADO_MAX) que se pide al llegar
#     a esa imagen y se guarda en memoria solo para las últimas
#     GALERIA_MUESTRAS_EN_MEMORIA (las demás se vuelven a pedir si hace falta).
MUESTRAS_ORIGINALES = True     # False → usar la miniatura de la API (más ligera, borrosa)
MUESTRA_LADO_MAX = 1600        # lado mayor de la muestra grande (visor y zoom)
MUESTRA_ICONO_LADO_MAX = 512   # lado mayor de la muestra de la tira de miniaturas
MUESTRA_CALIDAD_WEBP = 80      # calidad de las muestras (independiente del deslizador de descarga)
MUESTRA_MEJORAR = True         # aplicar UPSCALE_BUCKETS (con Lanczos) a la muestra grande
MAX_MUESTRA_BYTES = 12 * 1024 * 1024   # tope de descarga por muestra
GALERIA_MUESTRAS_EN_MEMORIA = 12       # muestras grandes que se conservan en memoria

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
    (0, 699, 4),       # hasta 699 px           -> 4x
    (700, 799, 3),     # de 700 a 799 px        -> 3x
    (800, 7679, 2),    # de 800 px en adelante  -> 2x, con tope de 8K
]
# Ojo: los tramos deben ser CONTIGUOS y no bajar de factor al subir de tamaño. El
# tramo antiguo (1501-1599 -> 1x) rompía eso: una imagen de 1550 px se quedaba sin
# reescalar mientras una de 1500 px se doblaba. Por encima del último tramo
# (>= 7680 px) no se reescala: solo se convierte a WebP.

# Por debajo de este lado mayor se avisa de que el origen es diminuto: el
# reescalado no inventa detalle real. Importa sobre todo si el destino es entrenar
# un modelo (un origen de 153 px no sirve para un dataset, por mucho que se agrande).
AVISO_ORIGEN_PEQUENO = 300

# Tope de resolución de salida: ninguna imagen mejorada supera este lado mayor
# (7680 px = 8K UHD). Si el factor la excediera, se reduce al tope (nunca se
# reduce por debajo del tamaño original).
MAX_OUTPUT_SIDE = 7680
# Límite de píxeles para usar IA (evita trabajos desmesurados que la GPU no
# terminaría en un tiempo razonable); por encima se usa Lanczos al tamaño objetivo.
AI_MAX_PIXELS = 50_000_000
# Desviación de color (por canal, en niveles de 0-255) que se tolera a la salida de
# la IA antes de devolverle la paleta del original. Los modelos Real-ESRGAN desplazan
# ~1 nivel (imperceptible): con ese valor no se toca nada; si un modelo cambia más el
# color, se corrige y queda en el registro.
AI_PALETA_TOLERANCIA = 1

WEBP_QUALITY_DEFAULT = 90     # calidad WebP configurable en la UI (1-100)
AI_EXE_OVERRIDE = ""          # ruta manual al exe IA si no está en vendor/PATH
AI_MODEL = "realesrgan-x4plus-anime"   # modelo x4 (fanart); "realesrgan-x4plus" para realista
# Modelo multiescala (variantes x2/x3/x4 incluidas). Se usa para 2x y 3x porque
# los modelos x4 con -s 2/3 producen imágenes corruptas en realesrgan-ncnn-vulkan.
AI_MODEL_ESCALA = "realesr-animevideov3"

# Definición (afilado): porcentaje de UnsharpMask aplicado tras el upscaling.
SHARPEN_LANCZOS = 20   # Lanczos: afilado SUAVE. Medido sobre líneas duras: con 65 el
                       # «ringing» (halos claros/oscuros pegados a las líneas) era 0,278
                       # y la nitidez 9,10; con 20 el ringing cae a 0,036 y la nitidez se
                       # queda en 7,58 (sin afilar: 0,016 y 7,28). El afilado fuerte
                       # cambiaba muy poca nitidez real por halos muy visibles.
SHARPEN_LANCZOS_RADIO = 1.5   # radio del afilado de Lanczos (antes 2,0: demasiado ancho)
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

# ================================================================== LISTA NEGRA
# TODA la lista negra vive AQUÍ, en arrays, y el código solo los lee (no hay valores
# escondidos en el código): para cambiarla, edita estas listas —o mejor sus copias en
# app/config_local.py / ~/.imaginteca/config_local.py, que sobreescriben este
# archivo y no se pierden al actualizar la app— y reinicia. Se admiten listas, tuplas o
# conjuntos; un "*" al final de una entrada significa «empieza por».

# 1) Tags que descartan el resultado (comparación exacta del tag completo).
PROHIBITED_TAG_TOKENS = [
    "childporn",
    "child_porn",
    "pedo_x",
]

# 2) Prefijos de tags: cualquier tag que EMPIECE por uno de ellos descarta el resultado
#    (p. ej. "pedo" descarta "pedo_x", "pedo_art"…). No afecta a "shot" ni "lollipop".
PROHIBITED_TAG_PREFIXES = [
    "childporn",
    "child_porn",
    "pedo",
]

# 3) Plataformas de pago / contenido exclusivo: se descarta el resultado cuyo enlace,
#    texto o página apunte a estos dominios (ver informe §4.5).
BLOCKED_PAID_DOMAINS = [
    "patreon.com", "fanbox.cc", "onlyfans.com", "fansly.com",
    "unifans.io", "fansky.social", "fansky.app", "subscribestar.adult",
    "gumroad.com",
]

# 4) TU lista de exclusión (lo que TÚ no quieres ver). Se SUMA a la de arriba.
#    Un "*" al final de un tag = «empieza por»:
#        EXCLUDED_TAG_TOKENS = ["gore", "vore", "scat", "guroli*"]
#        EXCLUDED_DOMAINS = ["deviantart.com", "pinterest.com"]
#        EXCLUDED_TEXT_TOKENS = ["commission open", "adopt", "ych"]
EXCLUDED_TAG_TOKENS: list[str] = []
EXCLUDED_DOMAINS: list[str] = []
EXCLUDED_TEXT_TOKENS: list[str] = []

# Indicadores de licencia considerados "material liberado" (archivo personal).
FREE_LICENSE_HINTS = (
    "cc0", "public domain", "cc-by", "cc by", "creative commons",
)

# ------------------------------------------------------------------ overrides locales (credenciales)
# Archivo config_local.py (IGNORADO por git) con tus claves y ajustes: cualquier
# constante en MAYÚSCULAS sobreescribe las de este archivo.
#
# Se busca en este orden (el primero que exista gana), lo que permite usarlo
# tanto en desarrollo como con la app empaquetada (.exe/.app/binario):
#   1) junto al ejecutable (o junto a main.py en desarrollo)
#   2) dentro del paquete empaquetado (por si se incluyó una plantilla)
#   3) en la carpeta de usuario:  ~/.imaginteca/config_local.py
import importlib.util as _importlib_util
import sys as _sys


def _cargar_config_local():
    candidatos = []
    if getattr(_sys, "frozen", False):
        candidatos.append(Path(_sys.executable).resolve().parent / "config_local.py")
        interior = getattr(_sys, "_MEIPASS", None)
        if interior:
            candidatos.append(Path(interior) / "config_local.py")
    else:
        candidatos.append(Path(__file__).resolve().parent / "config_local.py")
    candidatos.append(Path.home() / ".imaginteca" / "config_local.py")
    # Compatibilidad: hasta el cambio de nombre la carpeta de datos se llamaba
    # «.extractorfanarts». Si tus claves se quedaron ahí, se siguen leyendo (y
    # puedes moverlas a la carpeta nueva cuando quieras).
    candidatos.append(Path.home() / ".extractorfanarts" / "config_local.py")

    for ruta in candidatos:
        try:
            if not ruta.is_file():
                continue
            especificacion = _importlib_util.spec_from_file_location("config_local", ruta)
            if especificacion is None or especificacion.loader is None:
                continue
            modulo = _importlib_util.module_from_spec(especificacion)
            especificacion.loader.exec_module(modulo)
            return modulo
        except Exception:  # noqa: BLE001
            continue  # un archivo con errores no debe impedir arrancar
    return None


_config_local = _cargar_config_local()

# Constantes que deben ser rutas: si el usuario las escribe como texto en
# config_local.py (DEFAULT_OUTPUT_DIR = r"C:\..."), se convierten a Path.
_CONSTANTES_RUTA = ("DEFAULT_OUTPUT_DIR", "DB_PATH", "LOG_DIR", "AI_EXE_OVERRIDE")

if _config_local is not None:
    for _nombre in dir(_config_local):
        if _nombre.isupper():
            globals()[_nombre] = getattr(_config_local, _nombre)
    if "_nombre" in globals():
        del _nombre
    CONFIG_LOCAL_USADO = getattr(_config_local, "__file__", "") or ""
else:
    CONFIG_LOCAL_USADO = ""

for _nombre in _CONSTANTES_RUTA:
    _valor = globals().get(_nombre)
    if isinstance(_valor, str) and _valor.strip():
        globals()[_nombre] = Path(_valor.strip()).expanduser()
del _nombre

# ------------------------------------------------------------------ boorus añadidos
# `BOORU_SITES_EXTRA` (en config_local.py) se SUMA al array de arriba: así puedes añadir
# tus propios boorus sin reescribir `BOORU_SITES`. Si un nombre ya existe, se respeta el
# de `BOORU_SITES` (para eso está también sobreescribir el array completo).
def _con_boorus_extra(sitios: list, extra) -> list:
    """Suma a `sitios` los de BOORU_SITES_EXTRA (ignora repetidos e incompletos)."""
    if not extra:
        return sitios
    nombres = {sitio.get("name") for sitio in sitios}
    nuevos = [sitio for sitio in extra
              if isinstance(sitio, dict) and sitio.get("name") not in nombres
              and sitio.get("family") and sitio.get("base")]
    return list(sitios) + nuevos if nuevos else sitios


BOORU_SITES = _con_boorus_extra(BOORU_SITES, globals().get("BOORU_SITES_EXTRA"))
for _temporal in ("_extra", "_nombres", "_nuevos"):
    globals().pop(_temporal, None)
