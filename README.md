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

- **Buscar:** consulta la plataforma y muestra los resultados + una **galería de ejemplo**
  en forma de **carrusel alineado**: contador centrado, imagen grande con flechas `◀` `▶`
  y **tira de miniaturas exactamente del mismo ancho que la imagen** (clic en una para
  saltar a ella).
  - **Una casilla por CADA resultado** de la búsqueda o descarga: si hay 50 resultados,
    el carrusel muestra `1 / 50` … `50 / 50` (las casillas sin cargar aparecen en gris
    con su número).
  - **Carga bajo demanda:** al buscar se traen las primeras `MUESTRAS_GALERIA = 8`
    (4 si es una descarga) y el resto **solo cuando llegas a ellas**, para no lanzar
    decenas de peticiones de golpe.
  - **Clic sobre la imagen** → visor ampliado **dentro de la misma ventana** (estilo
    *fancybox*, sin abrir otra ventana): **rueda** = zoom (hasta 800 %), **arrastrar** =
    mover, **doble clic** = ajustar, `←`/`→` = cambiar de imagen, `Esc` o clic fuera = cerrar.
  - Se **recarga (vacía) en cada búsqueda o descarga**; si una miniatura falla lo indica
    (`⚠️`) sin quedarse con la anterior.
  - Widget: [app/views/galeria.py](app/views/galeria.py).
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

## 🎨 Icono e iconos de la interfaz

El icono (una **paleta de pintura con pincel**) se genera por código, sin depender de
imágenes ni fuentes externas, y se aplica a:

- el **ejecutable** (`.exe` / `.app` / binario) al compilar,
- la **ventana** y la **barra de tareas** (`QApplication.setWindowIcon`),
- los **controles clave** de la interfaz.

| Archivo | Para qué |
|---|---|
| `assets/icon.ico` | Windows: multi-tamaño 16, 24, 32, 48, 64, 128, 256 |
| `assets/icon.png` | 1024 px (macOS/Linux, vistas previas) |
| `assets/icon_256.png` | Icono de ventana en cualquier sistema |
| `assets/icon_preview.png` | Tira de comprobación en todos los tamaños |

Para cambiar el diseño o los colores (edita `PINTURAS` y la geometría en
[scripts/make_icon.py](scripts/make_icon.py)) y regenera:

```powershell
python scripts\make_icon.py
```

**Iconos en los controles (cada icono representa su función):**

| Control | Icono | Motivo |
|---|---|---|
| Buscar | 🔍 | lupa = buscar |
| Descargar / Cancelar | ⬇️ / ⏹️ | flecha abajo = descargar · señal de stop = cancelar |
| Limpiar | 🧹 | escoba = limpiar el formulario |
| Carpeta de salida | 📂 / 📁 | carpeta = destino de los archivos |
| Solo licencia liberada | ⚖️ | balanza = aspecto legal |
| Contenido adulto | 🔞 | símbolo de restricción +18 |
| Mejorar calidad | ✨ | destellos = mejora/retoque |
| Modo IA | 🤖 | robot = inteligencia artificial |
| Calidad WebP | 🎚️ | control deslizante = nivel |
| Limitar cantidad | 🔢 / 🔢 | números = cantidad |
| Metadatos .json | 🏷️ | etiqueta = datos del archivo |
| Conexión | 📡 | antena = conexión de red |
| Resultados | 🖼️ / 📋 | cuadro = imágenes · lista = resultados |
| Tipo / Plataforma | 🗂️ / 🌐 | clasificación · sitio web |
| @usuario · palabra · #hashtag | 👤 · 🔤 · #️⃣ | persona · texto · etiqueta |
| Instancia | 🌐 | servidor del fediverso |
| Tags · Fandom · Personaje · URL wiki | 🏷️ · 📚 · 🎭 · 🔗 | etiquetas · obra/lore · rol · enlace |
| Progreso | 🔍 buscando… / ⬇️ %p% | refleja la tarea en curso (se oculta al terminar) |

El icono de la ventana se resuelve con [app/icono.py](app/icono.py), que lo busca
tanto en desarrollo como dentro del paquete empaquetado.

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

## Windows: SmartScreen, antivirus y firma

Al ejecutar por primera vez el `.exe` recién compilado, Windows puede mostrar
**"Windows protegió su PC"** (SmartScreen). Es lo normal en un ejecutable **sin
firmar digitalmente** — no significa que tenga virus.

**Para ejecutarlo de todas formas:** *Más información* → **Ejecutar de todas formas**.
Si sigue bloqueado: clic derecho en el `.exe` → *Propiedades* → marca **Desbloquear** → *Aceptar*.

**Para que no vuelva a aparecer** hay que **firmar** el ejecutable con un certificado
de firma de código (se compra a una CA; los autofirmados no sirven para esto):

```powershell
# con un archivo .pfx
$env:EF_CERT_PFX = "C:\ruta\certificado.pfx"
$env:EF_CERT_PASSWORD = "tu_contraseña"
python scripts\build_exe.py --firmar

# o con un certificado ya instalado en Windows
$env:EF_CERT_THUMBPRINT = "HU3LL4..."
python scripts\build_exe.py --firmar
```

En GitHub Actions, si defines los secretos `WINDOWS_CERT_PFX_BASE64` (el `.pfx` en
base64) y `WINDOWS_CERT_PASSWORD`, el workflow firma automáticamente el paquete de
Windows. Un certificado **EV** obtiene reputación inmediata en SmartScreen.

