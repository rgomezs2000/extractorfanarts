# ExtractorFanarts — Guía del usuario

**Versión 0.1.0-beta.1 (fase beta)** · Windows · macOS · Linux

ExtractorFanarts es un programa de escritorio para **buscar, revisar y guardar
arte y fanart** de redes sociales, booros y wikis de fandom, todo desde una sola
ventana: eliges la plataforma, escribes lo que buscas, revisas los resultados en
una galería y descargas lo que te interese. Todo lo que guarda lo convierte a
**WebP** y, si quieres, le **mejora la calidad** antes de guardarlo.

> **Programa propietario.** © 2026 Roger Gomez · Todos los derechos reservados.
> Puedes usarlo gratis para tu archivo personal. No puedes copiarlo,
> redistribuirlo, venderlo ni modificarlo. Ver **Licencia** al final.

Este README es la guía completa. Si es tu primera vez, empieza por el archivo
**`LEEME-PRIMERO.txt`**, que trae los pasos mínimos.

---

## Índice

1. [Instalar y abrir](#1-instalar-y-abrir)
2. [Qué hay en esta carpeta](#2-qué-hay-en-esta-carpeta)
3. [Tus claves (opcional)](#3-tus-claves-opcional)
4. [Buscar y descargar, paso a paso](#4-buscar-y-descargar-paso-a-paso)
5. [Plataformas disponibles](#5-plataformas-disponibles)
6. [La galería y el visor](#6-la-galería-y-el-visor)
7. [Menú contextual (clic derecho)](#7-menú-contextual-clic-derecho)
8. [Atajos de teclado](#8-atajos-de-teclado)
9. [Dónde se guarda todo](#9-dónde-se-guarda-todo)
10. [Calidad y mejora de imagen](#10-calidad-y-mejora-de-imagen)
11. [Qué se filtra](#11-qué-se-filtra)
12. [Si algo va mal](#12-si-algo-va-mal)
13. [Preparar datasets para IA (LoRA, LyCORIS, checkpoints)](#13-preparar-datasets-para-ia-lora-lycoris-checkpoints)
14. [Licencia y uso responsable](#14-licencia-y-uso-responsable)

---

## 1. Instalar y abrir

El programa **no se instala**: se descomprime y se ejecuta.

1. **Descomprime el `.zip` completo** en una carpeta tuya (por ejemplo
   `C:\ExtractorFanarts`). No lo ejecutes desde dentro del archivo comprimido:
   necesita la carpeta `_internal` que va a su lado.
2. **Windows:** haz doble clic en **`ExtractorFanarts.exe`**.
   - La primera vez Windows puede mostrar un aviso azul, *«Windows protegió su
     PC»*. Es normal: el programa no está firmado digitalmente (un certificado
     de firma es de pago), no es un virus.
   - Pulsa **Más información → Ejecutar de todas formas**.
   - Si sigue bloqueado: clic derecho en el `.exe` → **Propiedades** → marca
     **Desbloquear** → **Aceptar**.
3. **macOS:** si dice *«no se puede abrir»*, haz clic derecho en la aplicación →
   **Abrir**. Si aun así se resiste, ejecuta en Terminal:
   `xattr -dr com.apple.quarantine ExtractorFanarts.app`
   Lo mismo vale para el asistente: si macOS bloquea `pixiv-token`, haz clic
   derecho sobre él → **Abrir**.
4. **Linux:** da permisos de ejecución la primera vez:
   `chmod +x ExtractorFanarts` y luego ejecútalo.

**Verifica que la descarga es íntegra** con el archivo `.sha256` que acompaña al
paquete:

```powershell
# Windows (PowerShell)
Get-FileHash .\ExtractorFanarts-*.zip -Algorithm SHA256
```
```bash
# Linux / macOS
shasum -a 256 ExtractorFanarts-*.zip
```

El resultado debe coincidir con el contenido del `.sha256`.

Al abrirlo por primera vez se crea la carpeta `%USERPROFILE%\.extractorfanarts`
(en Linux/macOS: `~/.extractorfanarts`), donde viven tus registros y tu
historial.

---

## 2. Qué hay en esta carpeta

| Archivo | Para qué sirve |
|---|---|
| `ExtractorFanarts.exe` | **El programa.** Es lo único que tienes que abrir |
| `config_local.py` | Tus claves y ajustes (viene vacío, como plantilla) |
| `LEEME-PRIMERO.txt` | Los primeros pasos, en texto plano |
| `LICENSE` | Las condiciones de uso del programa |
| `THIRD-PARTY-NOTICES.txt` | Licencias de las bibliotecas incluidas |
| `_internal/` | Biblioteca del programa. **No la borres ni la muevas**: el `.exe` la necesita |

Puedes mover la carpeta entera a donde quieras (por ejemplo al Escritorio), pero
mantén todos esos archivos **juntos en la misma carpeta**.

---

## 3. Tus claves (opcional)

El programa funciona sin configurar nada en varias plataformas. Para las que
piden credenciales, crea (o edita) el archivo **`config_local.py`** que está
**junto al ejecutable** y escribe dentro tus claves, una por línea:

```python
RULE34_API_KEY = "tu_clave"
RULE34_USER_ID = "tu_id"
GELBOORU_API_KEY = "tu_clave"
GELBOORU_USER_ID = "tu_id"
DEVIANTART_CLIENT_ID = "tu_id"
DEVIANTART_CLIENT_SECRET = "tu_secreto"
TUMBLR_API_KEY = "tu_clave"
CF_CLEARANCE = "valor_de_la_cookie"
CF_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
```

**Dónde se busca ese archivo** (por este orden):

1. junto al ejecutable (lo más cómodo),
2. dentro de la carpeta del programa,
3. en `%USERPROFILE%\.extractorfanarts\config_local.py` (Windows) o
   `~/.extractorfanarts/config_local.py` (Linux/macOS) — la mejor opción si
   quieres que sobreviva a las actualizaciones.

**Reinicia el programa** después de cambiar el archivo.

| Plataforma | Clave que necesita | Dónde se consigue |
|---|---|---|
| Safebooru, Danbooru, wikis, Fediverso, Bluesky | **ninguna** | — |
| Rule34.xxx | `RULE34_API_KEY` + `RULE34_USER_ID` | Opciones de tu cuenta → *API Access Credentials* |
| Gelbooru | `GELBOORU_API_KEY` + `GELBOORU_USER_ID` | Opciones de tu cuenta → *API Access Credentials* |
| DeviantArt | `DEVIANTART_CLIENT_ID` + `DEVIANTART_CLIENT_SECRET` | deviantart.com/developers |
| Tumblr | `TUMBLR_API_KEY` | tumblr.com/oauth/apps |
| Pixiv | `PIXIV_REFRESH_TOKEN` | Ver *Pixiv*, abajo |
| X (Twitter) | `X_BEARER_TOKEN` | App de desarrollador **de pago** |
| Pinterest | `PINTEREST_ACCESS_TOKEN` | App aprobada + permiso del usuario |

**Pixiv.** No permite el acceso anónimo: hay que usar tu propia cuenta con un
*refresh token* (el programa **no guarda tu contraseña**). En la **misma carpeta**
que el programa tienes un asistente: haz **doble clic en `pixiv-token.exe`** (o
`pixiv-token` en Linux/macOS) y sigue lo que te diga. Te dará un enlace para
iniciar sesión en Pixiv, le pegarás la dirección final y **el token se guarda
solo**. Después, **reinicia ExtractorFanarts**.

> 🔐 Guarda tus claves en `config_local.py`. Ese archivo queda en tu equipo: el
> programa no envía nada a ningún servidor propio y no incluye ninguna clave.

---

## 4. Buscar y descargar, paso a paso

1. **Tipo:** elige *Red social*, *Booru* o *Wiki*.
2. **Plataforma:** el sitio concreto (la lista cambia según el tipo).
3. **Escribe lo que buscas**, según el tipo:
   - *Red social:* `@usuario`, palabras clave y/o `#hashtags`. Puedes
     combinarlos y poner **varios valores** en un mismo campo (separados por
     espacios o comas): se busca todo a la vez.
   - *Booru:* las etiquetas que quieras, separadas por espacios o comas
     (`lola_loud 1girl solo`). También valen los operadores del sitio
     (`-etiqueta` para excluir, `rating:general`, `score:>10`).
   - *Wiki:* el fandom, el personaje y/o la URL de la wiki.
4. Pulsa **🔍 Buscar**. Aparecerán los resultados en una **galería** para que los
   revises antes de descargar nada.
5. Ajusta lo que quieras (cantidad, calidad, mejora, carpeta de destino) y pulsa
   **⬇️ Descargar**. Te pedirá confirmación y te dirá al terminar cuántos
   archivos guardó y dónde.
6. **⏹️ Cancelar** detiene la operación en cualquier momento (no se queda a
   medias). **🧹 Limpiar** vacía el formulario.

Puedes lanzar una búsqueda y, sin descargar nada, usar el **clic derecho** sobre
una imagen para guardar solo esa (ver más abajo).

---

## 5. Plataformas disponibles

| Tipo | Plataformas |
|---|---|
| **Redes sociales** | Fediverso (**cualquier** servidor de Mastodon, Misskey o CherryPick), Bluesky, DeviantArt, Tumblr, Pixiv, X (Twitter), Pinterest, Newgrounds |
| **Boorus** | Safebooru, Gelbooru, Rule34.xxx, The Big ImageBoard, Xbooru, Hypnohub, Danbooru, Safebooru (Donmai), Yande.re, Konachan, Konachan (SFW), Derpibooru, ATF Booru y Rule34 Paheal |
| **Wikis** | Fandom.com y cualquier wiki MediaWiki (búsqueda por franquicia, personaje y concepto) |

**En el fediverso** no hace falta elegir servidor: escribe `@usuario@servidor`
(por ejemplo `@alguien@baraag.net`) y se consulta su servidor; o escribe
`@usuario` y rellena el campo *Instancia*.

---

## 6. La galería y el visor

- Los resultados aparecen en un **carrusel**: contador, imagen grande y una tira
  de miniaturas del mismo ancho. Hay **una casilla por cada resultado**.
- **Clic en la imagen grande** → se abre un **visor** dentro de la misma ventana:
  - **rueda del ratón**: acercar y alejar (del 10 % al 800 %),
  - **arrastrar**: mover la imagen,
  - **doble clic** o tecla `0`: ajustar a la ventana,
  - `←` / `→`: imagen anterior y siguiente,
  - `+` / `-`: zoom, **`Esc`**: cerrar.
- Las imágenes de la galería se preparan a partir del **original**, así que se
  ven nítidas al ampliarlas, y se cargan **de una en una con cortesía** hacia los
  sitios (por eso la tira se va llenando poco a poco).

---

## 7. Menú contextual (clic derecho)

Con **clic derecho** sobre cualquier imagen (la grande, una miniatura o dentro
del visor):

| Opción | Qué hace | Atajo |
|---|---|---|
| 📋 Copiar imagen | Copia la imagen ya procesada para pegarla en otro programa | `Ctrl+C` |
| 💾 Guardar imagen | Guarda **solo esa** imagen en la carpeta de salida | `Ctrl+S` |
| 🗂️ Guardar como… | Igual, pero eligiendo carpeta y nombre | `Ctrl+Shift+S` |
| 🌐 Abrir imagen original en el navegador | Abre la página original | — |
| 🔗 Copiar enlace de la imagen original | Copia esa dirección web | `Ctrl+Shift+C` |

La calidad es **la misma** que en la descarga completa, y funciona **aunque solo
hayas pulsado Buscar**.

---

## 8. Atajos de teclado

| Tecla | Dónde | Qué hace |
|---|---|---|
| `Enter` | en cualquier campo o control de búsqueda | **Buscar** |
| `Shift+Enter` | igual | **Descargar** |
| `Enter` | en el campo **Salida** | elegir carpeta |
| `Enter` | sobre un botón enfocado | pulsarlo |
| `Enter` o `Esc` | mientras busca o descarga | **cancelar** |
| `Esc` | con el visor abierto | cerrarlo |
| `Alt+F4` o `Ctrl+Q` | en cualquier parte | cerrar el programa |

Si hay una descarga en curso y cierras, te preguntará antes y no dejará archivos
a medias.

---

## 9. Dónde se guarda todo

| Qué | Dónde |
|---|---|
| **Imágenes** | Carpeta de **Imágenes** del sistema, subcarpeta `ExtractorFanarts`, con una subcarpeta por plataforma |
| **Registros** | `%USERPROFILE%\.extractorfanarts\logs\app-AAAA-MM-DD.log` (un archivo por día) |
| **Historial** | `%USERPROFILE%\.extractorfanarts\historial.db` |

- Puedes cambiar la carpeta de salida con el botón de la carpeta 📂.
- Si esa carpeta no se puede escribir (permisos, protección contra ransomware…),
  el programa **te avisa al arrancar** y, al descargar, prueba alternativas
  (Descargas, `~/.extractorfanarts/descargas`, una carpeta junto al programa) y
  te dice cuál ha usado.
- Las descargas **nunca** van a Documentos.
- Junto a cada imagen se puede guardar un archivo `.json` con sus datos, si
  marcas **«Guardar metadatos .json»** en Opciones (desactivado por defecto).

---

## 10. Calidad y mejora de imagen

- **Todo se guarda en `.webp`**, con la calidad que elijas en el deslizador
  (1–100). El archivo original no se conserva.
- **✨ Mejorar calidad** aumenta la resolución según el tamaño de partida:
  **hasta 699 px → ×4** · **700–799 px → ×3** · **800 px o más → ×2**, con un tope
  de 8K, y aplica un afilado suave. Por encima de 7679 px solo se convierte a WebP.
- **Siempre verás lo que se ha hecho:** al guardar o copiar, la barra de estado
  indica el tamaño de partida y el resultado real
  (`153x153 → 612x612 · Lanczos 4x`). Si el origen era muy pequeño (menos de
  300 px) te avisa, porque **agrandar una imagen diminuta no crea detalle real**:
  para preparar un dataset conviene saberlo antes de entrenar.
- **🤖 Modo IA** usa los motores Real-ESRGAN / waifu2x si están incluidos en el
  paquete (dan más detalle, sobre todo en dibujos). Si no están disponibles, el
  programa lo dice y usa el reescalado clásico: **nunca** guarda una imagen
  corrupta ni a medias.
- **🔢 Limitar cantidad**: descarga solo el número que indiques (1–1000). Sin
  marcar, descarga todo lo encontrado.

---

## 11. Qué se filtra

El programa aplica **siempre** unos filtros antes de mostrarte o guardarte nada,
y te dice el motivo exacto de cada descarte:

- **Lista negra de contenido prohibido** (etiquetas y prefijos).
- **Plataformas de pago** (Patreon, Pixiv Fanbox, OnlyFans, Fansly, Unifans…):
  se descartan los enlaces a contenido exclusivo.
- **Contenido adulto (🔞):** por defecto **no** aparece. Si marcas
  «Permitir contenido adulto» en Opciones, sí.
- **Solo licencia liberada (⚖️):** opcional; solo procesa lo que declare
  CC0/CC-BY/dominio público.
- **Tu propia lista de exclusiones** (etiquetas, dominios o palabras) que puedes
  añadir en `config_local.py`.

Puedes ver y ajustar todo esto: en **Opciones**, botón
**«ℹ️ ¿Qué se filtra? (lista negra)»**.

> ⚠️ En **Rule34.xxx** y **Rule34 Paheal** casi todo el contenido es adulto: si
> no marcas «Permitir contenido adulto» verás **0 resultados** aunque la conexión
> funcione bien.

---

## 12. Si algo va mal

| Síntoma | Qué pasa y qué hacer |
|---|---|
| Aviso azul de Windows al abrir | Normal (no está firmado): *Más información → Ejecutar de todas formas* |
| «0 resultados» pero la conexión va bien | El contenido es adulto: marca **Permitir contenido adulto** en Opciones |
| **Acceso denegado** al guardar en Imágenes o Descargas | Abre el programa **con doble clic desde el Explorador** (no desde una terminal restringida). Si sigue igual, ejecuta `ExtractorFanarts.exe --selftest` y revisa `selftest.txt` |
| Cloudflare pide un CAPTCHA (p. ej. Rule34.xxx) | Abre el sitio en tu navegador, resuélvelo, y copia en `config_local.py` la cookie `cf_clearance` y tu `User-Agent` (F12 → Red → la primera petición → Cabeceras). El programa **nunca** evade CAPTCHAs |
| Una wiki o un sitio devuelve error 403 | Suele ser una defensa contra programas. Anótalo y avisa al autor |
| **El 🤖 Modo IA no mejora nada** (sigue usando Lanczos) | Los motores de IA pueden traer una etiqueta de Windows que les impide escribir su resultado (en el registro verás `encode image … failed`). Si sabes abrir una consola, ejecuta en la carpeta del programa: `icacls _internal\vendor /setintegritylevel Medium /T`. Si no, avisa al autor y usa **✨ Mejorar calidad** sin modo IA |
| Búsqueda muy lenta | Se espacian las peticiones a propósito (cortesía con los sitios). Con muchos hashtags o palabras clave tarda más |
| Cualquier error raro | Mira el `.log` del día: ahí está exactamente qué respondió cada servidor |

**Diagnóstico:** ejecuta `ExtractorFanarts.exe --selftest` (en Windows también
desde una consola) y se generará un archivo **`selftest.txt`** con el estado de
todo: bibliotecas, carpetas, permisos y si la ventana cabe en tu pantalla.

**Al abrir el `.exe` se abre además una ventana de consola** con los mismos
mensajes que el registro del día. Es normal y útil para ver qué está pasando.

---

## 13. Preparar datasets para IA (LoRA, LyCORIS, checkpoints)

Este programa también sirve para **preparar las imágenes con las que se entrena un
modelo de IA**: un **LoRA** de tu personaje, un **LyCORIS** (LoCon, LoHa) de estilo,
un **embedding** o un **checkpoint / DreamBooth**. Todo lo que hace falta antes de
entrenar —reunir el concepto correcto, quitar repetidas, dejar un formato y un
tamaño homogéneos y guardar las etiquetas de cada imagen— lo resuelve en una sola
pasada.

### Por qué sirve para esto

| Lo que necesita un dataset | Cómo te lo da el programa |
|---|---|
| Imágenes **del concepto correcto** | Búsqueda por **etiqueta exacta** en 14 boorus (el mejor etiquetado que existe para arte), por `@usuario` en redes y por personaje o franquicia en wikis |
| **Sin repetidas** | Deduplicación por hash: el mismo archivo no entra dos veces en una misma búsqueda |
| **Un solo formato** | Todo se guarda en `.webp`, con la calidad que elijas |
| **Tamaños coherentes** | Reescala automáticamente las imágenes pequeñas (hasta 4x) para que el dataset no mezcle 300 px con 3000 px |
| **Más definición** | ✨ *Mejorar calidad*, y con 🤖 *Modo IA* (Real-ESRGAN / waifu2x) recupera detalle de originales pequeños o bocetos |
| **Etiquetas para las captions** | Marcando **🏷️ Guardar metadatos .json** obtienes un `.json` por imagen con sus **tags**, artista, licencia, origen, rating y fecha |
| **Dataset limpio** | Filtros de contenido prohibido, plataformas de pago, contenido adulto y licencias |
| **Revisar antes de descargar** | La galería te deja ver y descartar **antes** de bajarte 300 archivos |
| **Saber de dónde salió cada imagen** | Los nombres son `Plataforma_id_hash.webp` y el `.json` guarda el enlace original |

### Cómo preparar un dataset, paso a paso

1. **Tipo: Booru** → **Plataforma: Danbooru o Gelbooru** (tienen el etiquetado más
   completo).
2. En **Tags**, escribe el personaje o el concepto y afina con etiquetas de calidad
   y encuadre: `solo`, `1girl`, `highres`. Excluye lo que no quieras con un guion
   delante: `-comic`, `-text`, `-sketch`.
3. Marca **✨ Mejorar calidad** (y **🤖 Modo IA** si el arte original es pequeño)
   para que todas las imágenes queden con una definición parecida.
4. Marca **🏷️ Guardar metadatos .json**: tendrás las etiquetas de cada imagen listas
   para convertirlas en captions.
5. **⬇️ Descargar** con un límite razonable: para un personaje suelen bastar
   **100–200 imágenes**; para un estilo, **30–50**.
6. **Revisa en la galería** y quédate con las buenas: variedad de poses, fondos y
   expresiones. Fuera las de cuerpo cortado, con marcas de agua o borrosas.
7. Usa las **etiquetas** del `.json` para escribir los archivos de caption (`.txt`)
   y entrena con tu herramienta habitual (kohya-ss, OneTrainer, ai-toolkit…).

### Consejos para que el dataset salga bien

- **Variedad antes que cantidad:** 40 imágenes distintas entrenan mejor que 200
  casi iguales.
- **Elige un tamaño objetivo:** decide si entrenas a 512, 768 o 1024 y quédate en
  esa franja. El programa reescala **hacia arriba**.
- **El programa no recorta:** si necesitas encuadres concretos, recórtalos con tu
  editor antes de entrenar.
- **¿Tu entrenador no acepta WebP?** Convierte la carpeta por lotes a PNG o JPG.
- **Entre sesiones puede repetir alguna imagen:** evita repetidos dentro de una
  misma búsqueda, pero si vuelves a buscar lo mismo otro día puede bajar algo que
  ya tenías.
- **Respeta a los artistas:** usa los campos `licencia` y `artista` del `.json` y
  ten en cuenta las listas de «no entrenar» de algunos autores. Si quieres quedarte
  solo con obras de licencia abierta, activa **⚖️ Solo licencia liberada**.

---

## 14. Licencia y uso responsable

### Licencia del programa

**ExtractorFanarts es un programa propietario.** © 2026 Roger Gomez.
**Todos los derechos reservados.**

- **Sí puedes:** ejecutarlo y usarlo **gratis**, para tu archivo personal, en tus
  equipos, y hacerte una copia de seguridad.
- **No puedes:** copiarlo, publicarlo, compartirlo, subirlo a ningún sitio,
  venderlo, alquilarlo, modificarlo, descompilarlo ni reutilizar su código
  fuente. Tampoco puedes quitar los avisos de autor de este paquete.
- **El código fuente es propiedad del autor** y no se licencia.

El texto legal completo está en el archivo **`LICENSE`** que acompaña al
ejecutable. Para cualquier permiso distinto (uso comercial, redistribución,
integración en otro producto…), escribe al autor:
**rogergomezs2003@gmail.com**.

### Componentes de terceros

El programa incluye bibliotecas de terceros (Qt/PySide6, Pillow, httpx,
curl_cffi y los motores de IA) que conservan **sus propias licencias**,
detalladas en **`THIRD-PARTY-NOTICES.txt`**.

### Uso responsable

- Es una herramienta para **archivo personal** de contenido al que tengas acceso
  legítimo.
- **Respeta a los artistas** y las condiciones de uso de cada plataforma.
- No redistribuyas el material que descargues: la mayoría del fanart **no** tiene
  licencia liberada.
- El programa **no evade** CAPTCHAs, inicios de sesión ni bloqueos, y espacia sus
  peticiones a propósito.
- **No se recogen datos**: no hay telemetría, no hay servidor propio y tus claves
  no salen de tu ordenador.

---

*ExtractorFanarts 0.1.0-beta.1 · fase beta: si encuentras un fallo, el registro
del día (`.extractorfanarts\logs`) y el `selftest.txt` son lo más útil para
reportarlo.*
