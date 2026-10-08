# Informe de factibilidad — Extractor de fanarts de escritorio (Python, Windows)

**Fecha:** 2026-10-06 · **Estado:** Solo análisis de factibilidad, sin desarrollo iniciado.
**Nota:** Este documento no es asesoría legal; las secciones legales son orientación general basada en fuentes públicas.

---

## 1. Veredicto ejecutivo

**VIABLE, con alcance ajustado por plataforma.** De las 11 plataformas solicitadas:

| Viabilidad | Plataformas |
|---|---|
| ✅ Alta (sin login, con API pública) | Mastodon, Misskey/CherryPick, Bluesky, Safebooru, wikis de fandoms (Fandom/MediaWiki) |
| 🟡 Media (sin login de usuario, pero con registro gratuito de app/clave) | Gelbooru, Rule34.xxx, Danbooru, DeviantArt, Tumblr |
| 🔴 Baja / no factible sin login o sin pago | Pixiv (exige cuenta), X/Twitter (sin plan gratis desde feb-2026), Pinterest (API restringida + scraping prohibido), Newgrounds (sin API pública de arte) |

Puntos críticos honestos:

1. **"Material liberado" no es verificable automáticamente en redes sociales.** Casi ningún post de X/Mastodon/Bluesky lleva metadatos de licencia. Un programa ético solo puede descargar automáticamente lo que tenga licencia explícita y permisiva (CC0, CC-BY, etc.) o autorización del artista. Eso reduce el volumen, pero es lo que pide el requisito.
2. **"Sin login" es incompatible con Pixiv, X y Pinterest** (y con Newgrounds en la práctica). No hay forma legítima de evitarlo: eludir logins o protecciones anti-bot violaría los ToS y, en varias jurisdicciones, normas anti-elusión de medidas técnicas.
3. **"Que no se bloquee" no se puede garantizar al 100 %.** Lo alcanzable éticamente es *minimizar* el riesgo (límites por sitio, pausas, backoff, respeto de robots.txt) y *recuperarse* con gracia cuando ocurra. La evasión activa de bloqueos (CAPTCHAs, Cloudflare) queda descartada por ética y legalidad.
4. **Plataformas de pago y contenido premium quedan excluidas por diseño:** Patreon, Pixiv Fanbox, Unifans, Fansky, OnlyFans, Fansly y cualquier sección exclusiva/premium no son fuentes del programa ni objetivo de extracción (ver §4.5).

---

## 2. Aclaración técnica: "Django" + "Windows Forms" es una mezcla contradictoria

- **Windows Forms (WinForms)** es un framework de UI de .NET. En Python no existe WinForms nativo; las opciones reales para una "ventana tradicional de escritorio" son:
  - **PySide6 / PyQt6** *(recomendado)*: ventanas nativas, modernas, maduro, con soporte para hilos + descargas en segundo plano.
  - **pythonnet (`clr`)** + `System.Windows.Forms`: WinForms *literal* de .NET desde Python. Técnicamente posible, pero incómodo de mantener y poco recomendado.
  - Tkinter (tradicional, limitado estéticamente), wxPython, Dear PyGui.
- **Django es un framework web (servidor HTTP + ORM + plantillas).** No "corre dentro" de una ventana de escritorio. Tres caminos posibles:
  - **(a) Omitir Django** y usar SQLite + SQLAlchemy/Peewee. *Recomendado*: mismo lenguaje, menos piezas móviles.
  - **(b) Usar solo el ORM de Django** en modo standalone (sin servidor): posible, pero es una dependencia pesada sin beneficio real.
  - **(c) Django como backend local + app de escritorio como cliente HTTP**: funciona, pero duplica la complejidad sin necesidad.
- **Conclusión:** para un programa de escritorio Python, la combinación práctica es **PySide6 + SQLite (SQLAlchemy) + httpx + APScheduler + PyInstaller** (para generar el .exe). Si el requisito "Django" es innegociable, se usa su ORM en modo (b), pero no aporta nada que SQLAlchemy no dé.

---

## 3. Matriz de factibilidad por plataforma (verificada con fuentes de 2025-2026)

