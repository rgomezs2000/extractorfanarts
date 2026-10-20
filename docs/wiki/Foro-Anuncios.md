# 📣 Foro · Anuncios

**Para qué:** avisos del proyecto: **versiones nuevas**, cambios importantes,
plataformas que se caen y arreglos.

> **Solo lectura para el resto:** esta página la actualiza el autor. Si quieres
> comentar algo de un anuncio, hazlo en el tablero que corresponda —normalmente
> [Soporte técnico](Foro-Soporte-tecnico) o [Ideas](Foro-Ideas)— mencionando el
> anuncio.

## Cómo enterarte de las versiones nuevas

- **Dentro del programa:** 🔄 **Actualizaciones** (o **Ayuda → Actualizaciones**).
  Detecta la versión nueva, la descarga, **verifica el SHA-256** y la instala
  reiniciándose sola. Ver [Actualizaciones](Actualizaciones).
- **En el repositorio:** [Releases](https://github.com/rgomezs2000/extractorfanarts/releases).
- **Aquí:** en esta página.

---

## Anuncios

### 2026-10-11 · v0.1.5-beta.56 — la beta definitiva (56.ª entrega)

- **Motor PyTorch opcional** (`AI_ENGINE = "torch"`): usa tu torch y elige solo CUDA,
  DirectML, TensorRT, MPS o CPU. Los pesos se descargan la primera vez.

### 2026-10-11 · v0.1.5-beta.55 — la beta definitiva (55.ª entrega)

- Ajustado el umbral de artefactos para que el propio reescalado no marque la imagen como
  defectuosa. Aclarado el estado de DirectX/DirectML (compatible, pero no incluido).

### 2026-10-11 · v0.1.5-beta.54 — la beta definitiva (54.ª entrega)

- **Elige motor de IA**: Real-ESRGAN o waifu2x (ambos Vulkan: NVIDIA, AMD/ATI, Intel) con
  `AI_ENGINE`, y el resultado indica cuál se usó.

### 2026-10-11 · v0.1.5-beta.53 — la beta definitiva (53.ª entrega)

- **Transparencia del motor**: el registro y el autoexamen dicen qué modelo de IA y qué
  tarjeta gráfica se están usando.

### 2026-10-11 · v0.1.5-beta.52 — la beta definitiva (52.ª entrega)

- **IA para anime/cartoon**: modelo **RealESRGAN_x4plus_anime_6B** y motor **Vulkan**, que
  vale para NVIDIA, AMD/ATI e Intel. `AI_GPU` permite elegir tarjeta.

### 2026-10-11 · v0.1.5-beta.51 — la beta definitiva (51.ª entrega)

- **Inkbunny** entra como red social: búsqueda por texto o `@usuario` con su API oficial.
  Requiere cuenta + «API Access» activado y las claves en `config_local.py`.

### 2026-10-11 · v0.1.5-beta.50 — la beta definitiva (50.ª entrega)

- **Adiós al aviso «zonas quemadas»** en stickers y dibujos con fondo blanco: se mide, pero
  no es un defecto ni bloquea nada.

### 2026-10-11 · v0.1.5-beta.49 — la beta definitiva (49.ª entrega)

- **Primero reescalar y después corregir** (antes era al revés y el reescalado difuminaba
  la reparación), con **realfinado final** proporcional al aumento. 153 px → 2448 px.

### 2026-10-11 · v0.1.5-beta.48 — la beta definitiva (48.ª entrega)

- **Enlaces rojos del wiki**: si el archivo no existe, no se ofrece (antes aparecía y daba
  404 al descargar).

### 2026-10-11 · v0.1.5-beta.47 — la beta definitiva (47.ª entrega)

- **Con IA ya amplía**: el guardado del WebP reintenta si el archivo está ocupado un
  instante (era lo que dejaba la imagen «como estaba» al usar Modo IA).

### 2026-10-11 · v0.1.5-beta.46 — la beta definitiva (46.ª entrega)

- **Todos los resultados**: sin «Limitar cantidad» se piden hasta 10000 (antes 100);
  Safebooru «kuromi» da ahora 1112. Con el límite marcado, hasta 100000.

### 2026-10-11 · v0.1.5-beta.45 — la beta definitiva (45.ª entrega)

- El **autoexamen** (`--selftest`) muestra y verifica los tramos de ampliación, para saber
  si el ejecutable que abres es el recién compilado.

### 2026-10-11 · v0.1.5-beta.44 — la beta definitiva (44.ª entrega)

- **El ancho manda**: el mínimo de 1600 px se calcula sobre el ancho (y se aplica a los dos
  lados), así las imágenes verticales también ganan ancho. 228×600 → 1824×4800.

### 2026-10-11 · v0.1.5-beta.43 — la beta definitiva (43.ª entrega)

- **Pequeñas, más grandes**: hasta 599 px el factor crece para llegar al menos a 1600 px
  (228 px → 1824 px con 8x; 120 px → 1920 px con 16x). 600–799 sigue 3x y 800+ sigue 2x.

### 2026-10-11 · v0.1.5-beta.42 — la beta definitiva (42.ª entrega)

- La plantilla de configuración documenta las claves de Danbooru, DeviantArt y Pinterest.

### 2026-10-11 · v0.1.5-beta.41 — la beta definitiva (41.ª entrega)

- **Danbooru con cuenta**: ya manda login + pi_key y descarga el **original**, no la
  versión reducida.

### 2026-10-11 · v0.1.5-beta.40 — la beta definitiva (40.ª entrega)

- **Descarga siempre del original**: se prueba ile_url (el original) y, si no está, las
  alternativas en orden; nunca se entrega la muestra salvo que no exista nada mejor (y se
  avisa).

### 2026-10-11 · v0.1.5-beta.39 — la beta definitiva (39.ª entrega)

- **tbib.org ya no pide captcha**: era un falso positivo (servía JSON como 	ext/html y la
  palabra «captcha» aparecía en el contenido). Se acepta el JSON y solo se avisa cuando hay
  señales reales de verificación.

### 2026-10-11 · v0.1.5-beta.38 — la beta definitiva (38.ª entrega)

- **Nada se entrega en mal estado**: se repara (ruido, bloques, nitidez) y se amplía; los
  archivos truncados se recuperan; si no hay arreglo, se descartan. Siempre en **WebP**,
  nunca jpg ni png.

### 2026-10-11 · v0.1.5-beta.37 — la beta definitiva (37.ª entrega)

- **Calidad medida, no adivinada**: antes de ampliar se comprueba nitidez, ruido, bloques
  de compresión y zonas quemadas. Si hay defectos serios no se amplía (no tiene sentido
  agrandar el ruido); si es plana se guarda sin pérdida. WebP nunca por debajo de 90.

### 2026-10-11 · v0.1.5-beta.36 — la beta definitiva (36.ª entrega)

- **X con FxTwitter**: filtra la galería de un usuario con palabra clave o #hashtag, y
  reintenta solo si el servicio falla a ratos.

### 2026-10-11 · v0.1.5-beta.35 — la beta definitiva (35.ª entrega)

- **X (Twitter) sin claves**: galería de un usuario y posts sueltos vía **FxTwitter**, con
  retardos entre peticiones para no comportarse como un bot. La búsqueda por palabra sigue
  sin ser posible (limitación de X).

### 2026-10-11 · v0.1.5-beta.34 — la beta definitiva (34.ª entrega)

- **Pinterest**: la plantilla de config_local.py trae las claves listas y el aviso explica
  cómo sacar el token OAuth y para qué sirve el código de país.

### 2026-10-11 · v0.1.5-beta.33 — la beta definitiva (33.ª entrega)

- **DeviantArt**: el token se renueva solo (antes caducaba a la hora y daba «401
  autenticación rechazada» hasta reiniciar el programa).

### 2026-10-11 · v0.1.5-beta.32 — la beta definitiva (32.ª entrega)

- **DeviantArt**: el aviso dice ahora dónde poner las claves (tu config_local.py) y la
  plantilla trae las líneas listas para pegar el client_id y el client_secret.

### 2026-10-11 · v0.1.5-beta.31 — la beta definitiva (31.ª entrega)

- **Avisos clicables**: al pulsar uno se abre en una ventanita y queda leído.
- **«Estado de las redes sociales»** pasa a **Ayuda** (tras Dependencias) y al clic derecho
  del icono; fuera del menú de la campana.
- **Arreglado** el error de JSON vacío en **Safebooru, Rule34.xxx** y otros: un tag sin
  resultados ahora dice «la búsqueda no trajo resultados».

### 2026-10-11 · v0.1.5-beta.30 — la beta definitiva (30.ª entrega)

- **Se retira el filtro** de advertencias (dejaba fuera contenido que antes pasaba). Se
  mantienen los apartados de **Propiedades**: Contenido adulto y Advertencias, solo cuando
  amerita.

### 2026-10-11 · v0.1.5-beta.29 — la beta definitiva (29.ª entrega)

- **Propiedades** con apartados propios de **Contenido adulto** y **Advertencias** (solo
  cuando amerita; SFW sin flags).
- **Nuevo filtro** «⚠️ Con advertencias» (con «Contenido adulto» marcado): sin él se omiten
  las imágenes con avisos.

### 2026-10-11 · v0.1.5-beta.28 — la beta definitiva (28.ª entrega)

- **Arreglado**: la ventana de comprobación ya no se cierra «en falso»; prueba la sesión
  desde el navegador y solo continúa si el sitio responde. Además el programa usa el
  **mismo User-Agent** con el que se resolvió, y hay botón **🔄 Recargar**.
- El programa **nunca** resuelve la comprobación solo: la resuelve la persona.

### 2026-10-11 · v0.1.5-beta.27 — la beta definitiva (27.ª entrega)

- **Arreglado**: con la comprobación superada, la búsqueda **sigue** (antes se cortaba con
  «la sesión no sirve todavía» porque una comprobación previa era demasiado estricta).

### 2026-10-11 · v0.1.5-beta.26 — la beta definitiva (26.ª entrega)

- El **icono de la bandeja alterna**: minimiza si la ventana se ve y la abre como estaba si
  está minimizada. El menú muestra «Minimizar Imaginteca» o «Abrir Imaginteca» según toque.

### 2026-10-11 · v0.1.5-beta.25 — la beta definitiva (25.ª entrega)

- **Menú del icono de las notificaciones**: abrir (restaura o maximiza), buscar, descargar,
  cancelar, ayuda, acerca de, actualizaciones, dependencias y salir, con sus atajos.

### 2026-10-11 · v0.1.5-beta.24 — la beta definitiva (24.ª entrega)

- El **estado de plataformas** incluye ya **boorus y wikis de fandom**: 22 plataformas en
  total, con columna de tipo.

### 2026-10-11 · v0.1.5-beta.23 — la beta definitiva (23.ª entrega)

- **Notificaciones**: búsquedas, descargas, errores, versiones nuevas y plataformas caídas,
  con contador en la campana 🔔 y —minimizada— en el sistema y en la insignia del icono.
- **Ayuda › 📡 Estado de las redes sociales**: comprueba si cada red está operativa.

### 2026-10-11 · v0.1.5-beta.22 — la beta definitiva (22.ª entrega)

- **Instaladores con el icono típico de cada sistema** (caja con flecha azul en Windows,
  disco plateado en macOS, paquete de cartón en Linux). La 21 falló al compilar el
  instalador por un comentario con # en el guion de Inno Setup: corregido.

### 2026-10-11 · v0.1.5-beta.21 — la beta definitiva (21.ª entrega)

- Los **instaladores** ya llevan el icono típico de instalación de cada sistema: la caja
  con flecha azul (Windows), el disco plateado (macOS) y el paquete de cartón (Linux).

### 2026-10-11 · v0.1.5-beta.20 — la beta definitiva (20.ª entrega)

- **Arreglado el bucle**: tras resolver la comprobación, la búsqueda **continúa sola** y las
  imágenes aparecen en Imaginteca. Si la sesión aún no sirviera, se avisa; y si el sitio la
  pide más de 3 veces seguidas, se detiene con una explicación.

### 2026-10-11 · v0.1.5-beta.19 — la beta definitiva (19.ª entrega)

- **Arreglado**: la ventana de comprobación ya abre también en la **versión compilada**
  (faltaba QtWebChannel en el paquete). El --selftest ahora lo comprueba.

### 2026-10-10 · v0.1.5-beta.18 — la beta definitiva (18.ª entrega)

- **Arreglado**: la ventana para resolver la comprobación **ya se abre** (antes el aviso
  salía como «Error inesperado» y no aparecía la ventana).

### 2026-10-10 · v0.1.5-beta.17 — la beta definitiva (17.ª entrega)

- La **ventana para resolver la comprobación** ya sale en **cualquier sitio** que la pida
  (Cloudflare, CAPTCHA, Turnstile, DDoS-Guard, prueba de trabajo), no solo en ATF Booru.

### 2026-10-10 · v0.1.5-beta.16 — la beta definitiva (16.ª entrega)

- Paquetes **83 MB más ligeros** (fuera los recursos del inspector del navegador, ya en
  las descargas publicadas).
- **Arreglado**: las claves de **ATF Booru** (FBOORU_API_KEY / FBOORU_LOGIN) ya se
  encuentran; y una línea comentada con # no cuenta (el aviso lo recuerda).

### 2026-10-10 · v0.1.5-beta.15 — la beta definitiva (15.ª entrega)

- **Arreglado**: las claves de **ATF Booru** (FBOORU_API_KEY / FBOORU_LOGIN) ya se
  encuentran, aunque el sitio se llame distinto a las constantes.
- Paquetes **83 MB más ligeros** (fuera los recursos del inspector del navegador).

### 2026-10-10 · v0.1.5-beta.14 — la beta definitiva (14.ª entrega)

- **La comprobación de los sitios la resuelves tú**: se abre una ventana con navegador,
  la superas y la operación continúa sola. El programa **ya no la resuelve por su
  cuenta** (no debe comportarse como un robot).

### 2026-10-10 · v0.1.5-beta.13 — la beta definitiva (13.ª entrega)

- **ATF Booru vuelve a funcionar**: el programa **resuelve sola** la comprobación (prueba
  de trabajo) que pide el sitio antes de entregar datos.

### 2026-10-10 · v0.1.5-beta.12 — la beta definitiva (12.ª entrega)

- Los avisos de «HTML en lugar de JSON» ahora dicen **qué página devolvió el sitio** y
  aclaran que no es culpa de las claves.
- Las claves van siempre en config_local.py (fuera del repositorio).

### 2026-10-10 · v0.1.5-beta.11 — la beta definitiva (11.ª entrega)

- **Arreglado**: las claves puestas en config_local.py ya llegan a los boorus (antes se
  pedían credenciales que sí estaban escritas). El aviso dice ahora **dónde** hay que
  ponerlas.

### 2026-10-09 · v0.1.5-beta.10 — la beta definitiva (10.ª entrega)

- **Wikis de fandom**: la búsqueda entra en **la ficha y en todas las pestañas**
  (Galería, Atuendos, Momentos…), filtra lo que no menciona lo buscado y admite
  **conceptos** (`pijama`, `traje de baño`…) con búsqueda **exacta** entre comillas.
- **Icono propio** para el asistente de Pixiv y **título sin emoji**.

### 2026-10-09 · v0.1.5-beta.9 — la beta definitiva (9.ª entrega)

- **`F3`**: abre ampliada la **miniatura sobre la que esté el ratón** (o la que estés
  viendo). Cómodo para revisar imágenes de ejemplo una a una.

### 2026-10-09 · v0.1.5-beta.8 — la beta definitiva (8.ª entrega)

- **📋 Propiedades de la imagen** (`Ctrl+I`, con el clic derecho): título, descripción,
  etiquetas, favoritos, reposts, respuestas, vistas, guardados, comentarios, puntuación,
  fuentes, quién la subió o aprobó, licencia… y el resto de datos del servicio.
- **Licencia corregida** en el punto 7.1: ya hay **instalador y portable**, sin registro
  y sin coste.

### 2026-10-09 · v0.1.5-beta.7 — la beta definitiva (7.ª entrega)

- **Chocolatey y winget** se suman a Scoop: los tres manifiestos viajan en el release.
- **Instalando con el asistente no aparece el aviso azul**: el instalador quita la marca
  de internet de los ejecutables que deja.

### 2026-10-09 · v0.1.5-beta.6 — la beta definitiva (6.ª entrega)

- **Scoop va dentro del release**: `imaginteca.json` se publica como adjunto de cada
  versión, así que instalar sin el aviso de Windows es **una sola orden** (sin crear
  ningún repositorio aparte).
- **La firma es automática**: cada compilación firma el ejecutable si hay certificado.

### 2026-10-09 · v0.1.5-beta.5 — la beta definitiva (5.ª entrega)

- **Informe de dependencias completo**: se corrigió el nombre de importación
  (`Pillow` → `PIL`) y se anota lo que va dentro al compilar. Ahora dice **9 de 9** en
  desarrollo y en la copia empaquetada.
- **Firma digital cableada**: ejecutable, asistente e instalador se firman solos en
  cuanto haya certificado (incluido Microsoft Trusted Signing). Sin certificado no se
  firma nada: el aviso de SmartScreen solo lo quita un certificado de una autoridad.

### 2026-10-09 · v0.1.5-beta.4 — la beta definitiva (4.ª entrega)

- **Informe de dependencias arreglado**: ya distingue la versión **en uso** de cada
  paquete y **de dónde sale** (paquete, vendor o entorno). Antes, en la copia
  empaquetada, aparecía «NO instalado» aunque las dependencias van dentro.
- **Comando nuevo**: `Imaginteca --dependencias` (también en macOS y Linux).

### 2026-10-09 · v0.1.5-beta.3 — la beta definitiva (3.ª entrega)

- **Nueva página [Qué se descarga](Contenido)**: fanarts, imágenes oficiales, cómics y
  fancomics, y el apartado **NSFW (+18)** completo (ratings, qué lo define, qué se
  extrae y qué no).
- **Verificación de edad**: con el 🔞 marcado, al **Buscar** o **Descargar** se pide la
  fecha de nacimiento; **menores de 18 no buscan ni descargan** contenido adulto. Tu
  fecha no se guarda ni se envía a ningún sitio.

### 2026-10-09 · v0.1.5-beta.2 — la beta definitiva (2.ª entrega)

- **Desarrollo vs producción**: las copias de desarrollo (código fuente o
  compilaciones propias) tienen las **actualizaciones desactivadas**; las de
  producción (instalador, portable y consola) las tienen **activadas**.
- **Comandos para Windows, macOS y Linux**: `--comprobar-actualizacion` y
  `--actualizar`, más los comandos de instalación de cada sistema.

### 2026-10-09 · v0.1.5-beta — la beta definitiva

- **`v0.1.5-beta` se publica como release OFICIAL** (ya no como pre-release): es la
  última versión del proyecto y la descarga recomendada.
- Reúne todo lo de las betas anteriores: tres modos de instalación, actualizaciones
  limpias, requisitos, dependencias del sistema, plataformas documentadas y copyright
  dinámico.

### 2026-10-09 · v0.1.4-beta

- **Tres modos de instalación**: portátil (`.zip` y `.tar.gz`), **instalador con
  asistente** para Windows, macOS y Linux, y **consola**.
- **Actualizaciones limpias**: al actualizar no queda nada viejo (se borran la
  versión anterior, los temporales y la descarga) y **tus claves se conservan**.
- Nuevo comando de consola: `Imaginteca --comprobar-actualizacion` y
  `Imaginteca --actualizar`.

### 2026-10-09 · v0.1.3-beta

- **[Requisitos](Requisitos)**, la página nueva: qué necesitas para usarlo y qué
  para compilarlo (y que el modo IA es opcional).
- **Ayuda → 🧩 Dependencias del sistema**: estado de Python, de los paquetes
  esenciales y de los motores de IA, con opción de **actualizarlos de una vez**.
- **La consola de mantenimiento ya no se cierra**: al actualizar el programa o sus
  dependencias se abre una consola con el informe que permanece abierta (el
  programa sí se reinicia).

### 2026-10-09 · v0.1.2-beta

- Nueva **versión 0.1.2-beta**.
- El **ejecutable muestra su versión y su copyright** en las propiedades del
  archivo (Detalles).
- **Copyright dinámico**: «© 2026 InfoArte» y, al cambiar el año,
  «© 2026-2027 InfoArte».

### 2026-10-09 · v0.1.0-beta.4

- **«Acerca de» sin datos personales**: **InfoArte** y **Discord `rgomezs2010`**,
  sin nombre propio, sin correo y sin el repositorio.
- **Nueva ventana de licencia** dentro del programa («📜 Ver licencia completa»).
- El autor pasa a ser **InfoArte** en la documentación y en la licencia.
- **Copyright dinámico**: el aviso pasa solo de «© 2026 InfoArte» a
  «© 2026-2027 InfoArte» cuando cambie el año; no hay que tocar nada.
- **Soporte de plataformas documentado**: [redes sociales](Redes-sociales),
  [boorus](Boorus) y [fandoms](Fandoms) **uno por uno**, con lo que busca cada una,
  sus claves, sus límites y las que vendrán. También en la ayuda del programa
  (`F1`) y resumido en las [preguntas frecuentes](Preguntas-frecuentes).

### 2026-10-09 · v0.1.0-beta.3

- **Documentación reescrita y al día**: guía del usuario, `LEEME-PRIMERO.txt` y
  README técnico, con la versión nueva y enlazados con esta wiki.
- **El foro ya está abierto** (estás en él): soporte técnico, fallos, ideas,
  plataformas, datasets, presentaciones y anuncios.
- **Contacto privado: Discord `rgomezs2010`**.
- El publicador de la wiki **protege los mensajes del foro** al actualizar la
  documentación.

### 2026-10-09 · v0.1.0-beta.2

- **Barra de herramientas** con lo esencial y lo de apoyo, menús **Archivo** y
  **Ayuda**, y atajos (`Ctrl+B`, `Ctrl+D`, `Ctrl+L`, `Ctrl+O`, `F1`).
- **Ayuda dentro del programa** con `F1`: el manual completo, con **índice** y
  buscador.
- **Acerca de**: tu versión, el autor, la licencia y dónde queda todo.
- **Actualizador**: busca la versión nueva, la descarga, comprueba la huella y la
  instala reiniciando.
- **Licencia v2**: la **garantía corre por cuenta del autor**.
- **Este foro**: la comunidad pasa a vivir en la wiki.
- El proyecto se llama **Imaginteca** (antes «ExtractorFanarts»).

### 2026-10-08 · v0.1.0-beta.1 — primera versión pública

- Búsqueda y descarga desde **8 redes sociales, 14 booros y wikis de fandom**.
- Galería con visor y guardado individual por clic derecho.
- Todo en **WebP**, con **mejora de calidad** por tramos y **modo IA**
  (Real-ESRGAN / waifu2x).
- Filtros legales y éticos en el núcleo.
- Paquetes para **Windows, macOS y Linux** con huella `.sha256`.

*El detalle completo está en [Historial de versiones](Historial-de-versiones).*

---

**[← Volver al foro](Foro)** · [Historial de versiones](Historial-de-versiones) ·
[Actualizaciones](Actualizaciones)
