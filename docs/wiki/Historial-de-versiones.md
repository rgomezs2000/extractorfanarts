# Historial de versiones

## v0.1.5-beta.84 — 11 de octubre de 2026 · la beta definitiva (84.ª entrega)

**Fin de las imágenes «papilla»: suelo de reescalado en 400 px**
- Las tres imágenes borrosas venían de originales **diminutos** (stickers de 256 px, iconos):
  la tabla llevaba cualquier imagen de menos de 400 px a **8x o 32x** para alcanzar 1600 px,
  y eso no añade detalle: convierte el dibujo en una mancha.
- Ahora, por debajo de **400 px de ancho no se amplía** (se entrega en WebP a su tamaño, con
  el aviso de «origen diminuto» en el resumen). De 400 px en adelante se mantiene el mínimo
  de 1600 px como estaba:

```
 120 px -> 1x ->  120 px     (antes 16x -> 1920)
 256 px -> 1x ->  256 px     (antes  8x -> 2048)
 399 px -> 1x ->  399 px     (antes  8x -> 3192)
 400 px -> 4x -> 1600 px
 700 px -> 3x -> 2100 px
 900 px -> 2x -> 1800 px
```

- Se puede volver a la tabla estricta con `UPSCALE_MIN_SOURCE = 0` en `config_local.py`.
- Nota de contexto: Bluesky **limita sus imágenes a 1000 px** y publica stickers/iconos de
  256 px; no existen originales mayores en su CDN, así que ésos nunca darán 1600 px reales.

---

## v0.1.5-beta.83 — 11 de octubre de 2026 · la beta definitiva (83.ª entrega)

**Bluesky: dos fallos corregidos (el 403 del CDN y las imágenes)**
- **HTTP 403 (BunnyCDN)** al buscar: el dominio `public.api.bsky.app` está detrás de un CDN
  que rechaza las peticiones de programas. Comprobado: `public.api.bsky.app` → **403** con
  cualquier User-Agent, y `api.bsky.app` → **200** con el mismo contenido. Ahora se usa
  `api.bsky.app` y, si falla, se reintenta con el otro.
- **Cero resultados aunque la API devolvía posts con imágenes**: el adaptador buscaba las
  imágenes en `record.embed`, pero la API de búsqueda las entrega en `post.embed` con tipos
  `…images#view`. Ahora se miran los dos sitios y las dos variantes (incluidas las citas con
  imagen).
- Comprobado con la API real:

```
palabra «odalia blight» -> 12 obras
palabra «odalia»        ->  5 obras
palabra «kuromi»        ->  5 obras
hashtag «#kuromi»       ->  7 obras
hashtag «#odalia_blight»->  9 obras
```

---

## v0.1.5-beta.82 — 11 de octubre de 2026 · la beta definitiva (82.ª entrega)

**Con todas las pestañas plegadas, ambas quedan arriba (sin franja blanca en medio)**
- Antes, al plegar las dos secciones, «Resultados» se quedaba pegada al fondo con un hueco
  blanco feo en el centro.
- Ahora el diseño tiene **dos huecos flexibles** y elige cuál crece según el estado:
  - **todo plegado** → los dos huecos se anulan salvo el de abajo: las **dos cabeceras
    quedan arriba**;
  - **formulario abierto** → crece el hueco de en medio y «Resultados» queda **al final**
    (como se pidió antes);
  - **resultados abiertos** → la galería ocupa todo el alto.
- Medido con la ventana real (y = posición vertical de cada cabecera):

```
todo plegado        fuente y=50 h=23 · resultados y=77  h=23
formulario abierto  fuente y=50 h=367 · resultados y=681 h=23
resultados abiertos fuente y=50 h=23 · resultados y=77  h=627
```

---

## v0.1.5-beta.81 — 11 de octubre de 2026 · la beta definitiva (81.ª entrega)

**Efecto de agrandado al abrir la imagen ampliada**
- Al hacer clic en la muestra de la galería, la imagen **crece** desde el hueco que ocupa en
  la galería hasta su tamaño final en el visor ampliado (220 ms con suavizado), en lugar de
  aparecer de golpe.
- El agrandado arranca del rectángulo real del visor de la galería, así que el movimiento
  «sale» de donde el usuario hizo clic, aunque la ventana esté redimensionada.
- Comprobado con la ventana real: progreso **0,45 → 0,83 → 0,98 → 1,0** en ~220 ms, y al
  terminar se libera el rectángulo de origen (sin dejar estado).
- La navegación dentro del visor mantiene la transición de **desplazamiento** de la entrega
  anterior: son dos efectos distintos y conviven.

---

## v0.1.5-beta.80 — 11 de octubre de 2026 · la beta definitiva (80.ª entrega)

**Transición de desplazamiento al pasar imágenes (efecto de página)**
- Antes la muestra aparecía con un fundido. Ahora **se desplaza**: la imagen que estabas
  viendo **sale por un lado** y la nueva **entra por el otro**, como pasar la página de un
  libro.
- Sentido correcto en cada caso: si avanzas (flecha ▶, tecla →, rueda del carrusel) las
  imágenes se mueven **hacia la izquierda**; si retrocedes (◀, ←) se mueven **hacia la
  derecha**. También al saltar del último al primero y viceversa.
- Se aplica en **los dos modos**:
  - **galería** (vista previa con el carrusel), con un marco que recorta el deslizamiento;
  - **visor ampliado**, donde la imagen anterior y la nueva se dibujan desplazándose.
- Duración 190 ms con suavizado, lo justo para que se note sin retrasar la navegación.

---

## v0.1.5-beta.79 — 11 de octubre de 2026 · la beta definitiva (79.ª edición)

**Arreglado: hacer clic en la muestra vuelve a abrirla ampliada**
- Al añadir el arrastre a otros programas se sustituyó el `mouseReleaseEvent` del visor, y
  ese era justo el que emitía la señal para **abrir la imagen ampliada**. El clic dejó de
  hacer nada (regresión introducida en la beta.76).
- Ahora el visor distingue **clic** (abre ampliada) de **arrastre** (lleva la imagen a otro
  programa): solo el arrastre cancela la apertura. Comprobado con un clic simulado: la señal
  se emite y la ventana pide el visor ampliado.
- El clic derecho (menú contextual) y el atajo F3 siguen igual.

---

## v0.1.5-beta.78 — 11 de octubre de 2026 · la beta definitiva (78.ª entrega)

