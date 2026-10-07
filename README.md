# ExtractorFanarts

Aplicación de escritorio **Python (PySide6, arquitectura MVC)** para extraer
fanarts, arte e imágenes desde redes sociales, boorus y wikis de fandom,
con restricciones legales y éticas integradas en el núcleo.

> Uso personal y privado. No redistribuyas el material descargado: la mayoría
> del fanart no tiene licencia liberada. Ver el informe de factibilidad:
> [INFORME-FACTIBILIDAD.md](INFORME-FACTIBILIDAD.md).

## Instalación

```powershell
python -m pip install --target vendor PySide6 httpx
python main.py
```

(Si ya existe la carpeta `vendor`, basta `python main.py`.)

## Fuentes soportadas

| Tipo | Plataformas |
|---|---|
| Redes sociales | **Fediverso: cualquier instancia de Mastodon / Misskey / CherryPick** (detección automática del software), Bluesky, DeviantArt (client credentials), Tumblr (consumer key), **Pixiv** (API oficial con tu cuenta vía refresh token), X/Twitter (API v2 de pago, credenciales propias), Pinterest (API v5, OAuth propio), Newgrounds (sin API pública de arte: aparece documentado y explica el motivo) |
| Boorus | Safebooru, Gelbooru, Rule34.xxx, The Big ImageBoard, Xbooru, Hypnohub, Danbooru, Safebooru (Donmai), Yande.re, Konachan, Konachan (SFW), Derpibooru — 4 familias de software (Gelbooru/Danbooru/Moebooru/Philomena), plantilla replicable: ver Anexo A del informe |
| Wikis de fandom | Fandom.com y cualquier wiki MediaWiki (búsqueda por franquicia, personaje y/o concepto) |

**Excluidos por diseño:** X/Twitter y Pinterest (sin acceso legítimo sin
login/pago), Pixiv (exige cuenta), Newgrounds (sin API de arte), plataformas de
pago (Patreon, Pixiv Fanbox, Unifans, Fansky, OnlyFans, Fansly, premium) y boorus
centrados en contenido prohibido (ATF Booru y similares).

## Claves necesarias (en `app/config_local.py`)

> **Recomendado:** edita **`app/config_local.py`** (ignorado por git): cualquier
> constante en MAYÚSCULAS que definas ahí sobreescribe `app/config.py`, así tus
> claves nunca llegan al repositorio. Si el archivo no existe, créalo copiando
> el bloque de credenciales de `app/config.py`. Requiere **reiniciar la app**.

- **Gelbooru / Rule34.xxx:** `GELBOORU_API_KEY` + `GELBOORU_USER_ID`,
  `RULE34_API_KEY` + `RULE34_USER_ID`. Se obtienen gratis en la página de
  opciones de tu cuenta de cada sitio (sección "API Access Credentials"):
  `https://rule34.xxx/index.php?page=account&s=options` y
  `https://gelbooru.com/index.php?page=account&s=options`.
  - **API key** = cadena larga (~128 letras/números). **User ID** = número corto (7 dígitos).
  - Pega solo el valor, sin el `&api_key=` ni comillas internas.
  - Si no ves la cadena, marca **"Generate New Key?"**, pulsa **Save** y recarga.
