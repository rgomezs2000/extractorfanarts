# ExtractorFanarts

Aplicación de escritorio **Python (PySide6, arquitectura MVC)** para extraer
fanarts, arte e imágenes desde redes sociales, boorus y wikis de fandom,
con restricciones legales y éticas integradas en el núcleo.

> Uso personal y privado. No redistribuyas el material descargado: la mayoría
> del fanart no tiene licencia liberada. Ver el informe de factibilidad:
> [INFORME-FACTIBILIDAD.md](INFORME-FACTIBILIDAD.md).

## Instalación

```powershell
python -m pip install --target vendor PySide6 httpx
python main.py
```

(Si ya existe la carpeta `vendor`, basta `python main.py`.)

## Fuentes soportadas

| Tipo | Plataformas |
|---|---|
| Redes sociales | Mastodon (instancias configurables), Misskey / CherryPick, Bluesky, DeviantArt (client credentials), Tumblr (consumer key), X/Twitter (API v2 de pago, credenciales propias), Pinterest (API v5, OAuth propio), Newgrounds (sin API pública de arte: aparece documentado y explica el motivo) |
| Boorus | Safebooru, Gelbooru, Rule34.xxx, The Big ImageBoard, Xbooru, Hypnohub, Danbooru, Safebooru (Donmai), Yande.re, Konachan, Konachan (SFW), Derpibooru — 4 familias de software (Gelbooru/Danbooru/Moebooru/Philomena), plantilla replicable: ver Anexo A del informe |
| Wikis de fandom | Fandom.com y cualquier wiki MediaWiki (búsqueda por franquicia, personaje y/o concepto) |

**Excluidos por diseño:** X/Twitter y Pinterest (sin acceso legítimo sin
login/pago), Pixiv (exige cuenta), Newgrounds (sin API de arte), plataformas de
pago (Patreon, Pixiv Fanbox, Unifans, Fansky, OnlyFans, Fansly, premium) y boorus
centrados en contenido prohibido (ATF Booru y similares).

## Claves necesarias (en `app/config.py`)

- **Gelbooru / Rule34.xxx:** `GELBOORU_API_KEY` + `GELBOORU_USER_ID`,
  `RULE34_API_KEY` + `RULE34_USER_ID` (cuentas gratuitas → opciones de cuenta).
- **DeviantArt:** `DEVIANTART_CLIENT_ID` + `DEVIANTART_CLIENT_SECRET`
  (https://www.deviantart.com/developers/).
- **Tumblr:** `TUMBLR_API_KEY` (https://www.tumblr.com/oauth/apps).
- **X/Twitter:** `X_BEARER_TOKEN` (o `X_API_KEY` + `X_API_SECRET`). La API es de
  pago por uso desde 2026: app de desarrollador con facturación.
- **Pinterest:** `PINTEREST_ACCESS_TOKEN` (app aprobada + OAuth del usuario);
  la búsqueda global además requiere `PINTEREST_COUNTRY_CODE` (endpoint beta).
- **Newgrounds:** no tiene API pública de arte (newgrounds.io es de juegos y el
  sitio protege sus páginas); el adaptador lo explica al usarse.
- **Mastodon / Misskey / Bluesky / Safebooru / Danbooru / wikis:** sin claves.

## Comportamiento de la UI

- **Buscar:** consulta la plataforma y muestra los resultados + **una imagen de ejemplo**.
- **Descargar:** busca y descarga todo a la carpeta de salida (se sobreescribe si el
  archivo ya existe); durante la descarga el botón se convierte en **Cancelar** y el
  formulario y **Limpiar** quedan bloqueados.
- **Cancelar:** detiene la operación y restaura la UI tal como estaba, conservando la
  imagen de ejemplo.
- **Limpiar:** limpia el formulario (no descarga nada; solo disponible en reposo).
- **Anti-bloqueo:** si un sitio responde 429/5xx o un posible bloqueo (401/403), el
  programa **pausa un tiempo prudente** (30 s → 5 min, con reintentos) y continúa;
  si el bloqueo persiste, descarta la fuente e informa. No evade CAPTCHAs ni logins.

## Mejora de calidad al descargar

- **Todo lo descargado se convierte SIEMPRE a `.webp`** con la calidad configurada
  (deslizador **Calidad WebP**, 1-100) y **el archivo original nunca se conserva**.
- La casilla **"Mejorar calidad (upscale IA/Lanczos)"** controla SOLO el upscaling,
  con estas reglas según el lado mayor de la imagen:
  `<700px → 4x` · `700-799px → 3x` · `800-1500px → 2x` · `1501-1599px → 1x` ·
  `≥1600px → sin upscale (solo WebP)`.
- **Modo IA:** usa Real-ESRGAN / waifu2x (ncnn-vulkan, GPU) si están instalados
  (`python scripts\setup_vendor.py --ai`); si no están disponibles, cae
  automáticamente a **Lanczos + afilado suave** y lo indica en el estado.
- El sidecar `.json` registra la conversión y mejora aplicada (modo, factor,
  resolución original y resultado).

## Filtros del núcleo (no desactivables)

1. Lista negra dura de tags (contenido de menores y afines).
2. Descartar resultados que enlacen plataformas de pago / contenido exclusivo.
3. Gate de rating adulto (questionable/explicit requieren activación explícita).
4. Opcional "Solo material con licencia liberada" (CC0/CC-BY/dominio público).
5. Deduplicación por hash **dentro de cada búsqueda** (cada Descargar re-descarga
   todo y sobreescribe los archivos existentes).

## Estructura (MVC)

```
main.py                     entrada (añade ./vendor al PYTHONPATH)
app/
  config.py                 credenciales, sitios, límites, listas negras
  models/                   Artwork, SearchQuery, almacén SQLite
  controllers/              MainController (hilos, estados, pipeline)
  services/
    http_client.py          HTTP con cooldown/backoff/pausa
    filters.py              filtros legales/éticos
    adapters/               plantillas por plataforma (booru, mastodon, misskey,
                            bluesky, deviantart, tumblr, mediawiki)
  views/                    MainWindow (Qt)
scripts/smoke_services.py   prueba de humo de los helpers (sin GUI)
```
