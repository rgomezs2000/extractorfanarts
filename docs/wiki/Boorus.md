# 🧩 Boorus compatibles

**14 booros integrados**, agrupados en **5 familias de API**. Los booros son la
mejor fuente para un [dataset](Datasets-IA): su **etiquetado** es el más completo
que existe para arte.

## Qué es un booru (y por qué importa)

Un booru es un archivo de imágenes **etiquetado por la comunidad**: cada imagen
lleva decenas de etiquetas (`1girl`, `solo`, `blue_eyes`, `highres`, el personaje,
la franquicia, el artista…). Eso permite búsquedas muy finas:

- **Etiquetas** separadas por espacios: `lola_loud 1girl solo`
- **Excluir** con un guion: `-comic -text -sketch`
- **Operadores** del sitio: `rating:general`, `score:>10`, `order:score`

## Las 5 familias de API

Muchos booros comparten software, así que **un mismo adaptador sirve para varios**.
Eso hace que añadir uno nuevo de una familia soportada sea trivial.

| Familia | Quiénes son | Notas |
|---|---|---|
| **Gelbooru** | Gelbooru, Safebooru (org), Rule34.xxx, TBIB, Xbooru, Hypnohub | La más extendida; clave gratuita en algunos |
| **Danbooru** | Danbooru, Safebooru (Donmai), ATF Booru | El mejor etiquetado; **límite anónimo de 2 etiquetas** |
| **Moebooru** | Yande.re, Konachan, Konachan (SFW) | Enfocados a alta resolución |
| **Philomena** | Derpibooru | Filtros y ratings propios |
| **Shimmie** | Rule34 Paheal | API sencilla vía web |

## Los 14, uno por uno

| Booru | Familia | 🔑 Claves | De qué va |
|---|---|---|---|
| **[Safebooru](https://safebooru.org)** | Gelbooru | No | Solo contenido **SFW**; ideal para empezar |
| **[Gelbooru](https://gelbooru.com)** | Gelbooru | Gratis (opcional) | Enorme y variado, con `rating:` para filtrar |
| **[Rule34.xxx](https://rule34.xxx)** | Gelbooru | Gratis (opcional) | **Adulto** casi al 100 %: sin *Permitir contenido adulto* verás 0 resultados |
| **[The Big ImageBoard](https://tbib.org)** | Gelbooru | No | Generalista y ordenado; buen `score:` |
| **[Xbooru](https://xbooru.com)** | Gelbooru | No | **Adulto**, con mucho arte *furry* |
| **[Hypnohub](https://hypnohub.net)** | Gelbooru | No | **Adulto**, temática concreta |
| **[Danbooru](https://danbooru.donmai.us)** | Danbooru | No | **El mejor etiquetado del mundo para anime/fanart**. Sin clave: **2 etiquetas** por búsqueda |
| **[Safebooru (Donmai)](https://safebooru.donmai.us)** | Danbooru | No | La parte **SFW** de Danbooru, con el mismo etiquetado |
| **[Yande.re](https://yande.re)** | Moebooru | No | Alta resolución; mezcla SFW y adulto |
| **[Konachan](https://konachan.com)** | Moebooru | No | Fondos y arte en gran tamaño |
| **[Konachan (SFW)](https://konachan.net)** | Moebooru | No | El mismo sitio, solo **SFW** |
| **[Derpibooru](https://derpibooru.org)** | Philomena | No | **My Little Pony** y su comunidad; ratings propios |
| **[ATF Booru](https://booru.allthefallen.moe)** | Danbooru | No | **Adulto**; se le aplican siempre los filtros de contenido prohibido |
| **[Rule34 Paheal](https://rule34.paheal.net)** | Shimmie | No | **Adulto**; API sencilla |

### Claves: solo dos, y son gratis

- **Gelbooru**: `GELBOORU_API_KEY` + `GELBOORU_USER_ID` (opciones de tu cuenta).
- **Rule34.xxx**: `RULE34_API_KEY` + `RULE34_USER_ID`.
- Sin ellas **también funcionan**, con menos resultados por página. El resto de
  booros no piden nada.
- **Danbooru** no acepta clave en esta versión: se consulta con el **límite
  anónimo de 2 etiquetas**. Para búsquedas más complejas, usa otro booro de la
  misma familia (Safebooru Donmai) o combina etiquetas en el sitio.

### Aviso sobre el contenido adulto

En **Rule34.xxx**, **Rule34 Paheal**, **Xbooru**, **Hypnohub** y **ATF Booru**
casi todo es adulto: si no marcas **«Permitir contenido adulto»** en Opciones
verás **0 resultados** aunque la conexión funcione bien. Y aunque lo marques, la
**lista negra de contenido prohibido se aplica siempre**.

## Próximamente

Candidatos estudiados. Los de una familia ya soportada son **los más fáciles**
(prácticamente una línea de configuración):

| Booru | Familia | Viabilidad | Por qué |
|---|---|---|---|
| **e621** | propia | 🟢 Alta | API pública JSON sin clave (contenido *furry*, adulto) |
| **Rule34.us** | Gelbooru | 🟢 Alta | Misma API que Gelbooru |
| **Realbooru** | Gelbooru | 🟢 Alta | Misma API que Gelbooru |
| **Sakugabooru** | Moebooru | 🟢 Alta | Misma API; clips y arte de animación |
| **Zerochan** | — | 🟡 Media | Sin API pública: lectura del sitio |
| **Sankakucomplex** | — | 🔴 Baja | Su API cambió y exige cuenta |

> **Cualquier booru de una familia soportada se puede añadir ya** sin esperar:
> ver [Claves y configuración](Claves-y-configuracion).

## Cómo se añade un booru

En `config_local.py` puedes añadir o cambiar sitios de las familias soportadas
(`gelbooru`, `danbooru`, `moebooru`, `philomena`, `shimmie`) con su nombre, su
dirección base y su familia. El programa lo toma como uno más, con los mismos
filtros y el mismo espaciado de peticiones.

---

**[← Soporte de plataformas](Plataformas)** · **[Redes sociales](Redes-sociales)** ·
**[Fandoms](Fandoms)** · **[Claves y configuración](Claves-y-configuracion)**