- **DeviantArt:** `DEVIANTART_CLIENT_ID` + `DEVIANTART_CLIENT_SECRET`
  (https://www.deviantart.com/developers/).
- **Tumblr:** `TUMBLR_API_KEY` (https://www.tumblr.com/oauth/apps).
- **Pixiv:** `PIXIV_REFRESH_TOKEN`. Pixiv **no tiene API anónima**, así que se usa la
  API oficial de la app con tu cuenta. Obtén el token con
  `python scripts\pixiv_token.py` (no se guarda tu contraseña; solo un refresh token
  que puedes revocar cerrando sesión en Pixiv).
- **X/Twitter:** `X_BEARER_TOKEN` (o `X_API_KEY` + `X_API_SECRET`). La API es de
  pago por uso desde 2026: app de desarrollador con facturación.
- **Pinterest:** `PINTEREST_ACCESS_TOKEN` (app aprobada + OAuth del usuario);
  la búsqueda global además requiere `PINTEREST_COUNTRY_CODE` (endpoint beta).
- **Newgrounds:** no tiene API pública de arte (newgrounds.io es de juegos y el
  sitio protege sus páginas); el adaptador lo explica al usarse.
- **Fediverso / Bluesky / Safebooru / Danbooru / wikis:** sin claves.

## Fediverso: cualquier instancia (Mastodon / Misskey / CherryPick)

Una sola plataforma cubre todos los servidores del fediverso. La app **detecta
automáticamente** de qué software se trata (`/api/v1/instance` para Mastodon,
`/api/meta` para Misskey/CherryPick) y guarda el resultado en caché por host.

| Cómo buscas | Qué hace |
|---|---|
| `@usuario@baraag.net` | Consulta **la instancia de ese usuario** (no la seleccionada) |
| `@usuario` + campo **Instancia** | Usa la instancia que escribas (ej. `mastodon.art`) |
| `#hashtag` / palabra clave | Busca en la instancia elegida (por defecto `mastodon.social`) |

- Todo con **endpoints públicos, sin login** (no se usa `resolve=true`, que Mastodon
  exige autenticado y provocaba `HTTP 401`).
- **Instancias restrictivas:** algunas (p. ej. `baraag.net`) responden
  `422 {"error":"This method requires an authenticated user"}` en las timelines por
  hashtag. La app lo detecta y usa el **RSS público de la etiqueta**
  (`/tags/<tag>.rss`) como respaldo; para palabras clave intenta la timeline pública.
  Los elementos del RSS se marcan como `sensitive` (el RSS no expone ese flag).
- Sin claves: no hay nada que configurar.
- Los filtros éticos del núcleo siguen aplicándose a lo que se descargue.

## Pixiv (requiere tu cuenta)

Pixiv no ofrece acceso anónimo: su API exige autenticación. La app usa la **API
oficial de la app** con **tu propia cuenta** mediante un *refresh token*
(no guarda tu contraseña y no hace scraping de la web).

1. Ejecuta: `python scripts\pixiv_token.py`
2. Abre el enlace que muestra e **inicia sesión** con tu cuenta de Pixiv.
3. El navegador terminará en una URL con `?code=...` (la página puede dar error: es normal).
   Copia esa URL completa o solo el código y pégala en la consola del script.
4. El script obtiene el **refresh token** y puede guardarlo en `app/config_local.py`.
5. **Reinicia la app**.

En la UI (Tipo: `Red social` → Plataforma: `Pixiv`):

| Filtro | Qué hace |
|---|---|
| palabra clave / `#hashtag` | Búsqueda por etiquetas (`/v1/search/illust`) |
| `@usuario` o id numérico | Obras de ese usuario (`/v1/user/illusts`) |

- Las obras de **varias páginas** se guardan como archivos separados (`_p0`, `_p1`, …).
- **Animaciones ugoira:** se descarga el ZIP de fotogramas (`/v1/ugoira_metadata`) y se
  componen en un **WebP animado** (con los retrasos originales de cada fotograma).
  - Integridad: ZIP válido + al menos 2 fotogramas decodificables + resultado
    reabierto y verificado (varios fotogramas); si algo falla no se guarda nada roto.
  - Límites configurables: `UGOIRA_MAX_FRAMES = 400`, `UGOIRA_MAX_ZIP_MB = 200`.
  - El CDN de Pixiv (`i.pximg.net`) exige la cabecera `Referer`; la app la envía
    automáticamente por dominio (`REFERER_DOMAINS` en config.py).
- Rating según `x_restrict`: R-18 → `questionable`, R-18G → `explicit` → requieren
  la casilla "Permitir contenido adulto".

## Si aparece un CAPTCHA de Cloudflare (p. ej. Rule34.xxx)

Algunos boorus activan defensas de Cloudflare que responden un **CAPTCHA** en lugar
de datos (la app lo detecta y lo informa de inmediato, sin quedarse esperando).
Solución **respetuosa** con el sitio (tú resuelves el reto como humano):

1. Abre el sitio en tu navegador (p. ej. https://rule34.xxx) y **resuelve el CAPTCHA**.
2. Pulsa **F12** → pestaña **Network/Red** → recarga la página.
3. Haz clic en la primera petición del documento → **Headers → Request Headers**:
   - copia la cookie **`cf_clearance`** (~450 caracteres),
   - copia el **`User-Agent`** completo.
4. Pégalos en `app/config_local.py` y reinicia la app:

```python
CF_CLEARANCE = "valor_de_cf_clearance"
CF_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
```

> `cf_clearance` solo es válido para el **mismo User-Agent** que resolvió el reto y
> **caduca** como en el navegador. La app nunca resuelve ni evade CAPTCHAs por sí sola.

**Paso 5 (automático): huella TLS de navegador.** Cloudflare también analiza la
"firma" de la conexión: `httpx` no se parece a Chrome y el CAPTCHA seguía
apareciendo aun con la cookie. La app incluye soporte para **`curl_cffi`** y, cuando
hay `CF_CLEARANCE`, usa automáticamente un transporte con **huella de Chrome** para
los dominios de `CF_DOMAINS` (el resto siguen usando httpx). Verificado: Rule34.xxx
pasó de `HTTP 403 text/html (CAPTCHA)` a `HTTP 200 application/json`.

- Se instala con `python scripts\setup_vendor.py --only=curl_cffi` (más
  `--only=cffi,pycparser` como dependencias).
- Se puede elegir otro navegador con `BROWSER_IMPERSONATE` en `app/config_local.py`
  (`"chrome"`, `"edge101"`, `"firefox133"`, …).

> ⚠️ **En Rule34.xxx debes marcar "Permitir contenido adulto"** en la UI: casi todo
> su contenido tiene rating `questionable`/`explicit`, que la app filtra por defecto
> (criterio legal/ético). Sin esa casilla verás "0 resultados" aunque la conexión
> funcione.

### Wikis de Fandom (mismo mecanismo, sin cookie)

El **CDN de imágenes de Fandom** (`static.wikia.nocookie.net`) y `Special:FilePath`
responden `403 "Just a moment..."` a los clientes que no parecen un navegador.
La app lo resuelve automáticamente porque `fandom.com`, `nocookie.net` y `wikia.com`
están en **`BROWSER_DOMAINS`**: esas peticiones usan el transporte con huella de
Chrome **más un User-Agent de navegador** (no hace falta `cf_clearance`).
Verificado: `403` → `HTTP 200 image/webp`.

- Si otro sitio nuevo diera ese error, solo añade su dominio a `BROWSER_DOMAINS`
  en `app/config_local.py` (el mensaje de error te lo recordará).
- El adaptador de wikis usa `prop=imageinfo`, así que también guarda el **autor
  (uploader)** y la **licencia** cuando la wiki la declara.

## Estatus de conexión y progreso (UI y consola)

- **UI:** debajo de la barra de progreso aparece **"Conexión: …"** con la última
  petición/respuesta (verde = correcta, rojo = CAPTCHA/error/pausa).
- **Consola y archivo `.log`:** cada línea de actividad queda registrada, por ejemplo:

```
16:38:47 | INFO | → GET api.rule34.xxx/index.php?page=dapi&...&api_key=6c0ed7…476e[128]&user_id=3691365
16:38:47 | INFO | ← HTTP 403 text/html 76.7 KB en 0.19 s (api.rule34.xxx)
16:38:47 | ERROR| api.rule34.xxx exige superar un CAPTCHA de Cloudflare (HTTP 403) ...
16:39:02 | INFO | [progreso] 2/5 (40%) Safebooru: Safebooru_123_ab12cd34.webp
16:39:02 | INFO | ⇩ Safebooru_123_ab12cd34.webp descargado: 812 KB (image/webp) en 0.9 s
```

Las claves (`api_key`) se muestran **enmascaradas** en los logs.

### Diagnóstico rápido

```powershell
python scripts\diag_conexion.py Rule34.xxx    # revisa credenciales + conexión
python scripts\diag_conexion.py Safebooru     # control sin claves
```

## Comportamiento de la UI

- **Buscar:** consulta la plataforma y muestra los resultados + **una imagen de ejemplo**.
  La imagen de ejemplo se **limpia al iniciar cada búsqueda** y se muestra la de esa
  búsqueda; si no se puede cargar, lo indica — nunca queda la de la búsqueda anterior.
- **Descargar:** busca y descarga todo a la carpeta de salida (se sobreescribe si el
  archivo ya existe); durante la descarga el botón se convierte en **Cancelar** y el
  formulario y **Limpiar** quedan bloqueados.
- **Carpeta de salida:** si no existe, **se crea automáticamente** (con subcarpetas
  por plataforma). Fail-safe: sin carpeta configurada no se descarga nada.
- **Límite de cantidad:** con la casilla **"Limitar cantidad de descargas"** se
  descarga solo la cantidad indicada (1-1000); sin marcar, se descarga todo lo
  encontrado (hasta el tope de seguridad `MAX_RESULTS_PER_SOURCE` de config.py).
- **Cancelar:** detiene la operación y restaura la UI tal como estaba, conservando la
  imagen de ejemplo.
- **Limpiar:** limpia el formulario (no descarga nada; solo disponible en reposo).
- **Anti-bloqueo:** si un sitio responde 429/5xx o un posible bloqueo (401/403), el
  programa **pausa un tiempo prudente** (30 s → 5 min, con reintentos) y continúa;
  si el bloqueo persiste, descarta la fuente e informa. No evade CAPTCHAs ni logins.

## Diálogos y registro de errores (logging)

- **Confirmación de descarga:** al pulsar Descargar se muestra un diálogo
  *"¿Deseas iniciar la descarga?"* con la plataforma, carpeta y límite; **Sí**
  inicia la descarga, **No** la deja sin iniciar (el formulario queda intacto).
- **Diálogos de resultado:** al terminar una descarga se muestra un diálogo de
  éxito (archivos guardados, fallos y carpeta), de cancelación o de error.
- **Errores:** cada controlador y manejador de UI tiene try/except; los errores
  fatales muestran un diálogo crítico.
- **Log:** todo se registra en consola y en un archivo `.log` rotativo
  (`~/.extractorfanarts/logs/app.log`, o `logs/app.log` si esa ruta no es
  escribible), con tracebacks detallados de las excepciones.

## Mejora de calidad al descargar

- **Todo lo descargado se convierte SIEMPRE a `.webp`** con la calidad configurada
  (deslizador **Calidad WebP**, 1-100) y **el archivo original nunca se conserva**.
- La casilla **"Mejorar calidad (upscale IA/Lanczos)"** controla SOLO el upscaling y
  la definición, con estas reglas según el lado mayor de la imagen:
  `<700px → 4x` · `700-799px → 3x` · `800-1500px → 2x` · `1501-1599px → 1x` ·
  `1600px+ → 2x`, siempre con **tope de 8K** (`MAX_OUTPUT_SIDE = 7680 px`).
- **Definición:** tras el upscaling se aplica afilado (UnsharpMask) configurable:
  `SHARPEN_LANCZOS = 65` (reescalado clásico) y `SHARPEN_AI = 25` (suave, el modelo
  de IA ya aporta nitidez; así se evitan halos).
- **Modo IA:** usa Real-ESRGAN / waifu2x (ncnn-vulkan, GPU) si están instalados
  (`python scripts\setup_vendor.py --ai`); si no están disponibles, cae
  automáticamente a **Lanczos + afilado suave** y lo indica en el estado.
  - Para 2x y 3x se usa el modelo multiescala `realesr-animevideov3` (los modelos
    `realesrgan-x4plus*` son **x4 nativos** y con `-s 2/3` devolvían imágenes
    corruptas tipo mosaico; ahora hay validación de tamaño y respaldo "x4 → reducir").
- **Transparencia respetada:** si la imagen original tiene canal alfa, el alfa se
  separa, se reescala por su cuenta y se vuelve a aplicar; el RGB se aplana sobre
  blanco antes de reescalar. Así no aparecen halos negros ni residuos en los bordes
  y el `.webp` final conserva la transparencia (`exact=True`).

### Control de integridad (anti-corrupción y anti-artefactos)

1. **Archivo descargado:** se decodifica completo antes de procesarlo; si está
   truncado o dañado → `ImagenCorruptaError`, se **reintenta la descarga una vez** y,
   si sigue mal, el archivo se **descarta** (no queda basura en el archivo local).
2. **Salida de IA validada:** cada resultado de la IA se compara con el original
   (diferencia media, MAE). Se midió: salidas válidas ≈ **1–2**, salida corrupta tipo
   mosaico ≈ **46**. Con `AI_MAX_MAE = 12`, cualquier salida anómala se **descarta** y
   se prueba el siguiente método (nunca se guarda una imagen corrupta).
3. **Tamaño validado:** si la IA devuelve dimensiones inesperadas, se rechaza.
4. **Fallback seguro:** si cualquier paso de la mejora falla, se aplica una
   conversión **directa a WebP** (sin upscaling) en lugar de dejar algo roto.
5. **Verificación final:** el `.webp` se vuelve a abrir y comprobar (decodifica +
   tamaño). Si no pasa, se conserva el original en vez de guardar un archivo dañado.
6. El afilado está limitado (0–150 %) y en IA es suave para no crear halos.
- El sidecar `.json` es **opcional**: se genera solo si marcas **"Guardar metadatos
  .json"** en Opciones (desactivado por defecto → se guarda únicamente la imagen).
  Si ya tienes `.json` antiguos: `python scripts\limpiar_sidecars.py "<carpeta>" --borrar`.

## Filtros del núcleo (no desactivables)

1. Lista negra dura de tags (contenido de menores y afines).
2. Descartar resultados que enlacen plataformas de pago / contenido exclusivo.
3. Gate de rating adulto (questionable/explicit requieren activación explícita).
4. Opcional "Solo material con licencia liberada" (CC0/CC-BY/dominio público).
5. Deduplicación por hash **dentro de cada búsqueda** (cada Descargar re-descarga
   todo y sobreescribe los archivos existentes).

## Empaquetar como ejecutable (Windows / macOS / Linux)

**PyInstaller no compila cruzado**: cada sistema operativo genera su propio ejecutable.

| Sistema | Comando (en ese sistema) |
|---|---|
| Windows (`.exe`) | `python scripts\build_exe.py --probar` |
| macOS (`.app`) | igual, ejecutado en un Mac |
| Linux (binario) | igual, ejecutado en Linux |

Para obtener **los tres a la vez** usa el workflow incluido
[.github/workflows/build.yml](.github/workflows/build.yml): compila en
Windows + macOS + Linux en paralelo y sube los paquetes como artefactos.

Requisitos en la máquina que compila:
```powershell
python -m pip install PySide6 httpx Pillow curl_cffi pyinstaller
# o, sin pip:  python scripts\setup_vendor.py vendor --ai
```

Opciones de `build_exe.py`: `--onefile` (un solo archivo), `--consola` (mantiene la
consola además de la ventana), `--probar` (ejecuta `--selftest` del resultado).

Notas importantes:

- **Las credenciales NO se empaquetan.** `config_local.py` se busca **junto al
  ejecutable** o en `~/.extractorfanarts/config_local.py`; el build deja una
  plantilla al lado del binario. Así tus claves nunca entran en el paquete.
- **Registros y base de datos** viven en `~/.extractorfanarts/` (logs + historial),
  fuera del paquete.
- **Tamaño**: el paquete `onedir` ronda los cientos de MB porque incluye Qt
  (PySide6) y los binarios de IA (Real-ESRGAN/waifu2x con sus modelos).
- **macOS**: un `.app` sin firmar muestra *"no se puede abrir"* → clic derecho →
  **Abrir**, o `xattr -dr com.apple.quarantine ExtractorFanarts.app`. Para
  distribuirlo a terceros hace falta un certificado de Apple (Developer ID) y
  notarización.
- **Linux**: conviene compilar en una distribución antigua (o contenedor) para que
  el binario funcione en más sistemas; alternativamente puede empaquetarse como
  AppImage.

## Estructura (MVC)

```
main.py                     entrada (añade ./vendor al PYTHONPATH)
app/
  config.py                 credenciales, sitios, límites, listas negras
  models/                   Artwork, SearchQuery, almacén SQLite
  controllers/              MainController (hilos, estados, pipeline)
  services/
    http_client.py          HTTP con cooldown/backoff/pausa
    filters.py              filtros legales/éticos
    adapters/               plantillas por plataforma (booru, mastodon, misskey,
                            bluesky, deviantart, tumblr, mediawiki)
  views/                    MainWindow (Qt)
scripts/smoke_services.py   prueba de humo de los helpers (sin GUI)
```
