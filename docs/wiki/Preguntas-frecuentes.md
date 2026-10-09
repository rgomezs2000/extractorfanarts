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