| Plataforma | Acceso sin login | Mecanismo | Filtro por tags/hashtags | Riesgo de bloqueo | Notas |
|---|---|---|---|---|---|
| **Mastodon** | ✅ Sí | API pública por instancia (timelines, búsqueda de hashtags, cuentas) | ✅ Hashtags | Bajo | Límite típico ~300 req/5 min por IP ([docs de Mastodon](https://docs.joinmastodon.org/api/rate-limits/)). Respetar instancias pequeñas. |
| **Misskey / CherryPick** | ✅ Parcial | API por instancia; timelines/trending públicos; la *búsqueda* de notas suele requerir token | ✅ Hashtags (con token de app) | Bajo | CherryPick es fork de Misskey → misma API ([repo CherryPick](https://github.com/kokonect-link/cherrypick/releases)). Algunos endpoints exigen token ([docs Misskey](https://misskey-hub.net/en/docs/for-developers/api/token/)). |
| **Bluesky** | ✅ Sí | atproto público (`app.bsky.feed.searchPosts` sin autenticación) | ✅ Palabras clave/hashtags | Bajo-Medio | Límites por IP documentados ([discusión atproto #2160](https://github.com/bluesky-social/atproto/discussions/2160)). |
| **Safebooru** | ✅ Sí | API JSON `dapi` sin clave | ✅ Tags (nativo) | Bajo | El caso ideal: filtrado por tags es la función central del sitio. |
| **Gelbooru** | 🟡 Clave gratuita | API exige `api_key` + `user_id` de cuenta gratuita | ✅ Tags | Bajo | Credenciales en opciones de cuenta ([docs en nazurin](https://raw.githubusercontent.com/y-young/nazurin/master/docs/site/gelbooru.md)). |
| **Rule34.xxx** | 🟡 Clave gratuita | API exige `userID` + `apiKey` de cuenta gratuita | ✅ Tags | Bajo | Mismo esquema Gelbooru ([clientes de la comunidad](https://pkg.go.dev/github.com/Momgoloid69/rule34-go/v2@v2.0.0)). Contenido adulto → ver §6. |
| **Danbooru** | 🟡 Parcial | Anónimo limitado a **2 tags** por búsqueda; con API key se amplía | ✅ Tags (limitado sin clave) | Medio | Límite anónimo confirmado por la comunidad ([foro Danbooru](https://safebooru.donmai.us/forum_topics/15379)). Política anti-bots estricta: tasas bajas obligatorias. |
| **DeviantArt** | 🟡 Registro de app | OAuth2 *client credentials* (sin login de usuario) para `/browse` | ✅ Palabras clave + **campo de licencia** | Bajo | Único gran sitio con metadata de licencia útil para "material liberado" ([política API](https://www.deviantart.com/about/policy/api/)). |
| **Tumblr** | 🟡 Registro de app | OAuth 1.0a con *consumer key* (sin login de usuario) para posts públicos | ✅ Tags de post | Bajo-Medio | Aplicaciones de consumo sin sesión de usuario ([docs de autenticación](https://deepwiki.com/tumblr/docs/2.2-authentication)). |
| **Pixiv** | 🔴 No | La App API exige OAuth con cuenta Pixiv; sin login no hay acceso legítimo | — | Alto si se intenta scraping | Clientes como pixivpy requieren sesión ([pixivpy](https://github.com/upbit/pixivpy)); los grabbers lo listan como "requiere login" ([imgbrd-grabber #1618](https://github.com/Bionus/imgbrd-grabber/issues/1618)). |
| **X / Twitter** | 🔴 No | Sin tier gratuito desde feb-2026; pay-per-use (~USD 0,005/post leído) ([análisis 2026](https://opentweet.io/answers/is-the-x-api-free-in-2026)) | — | Alto | Scraping prohibido por ToS y fuertemente bloqueado. |
| **Pinterest** | 🔴 No | API v5 exige OAuth de usuario + aprobación de app; scraping viola ToS ([informe ToS Pinterest](https://oag.ca.gov/sites/default/files/California%20AB-587%20Terms%20of%20Service%20Report%20%28H1%202025%29%20%5BPinterest%2C%20Inc.%5D.pdf/California%20AB-587%20Terms%20of%20Service%20Report%20%28H1%202025%29%20%5BPinterest%2C%20Inc.%5D.pdf)) | — | Alto | Protección anti-bot agresiva; no viable éticamente sin login. |
| **Newgrounds** | 🟡-🔴 | La API oficial (newgrounds.io) está orientada a juegos y pide app/sesión; el arte solo por HTML del sitio | — | Alto | Sin API pública de arte: scraping frágil y de dudosa conformidad. |
| **Wikis de fandoms (Fandom.com y otras MediaWiki)** | ✅ Sí | API pública `api.php` sin login: `list=allimages`, `prop=images`, `list=search` | ✅ Franquicia y/o personaje (búsqueda de páginas y prefijos de archivo) | Bajo | Muchas imágenes son arte oficial/capturas sin licencia permisiva → aplica confirmación manual de §4.1. Ver Anexo A.5. |

> **Excluidas por diseño (no son fuentes):** Patreon, Pixiv Fanbox, Unifans, Fansky, OnlyFans, Fansly y todo muro premium — ver §4.5. **ATF Booru y boorus similares centrados en contenido de menores: exclusión total — ver §4.6.**

---

## 4. Análisis de los 4 requisitos del usuario

### 4.1 "Restricciones de autor: el material debe estar liberado"
- **Factibilidad parcial.** Solo es verificable donde exista metadata: DeviantArt expone licencia por obra; algunos posts de fediverso y boorus llevan indicaciones (raras). En X, Pinterest, Mastodon en general: no existe el dato.
- **Solución honesta del programa:**
  - Motor de filtrado con 3 modos: (1) *Estricto*: solo descarga obras con licencia permisiva explícita o dominio público; (2) *Manual*: el usuario confirma obra por obra; (3) *Solo vista previa + atribución* (no descarga la obra completa).
  - Guardar siempre **metadatos de atribución** (artista, URL de origen, licencia) en un archivo sidecar JSON por imagen.
  - Recordatorio en la UI: "fanart" es obra derivada: derechos del artista sobre la obra y del dueño de la IP sobre los personajes; descargar ≠ derecho a redistribuir.

### 4.2 Restricciones legales
- **Derechos de autor:** el uso personal y privado de una copia está en zona gris según jurisdicción; la redistribución masiva o comercial, no. El programa debe ser **solo para archivo personal**.
- **ToS y robots.txt:** cada sitio tiene términos que prohíben scraping; la herramienta debe respetar `robots.txt`, usar APIs oficiales cuando existan y mostrar al usuario qué origen usa cada fuente.
- **Anti-elusión:** no implementar bypass de CAPTCHA, Cloudflare, ni de sistemas de login (riesgo legal real en varias jurisdicciones, p. ej. leyes tipo DMCA §1201). *Consecuencia directa: X y Pinterest quedan fuera.*
- **Contenido adulto / menores:** boorus como Rule34 son NSFW. Requisitos mínimos: verificación de mayoría de edad al configurar, **lista negra dura e inamovible de tags prohibidos** (p. ej. variantes de contenido de menores, que además ya están prohibidas en la mayoría de los boorus; ver §4.6), y exclusión por defecto de ratings adultos salvo activación explícita.
- **Jurisdicción del usuario:** en Venezuela rige la Ley sobre el Derecho de Autor (G.O. N.º 4.638 Ext. de 1993) para obras locales, y los ToS extranjeros aplican como contrato; ante la duda, el comportamiento por defecto más conservador es el correcto.

### 4.3 Descargas espaciadas y anti-bloqueo (sin violar nada)
- Política de tasas **por sitio** (ej. boorus: 1 req/1-2 s; fediverso: respetar el límite de la instancia; nunca más de lo que permite la API).
- **Jitter aleatorio** entre descargas para evitar patrones de bot.
- **Backoff exponencial** ante 429/403/5xx y reintentos limitados; si el sitio insiste, **pausar la fuente y notificar**, no insistir.
- **Peticiones condicionales** (ETag/If-Modified-Since) para no re-descargar lo ya visto.
- **Deduplicación por hash** (MD5/SHA-256) entre plataformas (el mismo fanart suele estar reposteado en varias).
- Cola persistente en SQLite: si se cierra la app o hay bloqueo, se retoma sin perder trabajo.
- **User-Agent identificado** (nombre de la app + contacto) y prioridad a APIs sobre scraping.
- Expectativa realista: *reducir* la probabilidad de bloqueo a casi cero con fuentes de API abierta (Mastodon/Bluesky/boorus) y *no poder garantizarla* en las demás.

### 4.4 Principios éticos
- Por defecto **no descargar** sin licencia permisiva o acción explícita del usuario (ver 4.1).
- Respeto al artista: guardar atribución, ofrecer botón "abrir página del artista", no incluir funciones de re-subida automática.
- Respeto al operador del sitio: tasas bajas, robots.txt, APIs oficiales, no golpear instancias pequeñas del fediverso.
- Respeto al usuario: transparencia sobre qué se descarga, de dónde y con qué licencia; logs visibles.

### 4.5 Plataformas de pago y contenido premium: exclusión explícita

- **Fuentes en lista negra dura:** Patreon, Pixiv Fanbox, Unifans, Fansky, OnlyFans, Fansly y cualquier plataforma o sección marcada como premium/exclusiva.
- **Motivo legal:** su contenido está tras un muro de pago; extraerlo sin suscripción implica eludir medidas técnicas de control de acceso (riesgo legal real en varias jurisdicciones) y viola los ToS de todas esas plataformas.
- **Motivo ético:** son la fuente de ingresos directa del artista; descargar contenido exclusivo sin pagar es daño económico directo, no "archivo personal".
- **Implicación técnica del pipeline:**
  1. Bloqueo por dominio de esas plataformas (no pueden añadirse como fuente).
  2. Detección y descarte de *enlaces* a ellas dentro de biografías y posts de redes libres (los artistas suelen enlazar su Patreon/Fanbox): el programa ignora esos destinos, no los sigue.
  3. Descartar publicaciones marcadas como exclusivas o recortes de vistas previas de contenido premium en fuentes libres (p. ej. "preview de Fanbox").
  - Lo que el artista **también** publica libremente en Mastodon, Bluesky, DeviantArt o boorus **sí** sigue siendo descargable por la vía pública normal; eso no afecta el requisito.

### 4.6 Boorus dedicados a contenido prohibido (ATF Booru): exclusión total

- **Qué es:** ATF Booru (All The Fallen) es un booru cuya razón de ser es contenido que los boorus convencionales (Gelbooru, Rule34.xxx, Danbooru, e621) **prohíben explícitamente**: representaciones de menores en contexto sexual (loli/shota). Está documentado como plataforma controversial por ese motivo ([análisis de la plataforma](https://skdesu.com/it/aftbooru-allthefallen-moe/)); es un fork de Danbooru ([repo del software](https://github.com/TravHSV/atfbooru)).
- **Impacto legal:** ese material es ilegal en la gran mayoría de jurisdicciones, incluso como dibujo (p. ej. EE. UU. bajo el PROTECT Act; Canadá, Reino Unido y Australia penalizan representaciones ficticias). Incluir esta fuente pondría al usuario en riesgo penal real y violaría los requisitos 2 (legal) y 4 (ético) del propio proyecto.
- **Conclusión de factibilidad: NO se incluye como fuente, sin excepciones ni opción de configuración.**
- **Efecto práctico si se intentara:** la lista negra dura de tags prohibidos del núcleo (§4.2) eliminaría justamente el contenido que define a ese booru; no existe un "modo filtrado" útil porque su contenido objetivo es el prohibido.
- **Regla general:** cualquier booru cuyo contenido central sean menores u otro material ilegal queda excluido por el mismo criterio. La lista negra de tags prohibidos es parte del núcleo y no puede desactivarse desde la UI.

---

## 5. Arquitectura propuesta (alto nivel, sin código)

```
┌─────────────────────────────────────────────────────┐
│  UI de escritorio (PySide6)                          │
│  pestañas: Fuentes · Filtros · Cola · Descargas · Log│
│  · Configuración: carpeta de salida, límites, claves │
└───────────────┬─────────────────────────────────────┘
                │
┌───────────────▼─────────────────────────────────────┐
│  Núcleo                                             │
│  • Planificador (APScheduler): rondas por fuente con │
│    cooldown/jitter/backoff por sitio                 │
│  • Pipeline de filtros:                              │
│    hashtags/palabras/tags → licencia → edad/NSFW →   │
│    lista negra → fuentes de pago/exclusivas → dedupe │
│  • Adaptadores por plataforma (interfaz común):      │
│    mastodon.py, misskey.py, bluesky.py,              │
│    booru_*.py, deviantart.py, tumblr.py              │
│  • Capa HTTP (httpx): UA identificado, ETag, robots  │
│  • Persistencia: SQLite (SQLAlchemy)                 │
│    obras, hashes, estado de cola, metadatos          │
└───────────────┬─────────────────────────────────────┘
                │
        Carpeta de salida (configurable en la UI):
        obras + sidecar JSON (artista, origen,
        licencia, tags, fecha)
```

- **Configuración:** perfiles YAML/JSON por fuente (intervalo, límites, filtros, credenciales opcionales en variables de entorno).
- **Carpeta de salida (requisito de UI):** seleccionable desde la pestaña Configuración con el diálogo nativo de Windows, con validación de permisos de escritura y espacio disponible al guardar. Estructura sugerida: `<salida>/<plataforma>/<artista_o_tag>/<id>_<md5>.ext` + sidecar `.json` con metadatos. **Fail-safe: si no hay carpeta configurada, el programa no descarga nada.**
- **Empaquetado:** PyInstaller → un solo `.exe` instalable en Windows.

### 5.1 Comportamiento de botones y archivos (requisitos de UI)

- **Limpiar:** borra **todo** — cola, historial, hashes y archivos de la carpeta de salida. Se implementará con diálogo de confirmación obligatorio para evitar pérdida accidental, pero el comportamiento es "limpiar todo".
- **Descargar:** lanza la descarga completa (todas las fuentes y filtros activos) y la UI pasa al estado *en ejecución*; en ese estado se **habilita Cancelar** y se deshabilita Descargar.
- **Cancelar:** envía señal de parada a los workers (las descargas en curso terminan de forma segura), descarta la cola parcial y la UI **vuelve al estado inicial** con Descargar habilitado de nuevo. Cancelar ≠ Limpiar: no borra lo ya descargado.
- **Sobrescritura:** si al descargar el archivo destino ya existe, **se sobreescribe** (requisito explícito). La deduplicación por hash sigue evitando reencolar contenido idéntico ya procesado, pero la escritura final reemplaza el archivo existente. (Nota: conviene dejar un toggle futuro "omitir si es idéntico", pero el comportamiento por defecto es sobreescribir.)

---

## 6. Fases recomendadas

| Fase | Alcance | Comentario |
|---|---|---|
| **1 (MVP)** | Safebooru, Gelbooru, Rule34 (claves gratuitas) + Mastodon + Bluesky | Cubre "boorus + fediverso" sin login; filtros por tags/hashtags nativos. |
| **2** | Misskey/CherryPick, DeviantArt, Tumblr (registro de app, sin login de usuario) + wikis de fandoms (Fandom/MediaWiki) | Añade el sitio con mejor metadata de licencia (DeviantArt) y la búsqueda por franquicia/personaje en wikis. |
| **3 (opcional)** | Pixiv (requiere cuenta del usuario), X (pay-per-use) | Solo si el usuario acepta login/pago; dejar los adaptadores "apagados" por defecto. |
| **Excluido** | Pinterest, Newgrounds | Sin acceso legítimo sin login / sin API de arte. |

---

## 7. Riesgos principales

1. **Cambios y cierres de APIs** (X ya cerró su tier gratuito; Gelbooru/Rule34 añadieron claves): mantenimiento continuo de adaptadores.
2. **Interpretación legal de "descarga"**: el programa es solo para archivo personal; cualquier función de redistribución quedaría fuera del alcance ético aquí definido.
3. **Volumen de almacenamiento**: fanarts en alta resolución + NSFW de boorus crecen rápido; prever límites por sesión/ronda.
4. **Contenido prohibido**: sin lista negra dura de tags, una fuente como Rule34 es inaceptable desde lo legal y lo ético; la lista debe estar en el núcleo, no en la UI.

---

## 8. Conclusión

- **Técnicamente:** un programa de escritorio Python (PySide6, no WinForms literal, y sin necesidad de Django) que extraiga fanarts **es perfectamente factible** para Mastodon, Misskey/CherryPick, Bluesky y los boorus principales, con registro gratuito de app para DeviantArt y Tumblr.
- **Legal y éticamente:** el requisito de "material liberado" impone que el motor solo descargue en automático lo que tenga licencia explícita permisiva; el resto requiere confirmación manual o queda en vista previa. Pixiv, X y Pinterest **no son factibles sin login/pago** por vías legítimas, y no deben intentarse por scraping. Las plataformas de pago (Patreon, Pixiv Fanbox, Unifans, Fansky, OnlyFans, Fansly) y el contenido premium quedan **excluidas por diseño**: bloqueo por dominio y detección de enlaces en el pipeline (§4.5). ATF Booru y cualquier booru centrado en contenido de menores quedan **totalmente excluidos** (§4.6).
- **El proyecto es viable y recomendable por fases**, empezando por el MVP de la Fase 1.

---

## Anexo A — Plantilla de conexión para boorus (patrón replicable)

### A.1 Por qué es replicable: las familias de software

Los boorus corren sobre pocos motores de software, y cada motor expone una API casi idéntica en todos los sitios que lo usan. Con **3 familias** se cubre la gran mayoría:

| Familia | Software | Ejemplos | Endpoint típico | Autenticación |
|---|---|---|---|---|
| **Gelbooru (dapi)** | Gelbooru 0.2.x | Gelbooru, Rule34.xxx, Safebooru.org, etc. | `GET /index.php?page=dapi&s=post&q=index&json=1&tags=a+b&limit=100&pid=0` | `api_key`+`user_id` en Gelbooru y Rule34.xxx (cuenta gratuita); sin clave en Safebooru.org |
| **Danbooru** | Danbooru | Danbooru, Safebooru.donmai.us, forks | `GET /posts.json?tags=a+b&limit=200&page=1` | Sin clave = máximo 2 tags; con `api_key` se amplía |
| **Moebooru** | Moebooru | Yande.re, Konachan | `GET /post.json?tags=a+b&limit=100&page=1` | Sin clave |

*(ATF Booru es un fork de Danbooru, pero queda excluido del programa por §4.6.)*

### A.2 El patrón: una configuración por sitio + un normalizador común

```python
# Pseudocódigo conceptual (documentación de diseño, no es el programa final)

@dataclass
class BooruConfig:
    nombre: str
    base_url: str
    familia: str                      # "gelbooru" | "danbooru" | "moebooru"
    auth: dict | None = None          # {"api_key": ..., "user_id": ...} si la pide
    intervalo_min: float = 1.5        # segundos entre peticiones (anti-bloqueo)
    limite_por_pagina: int = 100

SITIOS = [
    BooruConfig("gelbooru",  "https://gelbooru.com",        "gelbooru",
                auth={"api_key": CLAVE, "user_id": UID}),
    BooruConfig("rule34",    "https://api.rule34.xxx",      "gelbooru",
                auth={"api_key": CLAVE, "user_id": UID}),
    BooruConfig("safebooru", "https://safebooru.org",       "gelbooru"),   # sin clave
    BooruConfig("danbooru",  "https://danbooru.donmai.us",  "danbooru"),   # 2 tags anónimo
    BooruConfig("yandere",   "https://yande.re",            "moebooru"),
]

def construir_url(cfg, tags, pagina): ...   # arma la URL según la familia
def obtener_pagina(cfg, tags, pagina): ...  # HTTP con UA identificado + cooldown
def normalizar(cfg, post_crudo) -> Post: ...# mapea los campos del JSON a un modelo común:
#   id, url_archivo, url_muestra, url_miniatura, tags(lista),
#   rating (normalizado), md5, fuente, artista, fecha, licencia(=None casi siempre)
```

El `Post` común alimenta el pipeline único del núcleo: lista negra dura de tags → licencia → edad/NSFW → fuentes de pago → dedupe por md5 → cola de descarga.

### A.3 Cómo "replicar" la plantilla para un booru nuevo

1. **Identificar la familia:** probar su endpoint (`dapi` vs `/posts.json` vs `/post.json`) y mirar la forma del JSON. Si coincide con una de las 3 familias, **cero código nuevo**: solo se añade una entrada de `BooruConfig`.
2. **Verificar campos:** confirmar que el JSON trae `file_url`, `tags`, `rating`, `md5` (o equivalentes) y ajustar el mapeo del normalizador si hay variantes menores.
3. **Autenticación:** si el sitio pide `api_key`/`user_id`, generarlos en las opciones de cuenta (gratis); si es Danbooru anónimo, recordar el límite de 2 tags.
4. **Límites y cortesía:** respetar `robots.txt`, intervalo ≥ 1-2 s, paginación con `pid`/`page` hasta obtener menos resultados que el límite o llegar a IDs ya conocidos.
5. **Lista negra:** el booru nuevo pasa automáticamente por los mismos filtros duros del núcleo (nada de contenido prohibido, aunque el sitio lo tuviera).

### A.4 Referencias existentes que usan exactamente este patrón

- [imgbrd-grabber](https://github.com/Bionus/imgbrd-grabber) (sources configurables por sitio)
- [gallery-dl](https://github.com/mikf/gallery-dl) (extractores por familia)
- [nazurin](https://github.com/y-young/nazurin) y [Pybooru](https://github.com/LuqueDaniel/pybooru) (clientes por familia)

### A.5 Familia MediaWiki (wikis de fandoms: Fandom.com y otras)

Las wikis de fandoms (Fandom.com, wiki.gg, wikis independientes) corren sobre **MediaWiki**, cuya API pública `api.php` no exige login para leer:

| Operación | Endpoint (ejemplo) |
|---|---|
| Listar imágenes por prefijo | `GET https://<wiki>.fandom.com/api.php?action=query&list=allimages&aiprefix=<Personaje>&ailimit=500&aiprop=url&format=json&aicontinue=...` |
| Imágenes usadas en una página | `GET https://<wiki>.fandom.com/api.php?action=query&prop=images&titles=<Página>&format=json` |
| Buscar páginas/títulos | `GET https://<wiki>.fandom.com/api.php?action=query&list=search&srsearch=<franquicia>&format=json` |

Flujo propuesto para "buscar fandom (franquicia y/o personaje) en repositorios de wikis":

1. **Identificar la wiki:** subdominio de fandom.com de la franquicia (p. ej. `naruto.fandom.com`) o URL directa de cualquier wiki MediaWiki.
2. **Buscar el fandom/personaje:** `list=search` para localizar páginas relevantes; luego `prop=images` para obtener sus archivos, y/o `allimages` con prefijo por personaje/franquicia.
3. **Paginación:** continuar con `aicontinue`/`continue` hasta agotar resultados.
4. **Descarga:** `Special:FilePath/<Nombre>` o la URL directa del metadata, con User-Agent identificado y throttle moderado (las wikis son comunitarias).
5. **Licencias:** las wikis mezclan contenido libre (dominio público, CC) con capturas y arte oficial usados como "fair use". El filtro de §4.1 aplica igual: descarga automática solo con licencia permisiva explícita o confirmación manual. (Opcional complementario: Wikimedia Commons, que sí trae metadata de licencia real, p. ej. CC0/CC-BY.)

---

## Anexo B — Factibilidad: mejora de calidad / upscaling de las imágenes descargadas

**Veredicto: totalmente factible**, con tres niveles de costo creciente. Solo factibilidad (sin desarrollo iniciado).

### B.1 Niveles de mejora

| Nivel | Técnica | Detalle nuevo | VRAM | CPU | RAM pico | Tiempo por imagen (~1-2 MP) |
|---|---|---|---|---|---|---|
| **1. Ligero** | Re-muestreo Lanczos/bicúbico (Pillow/OpenCV, ya disponible) | ❌ No agrega detalle (solo re-escala) | 0 | Mínima | Baja | milisegundos |
| **2. IA GPU general** | waifu2x-ncnn-vulkan o Real-ESRGAN (ncnn) — Vulkan: NVIDIA/AMD/Intel | ✅ Reconstrucción IA (anime/fanart ideal) | ~0.5–2 GB | Baja | Media | ~1–5 s (2x) |
| **3. IA DirectML/ONNX** | Real-ESRGAN/SwinIR/HAT en ONNX Runtime + DirectML (Windows, cualquier GPU) | ✅ Idem | ~1–2 GB | Media | Media | ~2–10 s (2x) |
| **4. IA solo CPU** | ONNX Runtime CPU (fallback sin GPU) | ✅ Idem, más lento | 0 | **Alta** (100 % de los núcleos) | Alta (1–3 GB por imagen) | ~15–90 s (2x); 4x ≈ 4× ese tiempo |
| **5. PyTorch+CUDA** | Real-ESRGAN "completo" | ✅ Máxima flexibilidad | ~1.5–4 GB | Baja | Media | ~1–3 s (2x) |

*(Cifras estimadas, dependen del modelo y del hardware; los modelos pesan ~40–250 MB en disco.)*

### B.2 Qué recursos consume cada camino

- **VRAM (memoria de video):** solo en niveles IA con GPU (2–5). Sin GPU, los niveles 1 y 4 funcionan (el 4 a costa de CPU y tiempo).
- **CPU:** el nivel 4 satura todos los núcleos durante segundos/minutos por imagen. En una cola de 100 imágenes, CPU-only puede tardar 1–2 horas → obligatorio procesar **en cola secuencial**, con la barra de progreso y el botón Cancelar que la app ya tiene.
- **RAM:** el upscaling por *tiles* (el estándar: trozos de ~512×512) mantiene el pico contenido (1–3 GB). Sin tiles, un 4x de una imagen 4K exigiría decenas de GB.
- **Tamaño de archivos resultantes:** 1080p → 2x PNG ≈ 8–20 MB; → 4x PNG ≈ 30–80 MB. Conviene opción de guardado JPG/WebP con calidad configurable.
- **Disco (dependencias):** ncnn/onnxruntime-directml ≈ 100–200 MB; **evitar PyTorch** (~2 GB) para una app de escritorio ligera.

### B.3 Recomendación para este proyecto

1. **Modelos:** fanart es mayormente estilo anime → `waifu2x` (ncnn-vulkan) o `Real-ESRGAN x4plus-anime`; opción fotográfica `Real-ESRGAN x4plus` para arte realista.
2. **Escala por defecto 2x** (Full HD desde ~960p); 4x solo opcional (memoria y archivos 4–16×).
3. **Backend auto:** detectar en orden *Vulkan → DirectML → CPU*, con aviso al usuario del modo activo.
4. **Integración:** etapa post-descarga del pipeline existente (tras `download_to`, antes del sidecar): la arquitectura de workers ya tiene hilo, progreso y cancelación → solo se añade un paso y un selector en la UI ("Mejorar calidad: No / 2x / 4x").
5. **Ética/legal:** el upscaling crea una copia derivada sintética; para **archivo personal** es aceptable (no redistribuir, no usar para quitar marcas de agua o evadir derechos; se conserva el sidecar con autoría/origen).

### B.4 Riesgos

- Falsas expectativas: el detalle es **reconstruido**, no real; imágenes muy pequeñas no "recuperan" información inexistente.
- Sin GPU, el modo IA es lento: mitigar con cola + pausa/cancel + aviso de tiempo estimado.
- Artefactos en estilos complejos (tramas, texto): permitir comparar original/mejorado y conservar el original.
- Los boorus ya entregan la máxima resolución disponible (`file_url`); el upscaling solo aporta cuando la fuente es de baja resolución (capturas, previews de redes).

### B.5 Fases propuestas (si se aprueba el desarrollo)

| Fase | Alcance |
|---|---|
| A | Nivel 1 (Lanczos 2x) — cero dependencias nuevas |
| B | waifu2x/Real-ESRGAN ncnn-vulkan (GPU) + toggle en UI |
| C | ONNX Runtime DirectML + fallback CPU, escala 4x, formato de guardado configurable |

> **Estado (2026-10-06): implementado.** Pipeline post-descarga con reglas de
> buckets del usuario (<700px→4x · 700-799→3x · 800-1500→2x · 1501-1599→1x ·
> ≥1600→solo WebP), guardado siempre en `.webp` con calidad configurable en la
> UI, modo IA con Real-ESRGAN/waifu2x (ncnn-vulkan, probado en GPU real) y
> fallback automático a Lanczos + afilado. Pendiente opcional: backend
> DirectML/CPU y más modelos (Fase C).

> **Actualización (2026-10-08):** los tramos quedaron **≤699→4x · 700-799→3x ·
> ≥800→2x**, con tope de 8K y sin reescalar por encima de 7679 px. Se retiró el
> tramo `1501-1599→1x` porque rompía la coherencia de la tabla: una imagen de
> 1550 px se quedaba **sin** reescalar mientras una de 1500 px se doblaba. Además,
> el resultado de la mejora se informa siempre al usuario (tamaño de partida →
> resultado real, y aviso si el origen es diminuto).