**Búsqueda por hashtag en DeviantArt («#mymelody», «#my_melody»)**
- El registro mostraba `HTTP 200` con **102 KB** de respuesta y aun así «sin resultados»: la
  API devolvía las obras, pero el **filtro local** las descartaba porque comparaba la etiqueta
  carácter a carácter («my_melody» ≠ «my melody» ≠ «mymelody»).
- Ahora los hashtags se comparan **sin separadores ni almohadilla**, y la lista de formas que
  se prueban contra la API incluye también las variantes sin guion bajo (`my_melody` →
  `mymelody`, `MyMelody`, `my-melody`). Comprobado con la cuenta real:

```
«#mymelody»   -> 19 obras
«#my_melody»  -> 19 obras
«Rita Loud»   -> 20 obras
«kuromi»      -> 15 obras
```

- Recordatorio del criterio (igual en todas las redes): **hashtag** filtra por etiqueta,
  **palabra clave** busca en el texto, **usuario** por autor e **instancia** solo aplica al
  fediverso.

---

## v0.1.5-beta.77 — 11 de octubre de 2026 · la beta definitiva (77.ª entrega)

**DeviantArt: buscar «Rita Loud» devolvía cero (la API rechaza tags con espacios)**
- El registro mostraba `HTTP 400 · {"error":"invalid_request","error_description":"Tag not found."}`. La API de DeviantArt **solo acepta tags reales**: «Rita Loud» con
espacio no existe como tag, aunque en la web su buscador encuentre 17,9 K resultados.
- Ahora la frase se prueba en las formas que sí existen: **ritaloud**, **rita_loud** y
  **RitaLoud**; si ninguna responde, se prueban también sus palabras. Comprobado con la
  cuenta real:

```
«Rita Loud»    -> 14 obras
«ritaloud»     ->  4 obras
«rita_loud»    -> 11 obras
«theloudhouse» ->  3 obras
```

- Además, el filtro local compara **sin separadores**, así `ritaloud` casa con la etiqueta
  `rita_loud` (antes se descartaba por no coincidir literalmente). Esto vale para todas las
  redes que usan el mismo filtro.

---

## v0.1.5-beta.76 — 11 de octubre de 2026 · la beta definitiva (76.ª entrega)

**Propiedades con la fuente original, copiar fiable y arrastrar la imagen**
- **Propiedades**: nueva línea **🔗 Fuente original** en el grupo «Imagen» con el enlace del
  artista que publica el booru (Rule34/Gelbooru lo dan en `source`). Si la obra no la tiene,
  queda **en blanco**. Ejemplo comprobado: `https://www.pixiv.net/en/artworks/146461968`.
- **Copiar imagen** ahora funciona de verdad y sin límite:
  - copia **inmediata** de la imagen que ya está en pantalla (sin volver a descargarla), así
    que se puede repetir cuantas veces se quiera;
  - el portapapeles recibe la **imagen como imagen** (DIB/PNG, lo que pega en cualquier
    programa) más el `.webp` y el **enlace** como texto;
  - se **verifica** que el portapapeles quedó con la imagen y, si no, se reintenta con el
    método clásico. Antes, si Qt no decodificaba el `.webp`, quedaba un portapapeles vacío.
- **Arrastrar la imagen a otros programas**:
  - en la **vista previa**, arrastrar con el botón izquierdo;
  - en el **visor ampliado**, **Ctrl + arrastrar** (para no chocar con el desplazamiento del
    zoom). Se indica en la ayuda inferior del visor.

---

## v0.1.5-beta.75 — 11 de octubre de 2026 · la beta definitiva (75.ª entrega)

**Rule34.xxx: usaba las claves de Gelbooru y parecía «sin resultados»**
- Las credenciales se rellenaban **por familia de API**, y Rule34 comparte familia
  (`gelbooru`) con Gelbooru. Resultado: Rule34 enviaba el `api_key`/`user_id` **de
  Gelbooru**, su API contestaba `Missing authentication. Go to api.rule34.xxx…` con **HTTP
  200**, y la app lo interpretaba como búsqueda vacía («La búsqueda no devolvió resultados»).
- Ahora se elige el juego de claves **por dominio del sitio**: `api.rule34.xxx` →
  `RULE34_API_KEY`/`RULE34_USER_ID`; `gelbooru.com` → `GELBOORU_…`.
- Además, si una API de la familia Gelbooru responde **texto** (o un objeto con `error`) en
  vez de una lista, se muestra **ese mensaje** en lugar de decir que no hay resultados.
- Comprobado con las claves reales:

```
Rule34.xxx  «rita_loud»     ->  20 obras · 20 tras filtros
Gelbooru    «rita_loud»     ->  20 obras · 20 tras filtros
Safebooru   «blonde_hair»   ->  20 obras · 20 tras filtros
```

---

## v0.1.5-beta.74 — 11 de octubre de 2026 · la beta definitiva (74.ª entrega)

**La cabecera «Resultados» queda al final, no flotando en el centro**
- El aire sobrante estaba **dentro** de la sección del formulario, así que la cabecera plegada
  de Resultados aparecía a media altura. Ahora hay un **hueco flexible entre las dos
  secciones**: con Resultados plegado, su cabecera se queda **pegada al final**, justo encima
  de la barra de progreso (medido: y=681 de 776 px de ventana).
- Al desplegar Resultados ese hueco desaparece y la galería ocupa todo el alto.
- La cabecera plegada **informa del número de imágenes**: «🖼️ Resultados (50)».

---

## v0.1.5-beta.73 — 11 de octubre de 2026 · la beta definitiva (73.ª entrega)

**Secciones tipo acordeón: una abierta, la otra se pliega**
- Al arrancar se muestra **solo el formulario** («Fuente de búsqueda»); los resultados
  empiezan plegados.
- Cuando una búsqueda trae **imágenes**, la galería («Resultados») **se despliega sola** y el
  formulario se pliega, para que se vea la muestra a buen tamaño.
- Al abrir una sección **se pliega la otra** (acordeón): nunca compiten por el espacio.
- Eliminado el título duplicado «🖼️ Resultados» (lo pone la cabecera de la sección).

Comprobado con la ventana real:

```
inicio              formulario visible   resultados plegado
llegan 5 imágenes   formulario plegado   resultados visible   (23 / 627 px)
abrir formulario    formulario visible   resultados plegado   (627 / 23 px)
abrir resultados    formulario plegado   resultados visible   (23 / 627 px)
```

---

## v0.1.5-beta.72 — 11 de octubre de 2026 · la beta definitiva (72.ª entrega)

**Formularios compactos: etiqueta y campo en la misma fila, sin espacios en blanco**
- **Booru** y **wiki** usan ya el mismo patrón que **redes sociales**: etiqueta a la izquierda
  y campo a la derecha, una fila por dato.
- La pila de formularios reservaba la altura de la pestaña más alta y eso dejaba huecos
  (en booru sobraban ~80 px). Ahora se ajusta a la pestaña visible: booru **24 px**,
  wiki **74 px**, redes **100 px**.
- Eliminado el **título duplicado** «Fuente de búsqueda» (lo pone la cabecera de la sección)
  y el botón **Opciones** repetido (el bloque ya se llama así).
- El formulario queda pegado arriba y el espacio sobrante se va al final, nunca entre campos.

---

## v0.1.5-beta.71 — 11 de octubre de 2026 · la beta definitiva (71.ª entrega)

**Secciones plegables, formulario en una columna y galería sin solapes**
- La ventana se organiza en **dos secciones plegables**:
  - **🔎 Fuente de búsqueda**: tipo/plataforma, campos, **opciones** y los botones
    Buscar / Descargar / Limpiar.
  - **🖼️ Resultados**: galería y registro de resultados.
  El **progreso** y el **estado de conexión** quedan **fijos abajo**, fuera de las secciones.
- Al **plegar una sección, la otra se expande** (comprobado: plegando Fuente, Resultados
  pasa de 226 a 931 px y la galería de 100 a 651 px).
- **Formulario en una sola columna**, con **etiqueta en cada campo** (Usuario, Palabra clave,
  Hashtag, Instancia). Nada de dos columnas.
- **Sin barras de desplazamiento**: ya no hay área desplazable; el contenido se reparte solo.
- **Etiqueta del booru compacta**: el texto largo pasa al tooltip y desaparece el hueco blanco.
- **Galería**: el visor tiene altura mínima y el pintado está **recortado** a su área, así la
  muestra no se dibuja encima del carrusel. Al navegar (flechas ◀ ▶, teclado o clic en la
  tira) la muestra hace un **fundido** de entrada.
- **Registro de resultados compacto** (máx. 110 px) para dejar sitio a la galería.

---

## v0.1.5-beta.70 — 11 de octubre de 2026 · la beta definitiva (70.ª entrega)

**El endurecimiento de seguridad se aplica en Windows, macOS y Linux**
- Medidas comunes a los tres sistemas: tope de imagen de 120 MP, validación de ZIP
  (entradas, tamaños, rutas sin .. ni absolutas), nombres de archivo saneados, procesos sin
  shell=True con timeout, topes de descarga y verificación TLS activa.
- Medidas propias de **macOS y Linux**: el archivo de configuración con claves queda en
  **0600** (solo su dueño) y ~/.imaginteca en **0700**. En Windows no existe esa semántica
  POSIX: el archivo vive en el perfil del usuario con las ACL de Windows.
- La comprobación --seguridad funciona en los tres sistemas y **dice en cuál está
  corriendo**, con los límites activos y sus fallos (si los hubiera).

---

## v0.1.5-beta.69 — 11 de octubre de 2026 · la beta definitiva (69.ª entrega)

**Endurecimiento de seguridad del sistema (integridad, no credenciales)**
- Nuevo módulo pp/seguridad.py con las medidas y su comprobación:
  Imaginteca.exe --seguridad.
- **Bombas de descompresión**: tope de imagen de **120 MP** aplicado a Pillow antes de
  decodificar (una imagen de pocos KB puede declarar gigapíxeles).
- **ZIP hostiles** (ugoira de Pixiv y paquetes de actualización): máximo **5000** entradas,
  **60 MB** por entrada y **400 MB** total; se rechazan rutas con .. o absolutas
  (zip-slip). Comprobado: un paquete con ../../evil.txt se **rechaza** y uno normal pasa.
- **Nombres de archivo**: saneado de separadores, .., caracteres prohibidos y nombres
  reservados de Windows (CON, NUL, COM1…).
- Auditoría del código: **sin** shell=True, os.system, val, xec, pickle ni
  erify=False. Las descargas ya tenían tope de bytes y las claves se enmascaran.
- Documento **SECURITY.md** con la superficie protegida y lo que no se hace.

---

## v0.1.5-beta.68 — 11 de octubre de 2026 · la beta definitiva (68.ª entrega)

**Ventana 100 % responsiva: se adapta, no bloquea tamaños**
- Mínimo de ventana: **640×480** (antes 720 de alto).
- Las **opciones** (calidad, filtros, cantidad) se **recogen solas** cuando la ventana es
  baja y se vuelven a desplegar al agrandarla; también se pueden plegar a mano con el botón
  **⚙️ Opciones**. Así el formulario pasa de 415 a **273 px** cuando hace falta.
- Sigue **sin ninguna barra** de desplazamiento, y sin recortes: lo que no cabe se recoge,
  no se corta.
- Medido con la ventana real (barras V/H siempre no/no):

`
720x858   -> form 415 · 1360x768 -> form 415 · 1280x720 -> form 393
1024x600  -> form 273 (opciones recogidas)  · 800x600 -> form 273
 640x480  -> form 170  · 1920x1080 -> form 415
`

---

## v0.1.5-beta.67 — 11 de octubre de 2026 · la beta definitiva (67.ª entrega)

**Formulario compacto en dos columnas: ya no se corta la carpeta ni los botones**
- En la entrega anterior (sin barras) la última fila quedaba fuera cuando la ventana era
  baja: el panel declaraba 376 px pero necesitaba más.
- Los campos de redes sociales pasan a **dos columnas** (usuario/palabra clave arriba,
  hashtag/instancia abajo): la página baja de 100 a 48 px.
- El divisor usa el **tamaño natural** del formulario (más un margen), no su mínimo
  declarado, y el mínimo de ventana es **640×720**, el que garantiza que se vea entero.
- Medido con la ventana real (formulario completo, **sin barras**):

`
720x858   -> formulario 415 px · entero: sí · barras no/no
1360x768  -> formulario 415 px · entero: sí · barras no/no
1280x720  -> formulario 393 px · entero: sí · barras no/no
748x852   -> formulario 415 px · entero: sí · barras no/no
1034x914  -> formulario 415 px · entero: sí · barras no/no
1920x1080 -> formulario 415 px · entero: sí · barras no/no
640x720   -> formulario 393 px · entero: sí · barras no/no
`

---

## v0.1.5-beta.66 — 11 de octubre de 2026 · la beta definitiva (66.ª entrega)

**Ninguna barra de desplazamiento: el contenido siempre entero**
- Se **desactivan** las barras del panel de búsqueda (vertical y horizontal): el formulario
  no se desplaza, se ve completo o la ventana no se deja encoger más.
- El **mínimo de ventana pasa a 640×700**, que es lo que necesita el contenido para caber
  sin barras **y sin recortes** (formulario 376 + resultados útiles + barra de estado).
- El divisor reparte el espacio para que el formulario reciba su altura y los resultados el
  resto; la galería y la lista admiten menos altura para no robar sitio.
- Medido con la ventana real (formulario completo, sin barras V ni H):

```
748x852  -> formulario 415 · barras no/no
1360x768 -> formulario 415 · barras no/no
1280x720 -> formulario 393 · barras no/no
1034x914 -> formulario 415 · barras no/no
1920x1080-> formulario 415 · barras no/no
```

- Por debajo de ~700 px de alto la ventana **no se encoge** (así nunca hay corte ni barra);
  en pantallas más bajas, el sistema puede desplazar la ventana entera.

---

## v0.1.5-beta.65 — 11 de octubre de 2026 · la beta definitiva (65.ª entrega)

**Formulario compacto: sin barra de desplazamiento en pantallas normales**
- Tras la entrega anterior, el formulario aún mostraba barra porque pedía **415 px** de
  alto y el divisor le daba 380.
- Ahora ocupa **376 px**: la carpeta de salida pasa a una fila (sin caja), el párrafo de
  ayuda se convierte en tooltip de los campos, hay menos separación, y el divisor reparte el
  espacio fijando lo que necesita el formulario (con un ajuste diferido para que Qt no lo
  vuelva a repartir por proporción).
- Medido con la ventana real:

`
1360x768  -> formulario 415 · resultados 227 · BARRA: no
1280x720  -> formulario 393 · resultados 201 · BARRA: no
1034x914  -> formulario 415 · resultados 373 · BARRA: no
1920x1080 -> formulario 415 · resultados 539 · BARRA: no
1024x600 / 800x600 / 640x480 -> BARRA: sí (no hay sitio; se desplaza, nunca se solapa)
`

---

## v0.1.5-beta.64 — 11 de octubre de 2026 · la beta definitiva (64.ª entrega)

**La ventana se adapta a cualquier pantalla (sin cortes ni solapamientos)**
- Síntoma reportado en producción: en **1366×768** el formulario se cortaba o se montaba
  sobre los resultados, incluso maximizando. La causa: el formulario **no tenía
  desplazamiento** y su altura mínima (~800 px) superaba la de esas pantallas.
- Ahora el panel de búsqueda va en una **zona con desplazamiento** y los resultados van en
  un **divisor** que se puede arrastrar; la ventana admite desde **640×480** y se reajusta
  al restaurar, maximizar o cambiar de pantalla.
- Comprobado (medidas reales de la ventana y del divisor):
  `1360×768 → 1360×768 · 1280×720 → 1280×720 · 1024×600 → 1024×600 ·
   800×600 → 800×600 · 640×480 → 640×480 · 1920×1080 → 1920×1080 · 3840×2160 → 3840×2160`.
  Tamaño mínimo: **640×480**.

---

## v0.1.5-beta.63 — 11 de octubre de 2026 · la beta definitiva (63.ª entrega)

**Contenido adulto: la casilla manda de verdad (redes, boorus y wikis)**
- El filtro estaba **invertido**: al **desmarcar** «Contenido adulto» se usaba
  `ALLOW_ADULT_RATINGS`, que por defecto **permite todo**, así que se colaba contenido
  explícito igualmente.
- Ahora:
  - **sin marcar** → solo `general` y `sensitive` (se omite `questionable` y `explicit`);
  - **marcada** → se permiten las clasificaciones configuradas (por defecto, todas).
- Afecta a **todas** las plataformas porque el filtro está en el controlador, común a redes,
  boorus y wikis.
- Comprobado con Gelbooru (`rita_loud`, 40 resultados reales: 28 explicit, 6 questionable,
  5 sensitive, 1 general): **sin** la casilla se quedan **6**, **con** la casilla pasan **40**.

---

## v0.1.5-beta.62 — 11 de octubre de 2026 · la beta definitiva (62.ª entrega)

**Las imágenes de Gelbooru ya se ven y se descargan**
- Gelbooru (sus servidores `img1..img4.gelbooru.com`) exige la cabecera **Referer**: sin
  ella **no** devuelve la imagen, devuelve una **página HTML** con HTTP 200. De ahí el
  `UnidentifiedImageError: cannot identify image file` al preparar la vista previa y que la
  descarga no trajera la imagen.
- Se añade `gelbooru.com` a `REFERER_DOMAINS`. Comprobado con una imagen real: sin Referer
  llegaban 30 KB de HTML; con Referer llegan **136 KB de JPEG** y la vista previa se genera
  en WebP.

---

## v0.1.5-beta.61 — 11 de octubre de 2026 · la beta definitiva (61.ª entrega)

**Gelbooru: la búsqueda devolvía 0 resultados aunque hubiera posts**
- La API de Gelbooru contesta con un **objeto** `{"@attributes": …, "post": […]}` y el
  programa esperaba una **lista**, así que descartaba todo y la ventana decía «Sin
  resultados» aunque el navegador mostrase miles.
- Ahora se aceptan **las dos formas**. Comprobado con una cuenta real: `oyama_mahiro` →
  **15 resultados** (antes 0) y `kuromi` → 15, con las URL de imagen **originales**
  (`img4.gelbooru.com/images/…`).
- Además, el aviso de **HTTP 401** dice ahora **qué archivo de configuración se está
  leyendo** (`config_local.py` junto al ejecutable, no el del código) y, si el sitio da
  detalle, lo muestra: era justo lo que confundía al revisar las claves.

---

## v0.1.5-beta.60 — 11 de octubre de 2026 · la beta definitiva (60.ª entrega)

**Asistente de Pixiv: el enlace de continuación ya no sirve (404 de Pixiv)**
- Comprobado: el salto ccounts.pixiv.net/post-redirect lleva a
  pp-api.pixiv.net/web/v1/users/auth/pixiv/start, que **devuelve 404**. Ese flujo de
  login de Pixiv está roto **en su lado**, así que la página se queda en blanco aunque no
  haya bloqueadores (también en ventana privada).
- El asistente ya no sugiere abrir ese enlace (era un callejón sin salida): explica el 404,
  que no es culpa del navegador, y deja las opciones reales (reintentar más tarde o usar la
  web de Pixiv mientras tanto).
- El flujo con usuario/contraseña sigue **deshabilitado** por Pixiv (responde «invalid OAuth
  client»), así que el 
efresh_token solo puede salir del flujo PKCE cuando lo reparen.

---

## v0.1.5-beta.59 — 11 de octubre de 2026 · la beta definitiva (59.ª entrega)

**Asistente de Pixiv: qué hacer si la página sale en blanco**
- El salto intermedio de Pixiv (ccounts.pixiv.net/post-redirect) a veces se queda en
  blanco porque un bloqueador corta la redirección. El asistente explica ahora tres salidas:
  ventana privada sin extensiones, desactivar el bloqueador para pixiv.net, o pegar el
  enlace de continuación (pp-api.pixiv.net/.../start) que el propio asistente imprime.

---

## v0.1.5-beta.58 — 11 de octubre de 2026 · la beta definitiva (58.ª entrega)

**Asistente de Pixiv: distingue el `code_challenge` del `code`**
- Síntoma: al pegar una URL como
  `accounts.pixiv.net/post-redirect?return_to=…code_challenge=…`, el asistente tomaba el
  **`code_challenge`** como si fuera el código y Pixiv respondía
  `HTTP 400 · error 918 (不正なリクエスト)`.
- Ahora, si el valor pegado es el `code_challenge` de **esta** ejecución, se **detecta** y
  se explica: es parte del enlace de INICIO, no vale; hay que llegar a la URL final con
  `code=`.
- Las instrucciones del PASO 2 avisan de las dos pistas que delatan que aún no se ha
  terminado: `accounts.pixiv.net/post-redirect` o `code_challenge=`.
- Comprobado: con la URL intermedia el asistente guía al enlace de continuación; con un
  callback real extrae el código; con el challenge, lo rechaza y lo explica.

---

## v0.1.5-beta.57 — 11 de octubre de 2026 · la beta definitiva (57.ª entrega)

**El estado de las redes muestra TODAS las instancias del fediverso**
- Antes solo salía «Mastodon». El fediverso no es una plataforma: es cada **instancia**
  (Mastodon, Misskey, CherryPick…), y ahora se comprueban una por una:
  `Fediverso · baraag.net`, `Fediverso · misskey.io`, `Fediverso · pawoo.net`,
  `Fediverso · pisskey.io`, `Fediverso · dill.burggit.moe`, `Fediverso · shota.house`…
- La lista vive en **`FEDIVERSE_INSTANCIAS`** (config.py) y se puede ampliar en tu
  `config_local.py` con las que uses:

```python
FEDIVERSE_INSTANCIAS = ["baraag.net", "misskey.io", "mi.servidor"]
```

- Comprobado en vivo: baraag.net, misskey.io, pawoo.net y shota.house responden
  **operativo** (HTTP 200). La ventana muestra ahora **29 plataformas** (antes 23).

---

## v0.1.5-beta.56 — 11 de octubre de 2026 · la beta definitiva (56.ª entrega)

**Motor opcional por PyTorch: CUDA, DirectML, TensorRT o CPU, con TU instalación**
- El programa no trae PyTorch (cientos de MB), pero puede **usar el tuyo**: el motor
  `"torch"` lanza un script con el intérprete de Python que **tenga torch** y amplía con
  `RealESRGAN_x4plus_anime_6B`.
- Según lo que tengas instalado, el dispositivo se elige solo:
  **CUDA** (NVIDIA) · **DirectML** (`torch-directml`, cualquier GPU DX12 de Windows) ·
  **TensorRT** (`torch-tensorrt`) · **MPS** (Apple) · **CPU**.
- Se configura en `config_local.py`:

```python
AI_ENGINE = "torch"          # usa tu PyTorch
AI_PYTHON = ""               # opcional: ruta a tu python (si no se detecta)
AI_TORCH_DEVICE = "auto"     # auto | cuda | dml | trt | mps | cpu
AI_TORCH_MODEL = ""          # opcional: ruta a los .pth
```

- Los pesos (~18 MB) se **descargan solos** la primera vez a `~/.imaginteca/ia/`.
- Si no hay ningún Python con torch, se avisa en el registro y se sigue con el motor
  Vulkan o con Lanczos: nunca se queda sin imagen.
- Instalación necesaria (una vez): `pip install torch realesrgan` (y `torch-directml`
  si quieres DirectML).

---

## v0.1.5-beta.55 — 11 de octubre de 2026 · la beta definitiva (55.ª entrega)

**Ajustes del análisis y aclaración sobre DirectX/DirectML**
- El reescalado (Lanczos) deja un ringing muy suave que el analizador contaba como
  «artefactos de compresión»: se sube el umbral de bloques de 8 a 12 y las imágenes
  ampliadas ya no se marcan como defectuosas por ese motivo.
- Se probó el modo **CPU** de waifu2x (`-g -1`): el binario actual **crashea** (violación
  de acceso), así que se retira en vez de ofrecer algo que no funciona. Sin GPU o sin
  Vulkan, la IA se salta y se sigue con Lanczos: nunca se queda sin imagen.
- **Sobre DirectX**: DirectX por sí no hace IA. Lo que sirve es **DirectML** (la capa de
  *machine learning* sobre DirectX 12), compatible con **cualquier tarjeta DX12**
  (NVIDIA, AMD e Intel, integradas incluidas). No se incluye porque exige **ONNX Runtime**
  (~50 MB) y un modelo ONNX aparte (~60 MB); Vulkan ya cubre a los tres fabricantes con
  6 MB de motor. Si algún día se quiere, la vía limpia es un motor extra descargable.

---

## v0.1.5-beta.54 — 11 de octubre de 2026 · la beta definitiva (54.ª entrega)

**Dos motores de IA a elegir, y se ve cuál se usó**
- **Real-ESRGAN** (modelo anime 6B) y **waifu2x** (modelo de anime, escala nativa 2/4/8/16/32
  y eliminación de ruido). Los dos usan **Vulkan**, que vale para NVIDIA, AMD/ATI e Intel.
- Se elige en `config_local.py`:
  `AI_ENGINE = "auto"` (Real-ESRGAN y, si falla, waifu2x) · `"realesrgan"` · `"waifu2x"`.
- El resultado dice con qué se amplió: `IA 8x (Real-ESRGAN)` o `IA 8x (waifu2x)`, y el
  registro añade modelo, motor y GPU.
- Comprobado con la misma imagen: los tres modos dan 228 → 1824 px y cada uno informa de
  su motor.
- **Sobre CUDA y otros fabricantes**: los motores CUDA/DirectML no se incluyen porque
  exigen PyTorch u ONNX Runtime (cientos de MB) y este proyecto va sin dependencias
  pesadas; Vulkan cubre a los tres fabricantes y también las gráficas integradas. Si algún
  día se quieren, la forma limpia es un motor extra descargable aparte.

---

## v0.1.5-beta.53 — 11 de octubre de 2026 · la beta definitiva (53.ª entrega)

**Se puede ver qué modelo y qué tarjeta usa la IA**
- Al ampliar con IA, el registro deja una línea clara:
  `IA: modelo realesrgan-x4plus-anime · GPU detectada: Intel(R) UHD Graphics`.
- El **autoexamen** (`Imaginteca.exe --selftest`) muestra ahora también:
  `modelo IA: realesrgan-x4plus-anime (anime 6B)` y `GPU: …`, además de los tramos.
- Comprobado: 200 px con IA → 1600 px (`IA 8x`) y la GPU anotada en el resultado.

---

## v0.1.5-beta.52 — 11 de octubre de 2026 · la beta definitiva (52.ª entrega)

**Motor de IA: modelo de anime/cartoon y compatible con todas las tarjetas**
- El modelo queda fijado y documentado en **RealESRGAN_x4plus_anime_6B** (el fichero
  `realesrgan-x4plus-anime` del motor ncnn): es el que mejor va con dibujo 2D y 3D no
  realista, y es más rápido (6 bloques). `realesrgan-x4plus` (fotos reales) sigue
  disponible en `config_local.py` por si algún día hace falta.
- El motor es **`realesrgan-ncnn-vulkan`**, que usa **Vulkan**: funciona con tarjetas
  **NVIDIA, AMD (y ATI) e Intel**, sin necesidad de CUDA ni de drivers de un fabricante
  concreto. Con `AI_GPU` se puede forzar una tarjeta concreta (`-g 0`, `-g 1`…).
- Si la IA no puede ejecutarse en ese equipo (sin Vulkan, sin modelo o con un fallo), el
  programa sigue con **Lanczos + realfinado**: nunca se queda sin imagen.
- Comprobado: `228 px → 1824 px` con `IA 8x` y el modelo anime, más `realfinado final`.

---

## v0.1.5-beta.51 — 11 de octubre de 2026 · la beta definitiva (51.ª entrega)

**Nueva plataforma: Inkbunny (inkbunny.net)**
- Se añade a las redes sociales, con su **API oficial**: se busca por texto o por `@usuario`
  y devuelve las imágenes (una por archivo del envío).
- **Necesita cuenta**: usuario y contraseña en `config_local.py` y, en la web de Inkbunny,
  activar **«API Access»** en *Account Settings → API* (sin eso su API no responde).
  Sin credenciales el programa lo explica y no falla con un mensaje raro.
- La sesión se reutiliza entre búsquedas y, si caduca, se renueva sola. Con cortesía:
  `INKBUNNY_PAUSA` (1 s entre peticiones) y `INKBUNNY_MAX_PAGINAS` (6).
- Aparece también en **Estado de las redes sociales** (Ayuda y clic derecho del icono).

### Cómo configurarlo

```python
# config_local.py (junto al ejecutable, o app/config_local.py)
INKBUNNY_USERNAME = "tu_usuario"
INKBUNNY_PASSWORD = "tu_contraseña"
```

---

## v0.1.5-beta.50 — 11 de octubre de 2026 · la beta definitiva (50.ª entrega)

**El aviso de «zonas quemadas» era un falso positivo**
- Un sticker de Kuromi sobre fondo blanco tiene el 60-80 % de píxeles a 255 y el programa
  lo marcaba como «aceptable: zonas quemadas», cuando es su diseño.
- Las zonas quemadas ya **no cuentan como defecto** ni generan avisos: se siguen **midiendo**
  y aparecen como dato en la ficha, pero la imagen se considera limpia y se entrega igual.
- Comprobado con `Kuromi_KPJ_24.jpg` (153 px): «calidad tras reescalar: **limpia**»,
  «realfinado final (120 %)» y salida de **2448×2448** en WebP.

---

## v0.1.5-beta.49 — 11 de octubre de 2026 · la beta definitiva (49.ª entrega)

**El orden correcto: primero se reescala, después se corrige**
- Antes se reparaba la imagen pequeña y luego se ampliaba: el reescalado volvía a
  difuminar lo arreglado. Ahora el orden es:
  **reescalar (IA o Lanczos) → medir el resultado → reparar → realfinar → guardar WebP**.
- **Realfinado final**: un reescalado grande (8x-16x) deja la imagen blanda, así que se
  afila en proporción al aumento: 120 % con Lanczos 16x y 60 % cuando la IA ya aportó
  detalle (para no crear halos). Configurable con `AFILAR_TRAS_ESCALAR`.
- Comprobado con la imagen de 153 px de Fandom: **153 → 2448 px** (16x) sin IA y con IA,
  con `realfinado final` anotado en el registro y en la ficha.
- Las **vistas previas** siguen el mismo criterio (se redimensionan y después se reparan).
- Aviso honesto: con fuentes muy pequeñas la IA puede inventar detalle y deformar; si se
  nota, basta con desmarcar «Modo IA» (Lanczos + realfinado dan un resultado más fiel).

---

## v0.1.5-beta.48 — 11 de octubre de 2026 · la beta definitiva (48.ª entrega)

**Los archivos que no existen en el wiki ya no se ofrecen**
- Una página de Fandom puede enlazar un archivo **borrado** o que nunca se subió (un
  «enlace rojo»). El programa lo listaba y luego fallaba al descargarlo con **404**
  (`Special:FilePath/…`), contándolo como «con problemas».
- Ahora se consulta `imageinfo` y, si el archivo está marcado como `missing`, se **omite**:
  la búsqueda de «kuromi» en sanrio.fandom devuelve **4 resultados, todos descargables**
  (antes 5, uno roto).

---

## v0.1.5-beta.47 — 11 de octubre de 2026 · la beta definitiva (47.ª entrega)

**Arreglado: con «Modo IA» la imagen quedaba sin ampliar**
- Síntoma: con IA activa, el registro decía «mejora fallida; se aplica conversión directa a
  WebP» y la imagen se guardaba **como estaba** (sin ampliar). Sin IA, en cambio, salía bien.
- Causa: la IA tarda segundos; en ese hueco la galería abre la imagen y Windows bloquea el
  archivo, así que el guardado final fallaba con `OSError [Errno 22] Invalid argument` y el
  programa caía al «WebP directo».
- Arreglo: el guardado **reintenta hasta 3 veces** con una pausa breve. Comprobado con el
  archivo bloqueado a propósito: ahora se guarda la imagen mejorada de verdad.
- Si un archivo del wiki no existe (404 al bajarlo), se informa en el resumen en vez de
  darlo por bueno.

---

## v0.1.5-beta.46 — 11 de octubre de 2026 · la beta definitiva (46.ª entrega)

**Sin límite de cantidad: te trae TODOS los resultados**
- El tope interno de 100 resultados por fuente recortaba las búsquedas. Ahora, si **no**
  marcas «Limitar cantidad», se piden hasta **10000** (solo como red de seguridad: el
  adaptador para cuando el sitio se acaba).
- Comprobado: Safebooru «kuromi» → **1112** resultados (antes 100) y «1girl» → 10000.
- Si marcas **Limitar cantidad**, se pide exactamente esa cantidad: el control admite hasta
  **100000** (antes 1000).
- También se amplían las páginas de redes sociales (`SOCIAL_PAGINAS` 6 → 30 y
  `SOCIAL_MAX_CANDIDATOS` 240 → 2000). Todo ajustable en `config_local.py`.

---

## v0.1.5-beta.45 — 11 de octubre de 2026 · la beta definitiva (45.ª entrega)

**El autoexamen muestra los tramos de ampliación**
- `Imaginteca.exe --selftest` imprime ahora las reglas vigentes y comprueba que el
  ejecutable lleva la lógica buena: `228 px → 8x (1824)`, `120 px → 16x (1920)`,
  `520 px → 4x (2080)`, `600 px → 3x`, `800 px → 2x`, tope 8K.
- Sirve para confirmar de un vistazo que la copia que se abre es la recompilada.

---

## v0.1.5-beta.44 — 11 de octubre de 2026 · la beta definitiva (44.ª entrega)

**El mínimo de 1600 px se mide sobre el ANCHO**
- El factor de ampliación se decide por el **ancho** de la imagen (no por el lado mayor) y
  se aplica a los dos lados: así una imagen vertical gana ancho de verdad, que es lo que
  se nota en la calidad final.
- Ejemplo: **228×600 → 1824×4800** (8x). Antes mandaba el alto (600 px) y quedaba en
  684×1800 (3x), más estrecha de lo deseado.
- Los tramos siguen igual, ahora sobre el ancho: hasta 599 px se sube el factor para
  llegar a 1600 px de ancho; 600–799 → 3x; 800 px o más → 2x; tope 8K.

---

## v0.1.5-beta.43 — 11 de octubre de 2026 · la beta definitiva (43.ª entrega)

**Imágenes pequeñas: el múltiplo crece hasta llegar a 1600 px**
- Hasta 599 px ya no se aplica un 4x fijo: se sube el factor para que el resultado llegue
  **al menos a 1600 px** (con tope de 8K):
  `0–49 px → 32x · 50–99 → 32x · 100–199 → 16x · 200–399 → 8x · 400–599 → 4x`.
- Ejemplos reales: **228 px → 1824 px** (antes 912 px, borrosa), 120 px → 1920 px,
  520 px → 2080 px. 600–799 sigue en **3x** y 800 px o más en **2x** (tope 8K).
- Se mantiene: reparación de defectos antes de ampliar, recuperación de archivos dañados,
  **siempre WebP** con la mejor calidad (mínimo 90, sin pérdida si es plana) y **con IA o
  sin IA**.

---

## v0.1.5-beta.42 — 11 de octubre de 2026 · la beta definitiva (42.ª entrega)

**Plantilla de configuración al día**
- La plantilla que se crea junto al ejecutable documenta ya las claves de **Danbooru**
  (`DANBOORU_API_KEY` / `DANBOORU_LOGIN`), **DeviantArt** y **Pinterest**.

---

## v0.1.5-beta.41 — 11 de octubre de 2026 · la beta definitiva (41.ª entrega)

**Danbooru: la cuenta se usa de verdad (y entrega el ORIGINAL)**
- La ficha de Danbooru no pedía credenciales, así que el adaptador iba como anónimo y el
  sitio devolvía la versión reducida. Ahora envía login + pi_key de tu
  config_local.py y devuelve **ile_url (el original)**: comprobado con una cuenta real,
  todas las URL salen de cdn.donmai.us/original/….
- La plantilla local trae las líneas DANBOORU_API_KEY y DANBOORU_LOGIN listas.
- Si Danbooru pone su comprobación de Cloudflare, se resuelve una vez en la ventana y se
  reutiliza la sesión.

---

## v0.1.5-beta.40 — 11 de octubre de 2026 · la beta definitiva (40.ª entrega)

**Siempre la imagen ORIGINAL (nunca la muestra ni la reducida)**
- Al descargar, se prueba primero el **archivo original** (ile_url) y, si el sitio no lo
  entrega, se va bajando por las alternativas (large_file_url, sample_url) hasta la
  miniatura, dejando rastro en el registro de qué se usó.
- La muestra grande de la galería ya salía del original (MUESTRAS_ORIGINALES); se mantiene.
- En **Danbooru**, si el sitio exige comprobación (Cloudflare) o cuenta, el original puede
  venir vacío: se resuelve la comprobación en la ventana y se reintenta. Si aun así no
  estuviera, se usa la mayor disponible y queda anotado.
- La **miniatura** solo se usa para la tira de resultados (es una miniatura, a propósito).

---

## v0.1.5-beta.39 — 11 de octubre de 2026 · la beta definitiva (39.ª entrega)

**Arreglado el falso «captcha» de tbib.org (The Big Imageboard)**
- tbib no pide ninguna comprobación. Pasaba dos cosas: sirve su **JSON como 	ext/html**
  (como otros Gelbooru 0.2) y el detector se disparaba con que apareciera la palabra
  captcha en cualquier texto (¡hasta en una etiqueta de un post!).
- Ahora: un cuerpo que **empieza como JSON** se acepta aunque el Content-Type diga HTML, y
  solo se considera verificación cuando hay **señales reales** (widgets y scripts de
  Cloudflare/Turnstile/hCaptcha, «Just a moment…», etc.).
- Comprobado: tbib.org devuelve sus publicaciones, una Cloudflare real se sigue detectando y
  una página normal que menciona «captcha» ya no abre la ventana.

---

## v0.1.5-beta.38 — 11 de octubre de 2026 · la beta definitiva (38.ª entrega)

**Se repara y se mejora antes de entregar: nunca una imagen en mal estado**
- Si el análisis detecta defectos, la imagen **se arregla antes** de ampliarla y guardarla:
  se reduce el ruido, se alisan los bloques de compresión y se recupera la nitidez; después
  se amplía según los tramos de siempre.
- **Archivos dañados o truncados**: se intenta recuperar lo que llegó; si se recupera, se
  repara y se guarda igual. Si no, se descarta.
- **Siempre WebP**, con la mejor calidad y sin pérdida si la imagen es plana. **Nunca jpg ni
  png**: si no se puede generar un WebP válido, la imagen se descarta (no se entrega el
  original).
- La misma reparación se aplica a las **vistas previas**.

---

## v0.1.5-beta.37 — 11 de octubre de 2026 · la beta definitiva (37.ª entrega)

**Análisis de calidad antes de ampliar (ideas del inspector forense de 29a.ch)**
- Se **mide** la imagen antes de tocarla: nitidez, ruido, bloques de compresión (tabla de
  cuantización del JPEG y bits por píxel), zonas quemadas y número de colores.
- **No se amplía** una imagen con defectos graves (borrosa, ruidosa, re-comprimida):
  ampliarla solo agrandaría los defectos; se guarda igual en WebP con la mejor calidad y
  el motivo va al registro.
- Las imágenes **planas** (capturas, dibujos de línea) se guardan **sin pérdida**, que es
  donde la compresión con pérdida deja manchas y bordes sucios.
- Parámetros: WebP **calidad mínima 90** (WEBP_CALIDAD_MINIMA), method=6, tope 8K. La
  misma política se aplica a las **vistas previas**.
- Los tramos de mejora no cambian: 4x hasta 699 px · 3x de 700 a 799 · 2x de 800 a 1599.

---

## v0.1.5-beta.36 — 11 de octubre de 2026 · la beta definitiva (36.ª entrega)

**X (Twitter): cómo filtrar con FxTwitter**
- Se puede **filtrar la galería de un usuario**: @usuario + **palabra clave** o
  **#hashtag** → solo se quedan los posts que lo mencionan (se compara con el texto del
  tuit; X no entrega las etiquetas aparte).
