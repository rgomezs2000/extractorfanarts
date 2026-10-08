# ExtractorFanarts

**Versión 0.1.0-beta.1 (fase beta)** · Python 3.12 · PySide6 (Qt) · Windows · macOS · Linux · Licencia: Unlicense (dominio público)

Aplicación de escritorio para **buscar, revisar y archivar arte y fanart** desde
redes sociales, boorus e wikis de fandom, con **restricciones legales y éticas
integradas en el núcleo** y conversión de todo lo descargado a **WebP** con
mejora de calidad opcional.

---

## Índice

1. [Concepto](#1-concepto)
2. [Misión](#2-misión)
3. [Visión](#3-visión)
4. [Objetivos](#4-objetivos)
5. [Alcances](#5-alcances)
6. [Funciones](#6-funciones)
7. [Arquitectura](#7-arquitectura)
8. [Requisitos](#8-requisitos)
9. [Instalación](#9-instalación)
10. [Configuración](#10-configuración)
11. [Instrucciones de uso](#11-instrucciones-de-uso)
12. [Empaquetado como ejecutable](#12-empaquetado-como-ejecutable)
13. [Firma digital y SmartScreen](#13-firma-digital-y-smartscreen)
14. [Publicar un release](#14-publicar-un-release)
15. [Solución de problemas](#15-solución-de-problemas)
16. [Scripts del proyecto](#16-scripts-del-proyecto)
17. [Licencia y avisos legales](#17-licencia-y-avisos-legales)

---

## 1. Concepto

**ExtractorFanarts** es una herramienta de escritorio de **uso personal y
privado** que reúne en una sola ventana la búsqueda y el archivado de fanart
disperso en muchas plataformas distintas. La aplicación actúa como un
**cliente unificado**: no aloja, indexa ni redistribuye contenido; se conecta a
las API (o a los listados públicos) de cada sitio con **las credenciales del
propio usuario** y guarda en su equipo lo que ese usuario decide descargar.

El problema que resuelve es concreto: quien archiva fanart suele acabar con
decenas de pestañas, descargas manuales y nombres de archivo inconsistentes.
ExtractorFanarts convierte ese trabajo en una operación única —elegir
plataforma, escribir el criterio de búsqueda, revisar la galería de resultados y
descargar— aplicando siempre las mismas reglas de filtrado, el mismo formato de
salida y el mismo registro auditable.

El proyecto nace con una convicción de diseño: **la ética y la legalidad no son
un módulo opcional, sino la puerta de entrada**. Ningún resultado llega a la
pantalla ni al disco sin atravesar antes el filtro de contenido prohibido, el
control de licencias, el gate de contenido adulto y la exclusión de plataformas
de pago.

> **Uso personal y privado.** No redistribuyas el material descargado: la mayor
> parte del fanart no tiene licencia liberada. El análisis completo de
> implicaciones legales está en [docs/INFORME-FACTIBILIDAD.md](docs/INFORME-FACTIBILIDAD.md).

---

## 2. Misión

**Dar a cualquier persona una herramienta de archivo de fanart que sea, a la
vez, potente y respetuosa**: potente porque agrupa más de veinte fuentes bajo
una sola interfaz y un solo flujo de trabajo; respetuosa porque trata con
cuidado a las tres partes implicadas —el artista, la plataforma y el usuario—.

En la práctica, la misión se concreta en cinco compromisos:

| Compromiso | Cómo se cumple |
|---|---|
| **No dañar a las plataformas** | Intervalo de cortesía entre peticiones, *backoff* ante 429/5xx, pausa automática ante bloqueos y **cero evasión de CAPTCHAs o logins** |
| **No decidir por el usuario** | Todo filtro es visible, explicable y configurable; el motivo exacto de cada descarte se muestra en pantalla |
| **No dejar el trabajo a medias** | Control de integridad en cada etapa (descarga, mejora, guardado) y cierre ordenado que no deja archivos a medias |
| **No esconder lo que hace** | Registro diario en texto plano con cada petición, respuesta y decisión de filtrado |
| **No exigir confianza ciega** | Código abierto, sin telemetría, sin servidor propio y con las credenciales siempre en el equipo del usuario |

---

## 3. Visión

**Un archivo personal de arte, ordenado y sostenible, construido sin dañar el
ecosistema que lo hace posible.**

A medio plazo, ExtractorFanarts aspira a ser el instrumento de referencia para
quien archiva fanart de forma sistemática:

- **Multiplataforma y sin ataduras:** un único flujo de trabajo idéntico en
  Windows, macOS y Linux, sin cuentas obligatorias ni servicios propietarios.
- **Extensible por configuración, no por código:** añadir un booru de una
  familia ya soportada es **una entrada en un array**, no un desarrollo.
- **Sostenible frente al cambio:** las plataformas modifican sus API, activan
  defensas y desaparecen. La arquitectura de adaptadores permite absorber esos
  cambios en un solo archivo por plataforma, sin tocar el núcleo.
- **Referente en respeto:** que «archivar fanart a gran escala» y «respetar al
  artista y a la plataforma» sean la misma frase, no dos objetivos en tensión.

---

## 4. Objetivos

### 4.1 Objetivo general

Ofrecer una aplicación de escritorio que permita **buscar, revisar y descargar
fanart de múltiples plataformas** —redes sociales, boorus y wikis de fandom—
desde una sola interfaz, con formato de salida homogéneo, filtrado ético
obligatorio y trazabilidad completa de cada operación.

### 4.2 Objetivos específicos

| # | Objetivo | Estado |
|---|---|---|
| 1 | Unificar **14 boorus** de 5 familias de software bajo una plantilla de adaptador replicable | ✅ |
| 2 | Cubrir **8 redes sociales** mediante API oficiales o endpoints públicos, sin scraping de sesión | ✅ |
| 3 | Soportar **wikis MediaWiki/Fandom** con búsqueda por franquicia, personaje y concepto | ✅ |
| 4 | Aplicar filtros legales y éticos **antes** de mostrar o guardar cualquier resultado | ✅ |
| 5 | Convertir **siempre** la salida a `.webp` con calidad configurable y original descartado | ✅ |
| 6 | Ofrecer mejora de calidad opcional (**Real-ESRGAN / waifu2x** o Lanczos) con validación anti-corrupción | ✅ |
| 7 | Mantener la **galería de resultados navegable** (carrusel, miniaturas, visor con zoom) sin llenar la memoria | ✅ |
| 8 | Registrar cada petición, respuesta y descarte en un **`.log` diario** legible | ✅ |
| 9 | Permitir el uso de **todas las claves en un archivo local ignorado por git**, nunca dentro del paquete | ✅ |
| 10 | Compilar y publicar para **Windows, macOS y Linux** desde un flujo reproducible (GitHub Actions) | ✅ |

---

## 5. Alcances

### 5.1 Dentro del alcance

- Búsqueda y descarga de **imágenes y animaciones** desde las plataformas listadas en [§6.1](#61-fuentes-soportadas).
- Búsqueda por **usuario, palabra clave, hashtags, tags de booru y páginas de wiki**, con combinación de varios valores por campo.
- **Filtrado ético/legal configurable**: lista negra, exclusión propia por tag/dominio/texto, gate de contenido adulto, licencia y deduplicación.
- **Post-procesado local**: conversión a WebP, mejora de calidad (IA o Lanczos), respeto de transparencia y control de integridad.
- **Archivo organizado**: subcarpetas por plataforma, nombres consistentes y metadatos `.json` opcionales.
- **Diagnóstico**: autocomprobación (`--selftest`), registro diario y utilidades de reparación.

### 5.2 Fuera del alcance (excluido por diseño)

| Exclusión | Motivo |
|---|---|
| **X/Twitter y Pinterest sin credenciales propias** | No existe acceso legítimo sin app de desarrollador y facturación/OAuth del usuario |
| **Pixiv de forma anónima** | Su API exige autenticación; se usa la API oficial con la cuenta del usuario |
| **Newgrounds (arte)** | No tiene API pública de arte; el adaptador lo documenta y explica el motivo al usarse |
| **Plataformas de pago** (Patreon, Pixiv Fanbox, Unifans, Fansky, OnlyFans, Fansly, premium) | Contenido de pago o exclusivo: se descarta el resultado cuyo enlace, texto o página apunte a esos dominios |
| **Boorus de contenido prohibido** | Excluidos por la lista negra del núcleo |
| **Evasión de CAPTCHAs o inicios de sesión automatizados** | El usuario resuelve el reto como humano y aporta su cookie; la app nunca lo evade |
| **Scraping de sesión autenticada / ingeniería inversa de apps móviles** | Se usan API oficiales o endpoints públicos únicamente |
| **Servidor central, cuenta en la nube o telemetría** | Todo el estado vive en el equipo del usuario |
| **Redistribución del material descargado** | Uso personal y privado; la mayoría del fanart no tiene licencia liberada |

### 5.3 Limitaciones conocidas

- **PyInstaller no compila de forma cruzada**: cada sistema operativo genera su propio ejecutable.
- **El paquete `onedir` pesa cientos de MB** (Qt + modelos de IA).
- **Algunos sitios limitan los tags por consulta** (p. ej. Danbooru anónimo admite 2); la app consulta con los permitidos y exige el resto en local, pero la cobertura puede ser parcial.
- **`cf_clearance` caduca** y solo es válido para el User-Agent que resolvió el reto.
- **La búsqueda social depende de la instancia**: algunas no permiten búsqueda de texto sin cuenta y la app recurre a la etiqueta equivalente o al RSS público.

---

## 6. Funciones

### 6.1 Fuentes soportadas

| Tipo | Plataformas |
|---|---|
| **Redes sociales (8)** | **Fediverso: cualquier instancia de Mastodon / Misskey / CherryPick** (detección automática del software), Bluesky, DeviantArt, Tumblr, **Pixiv** (API oficial con tu cuenta vía refresh token), X/Twitter (API v2 de pago, credenciales propias), Pinterest (API v5, OAuth propio), Newgrounds |
| **Boorus (14)** | Safebooru, Gelbooru, Rule34.xxx, The Big ImageBoard, Xbooru, Hypnohub, Danbooru, Safebooru (Donmai), Yande.re, Konachan, Konachan (SFW), Derpibooru, ATF Booru y **Rule34 Paheal** |
| **Familias de booru (5)** | `gelbooru`, `danbooru`, `moebooru`, `philomena` y `shimmie` |
| **Wikis de fandom (1)** | Fandom.com y cualquier wiki MediaWiki (búsqueda por franquicia, personaje y/o concepto) |

**Todos los boorus viven en un único array** (`BOORU_SITES` en `app/config.py`)
y se añaden sin programar nada: ver [§10.4](#104-añadir-o-cambiar-un-booru).

**Sin claves:** Fediverso, Bluesky, Safebooru, Danbooru, wikis y la mayoría de
boorus públicos.

### 6.2 Búsqueda

- **Búsqueda social con filtros combinados.** Los tres campos de *Red social*
  (usuario, palabra clave y hashtags) **se aplican a la vez**: `@usuario` + una
  palabra clave + dos hashtags devuelve solo las publicaciones que cumplen
  **todos** los campos rellenados. Dentro de un campo se admiten **varios
  valores y sin límite**: hashtags separados por espacios, comas o almohadillas;
  palabras clave separadas por comas, punto y coma o barras (un valor con
  espacios es una frase; con comillas, exacta).
- **«Alguno» o «todos».** Por defecto basta con que se cumpla **cualquiera** de
  los valores de un campo; para exigirlos todos: `SOCIAL_VARIOS_EN_CAMPO = "todos"`.
- **Búsqueda por tags en boorus (N tags, sin límite).** Se separan con espacios
  o comas y se buscan **todos a la vez** (intersección). Los operadores del
  booru (`-1girl`, `rating:general`, `user:foo`, `score:>100`, `*hair`) se envían
  tal cual pero no se exigen como tags del resultado.
  - **Verificación local:** si un resultado no lleva alguno de los tags pedidos,
    se descarta. El log indica cuántos se descartaron por ese motivo.
  - **Sitios con límite de tags:** la app no falla; consulta con los permitidos,
    avisa en la línea de *Conexión* y exige el resto en local.
- **Wikis:** búsqueda por franquicia, personaje y concepto mediante `prop=imageinfo`,
  que además recupera **autor (uploader)** y **licencia** cuando la wiki la declara.
- **Cortesía entre peticiones:** las consultas se espacian `MIN_REQUEST_INTERVAL`
  (1,5 s por defecto, ajustable). Ejemplo medido: 8 hashtags ≈ 15 s.

### 6.3 Galería de resultados

- **Carrusel alineado**: contador centrado, imagen grande con flechas `◀` `▶` y
  **tira de miniaturas exactamente del mismo ancho que la imagen**.
- **Una casilla por cada resultado** de la búsqueda o descarga: si hay 50
  resultados, el carrusel muestra `1 / 50` … `50 / 50`.
- **Todas las miniaturas se cargan**: las primeras `MUESTRAS_GALERIA = 8` al
  instante y el resto **en segundo plano** (≈1,5 s por miniatura, cancelable al
  lanzar otra búsqueda o pulsar Limpiar). Tope de fondo: `GALERIA_MAX_SEGUNDO_PLANO = 120`.
- **Muestras nítidas propias** en `.webp` ligero, generadas por la aplicación
  (no son las miniaturas borrosas de la API):

  | Muestra | De dónde sale | Tamaño | Para qué |
  |---|---|---|---|
  | Tira de miniaturas | miniatura de la API | `MUESTRA_ICONO_LADO_MAX = 512` px | iconos de 64 px |
  | Imagen grande / visor | **imagen ORIGINAL** | `MUESTRA_LADO_MAX = 1600` px | carrusel, visor y zoom |

- **Memoria acotada**: se conservan solo las últimas `GALERIA_MUESTRAS_EN_MEMORIA = 12`
  muestras grandes (la que estás viendo nunca se descarta).
- **Visor ampliado dentro de la ventana** (estilo *fancybox*): rueda = zoom
  (10 %–800 %), arrastrar = mover, doble clic o `0` = ajustar, `←`/`→` = cambiar
  de imagen, `+`/`-` = zoom, `Esc` o clic fuera = cerrar.

### 6.4 Menú contextual de las imágenes (clic derecho)

Con clic derecho sobre la imagen grande, cualquier miniatura o dentro del visor:

| Opción | Qué hace | Atajo |
|---|---|---|
| 📋 **Copiar imagen** | Copia al portapapeles la imagen original ya procesada (`.webp` + mejora) | `Ctrl+C` |
| 💾 **Guardar imagen** | Descarga **solo esa** imagen con el mismo nombre, subcarpeta y `.json` que la descarga masiva | `Ctrl+S` |
| 🗂️ **Guardar como…** | Igual, eligiendo carpeta y nombre en un diálogo | `Ctrl+Shift+S` |
| 🌐 **Abrir imagen original en el navegador** | Abre la URL original en el navegador predeterminado | — |
| 🔗 **Copiar enlace de la imagen original** | Copia esa URL al portapapeles | `Ctrl+Shift+C` |

- La calidad es **la misma que en la descarga masiva**: una sola implementación
  compartida descarga el original, lo convierte a `.webp` con la calidad del
  deslizador y aplica el upscaling configurado.
- Funciona **también tras solo pulsar Buscar**, sin descarga masiva previa.
- Al copiar, el portapapeles recibe el `.webp` **y** una imagen estándar, desde
  una carpeta temporal que se borra al terminar.
- Mientras hay una operación en curso, *Copiar*, *Guardar* y *Guardar como…*
  quedan deshabilitadas; *Abrir* y *Copiar enlace* siguen disponibles.

### 6.5 Descarga y mejora de calidad

- **Todo lo descargado se convierte siempre a `.webp`** con la calidad
  configurada (deslizador 1–100) y **el original nunca se conserva**.
- **Upscaling opcional** («✨ Mejorar calidad») según el lado mayor de la imagen:
  `<700px → 4x` · `700-799px → 3x` · `800-1500px → 2x` · `1501-1599px → 1x` ·
  `1600px+ → 2x`, con tope de 8K (`MAX_OUTPUT_SIDE = 7680 px`).
- **Modo IA** con Real-ESRGAN / waifu2x (ncnn-vulkan, GPU) si están instalados;
  si no, cae automáticamente a **Lanczos + afilado suave** y lo indica en el estado.
  - Para 2x y 3x se usa el modelo multiescala `realesr-animevideov3`; los
    `realesrgan-x4plus*` son x4 nativos y devolvían mosaicos con `-s 2/3`.
- **Transparencia respetada:** el canal alfa se separa, se reescala por su cuenta
  y se vuelve a aplicar (el RGB se aplana sobre blanco), evitando halos negros.
- **Deduplicación por hash (md5)** y **tope por fuente** (`MAX_RESULTS_PER_SOURCE`).
- **Metadatos `.json` opcionales**: solo si marcas «Guardar metadatos .json»
  (desactivado por defecto). Para limpiar `.json` antiguos:
  `python scripts\limpiar_sidecars.py "<carpeta>" --borrar`.

### 6.6 Control de integridad (anti-corrupción y anti-artefactos)

1. **Archivo descargado:** se decodifica completo antes de procesarlo; si está
   truncado o dañado → `ImagenCorruptaError`, se reintenta una vez y, si sigue
   mal, se descarta (no queda basura).
2. **Salida de IA validada:** cada resultado se compara con el original por
   diferencia media (MAE). Medido: salidas válidas ≈ 1–2, salida corrupta tipo
   mosaico ≈ 46. Con `AI_MAX_MAE = 12` cualquier salida anómala se descarta.
3. **Tamaño validado:** dimensiones inesperadas de la IA → rechazo.
4. **Fallback seguro:** si falla cualquier paso de la mejora, se aplica
   conversión directa a WebP en lugar de dejar algo roto.
5. **Verificación final:** el `.webp` se reabre y se comprueba (decodifica +
   tamaño); si no pasa, se conserva el original.
6. **El historial no puede tumbar una descarga ya guardada:** si la base de datos
   no es escribible, el archivo se conserva y solo queda el aviso en el log.

### 6.7 Filtros legales y éticos

Se aplican **siempre**, antes de mostrar o descargar. Puedes verlos con el botón
**«ℹ️ ¿Qué se filtra? (lista negra)»**, que muestra los arrays tal como están
configurados y la ruta del `config_local.py` en uso.

**Toda la lista negra vive en arrays de [`app/config.py`](app/config.py)** y el
código solo los lee ([`app/services/filters.py`](app/services/filters.py) no
guarda ningún valor), así que no hay que tocar código para gestionarla:

| Array (en `app/config.py`) | Qué hace |
|---|---|
| `PROHIBITED_TAG_TOKENS` | tags **exactos** que descartan el resultado |
| `PROHIBITED_TAG_PREFIXES` | cualquier tag que **empiece** por uno de estos prefijos |
| `BLOCKED_PAID_DOMAINS` | dominios de plataformas de pago excluidas |
| `EXCLUDED_TAG_TOKENS` | tu lista: tags (un `*` final = «empieza por») |
| `EXCLUDED_DOMAINS` | tu lista: dominios |
| `EXCLUDED_TEXT_TOKENS` | tu lista: texto del título/descripción |

Se admiten listas, tuplas o conjuntos. Además se aplican el **gate de rating
adulto** (`ALLOW_ADULT_RATINGS`), la **licencia** (`REQUIRE_FREE_LICENSE` +
`FREE_LICENSE_HINTS`), la **deduplicación por hash** y el **tope por fuente**.

```python
# en config_local.py (por ejemplo)
PROHIBITED_TAG_PREFIXES = ["pedo"]                  # descarta «pedo_x», «pedo_art»…
BLOCKED_PAID_DOMAINS = ["patreon.com", "fanbox.cc", "onlyfans.com", "fansly.com",
                        "unifans.io", "fansky.social", "fansky.app",
                        "subscribestar.adult", "gumroad.com"]
EXCLUDED_TAG_TOKENS = ["gore", "vore", "scat", "guroli*"]
EXCLUDED_DOMAINS = ["deviantart.com", "pinterest.com"]
EXCLUDED_TEXT_TOKENS = ["commission open", "adopt", "ych"]
```

En los resultados verás el **motivo exacto** de cada descarte (*«contenido
prohibido (lista negra)»*, *«excluido por tu lista (tag gore)»*, *«rating no
permitido (explicit)»*…), también en la línea de *Conexión* y en el registro
diario (`resultados filtrados: N aceptados; descartados -> …`).

### 6.8 Registro, consola y diagnóstico

- **Un solo aviso por operación:** si una búsqueda no da resultados sale **un
  único** aviso con el motivo; si el fallo es crítico, **un único** diálogo de
  error. Nunca los dos.
- **Errores resumidos en pantalla, detalle en el registro:** el diálogo muestra
  solo la primera línea; el texto completo con traceback va al `.log` y a la consola.
- **Log por día:** `~/.extractorfanarts/logs/app-AAAA-MM-DD.log` (o
  `<proyecto>/logs/…` si esa ruta no es escribible), con
  `LOG_DIAS_A_CONSERVAR = 30` días (0 = no borrar nunca). Si la app sigue abierta
  al cambiar el día, **pasa sola** al archivo nuevo. Cada arranque deja una
  cabecera de sesión (fecha, versión, PID).
- **Consola de registros:** el ejecutable de Windows abre además una ventana de
  consola con los mismos registros que el `.log` del día. Se puede desactivar con
  `LOG_EN_CONSOLA = False` en `app/config_local.py`.
- **Las claves se enmascaran** en los logs (`api_key=6c0ed7…476e[128]`).

```
16:38:47 | INFO | → GET api.rule34.xxx/index.php?page=dapi&...&api_key=6c0ed7…476e[128]&user_id=3691365
16:38:47 | INFO | ← HTTP 403 text/html 76.7 KB en 0.19 s (api.rule34.xxx)
16:38:47 | ERROR| api.rule34.xxx exige superar un CAPTCHA de Cloudflare (HTTP 403) ...
16:39:02 | INFO | [progreso] 2/5 (40%) Safebooru: Safebooru_123_ab12cd34.webp
16:39:02 | INFO | ⇩ Safebooru_123_ab12cd34.webp descargado: 812 KB (image/webp) en 0.9 s
```

- **Anti-bloqueo:** ante 429/5xx o un posible bloqueo (401/403) la app **pausa**
  (30 s → 5 min, con reintentos) y continúa; si el bloqueo persiste, descarta la
  fuente e informa. **No evade CAPTCHAs ni logins.**

### 6.9 Icono e interfaz adaptable

- **Icono generado por código** (una paleta de pintura con pincel), sin depender
  de imágenes ni fuentes externas: se aplica al ejecutable, a la ventana, a la
  barra de tareas y a los controles clave.

  | Archivo | Para qué |
  |---|---|
  | `assets/icon.ico` | Windows: multi-tamaño 16, 24, 32, 48, 64, 128, 256 |
  | `assets/icon.png` | 1024 px (macOS/Linux, vistas previas) |
  | `assets/icon_256.png` | Icono de ventana en cualquier sistema |
  | `assets/icon_preview.png` | Tira de comprobación en todos los tamaños |

- **Icono propio en la barra de tareas (Windows):** la app fija un
  **AppUserModelID** (`ExtractorFanarts.App`) antes de crear la aplicación Qt;
  sin eso Windows agruparía el proceso bajo el intérprete y mostraría el icono de Python.
- **La ventana nunca tapa la barra de tareas:** se ajusta a
  `QScreen.availableGeometry()` (que ya descuenta barra de tareas, dock o panel).
- **Interfaz responsive real:** los campos se estiran, el deslizador crece, las
  casillas usan una rejilla estable de 2 columnas y las etiquetas largas ajustan
  línea. Medidas reales: **mínimo 728×695**, verificado a 1020×820, 1400×950,
  1000×760, 900×700 y maximizada/restaurada, sin barras de desplazamiento.

### 6.10 Atajos de teclado

| Tecla | Dónde | Qué hace |
|---|---|---|
| `Enter` | cualquier campo o control de búsqueda (usuario, palabra clave, hashtags, instancia, tags, fandom, personaje, URL, calidad, cantidad, casillas, desplegables…) | **Buscar** |
| `Shift+Enter` | igual que arriba | **Descargar** (con la confirmación habitual) |
| `Enter` | campo **Salida** (carpeta) | abre el diálogo para **elegir carpeta** |
| `Enter` | botón enfocado: **Buscar**, **Descargar/Cancelar** o **Limpiar** | lo pulsa |
| `Enter` / `Esc` | con una búsqueda o descarga en curso | **cancela** la operación |
| `Esc` | con el visor ampliado abierto | lo cierra |
| `Enter` o `Espacio` | imagen grande del carrusel (se enfoca con `Tab`) | abre el visor ampliado |
| `Enter` | miniatura seleccionada de la tira (se mueve con `←`/`→`) | la muestra y abre el visor |
| `Alt+F4` / `Ctrl+Q` | en cualquier parte de la ventana | **cierra** con cierre ordenado |

Los desplegables conservan su comportamiento: con la lista abierta, `Enter`
elige la opción; con la lista cerrada, busca.

**Cierre ordenado** (Alt+F4, Ctrl+Q, la X o la barra de tareas): si hay una
operación en curso se pregunta antes; al aceptar se cancela el trabajo pendiente,
se **espera a las tareas de fondo** (hasta 3 s) y se **cierra el almacén**, de
modo que no queden archivos a medias ni la base de datos abierta. El cierre es
**idempotente** y queda registrado (`aplicación cerrada correctamente`).

---

## 7. Arquitectura

### 7.1 Patrón MVC

El proyecto sigue una separación estricta **Modelo–Vista–Controlador** sobre
PySide6, con una capa de **adaptadores** que aísla por completo las diferencias
entre plataformas.

```
        ┌──────────────────────────────────────────────────────┐
        │                      VISTA (Qt)                      │
        │  main_window.py · galeria.py · icono.py              │
        │  Solo presenta y captura intención del usuario.      │
        └───────────────┬──────────────────────────────────────┘
                        │ señales / llamadas
        ┌───────────────▼──────────────────────────────────────┐
        │              CONTROLADOR (orquestación)              │
        │  main_controller.py: hilos, estados, pipeline,       │
        │  progreso, cancelación, cierre ordenado              │
        └───────────────┬──────────────────────────────────────┘
                        │
        ┌───────────────▼──────────────────────────────────────┐
        │                   SERVICIOS                          │
        │  http_client.py  → cooldown, backoff, pausa, huella  │
        │  filters.py      → filtros legales/éticos            │
        │  muestras.py     → muestras .webp de la galería      │
        │  enhance.py      → WebP, upscaling, integridad       │
        │  ugoira.py       → animaciones de Pixiv              │
        │  adapters/       → UNA plantilla por plataforma      │
        └───────────────┬──────────────────────────────────────┘
                        │
        ┌───────────────▼──────────────────────────────────────┐
        │                MODELO / PERSISTENCIA                 │
        │  artwork.py · store.py (SQLite) · config.py          │
        └──────────────────────────────────────────────────────┘
```

**Principios rectores:**

1. **La vista no decide nada ético.** Los filtros viven en el controlador y en
   los servicios; la vista únicamente representa lo que ya pasó el filtro.
2. **Un adaptador por plataforma.** Cada sitio implementa la misma interfaz
   (`SearchAdapter`), devolviendo un contrato común (`Artwork`). Añadir un sitio
   no obliga a tocar el núcleo.
3. **La configuración no se compila.** `config_local.py` sobreescribe cualquier
   constante en MAYÚSCULAS de `app/config.py` y está ignorado por git.
4. **Nada se guarda sin verificar.** Toda ruta de escritura termina en una
   comprobación de integridad.
5. **Degradar, no fallar.** Sin IA se usa Lanczos; sin red se explica el motivo;
   sin carpeta escribible se proponen alternativas.

### 7.2 Estructura del repositorio

```
main.py                       entrada: prepara ./vendor, consola, logging y Qt
                              (--selftest, --version)
app/
  config.py                   sitios, límites, listas negras, rutas (fuente de verdad)
  config_local.py             TUS claves y ajustes (ignorado por git, no se versiona)
  consola.py                  consola propia de registros en Windows
  icono.py                    resolución del icono y AppUserModelID
  logging_setup.py            log diario, rotación por días, cabecera de sesión
  models/
    artwork.py                modelo de resultado (Artwork, SearchQuery)
    store.py                  almacén SQLite (historial y deduplicación)
  controllers/
    main_controller.py        hilos, estados, pipeline, progreso, cancelación
  services/
    http_client.py            HTTP con cooldown, backoff, pausa y huella de navegador
    filters.py                filtros legales y éticos (solo lee config)
    muestras.py               muestras .webp nítidas para la galería
    enhance.py                conversión WebP, upscaling IA/Lanczos, integridad
    ugoira.py                 composición de animaciones de Pixiv
    adapters/
      __init__.py             registro: BOORU_ADAPTERS, SOCIAL_ADAPTERS, WIKI_ADAPTERS
      base.py                 contrato SearchAdapter
      booru.py                plantilla de las 5 familias de booru
      fediverso.py            detección Mastodon / Misskey / CherryPick
      mastodon.py misskey.py bluesky.py deviantart.py tumblr.py
      twitter.py pinterest.py pixiv.py newgrounds.py
      mediawiki.py            wikis MediaWiki / Fandom
      social_filtros.py       criterios combinados de búsqueda social
  views/
    main_window.py            ventana principal, formulario, opciones, estado
    galeria.py                carrusel, miniaturas y visor ampliado
assets/                       iconos generados (icon.ico, icon.png…)
docs/
  INFORME-FACTIBILIDAD.md     análisis legal, técnico y de viabilidad
scripts/                      herramientas de desarrollo, build, firma y release
.github/workflows/build.yml   compilación y publicación para los 3 sistemas
compilar.bat                  compila el .exe (con consola de registros)
ejecutar.bat                  ejecuta en desarrollo aplicando los ajustes locales
crear_certificado.bat         crea un certificado autofirmado
firmar.bat                    firma el ejecutable con signtool
LEEME-PRIMERO.txt             guía de primeros pasos que se adjunta al paquete
THIRD-PARTY-NOTICES.txt       licencias de los componentes redistribuidos
```

### 7.3 Flujo de una operación

```
Usuario pulsa Buscar/Descargar
        │
        ▼
Controlador valida el formulario y lanza un hilo de trabajo
        │
        ▼
Adaptador de la plataforma elegida
        ├── construye la consulta (usuario / palabra / hashtag / tags / wiki)
        ├── la espacia con MIN_REQUEST_INTERVAL y aplica backoff si hay bloqueo
        └── devuelve candidatos normalizados como Artwork
        │
        ▼
filters.py  →  lista negra · tu lista · rating adulto · licencia · pago · dedup · tope
        │
        ▼
Galería (muestras .webp)  ──►  revisión del usuario
        │
        ▼
enhance.py  →  descarga original → verifica integridad → WebP (+ upscaling)
            →  reabre y comprueba  →  guarda en <salida>/<plataforma>/
        │
        ▼
store.py (historial SQLite)  +  logging_setup.py (.log del día)
```

### 7.4 Decisiones de diseño destacadas

| Decisión | Por qué |
|---|---|
| **Sin servidor propio ni telemetría** | Privacidad: el historial y las claves nunca salen del equipo |
| **Credenciales fuera del paquete** | `config_local.py` se lee junto al ejecutable o en `~/.extractorfanarts/`; el build deja solo una plantilla |
| **Deduplicación por md5** | Evita volver a descargar y procesar lo ya archivado |
| **Muestras propias en vez de miniaturas de la API** | La miniatura de la API se ve borrosa al ampliarla; la muestra se genera del original |
| **Modo IA solo para archivos guardados** | Aplicar IA a cada muestra de pantalla multiplicaría el tiempo sin nitidez visible |
| **Verificación por MAE en las salidas de IA** | Detecta el fallo real observado (imágenes tipo mosaico) y activa el respaldo |
| **Etiqueta de integridad del paquete a «Media»** | Evita que un build hecho en un entorno restringido deje la app sin permiso de escritura |

---

## 8. Requisitos

| Elemento | Requisito |
|---|---|
| **Sistema** | Windows 10/11, macOS o Linux de escritorio |
| **Python** (solo desde código) | **3.12** recomendado (el workflow usa 3.12) |
| **Dependencias** | `PySide6>=6.6`, `httpx>=0.27`, `Pillow>=10`, `curl_cffi>=0.7` |
| **Empaquetado** (solo dev) | `PyInstaller>=6.0` |
| **Motores de IA** (opcional) | Real-ESRGAN / waifu2x ncnn-vulkan con GPU |
| **Red** | Conexión a internet; algunas fuentes requieren claves propias |

---

## 9. Instalación

### 9.1 Usuario final (ejecutable)

1. Descarga el `.zip` de tu sistema desde
   [Releases](https://github.com/rgomezs2000/extractorfanarts/releases) y
   **verifica la descarga** con el `.sha256` que lo acompaña:
   ```powershell
   Get-FileHash .\ExtractorFanarts-*.zip -Algorithm SHA256
   ```
2. Descomprime y ejecuta `ExtractorFanarts.exe` (o el binario / `.app`).
   En Windows aparecerá el aviso de SmartScreen la primera vez: ver [§13](#13-firma-digital-y-smartscreen).
3. **Opcional:** crea `config_local.py` **junto al ejecutable** (o en
   `~/.extractorfanarts/config_local.py`) con tus claves. Ver [§10](#10-configuración).
4. Lee **`LEEME-PRIMERO.txt`**, incluido en el paquete, para los primeros pasos.

### 9.2 Desde el código fuente

```powershell
git clone https://github.com/rgomezs2000/extractorfanarts.git
cd extractorfanarts

# Opción A — con pip, instalando en ./vendor
python -m pip install --target vendor PySide6 httpx Pillow curl_cffi

# Opción B — sin pip (instalador propio, útil si pip está restringido)
python scripts\setup_vendor.py vendor

python main.py
```

Doble clic en **`ejecutar.bat`** hace lo mismo aplicando los ajustes locales.

> `main.py` añade `./vendor` al `PYTHONPATH` automáticamente, así que basta con
> que las dependencias estén ahí (o instaladas de forma global).

### 9.3 Modo IA (opcional)

```powershell
python scripts\setup_vendor.py --ai
```

Descarga Real-ESRGAN y waifu2x (ncnn-vulkan) con sus modelos. Sin ellos la
aplicación funciona igual y usa **Lanczos + afilado suave**.

### 9.4 Comprobar la instalación

```powershell
python main.py --selftest      # informe de entorno (dependencias, adaptadores, carpetas)
python main.py --version       # versión instalada
```

`--selftest` comprueba PySide6, httpx, PIL, certifi, curl_cffi, el número de
adaptadores, el motor de IA, la escritura en la carpeta de salida y la
construcción de la ventana en segundo plano. Deja el informe en
`selftest.txt` junto al ejecutable.

---

## 10. Configuración

### 10.1 Dónde van las claves

> **Recomendado:** edita **`app/config_local.py`** (ignorado por git). Cualquier
> constante en MAYÚSCULAS que definas ahí **sobreescribe** `app/config.py`, así
> tus claves nunca llegan al repositorio. Requiere **reiniciar la app**.

Con el ejecutable, `config_local.py` se busca **por este orden**:

1. junto al ejecutable (o junto a `main.py` en desarrollo),
2. dentro del paquete empaquetado,
3. `~/.extractorfanarts/config_local.py` ← lo más cómodo con el `.exe`.

El archivo que viene en el paquete es **solo una plantilla sin claves**, y
`scripts/release.py` verifica que el `.zip` no contenga credenciales antes de
publicarlo.

### 10.2 Claves por plataforma

| Plataforma | Constantes | Dónde se obtienen |
|---|---|---|
| **Gelbooru / Rule34.xxx** | `GELBOORU_API_KEY` + `GELBOORU_USER_ID`, `RULE34_API_KEY` + `RULE34_USER_ID` | Página de opciones de tu cuenta → *API Access Credentials*: [rule34.xxx](https://rule34.xxx/index.php?page=account&s=options) · [gelbooru.com](https://gelbooru.com/index.php?page=account&s=options). **API key** = cadena larga; **User ID** = número corto |
| **FBooru** | `FBOORU_API_KEY` + `FBOORU_LOGIN` | Perfil de su API (`booru.fbooru.net/profile.json`); se envían en cada consulta |
| **DeviantArt** | `DEVIANTART_CLIENT_ID` + `DEVIANTART_CLIENT_SECRET` | [deviantart.com/developers](https://www.deviantart.com/developers/) |
| **Tumblr** | `TUMBLR_API_KEY` | [tumblr.com/oauth/apps](https://www.tumblr.com/oauth/apps) |
| **Pixiv** | `PIXIV_REFRESH_TOKEN` | `python scripts\pixiv_token.py` — ver [§10.3](#103-pixiv-tu-cuenta) |
| **X/Twitter** | `X_BEARER_TOKEN` (o `X_API_KEY` + `X_API_SECRET`) | App de desarrollador **con facturación**: la API v2 es de pago por uso |
| **Pinterest** | `PINTEREST_ACCESS_TOKEN` (+ `PINTEREST_COUNTRY_CODE`) | App aprobada + OAuth del usuario; la búsqueda global usa un endpoint beta |
| **Cloudflare** | `CF_CLEARANCE` + `CF_USER_AGENT` | Ver [§15.1](#151-captcha-de-cloudflare-p-ej-rule34xxx) |
| **Fediverso, Bluesky, Safebooru, Danbooru, wikis** | — | sin claves |

### 10.3 Pixiv (tu cuenta)

Pixiv no ofrece acceso anónimo: su API exige autenticación. La aplicación usa la
**API oficial de la app** con **tu propia cuenta** mediante un *refresh token*
(no guarda tu contraseña y no hace scraping de la web).

1. Ejecuta `python scripts\pixiv_token.py`.
2. Abre el enlace que muestra e **inicia sesión** con tu cuenta de Pixiv.
3. El navegador terminará en una URL con `?code=...` (la página puede dar error:
   es normal). Copia esa URL completa o solo el código y pégala en la consola.
4. El script obtiene el **refresh token** y puede guardarlo en `app/config_local.py`.
5. **Reinicia la app.**

En la UI (Tipo: *Red social* → Plataforma: *Pixiv*):

| Filtro | Qué hace |
|---|---|
| palabra clave / `#hashtag` | búsqueda por etiquetas (`/v1/search/illust`) |
| `@usuario` o id numérico | obras de ese usuario (`/v1/user/illusts`) |

- Las obras de **varias páginas** se guardan como archivos separados (`_p0`, `_p1`, …).
- **Animaciones ugoira:** se descarga el ZIP de fotogramas y se compone un
  **WebP animado** con los retrasos originales. Límites:
  `UGOIRA_MAX_FRAMES = 400`, `UGOIRA_MAX_ZIP_MB = 200`. El CDN de Pixiv
  (`i.pximg.net`) exige la cabecera `Referer`, que la app envía por dominio
  (`REFERER_DOMAINS`).
- Rating según `x_restrict`: R-18 → `questionable`, R-18G → `explicit`.

### 10.4 Añadir o cambiar un booru

**Todos los boorus están en un único array** en [`app/config.py`](app/config.py)
→ `BOORU_SITES`, y cada entrada lleva su **nombre**, su **sitio** y **sus
tokens**. El adaptador es una plantilla replicable: **no hay que programar nada**
para añadir un booru de una familia ya soportada.

```python
BOORU_SITES = [
    {"name": "Safebooru", "family": "gelbooru", "base": "https://safebooru.org",
     "auth": None,                                   # público, sin credenciales
     "view_tpl": "https://safebooru.org/index.php?page=post&s=view&id={id}"},

    {"name": "Gelbooru", "family": "gelbooru", "base": "https://gelbooru.com",
     "auth": {"api_key": GELBOORU_API_KEY, "user_id": GELBOORU_USER_ID},
     "view_tpl": "https://gelbooru.com/index.php?page=post&s=view&id={id}"},

    # Booru de la familia Danbooru con sus propias credenciales
    {"name": "FBooru", "family": "danbooru", "base": "https://booru.fbooru.net",
     "auth": {"api_key": FBOORU_API_KEY, "login": FBOORU_LOGIN},
     "view_tpl": "https://booru.fbooru.net/posts/{id}"},
]
```

- **`auth`** admite `{"api_key":…, "user_id":…}` (Gelbooru/Rule34),
  `{"api_key":…, "login":…}` (Danbooru y familia),
  `{"login":…, "password_hash":…}` (Moebooru) y `{"api_key":…}` (Philomena,
  opcional). Si falta un campo, la app lo dice por su nombre al usar ese booru.
- También se admite la forma abreviada `"auth": ("GELBOORU",)`, que lee las
  claves de las constantes de `app/config.py` (compatibilidad con configuraciones
  antiguas).
- **Para no subir tus tokens**, define el array completo (o solo el booru nuevo)
  en `config_local.py`: lo que pongas ahí sobreescribe `app/config.py`.
- **Si el dominio no existe** o no hay internet, la búsqueda no revienta: verás
  *«no se pudo conectar con … — Comprueba que el dominio del sitio exista y esté
  bien escrito, y tu conexión a internet»*, y la traza completa queda en el registro.
- **Familias:** `gelbooru`, `danbooru`, `moebooru`, `philomena` y `shimmie`
  (Rule34 Paheal y demás tableros Shimmie: `/post/list/<tags>/<página>`, 70 por
  página, tags separados por espacios).

**Rule34 Paheal (familia Shimmie).** Corre Shimmie 2 y trae la **API pública
desactivada**: `/api/…` responde HTML, no JSON. Por eso la familia `shimmie` lee
su **listado público** (el mismo HTML que recibe tu navegador), de donde obtiene
por cada resultado el id, **la lista completa de etiquetas** (`data-tags`), el
tipo (`data-mime`; los vídeos se descartan), la miniatura y el enlace del
**archivo completo**, cuyo nombre es su **md5** (sirve para deduplicar). Es un
tablero **adulto**: sus resultados entran con rating `explicit`, así que hay que
marcar **«Contenido adulto»** en Opciones.

### 10.5 Ajustes frecuentes

| Constante | Para qué |
|---|---|
| `DEFAULT_OUTPUT_DIR` | carpeta de salida por defecto (también se cambia con 📂 en la UI) |
| `MIN_REQUEST_INTERVAL` | intervalo de cortesía entre peticiones (1,5 s por defecto) |
| `MUESTRA_LADO_MAX`, `MUESTRA_CALIDAD_WEBP` | tamaño y calidad de las muestras de la galería |
| `MUESTRAS_ORIGINALES = False` | vuelve al comportamiento ligero (miniaturas de la API, borrosas al ampliar) |
| `SOCIAL_VARIOS_EN_CAMPO = "todos"` | exige **todos** los valores de un campo social en vez de cualquiera |
| `BROWSER_IMPERSONATE` | navegador cuya huella TLS se imita (`"chrome"`, `"edge101"`, `"firefox133"`…) |
| `BROWSER_DOMAINS` | dominios que usan huella de navegador (añade aquí un sitio nuevo con `403 "Just a moment…"`) |
| `CF_DOMAINS` | dominios que usan `curl_cffi` cuando hay `CF_CLEARANCE` |
| `ALLOW_ADULT_RATINGS` | ratings permitidos (gate de contenido adulto) |
| `REQUIRE_FREE_LICENSE`, `FREE_LICENSE_HINTS` | exigir y reconocer licencia liberada (CC0/CC-BY/dominio público) |
| `MAX_RESULTS_PER_SOURCE` | tope de resultados por fuente |
| `SHARPEN_LANCZOS = 65`, `SHARPEN_AI = 25` | afilado tras el reescalado |
| `MAX_OUTPUT_SIDE = 7680` | tope de lado de salida (8K) |
| `AI_MAX_MAE = 12` | umbral de descarte de salidas anómalas de la IA |
| `LOG_DIAS_A_CONSERVAR = 30` | días de `.log` que se conservan (0 = nunca borrar) |
| `LOG_EN_CONSOLA = False` | desactiva la consola de registros |

---

## 11. Instrucciones de uso

### 11.1 Flujo básico

1. **Tipo** → *Red social*, *Booru* o *Wiki*.
2. **Plataforma** → el sitio concreto (la lista cambia según el tipo).
3. **Criterio de búsqueda** según el tipo:
   - *Red social:* `@usuario` · palabra(s) clave · `#hashtag(s)` · instancia (fediverso).
   - *Booru:* tags (los que quieras, separados por espacios o comas).
   - *Wiki:* fandom · personaje · URL de la wiki.
4. Pulsa **🔍 Buscar** (o `Enter`) y revisa la galería de resultados.
5. Ajusta **📂 Salida**, **🎚️ Calidad WebP**, **✨ Mejorar calidad**, **🤖 Modo IA**,
   **🔢 Limitar cantidad** y **🏷️ Metadatos .json** si lo necesitas.
6. Pulsa **⬇️ Descargar** (o `Shift+Enter`) y confirma el diálogo.

### 11.2 Búsqueda en el fediverso (Mastodon / Misskey / CherryPick)

Una sola plataforma cubre todos los servidores: la app **detecta
automáticamente** el software (`/api/v1/instance` para Mastodon, `/api/meta`
para Misskey/CherryPick) y guarda el resultado en caché por host.

| Cómo buscas | Qué hace |
|---|---|
| `@usuario@baraag.net` | consulta **la instancia de ese usuario** (no la seleccionada) |
| `@usuario` + campo **Instancia** | usa la instancia que escribas (p. ej. `mastodon.art`) |
| `#hashtag` / palabra clave | busca en la instancia elegida (por defecto `mastodon.social`) |

- Todo con **endpoints públicos, sin login** (no se usa `resolve=true`, que
  Mastodon exige autenticado y provocaba `HTTP 401`).
- **Instancias restrictivas:** algunas (p. ej. `baraag.net`) responden
  `422 {"error":"This method requires an authenticated user"}` en las timelines
  por hashtag. La app lo detecta y usa el **RSS público de la etiqueta**
  (`/tags/<tag>.rss`) como respaldo; los elementos del RSS se marcan como
  `sensitive`.
- En Bluesky, el `@usuario@host` del fediverso se traduce a `usuario.host`.

### 11.3 Carpeta de salida

- **Se crea automáticamente** si no existe, con subcarpetas por plataforma.
- **Aviso al arrancar:** se comprueba (sin cambiar nada) si es escribible; si no
  lo es, lo dice desde el principio en la barra de estado.
- **Buscar nunca falla por la carpeta**; **Descargar** sí necesita una carpeta
  escribible: si la elegida da *Acceso denegado*, la app prueba alternativas
  (`~/Downloads/ExtractorFanarts`, `~/.extractorfanarts/descargas`,
  `~/ExtractorFanarts` y, como último recurso, `descargas` junto a la aplicación)
  y **actualiza el campo «Salida»** con la que funcione.
- **Por defecto apunta a la carpeta de IMÁGENES del sistema** con la subcarpeta
  `ExtractorFanarts`, nunca a Documentos:
  - **Windows:** valor `My Pictures` del registro (funciona también si OneDrive la redirige) → `C:\Users\<usuario>\Pictures\ExtractorFanarts`
  - **Linux:** `XDG_PICTURES_DIR` de `~/.config/user-dirs.dirs` (puede estar en tu idioma, p. ej. `~/Imágenes`) → `~/Imágenes/ExtractorFanarts`
  - **macOS:** `~/Pictures/ExtractorFanarts`

### 11.4 Otros controles

- **Límite de cantidad:** con «Limitar cantidad de descargas» se descarga solo la
  cantidad indicada (1–1000); sin marcar, todo lo encontrado (hasta
  `MAX_RESULTS_PER_SOURCE`).
- **Cancelar:** detiene la operación y restaura la UI, conservando la imagen de ejemplo.
- **Limpiar:** limpia el formulario (no descarga nada; solo disponible en reposo).
- **Barra de progreso siempre visible** debajo del panel de resultados: en reposo
  `⬇️ 0% · en reposo`, al buscar `🔍 buscando…`, al descargar `⬇️ %p% (n/total)`.
  Debajo, **«📡 Conexión: …»** con la última petición/respuesta (verde = correcta,
  rojo = CAPTCHA/error/pausa).

### 11.5 Diagnóstico rápido

```powershell
python main.py --selftest                    # informe completo del entorno
python scripts\diag_conexion.py Rule34.xxx   # credenciales + conexión de un sitio
python scripts\diag_conexion.py Safebooru    # control sin claves
```

---

## 12. Empaquetado como ejecutable

**PyInstaller no compila de forma cruzada**: cada sistema operativo genera su
propio ejecutable.

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

Atajos: **`compilar.bat`** (doble clic) hace todo el proceso y compila **con
consola**. Opciones de `build_exe.py`: `--onefile` (un solo archivo), `--consola`
(ventana de consola con los registros), `--probar` (ejecuta `--selftest` del
resultado), `--firmar` (firma el ejecutable).

Al terminar, la compilación **devuelve la etiqueta de integridad del paquete a
«Media»** (`icacls … /setintegritylevel Medium /T`). Es imprescindible si
compilas desde un entorno restringido; para un paquete ya compilado:
`python scripts\arreglar_integridad.py`.

**Notas importantes:**

- **Las credenciales NO se empaquetan.** El build deja una **plantilla** al lado
  del binario. Así tus claves nunca entran en el paquete.
- **Registros y base de datos** viven en `~/.extractorfanarts/`, fuera del paquete.
- **Tamaño:** el paquete `onedir` ronda los cientos de MB por Qt y los binarios de IA.
- **macOS:** un `.app` sin firmar muestra *«no se puede abrir»* → clic derecho →
  **Abrir**, o `xattr -dr com.apple.quarantine ExtractorFanarts.app`. Para
  distribuirlo a terceros hace falta un certificado de Apple (Developer ID) y notarización.
- **Linux:** conviene compilar en una distribución antigua (o contenedor) para
  que el binario funcione en más sistemas; también puede empaquetarse como AppImage.
- ⚠️ **No ejecutes nunca el `.exe` de `build\`.** Esa carpeta contiene un paso
  intermedio incompleto y falla con *«Failed to load Python DLL …»*. El ejecutable
  bueno es **`dist\ExtractorFanarts\ExtractorFanarts.exe`**. La compilación borra
  `build\` automáticamente al terminar.

---

## 13. Firma digital y SmartScreen

Al ejecutar por primera vez el `.exe` recién compilado, Windows puede mostrar
**«Windows protegió su PC»** (SmartScreen). Es lo normal en un ejecutable **sin
firmar digitalmente**: no significa que tenga virus.

**Para ejecutarlo de todas formas:** *Más información* → **Ejecutar de todas
formas**. Si sigue bloqueado: clic derecho en el `.exe` → *Propiedades* → marca
**Desbloquear** → *Aceptar*.

**Para que no vuelva a aparecer** hay que firmar con un certificado de firma de
código (se compra a una CA; **los autofirmados no eliminan SmartScreen**):

```powershell
# con un archivo .pfx
$env:EF_CERT_PFX = "C:\ruta\certificado.pfx"
$env:EF_CERT_PASSWORD = "tu_contraseña"
python scripts\build_exe.py --firmar

# o con un certificado ya instalado en Windows
$env:EF_CERT_THUMBPRINT = "HU3LL4..."
python scripts\build_exe.py --firmar
```

En GitHub Actions, si defines los secretos `WINDOWS_CERT_PFX_BASE64` (el `.pfx`
en base64) y `WINDOWS_CERT_PASSWORD`, el workflow firma automáticamente el
paquete de Windows. Un certificado **EV** obtiene reputación inmediata.

### 13.1 Crear un certificado autofirmado (para tu equipo)

```powershell
# opción recomendada: doble clic en  crear_certificado.bat
# equivalentes:
python scripts\hacer_certificado.py --simular   # muestra los comandos, sin ejecutar nada
python scripts\hacer_certificado.py             # crea certs\codigo.pfx y certs\codigo.cer
python scripts\hacer_certificado.py --confiar   # + marcarlo de confianza en TU usuario
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\hacer_certificado.ps1
```

> ⚠️ **Si falla con «No existe ninguna unidad con el nombre 'Cert'»:** no es tu
> Windows. El **Python de la Microsoft Store** lanza sus procesos hijos en un
> contenedor (MSIX) que **no puede leer el registro de certificados**, así que
> `Microsoft.PowerShell.Security` no carga y desaparecen `Cert:\` y
> `ConvertTo-SecureString`. Solución: usa **`crear_certificado.bat`** (doble clic)
> o un PowerShell normal. Compruébalo con `Test-Path Cert:\CurrentUser\My` → debe dar `True`.

Luego firma (recomendado: doble clic en **`firmar.bat`**, que localiza `signtool`
solo y lee la clave de `certs\clave.txt`):

```powershell
$env:EF_CERT_PFX = "$PWD\certs\codigo.pfx"
$env:EF_CERT_PASSWORD = (Get-Content certs\clave.txt)
python scripts\build_exe.py --firmar
```

- Sirve para que **tu PC** reconozca al editor (deja de decir «Editor desconocido»).
- **No elimina SmartScreen** en los equipos de otras personas.
- 🔐 `certs/`, `*.pfx` y `*.cer` están en `.gitignore`: **la clave privada no se sube nunca**.

### 13.2 Certificado de una CA (de pago)

| Tipo | Precio aprox. | SmartScreen | Requisito |
|---|---|---|---|
| OV (organización) | 200–400 €/año | reputación progresiva | clave privada en **token/HSM** (desde 2023) |
| EV (validación extendida) | 400–700 €/año | **inmediata** | token/HSM |
| **Azure Trusted Signing** | ~10 €/mes | progresiva | **sin token**, integrable en GitHub Actions |

Proveedores: DigiCert, Sectigo, SSL.com, Certum, GlobalSign. Como la clave ya no
puede estar en un `.pfx` suelto, la firma se hace con su servicio en la nube
(DigiCert KeyLocker, SSL.com eSigner, Sectigo Cloud) o con Azure Trusted Signing.

### 13.3 Sin certificado (lo habitual en proyectos abiertos)

Publica en GitHub Releases con el **`LEEME-PRIMERO.txt`** (ya se añade al
paquete) explicando el aviso y el archivo **`.sha256`** para que cada usuario
verifique su descarga.

---

## 14. Publicar un release

La versión se toma de `APP_VERSION` en [`app/config.py`](app/config.py) y puede
forzarse con `python scripts\release.py --version 0.2.0`.

> **Fase beta.** Una etiqueta con sufijo (`v0.1.0-beta.1`) se publica
> automáticamente como **pre-release** de GitHub: queda marcada como beta, no
> sustituye a la última versión estable y no se ofrece como descarga recomendada.

### Opción A — automática (recomendada)

Al subir una etiqueta `v*`, GitHub Actions compila **Windows + macOS + Linux** y
crea el Release con los tres `.zip` adjuntos:

```powershell
git add -A
git commit -m "release v0.1.0-beta.1"
git push
python scripts\release.py --tag        # crea y sube la etiqueta v0.1.0-beta.1
```

Resultado en unos minutos:
[github.com/rgomezs2000/extractorfanarts/releases](https://github.com/rgomezs2000/extractorfanarts/releases)

### Opción B — local (sube el `.zip` ya compilado)

```powershell
python scripts\release.py              # crea dist\ExtractorFanarts-v0.1.0-beta.1-windows.zip
gh release create v0.1.0-beta.1 "dist\ExtractorFanarts-v0.1.0-beta.1-windows.zip" `
   --title "ExtractorFanarts v0.1.0-beta.1" --prerelease --generate-notes
```

*(si no tienes GitHub CLI: `winget install --id GitHub.cli` y luego `gh auth login`)*

### Opción C — a mano desde la web

*Releases → Draft a new release* → etiqueta `v0.1.0-beta.1` (crear al publicar) →
marca **«Set as a pre-release»** → adjuntar el `.zip`.

**Notas:**

- `dist/`, `build/`, `vendor/`, `.wheels/` y `certs/` están en `.gitignore`:
  **los binarios no se suben al repositorio**, solo se adjuntan al Release.
- `scripts/release.py` **sustituye temporalmente** `config_local.py` del paquete
  por la plantilla vacía, comprime, verifica que **no haya claves** en el `.zip`,
  genera el **SHA-256** y restaura tu archivo.
- El paquete incluye `THIRD-PARTY-NOTICES.txt` con las licencias de los
  componentes redistribuidos (Qt/PySide6 LGPL v3, Pillow, httpx, curl_cffi, motores IA…).
- Tamaño del paquete de Windows: ~132 MB comprimido (Qt + motores IA).

---

## 15. Solución de problemas

### 15.1 CAPTCHA de Cloudflare (p. ej. Rule34.xxx)

Algunos boorus activan defensas que responden un **CAPTCHA** en lugar de datos
(la app lo detecta y lo informa de inmediato, sin quedarse esperando). La
solución es **respetuosa** con el sitio: tú resuelves el reto como humano.

1. Abre el sitio en tu navegador (p. ej. <https://rule34.xxx>) y **resuelve el CAPTCHA**.
2. Pulsa **F12** → pestaña **Network/Red** → recarga la página.
3. Haz clic en la primera petición del documento → **Headers → Request Headers**:
   copia la cookie **`cf_clearance`** (~450 caracteres) y el **`User-Agent`** completo.
4. Pégalos en `app/config_local.py` y reinicia la app:

```python
CF_CLEARANCE = "valor_de_cf_clearance"
CF_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
```

> `cf_clearance` solo es válido para el **mismo User-Agent** que resolvió el reto
> y **caduca** como en el navegador. La app nunca resuelve ni evade CAPTCHAs.

**Paso 5 (automático): huella TLS de navegador.** Cloudflare también analiza la
«firma» de la conexión: `httpx` no se parece a Chrome y el CAPTCHA seguía
apareciendo aun con la cookie. Cuando hay `CF_CLEARANCE`, la app usa
automáticamente un transporte con **huella de Chrome** (`curl_cffi`) para los
dominios de `CF_DOMAINS`; el resto siguen usando httpx. Verificado: Rule34.xxx
pasó de `HTTP 403 text/html (CAPTCHA)` a `HTTP 200 application/json`.

- Se instala con `python scripts\setup_vendor.py --only=curl_cffi,cffi,pycparser`.
- Se puede elegir otro navegador con `BROWSER_IMPERSONATE`.

> ⚠️ **En Rule34.xxx debes marcar «Permitir contenido adulto»**: casi todo su
> contenido tiene rating `questionable`/`explicit`, que la app filtra por defecto.
> Sin esa casilla verás «0 resultados» aunque la conexión funcione.

### 15.2 `403 "Just a moment…"` en wikis de Fandom

El **CDN de imágenes de Fandom** (`static.wikia.nocookie.net`) y
`Special:FilePath` responden `403 "Just a moment..."` a los clientes que no
parecen un navegador. La app lo resuelve automáticamente porque `fandom.com`,
`nocookie.net` y `wikia.com` están en **`BROWSER_DOMAINS`**: esas peticiones usan
el transporte con huella de Chrome **más un User-Agent de navegador** (no hace
falta `cf_clearance`). Verificado: `403` → `HTTP 200 image/webp`.

Si otro sitio nuevo diera ese error, añade su dominio a `BROWSER_DOMAINS` (el
mensaje de error te lo recordará).

### 15.3 «Acceso denegado» al guardar en Imágenes o Descargas

Hay **dos causas** y las dos se arreglan sin tocar tus permisos:

**1) La app se lanzó desde una consola restringida** (p. ej. la terminal de un
agente/IDE con sandbox), que solo permite escribir dentro del proyecto.
*Síntoma:* mientras la app está abierta, su log (`~/.extractorfanarts/logs`) no
se actualiza. *Solución:* ábrela **con doble clic desde el Explorador**
(`ejecutar.bat` o el `.exe`) o desde una consola normal.

**2) El paquete compilado tiene la etiqueta de integridad «baja»** (le pasa a
cualquier compilación hecha dentro de un entorno restringido: los archivos
heredan esa etiqueta y Windows abre el proceso en modo restringido **aunque lo
lances desde el Explorador**, porque la etiqueta viaja con el archivo).
*Síntoma:* `ExtractorFanarts.exe --selftest` dice `escritura: FALLO … Permission
denied` aunque `~/.extractorfanarts` e `Imágenes` tengan control total para tu
usuario. *Solución:*

```powershell
python scripts\arreglar_integridad.py                 # repara dist\ExtractorFanarts
python scripts\arreglar_integridad.py "otra\carpeta"  # o el paquete que quieras
```

(equivale a `icacls "dist\ExtractorFanarts" /setintegritylevel Medium /T`).
`compilar.bat` y `ejecutar.bat` **ya lo aplican solos**.

### 15.4 Otras comprobaciones

| Síntoma | Causa y solución |
|---|---|
| «0 resultados» con la conexión correcta | El contenido es `questionable`/`explicit`: marca **«Contenido adulto»** en Opciones |
| «Solo licencia liberada» no devuelve casi nada | Desactivado por defecto porque la mayoría del fanart no declara licencia |
| Un booru devuelve pocos resultados con muchos tags | Cada página trae hasta 200 resultados y puede haber pocas coincidencias: quita un tag |
| `deps` fallan al arrancar | Comprueba con `python main.py --selftest`; instala con `scripts\setup_vendor.py` |
| Errores raros tras actualizar | Reinicia la app (los ajustes se leen al arrancar) y revisa el `.log` del día |

---

## 16. Scripts del proyecto

| Script | Para qué |
|---|---|
| `scripts\setup_vendor.py` | instala las dependencias en `./vendor` **sin pip** (`--ai` motores de IA, `--only=pkg1,pkg2`) |
| `scripts\build_exe.py` | empaqueta con PyInstaller (`--onefile`, `--consola`, `--probar`, `--firmar`) |
| `scripts\release.py` | crea el `.zip` + `.sha256` y publica el Release (`--tag`, `--gh`, `--version`) |
| `scripts\make_icon.py` | regenera los iconos de `assets/` |
| `scripts\hacer_certificado.py` / `.ps1` | crea un certificado autofirmado (`--simular`, `--confiar`) |
| `scripts\pixiv_token.py` | obtiene el refresh token de Pixiv (OAuth PKCE) |
| `scripts\pixiv_url.py` | utilidad de URL/identificadores de Pixiv |
| `scripts\arreglar_integridad.py` | devuelve la etiqueta de integridad del paquete a «Media» |
| `scripts\limpiar_sidecars.py` | detecta o borra los `.json` antiguos de una carpeta (`--borrar`) |
| `scripts\diag_conexion.py` | diagnóstico de credenciales y conexión de un sitio |
| `scripts\diag_net.py` | diagnóstico de red y resolución de dominios |
| `scripts\smoke_services.py` | prueba de humo de los servicios (sin GUI) |
| `scripts\e2e_test.py` | prueba de extremo a extremo con base de datos aparte |
| `scripts\probe_boorus.py` | sonda de conectividad de los boorus configurados |
| `scripts\verify_new_boorus.py` | verifica que un booru nuevo devuelve resultados válidos |

Scripts auxiliares de Windows: `compilar.bat`, `ejecutar.bat`,
`crear_certificado.bat`, `firmar.bat`.

---

## 17. Licencia y avisos legales

- **Licencia del proyecto:** [Unlicense](LICENSE) — software liberado al
  **dominio público**. Puedes copiarlo, modificarlo, publicarlo, usarlo,
  compilarlo, venderlo o distribuirlo con cualquier propósito.
- **Componentes de terceros:** las licencias de Qt/PySide6 (LGPL v3), Pillow,
  httpx, curl_cffi y los motores de IA están en
  [THIRD-PARTY-NOTICES.txt](THIRD-PARTY-NOTICES.txt).
- **Uso responsable:** ExtractorFanarts es una herramienta de archivo personal.
  **Respeta el trabajo de los artistas** y las condiciones de uso de cada
  plataforma. No redistribuyas el material descargado ni lo uses con fines
  comerciales sin la licencia correspondiente. El análisis completo está en
  [docs/INFORME-FACTIBILIDAD.md](docs/INFORME-FACTIBILIDAD.md).
- **Sin garantía:** el software se ofrece «tal cual», sin garantía de ningún
  tipo. El usuario es responsable del uso que haga de él.
