# 🌐 Redes sociales compatibles

**8 integradas**, cada una con su forma de buscar y sus credenciales. Aquí está
todo lo que hace y lo que no hace cada una.

## Resumen

| Red | Qué se busca | 🔑 Claves | Notas |
|---|---|---|---|
| **[Fediverso](#fediverso-mastodon--misskey--cherrypick)** (Mastodon / Misskey / CherryPick) | `@usuario`, `@usuario@servidor`, `#hashtags`, palabras | **No** | Cualquier instancia; detecta el software solo |
| **[Bluesky](#bluesky)** | palabras clave y `#hashtags` | **No** | API pública (atproto) |
| **[DeviantArt](#deviantart)** | palabras clave + **licencia** | Sí (app propia, gratis) | Puede filtrar por licencia |
| **[Tumblr](#tumblr)** | etiquetas de post | Sí (consumer key, gratis) | Solo posts públicos |
| **[Pixiv](#pixiv)** | obras de un autor, etiquetas | Sí (tu cuenta) | También animaciones *ugoira* |
| **[X / Twitter](#x--twitter)** | palabras y `#hashtags` | Sí (**de pago**) | Sin plan gratuito |
| **[Pinterest](#pinterest)** | pines y tableros | Sí (app aprobada) | Solo contenido al que tengas acceso |
| **[Newgrounds](#newgrounds)** | arte público del sitio | **No** | Lectura del sitio (más frágil) |

## Una por una

### Fediverso (Mastodon / Misskey / CherryPick)

La red descentralizada: **miles de servidores** independientes. No hay que elegir
instancia de antemano: escribe `@usuario@servidor` (por ejemplo
`@alguien@baraag.net`) y se consulta **su** servidor; o escribe `@usuario` y
rellena el campo *Instancia*.

- **Se puede buscar:** publicaciones de un usuario, y por `#hashtag` o palabras
  clave (si la instancia lo permite sin cuenta).
- **Claves:** no. La app **detecta el software** del servidor (Mastodon, Misskey o
  CherryPick) y usa su API pública.
- **Límites:** cada servidor pone los suyos (lo típico, unos 300 req/5 min por IP).
  En **Misskey**, buscar notas por texto suele requerir token, así que el programa
  busca por la **etiqueta** equivalente del texto que escribas.
- **Consejo:** si tu instancia favorita no responde, prueba con otra: el contenido
  del fediverso suele estar federado.

### Bluesky

Red social sobre **atproto**, con API pública de búsqueda.

- **Se puede buscar:** palabras clave y `#hashtags` (búsqueda de publicaciones).
- **Claves:** no.
- **Límites:** hay límites por IP documentados; el programa espacia las peticiones.
- **Nota:** la búsqueda puede devolver **coincidencias parciales**; el filtro de
  palabras clave de la app afina el resultado.

### DeviantArt

La comunidad de arte más antigua que sigue viva.

- **Se puede buscar:** por palabras clave, con **OAuth2 de aplicación** (sin que
  tengas que iniciar sesión).
- **Claves:** `DEVIANTART_CLIENT_ID` + `DEVIANTART_CLIENT_SECRET` de **tu** app en
  `deviantart.com/developers` (gratis, unos minutos).
- **Ventaja:** trae el **campo de licencia**, que se puede aprovechar con el filtro
  **⚖️ Solo licencia liberada**.
- **Nota:** el original solo se descarga si el artista lo permite.

### Tumblr

- **Se puede buscar:** publicaciones públicas por **etiqueta**.
- **Claves:** `TUMBLR_API_KEY` (una *consumer key* de `tumblr.com/oauth/apps`,
  gratis).
- **Límites:** moderados; el programa espera entre peticiones.
- **Nota:** es habitual que muchas entradas sean *reblogs*: la deduplicación por
  hash evita guardar la misma imagen dos veces.

### Pixiv

La mayor plataforma de ilustración japonesa. **No permite el acceso anónimo.**

- **Se puede buscar:** obras de un autor y por etiquetas, con **tu cuenta**.
- **Claves:** `PIXIV_REFRESH_TOKEN`, que consigues con el asistente
  **`pixiv-token.exe`** (ver [Claves y configuración](Claves-y-configuracion)).
  **El programa no guarda tu contraseña** y puedes revocar el acceso cuando quieras.
- **Extra:** soporta las **animaciones *ugoira*** (las convierte para que se vean).
- **Nota:** respeta las condiciones de la plataforma: hay obras de pago que el
  programa **descarta** por sus filtros.

### X / Twitter

- **Se puede buscar:** palabras y `#hashtags` por la **API v2**.
- **Claves:** `X_BEARER_TOKEN` de una app de desarrollador **de pago**: desde 2026
  no hay plan gratuito (se cobra por publicación leída).
- **Nota:** por eso la mayoría de usuarios no la activará; el adaptador está
  preparado y **apagado** hasta que pongas tu token.

### Pinterest

- **Se puede buscar:** pines y tableros, con la **API v5**.
- **Claves:** `PINTEREST_ACCESS_TOKEN` de una app **aprobada** y con permiso del
  usuario (OAuth).
- **Nota:** solo se accede a contenido al que tengas acceso legítimo; no se
  descarga nada reservado.

### Newgrounds

- **Se puede buscar:** el **arte público** del sitio.
- **Claves:** no.
- **Nota:** la API oficial está orientada a juegos, así que la lectura del arte se
  hace del propio sitio: funciona, pero es la más **frágil** ante cambios de la
  web.

## Próximamente

Candidatas estudiadas, de más a menos viable. **No hay fechas**: dependen de que su
API lo permita y de respetar sus condiciones.

| Red | Viabilidad | Por qué |
|---|---|---|
| **Reddit** | 🟢 Alta | API OAuth gratuita con límites y `User-Agent` propio |
| **ArtStation** | 🟡 Media | API pública limitada para perfiles y proyectos |
| **Instagram / Threads** | 🔴 Baja | Su API exige app revisada **y** token de usuario; el scraping está prohibido |
| **FurAffinity / Inkbunny** | 🔴 Baja | Sin API oficial: lectura del sitio detrás de Cloudflare (frágil) |
| **Pixiv Sketch / Pixivision** | 🔴 Baja | Requieren cuenta y no tienen API pública estable |

> Si quieres que alguna suba de prioridad, dilo en el
> **[foro · Plataformas y sitios](Foro-Plataformas)**.

---

**[← Soporte de plataformas](Plataformas)** · **[Boorus](Boorus)** ·
**[Fandoms](Fandoms)** · **[Claves y configuración](Claves-y-configuracion)**