- **Reintentos con paciencia**: FxTwitter devuelve fallos transitorios (un 404 en una URL
  buena y al segundo intento 200). Ahora se reintenta hasta 3 veces con espera
  (FXTWITTER_INTENTOS, FXTWITTER_PAUSA), sin martillear el servicio.
- Comprobado: sin filtro 30 imágenes · con «rover» 1 · con una palabra ausente 0.

---

## v0.1.5-beta.35 — 11 de octubre de 2026 · la beta definitiva (35.ª entrega)

**X (Twitter) sin claves, con FxTwitter**
- El adaptador de X usa ahora la **API pública de FxTwitter** (FxEmbed, MIT): **sin cuenta
  y sin claves**. Trae la **galería de un usuario** (@usuario, paginada) y un **post
  concreto** (pegando su enlace o su id).
- **Búsqueda por palabra/hashtag: no** — X no la sirve sin sesión y FxTwitter responde 404;
  el programa lo explica y sugiere las plataformas que sí buscan.
- **Cortesía**: retardo explícito entre peticiones (FXTWITTER_PAUSA, 1,2 s) y un tope de
  páginas (FXTWITTER_MAX_PAGINAS), muy por debajo del límite de FxTwitter, para no
  comportarse como un bot. Los vídeos y GIF se ignoran (esto es de fotos).

