# Plataformas

Imaginteca reúne **8 redes sociales**, **14 booros**, **5 familias de booru** y
**wikis de fandom**, todo detrás de la misma ventana.

## Redes sociales (8)

| Plataforma | ¿Clave? |
|---|---|
| **Fediverso** (cualquier instancia de Mastodon, Misskey o CherryPick; detecta el software solo) | No |
| **Bluesky** | No |
| **DeviantArt** | Sí (`DEVIANTART_CLIENT_ID` + `DEVIANTART_CLIENT_SECRET`) |
| **Tumblr** | Sí (`TUMBLR_API_KEY`) |
| **Pixiv** (API oficial con tu cuenta) | Sí (`PIXIV_REFRESH_TOKEN`, con el asistente) |
| **X / Twitter** (API v2) | Sí, y es de **pago** (`X_BEARER_TOKEN`) |
| **Pinterest** (API v5, OAuth propio) | Sí (`PINTEREST_ACCESS_TOKEN`, app aprobada) |
| **Newgrounds** | No |

## Boores (14)

Safebooru · Gelbooru · Rule34.xxx · The Big ImageBoard · Xbooru · Hypnohub ·
Danbooru · Safebooru (Donmai) · Yande.re · Konachan · Konachan (SFW) ·
Derpibooru · ATF Booru · Rule34 Paheal

| Booru | ¿Clave? |
|---|---|
| Safebooru, Danbooru, Konachan (SFW), Yande.re, Derpibooru, ATF Booru… | No |
| **Rule34.xxx** | Sí (`RULE34_API_KEY` + `RULE34_USER_ID`) |
| **Gelbooru** | Sí (`GELBOORU_API_KEY` + `GELBOORU_USER_ID`) |

Los booros también se pueden consultar por **familia de API**: `gelbooru`,
`danbooru`, `moebooru`, `philomena` y `shimmie`.

## Wikis (1 tipo)

**Fandom.com** y cualquier wiki MediaWiki: búsqueda por **franquicia**,
**personaje** y/o **concepto**. No piden clave.

---

## Notas que ahorran tiempo

- **Sin claves funcionan:** fediverso, Bluesky, wikis, Newgrounds y la mayoría de
  booros públicos. Puedes empezar a usarlo sin configurar nada.
- **Rule34.xxx y Rule34 Paheal** son casi todo contenido adulto: si no marcas
  **Permitir contenido adulto** en Opciones verás **0 resultados** aunque la
  conexión funcione perfectamente.
- **Cloudflare** (por ejemplo en Rule34.xxx) puede pedir un CAPTCHA: ábrelo en tu
  navegador, resuélvelo y copia en `config_local.py` la cookie `cf_clearance` y tu
  `User-Agent`. El programa **nunca** evade CAPTCHAs.
- **Se espacian las peticiones a propósito** (cortesía con los sitios): con muchos
  hashtags o palabras clave, la búsqueda tarda más. Es normal y deliberado.
- **Cada plataforma guarda en su propia subcarpeta** dentro de la carpeta de
  salida.

---

**Siguiente:** [Claves y configuración](Claves-y-configuracion) ·
**¿Algo no responde?** [Problemas frecuentes](Problemas-frecuentes)
