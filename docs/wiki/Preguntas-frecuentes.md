# Preguntas frecuentes

## Sobre el programa

**¿Qué es exactamente?**
Una aplicación de escritorio para **reunir, ordenar y preparar una colección
personal de imágenes**: buscar en redes, booros y wikis, revisar en una galería,
guardar en WebP y, si quieres, mejorar la calidad o preparar un
[dataset](Datasets-IA).

**¿Es gratis?**
Sí. No hay que pagar, ni registrarse, ni hay versión «premium». Es **propietario**
(no software libre) y su código fuente no se publica: ver [Licencia](Licencia).

**¿Funciona sin configurar nada?**
Sí: fediverso, Bluesky, wikis, Newgrounds y la mayoría de booros públicos
funcionan sin claves.

**¿Necesito tarjeta gráfica?**
No. El **🤖 Modo IA** la aprovecha si la tienes (usa Vulkan), pero sin ella todo
funciona: la mejora de calidad tiene un modo clásico (Lanczos).

**¿En qué idioma está?**
En español.

**¿Se puede usar para otro tipo de arte o de imágenes?**
Sí: técnicamente es un archivador de imágenes. Las fuentes integradas son arte y
fanart de esas plataformas.

## Sobre las plataformas

> El detalle de cada una (qué busca, qué claves pide y qué límites tiene) está en
> **[Soporte de plataformas](Plataformas)**.

**¿Qué redes sociales son compatibles?**
Estas **8**: **Fediverso** (cualquier servidor de Mastodon, Misskey o CherryPick),
**Bluesky**, **DeviantArt**, **Tumblr**, **Pixiv**, **X (Twitter)**,
**Pinterest** y **Newgrounds**. Sin claves funcionan el fediverso, Bluesky y
Newgrounds; las demás piden credenciales tuyas (X, además, de pago).
→ **[Ver las redes una por una](Redes-sociales)** · *Próximamente: Reddit,
ArtStation, Instagram/Threads, FurAffinity.*

**¿Qué boorus son compatibles?**
Estos **14**: **Safebooru**, **Gelbooru**, **Rule34.xxx**, **The Big ImageBoard**,
**Xbooru**, **Hypnohub**, **Danbooru**, **Safebooru (Donmai)**, **Yande.re**,
**Konachan**, **Konachan (SFW)**, **Derpibooru**, **ATF Booru** y **Rule34
Paheal**. **12 no piden nada**; solo Gelbooru y Rule34.xxx aceptan una clave
gratuita (y funcionan igual sin ella).
→ **[Ver los boorus uno por uno](Boorus)** · *Próximamente: e621, Rule34.us,
Realbooru, Sakugabooru, Zerochan.*

**¿Qué fandoms son compatibles?**
**Todos los que estén en Fandom.com**, además de **cualquier wiki MediaWiki** (por
su URL): anime y manga, videojuegos, animación occidental, comics y superhéroes,
cine, TV, libros, música… No hay lista cerrada: se busca por **franquicia**,
**personaje** o **concepto**, y las imágenes salen de la propia wiki. En la página
tienes los fandoms más buscados por categoría, con lo que encuentras en cada uno.
→ **[Ver fandoms y wikis](Fandoms)**

**¿Y si la plataforma que quiero no está?**
Pídela en el **[foro · Plataformas y sitios](Foro-Plataformas)**: las peticiones
con más interés se estudian primero, y las de familias ya soportadas (más booros
Gelbooru, Danbooru o Moebooru) son las más rápidas de añadir.

## Sobre el uso y lo legal

**¿Es legal?**
La herramienta lo es: descarga **con tus credenciales**, respeta las condiciones
de cada plataforma, espacia las peticiones y **no evade CAPTCHAs ni inicios de
sesión**. Lo que descargues y lo que hagas con ello **es tu responsabilidad**: la
mayoría del fanart **no** tiene licencia liberada.

**¿Puedo redistribuir o vender lo que descargue?**
No sin permiso de sus autores. Usa los campos `licencia` y `artista` del `.json`
y respeta las listas de «no entrenar» de algunos autores.

**¿Puedo entrenar un modelo con esto?**
Es una de sus funciones ([Datasets para IA](Datasets-IA)), pero entrena con
material que puedas usar y **cita a los artistas**. Si quieres quedarte solo con
obras de licencia abierta, activa **⚖️ Solo licencia liberada**.

**¿Por qué no descarga de X sitio o de contenido de pago?**
Porque el programa lleva **filtros de ética y legalidad en el núcleo**: bloquea
plataformas de pago (Patreon, Fanbox, OnlyFans…), contenido prohibido y, por
defecto, contenido adulto.

## Sobre mis datos

**¿Se envían mis claves a algún servidor?**
**No.** No hay servidor propio ni telemetría: cada petición va directamente a la
plataforma que consultas.

**¿Dónde se guarda todo?**
Imágenes en tu carpeta de salida (por defecto `Imágenes\Imaginteca`, o
`~/Pictures/Imaginteca`), y en `~/.imaginteca`: registro del día, historial y (si
quieres) tus claves.

**¿Puedo usar la misma carpeta en varios equipos?**
Puedes copiar el programa y tu `config_local.py`, pero el historial y los registros
son locales.

**¿Por qué todo se guarda en WebP?**
Porque da mucha calidad con archivos pequeños y admite transparencia. Si tu
entrenador no lo acepta, convierte la carpeta a PNG/JPG por lotes.

## Sobre el proyecto

**¿Puedo proponer cosas o reportar fallos?**
Sí, y se agradece: [foro](Foro-y-comunidad),
[fallos](https://github.com/rgomezs2000/extractorfanarts/wiki/Foro-Fallos) o
[Soporte técnico](Soporte-tecnico).

**¿Aceptan código o traducciones del programa?**
Código no (es propietario). Textos de la wiki, reportes e ideas, sí.

**Si el programa falla, ¿quién responde?**
**El autor.** La garantía corre por cuenta del autor: los defectos reportados se
corrigen sin coste y se publica la versión corregida; también responde de los
**daños directos** que un defecto cause en tus archivos. Ver
[Soporte técnico](Soporte-tecnico) y [Licencia](Licencia).

**¿Cómo me entero de las versiones nuevas?**
Con **🔄 Actualizaciones** dentro del programa (o mirando
[Releases](https://github.com/rgomezs2000/extractorfanarts/releases)).

---

**¿No está tu pregunta?** Pregúntala en el
**[foro](https://github.com/rgomezs2000/extractorfanarts/wiki/Foro)**: con eso
también ayudas a quien venga detrás.