---

## v0.1.5-beta.34 — 11 de octubre de 2026 · la beta definitiva (34.ª entrega)

**Pinterest: configurar la API, más claro**
- El aviso de credenciales decía «en app/config.py»; ahora indica **tu config_local.py**,
  recuerda que **una línea comentada no cuenta** y explica el paso a paso (app + token
  OAuth + código de país para la búsqueda global).
- La plantilla local trae ya las líneas **activas y vacías**:
  PINTEREST_ACCESS_TOKEN y PINTEREST_COUNTRY_CODE, con las instrucciones al lado.

---

## v0.1.5-beta.33 — 11 de octubre de 2026 · la beta definitiva (33.ª entrega)

**Arreglado el «401 autenticación rechazada» de DeviantArt**
- El token de DeviantArt **caduca a la hora** y el adaptador lo seguía usando: tras un rato,
  todas las consultas daban 401. Ahora se **renueva antes** de caducar y, si el sitio lo
  rechaza igualmente, se **renueva y se reintenta** una vez.
- Comprobado con la API real: búsquedas por **palabra clave** («kuromi», «cinnamoroll») con
  resultados, y renovación correcta tanto con token caducado como inválido.

---

## v0.1.5-beta.32 — 11 de octubre de 2026 · la beta definitiva (32.ª entrega)

