# Historial de versiones

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