> ⚠️ **No ejecutes nunca el `.exe` de `build\`.** Esa carpeta contiene un paso
> intermedio incompleto y falla con *"Failed to load Python DLL … _internal\python312.dll"*.
> El ejecutable bueno es **`dist\ExtractorFanarts\ExtractorFanarts.exe`** (o haz doble
> clic en `ejecutar.bat`). La compilación borra `build\` automáticamente al terminar.

### Crear un certificado

**A) Autofirmado (gratis) — para tu equipo y para probar el flujo de firma**

```powershell
# opción recomendada: doble clic en  crear_certificado.bat
#   (se ejecuta desde el Explorador, sin pasar por Python)

# equivalentes:
python scripts\hacer_certificado.py --simular   # muestra los comandos, sin ejecutar nada
python scripts\hacer_certificado.py             # crea certs\codigo.pfx y certs\codigo.cer
python scripts\hacer_certificado.py --confiar   # + marcarlo de confianza en TU usuario

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\hacer_certificado.ps1
```

> ⚠️ **Si falla con *"No existe ninguna unidad con el nombre 'Cert'"*:** no es tu
> Windows, es que el **Python de la Microsoft Store** lanza sus procesos hijos en un
> contenedor (MSIX) que **no puede leer el registro de certificados**; entonces el
> módulo `Microsoft.PowerShell.Security` no carga y desaparecen `Cert:\` y
> `ConvertTo-SecureString`. Solución: usa **`crear_certificado.bat`** (doble clic) o
> PowerShell normal. Compruébalo con `Test-Path Cert:\CurrentUser\My` → debe dar `True`.

Luego firma:

```powershell
# opción recomendada: doble clic en  firmar.bat
#   (localiza signtool solo y lee la clave de certs\clave.txt)

# o por línea de comandos:
$env:EF_CERT_PFX = "$PWD\certs\codigo.pfx"
$env:EF_CERT_PASSWORD = (Get-Content certs\clave.txt)
python scripts\build_exe.py --firmar
```

> Igual que con el certificado, la **firma también conviene hacerla sin Python**
> (doble clic en `firmar.bat`): `signtool` necesita crear un contenedor de claves y el
> contenedor del Python de la Store puede denegarlo con *"Acceso denegado"*.

- Sirve para que **tu PC** reconozca al editor (deja de decir "Editor desconocido").
- **No elimina SmartScreen** en los equipos de otras personas.
- `--confiar` muestra un diálogo de Windows pidiendo confirmación (acepta).
- 🔐 `certs/`, `*.pfx` y `*.cer` están en `.gitignore`: **la clave privada no se sube nunca**.

Si tu consola es un entorno restringido (sandbox/IDE) el script no podrá tocar el
almacén de certificados: ábrelo en un **PowerShell normal** — o pega los comandos que
el propio script imprime.

**B) Certificado de una CA (de pago) — para distribuir sin avisos**

| Tipo | Precio aprox. | SmartScreen | Requisito |
|---|---|---|---|
| OV (organización) | 200–400 €/año | reputación progresiva | clave privada en **token/HSM** (desde 2023) |
| EV (validación extendida) | 400–700 €/año | **inmediata** | token/HSM |
| **Azure Trusted Signing** (Microsoft) | ~10 €/mes | progresiva | **sin token**, integrable en GitHub Actions |

Proveedores: DigiCert, Sectigo, SSL.com, Certum, GlobalSign. Como la clave ya no puede
estar en un `.pfx` suelto, la firma se hace con su servicio en la nube (DigiCert
KeyLocker, SSL.com eSigner, Sectigo Cloud) o con **Azure Trusted Signing** en CI.

**C) Sin certificado** (lo habitual en proyectos abiertos): publica en GitHub Releases
e incluye el **`LEEME-PRIMERO.txt`** (ya se añade al paquete) explicando el aviso, junto
con el archivo **`.sha256`** para que cada usuario verifique su descarga:

```powershell
Get-FileHash .\ExtractorFanarts-v0.1.0-windows.zip -Algorithm SHA256
```

## Publicar un release (con el compilado)

**Opción A — automática (recomendada).** Al subir una etiqueta `v*`, GitHub Actions
compila **Windows + macOS + Linux** y crea el Release con los tres `.zip` adjuntos:

```powershell
git add -A
git commit -m "release v0.1.0"
git push
python scripts\release.py --tag        # crea y sube la etiqueta v0.1.0
```

Resultado en unos minutos: `https://github.com/rgomezs2000/extractorfanarts/releases`

**Opción B — local (sube el `.zip` ya compilado en tu equipo):**

```powershell
python scripts\release.py              # crea dist\ExtractorFanarts-v0.1.0-windows.zip
gh release create v0.1.0 "dist\ExtractorFanarts-v0.1.0-windows.zip" ^
   --title "ExtractorFanarts v0.1.0" --generate-notes
```
*(si no tienes GitHub CLI: `winget install --id GitHub.cli` y luego `gh auth login`)*

**Opción C — a mano desde la web:** *Releases → Draft a new release* → etiqueta
`v0.1.0` (crear al publicar) → adjuntar el `.zip`.

Notas:

- `dist/`, `build/` y `vendor/` están en `.gitignore`: **los binarios no se suben al
  repositorio**, solo se adjuntan al Release (por eso el repo pesa unos pocos KB).
- El paquete incluye `THIRD-PARTY-NOTICES.txt` con las licencias de los componentes
  redistribuidos (Qt/PySide6 LGPL v3, Pillow, httpx, curl_cffi, motores IA…).
- Tamaño del paquete de Windows: ~132 MB comprimido (Qt + motores IA).
- La versión de la etiqueta se toma de `APP_VERSION` (`app/config.py`); se puede
  forzar con `python scripts\release.py --version 0.2.0`.

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