**DeviantArt: configurar la API es más fácil**
- El aviso de credenciales decía «en app/config.py»; ahora indica **tu config_local.py**
  (el que está junto al ejecutable), recuerda que **una línea comentada no cuenta** y da el
  enlace donde se crean las claves.
- La plantilla local trae ya las líneas **activas y vacías**:
  DEVIANTART_CLIENT_ID y DEVIANTART_CLIENT_SECRET (antes estaban comentadas).

---

## v0.1.5-beta.31 — 11 de octubre de 2026 · la beta definitiva (31.ª entrega)

**Avisos: se abren al pulsarlos**
- En el menú de la **campana**, cada aviso se puede **pulsar**: se abre en una **ventanita**
  con el texto entero y **queda marcado como leído** (baja el contador y la insignia).
- Se mantienen «Marcar todo como leído» y «Borrar los avisos».

**«Estado de las redes sociales» donde toca**
- Sale del menú de la campana (ahí no pintaba nada) y queda en **Ayuda**, justo **después de
  «Dependencias del sistema»**, y también en el **clic derecho del icono** de la bandeja, en
  el mismo orden.

**Arreglado: el error «no devolvió JSON válido» en Safebooru, Rule34.xxx y otros boorus**
- Cuando el tag no tiene resultados, esos sitios contestan **200 con el cuerpo vacío**. El
  programa lo trataba como error («Expecting value: line 1 column 1»). Ahora se entiende
  como lo que es: **«la búsqueda no trajo resultados»**, sin aviso rojo.

---

## v0.1.5-beta.30 — 11 de octubre de 2026 · la beta definitiva (30.ª entrega)

**Se retira el filtro de advertencias (se mantiene el apartado informativo)**
- La casilla **«⚠️ Con advertencias»** desaparece, y con ella el descarte de imágenes por
  traer avisos: **la búsqueda y la descarga vuelven a comportarse como siempre** (lista
  negra, enlaces de pago, ratings y licencia). Ese filtro estaba dejando fuera contenido que
  antes sí pasaba.
- Se **mantiene** lo que sí se quería: en **Propiedades**, los apartados **Contenido
  adulto** y **Advertencias**, solo cuando amerita (las imágenes SFW no llevan ninguno).

---

## v0.1.5-beta.29 — 11 de octubre de 2026 · la beta definitiva (29.ª entrega)

**Advertencias de contenido y aviso de adulto, en su apartado**
- **Propiedades** muestra dos apartados nuevos, **solo cuando amerita**:
  - **Contenido adulto** (NSFW): clasificación questionable/xplicit o marcas de la
    plataforma (Pixiv x_restrict, sexual, sensitive…). Las SFW **no se marcan**.
  - **Advertencias**: aviso de contenido del autor (spoiler_text del fediverso), «marcada
    como sensible», «oculta por la plataforma» y «marcada por moderación» (boorus).
- Nuevo detector (pp/services/advertencias.py) con las señales de cada plataforma.
- **Filtro nuevo** en búsqueda y descarga: la casilla **⚠️ Con advertencias** se habilita
  con «🔞 Contenido adulto» y decide si se dejan pasar las imágenes con advertencias
  (sin ella se **omiten**, y quedan contadas en el resumen de descartes).

---

## v0.1.5-beta.28 — 11 de octubre de 2026 · la beta definitiva (28.ª entrega)

**Arreglado: la comprobación se daba por superada sin estarlo (y por eso se repetía 3 veces)**
- La ventana daba la sesión por buena en cuanto la página **parecía** la definitiva. Ahora
  **prueba la sesión desde el propio navegador** (pide /posts.json?limit=1 con la sesión
  de la persona): solo se cierra y continúa si el sitio **responde de verdad** (2xx/3xx).
  Si responde 403 o falla, sigue esperando y lo dice («espera unos segundos o pulsa 🔄
  Recargar»), y se añade el botón **🔄 Recargar**.
- El programa envía ahora **el User-Agent exacto del navegador que resolvió** la
  comprobación (antes el transporte con huella metía el suyo y el sitio, que firma la
  cookie con el agente, seguía pidiéndola). Con esto la sesión sirve de verdad.
- Recordatorio: **el programa nunca resuelve la comprobación por su cuenta**; la resuelve
  la persona en esa ventana y solo se reutiliza **su** sesión.

---

## v0.1.5-beta.27 — 11 de octubre de 2026 · la beta definitiva (27.ª entrega)

**Arreglado: ATF Booru se quedaba en «la sesión no sirve todavía» con la comprobación ya
superada**
- La comprobación de sesión que se hacía después del navegador era demasiado estricta:
  pedía la **portada** del sitio y, si esa página volvía a pedir el reto (aunque la
  búsqueda fuera a funcionar), **cortaba la operación** con un aviso. Ahora es solo
  **informativa**: se intenta la búsqueda o la descarga de verdad y manda el resultado real.
- Se espera algo más (1,5 s) antes de cerrar la ventana, para que las cookies estén puestas
  incluso en equipos lentos.
- Se mantiene el límite de **3 comprobaciones seguidas** y, pasado ese punto, el aviso
  claro, para que nunca se quede en un bucle.

---

## v0.1.5-beta.26 — 11 de octubre de 2026 · la beta definitiva (26.ª entrega)

**El icono de la bandeja alterna, como el botón de la barra de tareas**
- Con la ventana **restaurada o maximizada**, pulsar el icono la **minimiza**.
- Con la ventana **minimizada**, pulsar el icono la **abre como estaba**: maximizada si lo
  estaba y restaurada si no.
- El menú del icono lo dice: cambia entre **«🪟 Minimizar Imaginteca»** y **«🪟 Abrir
  Imaginteca»** según el estado, y hace lo mismo.

---

## v0.1.5-beta.25 — 11 de octubre de 2026 · la beta definitiva (25.ª entrega)

**Menú del icono de la bandeja (el de las notificaciones)**
- **Clic derecho**: abrir (restaura o maximiza, según como estuviera la ventana), buscar,
  descargar, **cancelar** la operación en curso, ayuda, acerca de, actualizaciones,
  dependencias del sistema y **salir** — cada uno con su atajo.
- **Clic izquierdo**: abre la ventana (restaurar o maximizar).
- **Al señalarlo**: el nombre del programa y la versión, con los avisos sin leer.
- Atajos nuevos: **Cancelar Ctrl+.**, **Acerca de Ctrl+Shift+A**, **Actualizaciones
  Ctrl+U**, **Dependencias Ctrl+Shift+D** y **Salir Ctrl+Q** (ahora sí, también en el
  menú Archivo).

---

## v0.1.5-beta.24 — 11 de octubre de 2026 · la beta definitiva (24.ª entrega)

**El estado de plataformas incluye también boorus y wikis de fandom**
- La ventana de **Ayuda › 📡 Estado de las redes sociales** comprueba ahora **las 22
  plataformas del programa**: 7 redes sociales, **14 boorus** y la **wiki de fandom**.
- La lista de boorus **no se copia a mano**: sale de BOORU_SITES, así que también
  aparecen los que añadas en config_local.py.
- La tabla lleva columna **Tipo** (Red social / Booru / Wiki de fandom) y el resumen separa
  cuántas responden de cada tipo.

---

## v0.1.5-beta.23 — 11 de octubre de 2026 · la beta definitiva (23.ª entrega)

**Sistema de notificaciones**
- Avisa de lo importante: **búsquedas y descargas** terminadas (o sin resultados),
  **errores**, **versiones nuevas** al arrancar y **plataformas caídas**.
- Se cuentan y se ven en la **campana 🔔** de la barra (número sin leer), en la barra de
  estado y —con la ventana **minimizada**— como **notificación del sistema operativo** y
  en la **insignia del icono** de la barra de tareas / Dock, con el mismo icono de la
  aplicación.
- Nuevo en **Ayuda › 📡 Estado de las redes sociales**: comprueba si X, Pinterest,
  DeviantArt, Tumblr, Pixiv, Bluesky, Mastodon y Fandom responden, con estado, latencia y
  enlace a su página de estado; avisa de las que fallan.
- Se puede silenciar con `NOTIFICACIONES = False` en `config_local.py`.

---

## v0.1.5-beta.22 — 11 de octubre de 2026 · la beta definitiva (22.ª entrega)

**Arreglado el instalador de Windows (la 21 no llegó a publicarse)**
- El icono del instalador quedó anotado con # en el guion de Inno Setup, donde la
  almohadilla es una **directiva** y no un comentario: la compilación fallaba. Ahora el
  comentario va con ;, como corresponde.

**Los instaladores llevan el icono típico de instalación de cada sistema** (lo de la 21)
- **Windows**: la clásica **caja con la flecha azul** (instalador_windows.ico).
- **macOS**: el **disco plateado** como icono del volumen del .dmg.
- **Linux**: el icono de la aplicación en **48 y 128 px** (menú y centro de software) y el
  icono de **paquete de cartón** para difusión.
- Se generan con python scripts\generar_iconos_instaladores.py.

---

## v0.1.5-beta.21 — 11 de octubre de 2026 · la beta definitiva (21.ª entrega)

**Los instaladores llevan el icono típico de instalación de cada sistema**
- **Windows**: la clásica **caja con la flecha azul** hacia dentro (instalador_windows.ico,
  con 7 tamaños), en lugar del icono de la aplicación.
- **macOS**: el **disco plateado** de las imágenes de disco, como icono del volumen del
  .dmg (.VolumeIcon.icns).
- **Linux**: el icono de la aplicación se instala ahora también en **48 y 128 px**, y se
  incluye el icono de **paquete de cartón** para material de difusión.
- Se generan con python scripts\generar_iconos_instaladores.py.

---

## v0.1.5-beta.20 — 11 de octubre de 2026 · la beta definitiva (20.ª entrega)

**Arreglado: tras resolver la comprobación, la búsqueda continúa sola (sin bucle)**
- El reintento automático se perdía después de la primera vuelta: el aviso decía «vuelve a
  pulsar Buscar», se pulsaba, el sitio volvía a pedir la comprobación y así en bucle, sin
  llegar a traer imágenes. Ahora el reintento **no se borra** y la operación continúa sola
  hasta terminar.
- Antes de repetirla se **comprueba en el acto** que el programa puede pedir datos con la
  sesión que consiguió la ventana: si aún no sirviera, se avisa con claridad («la sesión no
  sirve todavía, resuélvela y espera unos segundos») en lugar de dar vueltas.
- Límite de seguridad: si el sitio pide la comprobación **más de 3 veces seguidas**, se
  detiene y se explica, para no quedarse en un bucle.
- Recordatorio: las imágenes aparecen **en Imaginteca** (en la tira de resultados y en la
  galería), no dentro de la ventana del navegador.

---

## v0.1.5-beta.19 — 11 de octubre de 2026 · la beta definitiva (19.ª entrega)

**Arreglado: la ventana de comprobación fallaba en la versión compilada**
- El paquete excluía **QtWebChannel** (y QtWebSockets, QtQuick y QtQml), que son
  dependencias del navegador incrustado: al abrir la ventana saltaba
  could not import module 'PySide6.QtWebChannel'. Ahora se incluyen.
- El **autoexamen** (--selftest) comprueba el navegador incrustado y lo dice en su
  informe, para que un fallo así se vea antes de publicar.

---

## v0.1.5-beta.18 — 10 de octubre de 2026 · la beta definitiva (18.ª entrega)

**Arreglado: la ventana de comprobación no llegaba a abrirse**
- El controlador convertía la petición de comprobación en un **«Error inesperado»** antes
  de que la ventana se enterara (un xcept Exception general se la comía). Por eso el
  aviso decía «pide una comprobación… resuélvela en la ventana» **pero la ventana no
  aparecía**.
- Ahora la búsqueda y la descarga avisan por su canal propio y **la ventana se abre**; las
  acciones individuales (guardar una imagen del carrusel) también.
- Red de seguridad añadida: si por cualquier camino el aviso llegara como texto, la
  ventana se abre igualmente.
- Comprobado de punta a punta: buscar en ATF Booru pide la ventana y **no** da error.

---

## v0.1.5-beta.17 — 10 de octubre de 2026 · la beta definitiva (17.ª entrega)

**La ventana de comprobación vale para cualquier sitio (Rule34.xxx incluido)**
- Antes solo se abría cuando el sitio devolvía su página de **prueba de trabajo** (ATF
  Booru). Ahora también cuando responde un **muro de Cloudflare** («Just a moment…»,
  «Attention Required»), un **CAPTCHA**, **Turnstile**, **DDoS-Guard** o similares.
- El procedimiento es el mismo en todos: se abre la ventana con el navegador, **la
  resuelves tú**, y al superarla **se cierra sola** y la búsqueda o la descarga continúan
  con las cookies de esa sesión. Si **no** se supera, se avisa y **no se continúa**.
- Un error normal del sitio (un 404, una página de «no encontrado») **no** abre la
  ventana: se informa como siempre.

---

## v0.1.5-beta.16 — 10 de octubre de 2026 · la beta definitiva (16.ª entrega)

**Paquetes 83 MB más ligeros (ya en las descargas)**
- La publicación quita los recursos del **inspector (DevTools)** del navegador
  incrustado: 83 MB que esta aplicación no usa nunca. Los .zip, .tar.gz, instaladores y
  manifiestos de esta versión salen más pequeños.

**Arreglado: las claves de ATF Booru (las «FBOORU») no se encontraban**
- El sitio se llama **ATF Booru** (ooru.allthefallen.moe) y sus claves son
  FBOORU_API_KEY / FBOORU_LOGIN: ahora se reconocen por llthefallen, tf y
  booru, así que se encuentran aunque los nombres no coincidan.
- El aviso de credenciales recuerda que **una línea comentada (con #) no cuenta**, que
  es el tropiezo más habitual al rellenar config_local.py.
- Las claves de un sitio **no se usan nunca para otro**, aunque compartan familia de API
  (Gelbooru y Rule34.xxx): si faltan las de un sitio, se piden las suyas.

---

## v0.1.5-beta.15 — 10 de octubre de 2026 · la beta definitiva (15.ª entrega)

**Arreglado: las claves de ATF Booru (las «FBOORU») no se encontraban**
- El sitio se llama **ATF Booru** (ooru.allthefallen.moe) pero sus claves son
  FBOORU_API_KEY / FBOORU_LOGIN (así se llamaba antes el sitio): la búsqueda de
  credenciales no relacionaba ambos nombres y decía «necesita api_key, login» aunque
  estuvieran escritas. Ahora se reconocen por llthefallen, tf y booru.
- El aviso de credenciales recuerda que **una línea comentada (con #) no cuenta**, que
  es el tropiezo más habitual al rellenar config_local.py.
- Las claves de un sitio **no se usan nunca para otro**, aunque compartan familia de API
  (Gelbooru y Rule34.xxx): si faltan las de un sitio, se piden las suyas.

**Paquetes más ligeros**
- La compilación quita los recursos de *DevTools* del navegador incrustado (83 MB que la
  aplicación no usa): cada paquete publicado pesa eso menos.

---

## v0.1.5-beta.14 — 10 de octubre de 2026 · la beta definitiva (14.ª entrega)

**La comprobación de los sitios la resuelve la persona, no el programa**
- Antes el programa resolvía la prueba de trabajo por su cuenta. **Se ha quitado**: eso
  sería comportarse como un robot y no es lo correcto.
- Ahora, cuando un sitio pide su comprobación, se abre una **ventana con un navegador
  incrustado** (QtWebEngine) y **la resuelves tú**, como en tu navegador. En cuanto la
  superas, **la ventana se cierra sola** y la búsqueda o la descarga **siguen donde
  estaban** (se repiten con las cookies de esa sesión).
- Si no la superas, el aviso lo dice y la operación no continúa («la comprobación no se
  ha superado»); puedes volver a intentarlo.
- El navegador de esa ventana usa un **perfil propio y persistente**
  (~/.imaginteca/verificacion/), así que no se repite en cada búsqueda.
- Nota: incluir el navegador incrustado hace que las descargas del programa **ocupen
  más** (unos 130 MB), pero es lo que permite no comportarse como un robot.

---

## v0.1.5-beta.13 — 10 de octubre de 2026 · la beta definitiva (13.ª entrega)

**El programa resuelve las comprobaciones de los sitios que las piden**
- Algunos boorus (ATF Booru, ooru.allthefallen.moe) no entregan datos a programas:
  responden una página con una **prueba de trabajo**. Ahora Imaginteca **la resuelve
  sola** (pp/services/verificacion.py): busca el número cuya huella sha1 empieza por
  el prefijo pedido, espera el tiempo que indica la página, lo canjea por la cookie y
  **repite la petición**. A partir de ahí el sitio funciona con normalidad.
- Probado en vivo: la primera consulta tarda ~10 s y después llegan los datos (la cookie
  dura unos 7 días).
- Con esto, **ATF Booru vuelve a funcionar** (y cualquier otro sitio que use el mismo
  sistema).

---

## v0.1.5-beta.12 — 10 de octubre de 2026 · la beta definitiva (12.ª entrega)

**Avisos claros cuando un sitio bloquea**
- Cuando un booru responde con HTML en vez de datos, el aviso ahora incluye **el título
  de la página** («Verification», «Just a moment…», «Domain for sale»…) y dice que **no
  es un problema de las claves**. Así se distingue un bloqueo del sitio de un error de
  configuración.
- Documentado que **ATF Booru** (ooru.allthefallen.moe) pide comprobación anti-bot y
  no entrega datos a programas.

**Seguridad**
- Las claves de FBooru se han **sacado del archivo del repositorio** (pp/config.py,
  que es público): van en config_local.py, junto al programa.

---

## v0.1.5-beta.11 — 10 de octubre de 2026 · la beta definitiva (11.ª entrega)

**Arreglado: las claves de config_local.py no llegaban a los boorus**
- BOORU_SITES se arma **antes** de leer config_local.py, así que las entradas con
  uth se quedaban con los valores vacíos y la aplicación pedía unas credenciales que
  **sí** estaban escritas («Rule34.xxx necesita api_key, user_id»).
- Además, Rule34.xxx usa la **misma familia** que Gelbooru, así que se buscaban las
  constantes equivocadas: ahora se eligen **por sitio** (Rule34, Gelbooru, Danbooru…).
- El aviso de credenciales ahora dice **la ruta exacta** del archivo que lee el programa
  y recuerda que las claves de pp/config.py no cuentan en una copia compilada.
- Comprobado en vivo: Rule34.xxx responde con las claves del usuario.

---

## v0.1.5-beta.10 — 9 de octubre de 2026 · la beta definitiva (10.ª entrega)

**Búsqueda en las wikis de fandom, mucho más completa**
- Entra en **la página del personaje y en todas sus pestañas** (`Galería`, `Atuendos`,
  `Momentos…`, con las de cada temporada), no solo en su ficha.
- **Filtro de relevancia**: de las páginas ajenas solo se aceptan las imágenes que
  **mencionan** lo buscado (se acabaron las banderas, iconos y personajes que no van).
- **Búsqueda por concepto** (`traje de gala`, `pijama`, `traje de baño`, `ropa
  interior`, `poses`…): devuelve **los personajes que lo tienen** con sus imágenes.
  Con **comillas** es **exacta**; sin ellas, por palabras. Varios valores con comas.
- Arreglado un fallo silencioso: en las wikis en español las imágenes viven en el
  espacio `Archivo:` (no `File:`) y se descartaban **todas**; ahora se usa el número de
  espacio de nombres, así que funciona en cualquier idioma.

**Icono propio del asistente de Pixiv**
- `pixiv-token` deja de llevar el mismo icono que la aplicación: ahora tiene el suyo
  (azul de Pixiv con la «p», `assets/icon_pixiv.ico`), para distinguirlo en el escritorio
  y en la barra de tareas.

**Título de la ventana**
- Fuera el emoji del título (`Imaginteca — tu colección de imágenes`): el icono ya
  identifica la aplicación y el emoji se veía recargado.

---

## v0.1.5-beta.9 — 9 de octubre de 2026 · la beta definitiva (9.ª entrega)

**Atajo `F3` en la galería**
- Con el ratón parado sobre una **miniatura**, `F3` la abre **ampliada** (sin tener que
  seleccionarla ni hacer doble clic). Si no hay ninguna debajo del cursor, abre la que se
  está viendo, y el carrusel se coloca en ella. Funciona desde cualquier punto de la
  ventana.

---

## v0.1.5-beta.8 — 9 de octubre de 2026 · la beta definitiva (8.ª entrega)

**Propiedades de la imagen**
- Nuevo **📋 Propiedades de la imagen** (`Ctrl+I`) en el clic derecho sobre cualquier
  imagen, miniatura o en el visor: **todo lo que la plataforma sabe** de ella —
  título, descripción, etiquetas, favoritos, reposts, respuestas, vistas, guardados,
  comentarios, puntuación, fuentes, quién la subió y quién la aprobó, licencia, fecha,
  resolución…— con botón para **copiarlo todo**.
- Se adapta a cada familia: **boorus** (fuentes y etiquetas por categoría),
  **wikis** (descripción y licencia originales), **fediverso** y redes (favoritos,
  reposts, respuestas, vistas, guardados, citas) y un apartado con **el resto de datos
  del servicio**. En el fediverso se indica que los totales son del **servidor de
  origen**.

**Licencia corregida**
- El punto **7.1** ya describe la forma de entrega real: **instalador con asistente y
  ejecutable portable**, sin registro (**por ahora**) y sin coste (un aporte del autor a
  la comunidad); no se garantiza que los servicios de terceros sigan abiertos.

---

## v0.1.5-beta.7 — 9 de octubre de 2026 · la beta definitiva (7.ª entrega)

**Los tres gestores de paquetes, en el release**
- **Chocolatey** (`chocolatey/`) y **winget** (`winget/`) se suman a **Scoop**: los tres
  manifiestos se generan en cada versión (`scripts\empaquetadores\generar_manifiestos.py`)
  y se publican como adjuntos (`imaginteca.json`, `chocolatey-<versión>.zip`,
  `winget-<versión>.zip`), con sus guías de publicación.
- **El instalador deja el programa sin el aviso azul**: en el paso final quita la *marca
  de internet* (`Zone.Identifier`) de los ejecutables instalados.
- Como los ejecutables se firman **al compilar**, toda instalación recibe copias ya
  firmadas cuando hay certificado (la clave privada nunca sale del equipo de compilación:
  el instalador no firma, firma el flujo).

---

## v0.1.5-beta.6 — 9 de octubre de 2026 · la beta definitiva (6.ª entrega)

**Scoop, dentro del propio release**
- El manifiesto de Scoop (`imaginteca.json`) **viaja con el proyecto y con cada
  release**: el flujo lo regenera desde el `.zip` publicado (con su hash) y lo publica
  como adjunto, así que **no hay que crear ni mantener ningún repositorio aparte**.
- Instalación sin ventana azul, en **una sola orden**:
  `scoop install https://github.com/rgomezs2000/extractorfanarts/releases/latest/download/imaginteca.json`

**Firma automática en cada compilación**
- `scripts\build_exe.py` firma el ejecutable **solo** cuando hay certificado
  configurado (y avisa cuando no lo hay). En el flujo se firman el ejecutable, el
  asistente de Pixiv y el instalador.

---

## v0.1.5-beta.5 — 9 de octubre de 2026 · la beta definitiva (5.ª entrega)

**Informe de dependencias, corregido del todo**
- Los paquetes cuyo módulo no se llama igual que el paquete salían como «NO
  ENCONTRADO»: ahora se importa el módulo correcto (**Pillow se importa como `PIL`**) y
  se anota la versión de lo que va dentro al compilar (`dependencies.json`), así que
  **anyio** y compañía también muestran su versión. Resultado: **9 de 9** en desarrollo
  y en la copia empaquetada.

**Firma digital preparada**
- El flujo firma el **ejecutable**, el **asistente de Pixiv** y el **instalador** en
  cuanto haya certificado (`.pfx`, certificado instalado o **Microsoft Trusted
  Signing**), con `scripts\firmar_windows.ps1`.
- Sin certificado **no se firma nada** (y se dice): el aviso azul de SmartScreen solo
  desaparece con un certificado de una autoridad; uno autofirmado no sirve.

---

## v0.1.5-beta.4 — 9 de octubre de 2026 · la beta definitiva (4.ª entrega)

**El informe de dependencias ahora dice la verdad**
- Antes, dentro del paquete las dependencias salían como «NO instalado»: van
  **dentro** del ejecutable y no quedan sus metadatos. Ahora se comprueba
  **importando** cada módulo, se lee su versión real y se indica **de dónde sale**
  (`paquete`, `vendor` o el entorno), además de lo que anotó el flujo al empaquetar.
- Resumen final: **cuántas están presentes** (por ejemplo `9 de 9`) y el estado de los
  motores de IA.
- Comando nuevo en los tres sistemas: **`Imaginteca --dependencias`** (Windows:
  `Imaginteca.exe --dependencias`).

---

## v0.1.5-beta.3 — 9 de octubre de 2026 · la beta definitiva (3.ª entrega)

**Contenido y contenido adulto**
- Página nueva **[Qué se descarga](Contenido)**: fanarts, imágenes oficiales, **cómics
  y fancomics**, qué se guarda y qué **nunca** se descarga.
- Dentro, el apartado **NSFW (+18)**: qué significa, los **ratings**, los elementos que
  lo definen (fluidos, partes del cuerpo, atuendo explícito y sugestivo, actividades
  individuales y colectivas), **qué se puede extraer y qué no** y las condiciones de
  acceso.
- **Sin el 🔞 marcado nada se bloquea**: Buscar y Descargar siguen funcionando y el
  contenido adulto (`questionable`/`explicit`) se filtra; la lista negra y el bloqueo
  de plataformas de pago se aplican siempre, marques o no el 🔞.
- **Verificación de edad en el programa**: al marcar «🔞 Contenido adulto» y pulsar
  **Buscar** (o **Descargar**) se pide la **fecha de nacimiento** y se calcula la edad
  contra la fecha actual. Con **menos de 18 años no se busca ni se descarga nada**: se
  avisa y la casilla se desmarca. La fecha **no se guarda ni se envía**.

---

## v0.1.5-beta.2 — 9 de octubre de 2026 · la beta definitiva (2.ª entrega)

**Canal: desarrollo y producción**
- El programa distingue de dónde viene: **desarrollo** (código fuente o compilación
  propia) y **producción** (instalador, portable o consola, con la marca de release
  `release.json` que escribe el flujo).
- En **desarrollo** las actualizaciones quedan **desactivadas**: el programa, sus
  dependencias, la interfaz y el comando `--actualizar`. En **producción** se activan.
- En **Ayuda → Acerca de** se ve el canal de la copia.

**Comandos para los tres sistemas**
- Actualización: `Imaginteca --comprobar-actualizacion` y `Imaginteca --actualizar`
  (Windows y Unix), con la consola visible (Terminal en macOS y el emulador de
  terminal del escritorio en Linux).
- Instalación: instalador `.exe` en Windows (con modo silencioso), `.dmg` + copia a
  Aplicaciones en macOS y `apt install ./…deb` en Linux.

---

## v0.1.5-beta — 9 de octubre de 2026 · **la beta definitiva**

**Release oficial.** Desde esta versión los releases se publican como **oficiales**
(`prerelease: false`): `v0.1.5-beta` es la **última versión** del proyecto y la descarga
recomendada. Las anteriores (`v0.1.0-beta.1` … `v0.1.4-beta`) quedan como pre-release en
el historial. La versión sigue llamándose «beta», y el programa la reconoce por su
nombre.

**Lo que incluye** (todo lo de las betas anteriores, ya estable):
- **Tres modos de instalación**: portátil (`.zip` y `.tar.gz`), **instaladores con
  asistente** para Windows (Inno Setup), macOS (`.dmg`) y Linux (`.deb`), y **consola**.
- **Actualizaciones limpias**: conservan tus claves y borran la versión anterior, los
  temporales y la descarga; comandos `--comprobar-actualizacion` y `--actualizar`.
- **[Requisitos](Requisitos)**, **[Plataformas](Plataformas)** (redes, boorus y
  fandoms), **[Dependencias del sistema](Actualizaciones)** y copyright dinámico
  (`© 2026 InfoArte`).

---

## v0.1.4-beta — 9 de octubre de 2026

**Instaladores y modos de instalación**
- **Tres modos**: **portátil** (`.zip` y `.tar.gz`), **instalador con asistente**
  (`…-windows-installer.exe` con Inno Setup, `…-macos-installer.dmg` con acceso a
  Aplicaciones y `…-linux-installer.deb`) y **consola**.
- Los instaladores se generan en cada sistema dentro del flujo de compilación y se
  publican junto a los paquetes portátiles, con su `.sha256`.
- El instalador de Windows instala **por usuario** (sin administrador), deja accesos
  directos y desinstalador, y **conserva `config_local.py`** al actualizar.

**Actualizaciones limpias y comando de consola**
- `--comprobar-actualizacion` y `--actualizar`: mantenimiento desde la consola, con
  el proceso paso a paso (versión, paquete, descarga y huella SHA-256).
- La actualización ahora es **limpia**: descomprime aparte, conserva tus claves,
  reemplaza la carpeta entera y **borra la versión anterior, los temporales y el
  paquete descargado**.

---

## v0.1.3-beta — 9 de octubre de 2026

**Requisitos y dependencias**
- Página nueva **[Requisitos](Requisitos)** (en la wiki y en la ayuda del programa,
  **antes** de Instalación): qué hace falta para usarlo, qué hace falta para
  compilarlo y qué es opcional (el modo IA).
- **Ayuda → 🧩 Dependencias del sistema**: comprueba el **intérprete de Python**,
  los **paquetes esenciales** (frente a la última versión de PyPI) y los **motores
  de IA**; el informe sale **en pantalla y en la consola** y se pueden
  **actualizar de una vez**.

**Consola de mantenimiento**
- Al actualizar el programa **o sus dependencias** se abre una **consola propia**
  con el proceso y el informe, y **no se cierra ni se reinicia**: el programa se
  reinicia solo y la consola se queda para leerla.

---

## v0.1.2-beta — 9 de octubre de 2026

**Versión y propiedades del ejecutable**
- La versión pasa a **0.1.2-beta**.
- El ejecutable lleva **recurso de versión**: en «Propiedades → Detalles» se ven el
  **producto**, la **versión** y el **copyright** («{© 2026 InfoArte} · Todos los
  derechos reservados»), calculado con el año en curso al compilar.

**Copyright dinámico**
- El aviso es «© 2026 InfoArte» y pasa solo a «© 2026-2027 InfoArte» cuando cambia
  el año: en el programa, en la ayuda `F1` y en la documentación
  (`scripts\actualizar_copyright.py`).

---

## v0.1.0-beta.4 — 9 de octubre de 2026

**Sin datos personales**
- **El cuadro «Acerca de» ya no muestra nada personal**: ni nombre propio, ni
  correo, ni el repositorio. Aparece **InfoArte** y el contacto privado
  (**Discord `rgomezs2010`**).
- **El autor pasa a ser InfoArte** en todos los documentos y en la licencia, con
  el aviso **«© 2026 InfoArte · Todos los derechos reservados»**.
- Las rutas de «Acerca de» se muestran como `%USERPROFILE%…`, así que no aparece
  el nombre de usuario del equipo.
- **Nueva ventana de licencia**: «📜 Ver licencia completa» abre el texto entero
  dentro del programa (con botón para copiarlo), en vez de remitir a un archivo.
- **Aviso de copyright dinámico**: «© 2026 InfoArte» mientras el año en curso sea
  el de creación, y «© 2026-2027 InfoArte» en cuanto cambie el año. Lo calcula el
  programa en cada arranque (y `scripts\actualizar_copyright.py` lo pone al día en
  los documentos).

**Soporte de plataformas**
- Páginas nuevas en la wiki: **[Soporte de plataformas](Plataformas)**,
  **[Redes sociales](Redes-sociales)**, **[Boorus](Boorus)** y
  **[Fandoms](Fandoms)**: cada plataforma explicada —qué busca, qué claves pide,
  qué límites tiene y de qué va— y **las que vendrán**.
- La **guía del usuario** (y por tanto la ayuda `F1` del programa) incluye el mismo
  detalle, plataforma por plataforma.
- Las **[preguntas frecuentes](Preguntas-frecuentes)** responden de un vistazo qué
  **redes**, qué **boorus** y qué **fandoms** son compatibles.

---

## v0.1.0-beta.3 — 9 de octubre de 2026

**Documentación**
- **Redacción limpia y actualizada** de los tres documentos: la guía del usuario,
  el `LEEME-PRIMERO.txt` y el README técnico, con la versión al día.
- **La wiki con su foro es la fuente de más información**: los tres documentos
  enlazan con ella desde el principio.
- **Contacto privado unificado: Discord `rgomezs2010`** (fallos de seguridad y
  asuntos que no deban ser públicos). No se publica ningún correo.

**Wiki y foro**
- La **wiki está publicada**: documentación y **9 tableros de foro**, con índice,
  barra lateral y pie.
- El publicador de la wiki **protege las páginas del foro**: actualizar la
  documentación **ya no puede borrar los mensajes** de nadie.

---

## v0.1.0-beta.2 — 9 de octubre de 2026

**Interfaz y ayuda**
- **Barra de herramientas** con todas las funciones clave: Buscar (`Ctrl+B`),
  Descargar/Cancelar (`Ctrl+D`), Limpiar (`Ctrl+L`), Carpeta (`Ctrl+O`), Filtros,
  Ayuda (`F1`), Actualizaciones y Acerca de. Refleja el estado del formulario: no
  se puede pulsar nada que esté bloqueado.
- **Menús** Archivo y Ayuda, con los mismos accesos y sus atajos.
- **Ayuda dentro del programa (`F1`)**: el manual completo con **índice**,
  **buscador** y formato; lee la guía que viaja con la aplicación.
- **Acerca de**: versión instalada, autor, licencia, repositorio y **dónde queda
  todo** (registros, historial, claves, carpeta de salida).
- **Actualizador**: consulta las versiones publicadas, muestra **cuál tienes y
  cuál hay** (con fecha, peso y notas), descarga con progreso, **verifica el
  SHA-256**, se instala y **se reinicia solo**.

**Licencia**
- **Licencia v2**: la **garantía corre por cuenta del autor** (se corrigen sin
  coste los defectos reportados, se atienden los avisos y se responde de los daños
  directos causados por un defecto del programa). Se puede hacer valer por el foro
  de la wiki.

**Nombre del proyecto**
- El proyecto pasa a llamarse **Imaginteca** (antes «ExtractorFanarts»): imágenes,
  colección y preparación de datasets. El ejecutable, las carpetas de datos y los
  paquetes usan el nombre nuevo. Tus claves anteriores se siguen leyendo.

**Comunidad**
- **El foro vive en la wiki** (no en el repositorio): tableros de soporte técnico,
  fallos, ideas, plataformas y datasets, más las normas de convivencia. Se publica
  un mensaje editando la página, y todo queda junto a la documentación.
- La **garantía del autor** se hace valer dejando el reporte en el foro de la wiki.

**Calidad y limpieza**
- El modo IA ya no deja registros ni archivos temporales: el proceso queda limpio.
- Se garantiza que la IA **no cambie la paleta** de la obra.
- Se documenta el orden de reescalado y el tope de 8K con afilado calibrado
  (sin halos).

## v0.1.0-beta.1 — 8 de octubre de 2026

Primera versión pública (beta).

- Búsqueda y descarga desde **8 redes sociales, 14 booros y wikis de fandom**.
- Galería con visor, menú contextual (copiar, guardar, guardar como…).
- Conversión obligatoria a **WebP** con calidad ajustable.
- **Mejora de calidad** por tramos (hasta 699 px ×4, 700–799 px ×3, 800 px o más
  ×2, tope 8K) y **modo IA** con Real-ESRGAN / waifu2x.
- Filtros legales y éticos en el núcleo (lista negra, plataformas de pago,
  contenido adulto, licencias).
- Paquetes para **Windows, macOS y Linux** con huellas `.sha256`.
- **Licencia propietaria** (todos los derechos reservados).

---

*¿Falta algo en el historial? Dilo en el
[foro](https://github.com/rgomezs2000/extractorfanarts/wiki/Foro).*
