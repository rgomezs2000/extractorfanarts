# Claves y configuración

El programa funciona **sin configurar nada** en varias plataformas. Para las que
piden credenciales, se usa un archivo llamado **`config_local.py`**.

## Dónde se busca (por este orden)

1. **Junto al ejecutable** (lo más cómodo).
2. Dentro de la carpeta del programa.
3. En `%USERPROFILE%\.imaginteca\config_local.py` (Windows) o
   `~/.imaginteca/config_local.py` (Linux/macOS) — **la mejor opción si quieres
   que sobreviva a las actualizaciones**.

**Reinicia el programa** después de cambiarlo. El botón **🛡️ Filtros** te dice
qué archivo se está usando.

## Tus claves

```python
RULE34_API_KEY = "tu_clave"
RULE34_USER_ID = "tu_id"
GELBOORU_API_KEY = "tu_clave"
GELBOORU_USER_ID = "tu_id"
DEVIANTART_CLIENT_ID = "tu_id"
DEVIANTART_CLIENT_SECRET = "tu_secreto"
TUMBLR_API_KEY = "tu_clave"
X_BEARER_TOKEN = "tu_token"
PINTEREST_ACCESS_TOKEN = "tu_token"
CF_CLEARANCE = "valor_de_la_cookie"
CF_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
```

| Plataforma | Dónde se consiguen |
|---|---|
| Rule34.xxx | Opciones de tu cuenta → *API Access Credentials* |
| Gelbooru | Opciones de tu cuenta → *API Access Credentials* |
| DeviantArt | `deviantart.com/developers` |
| Tumblr | `tumblr.com/oauth/apps` |
| X (Twitter) | App de desarrollador (**de pago**) |
| Pinterest | App aprobada + permiso del usuario |

> 🔐 **Tus claves no salen de tu ordenador.** No hay servidor propio, no hay
> telemetría y el paquete que se publica no incluye ninguna clave.

## Pixiv (con asistente)

Pixiv no permite el acceso anónimo: hay que usar **tu cuenta** con un *refresh
token*. El programa **no guarda tu contraseña**.

1. Haz **doble clic en `pixiv-token.exe`** (`pixiv-token` en Linux/macOS), en la
   misma carpeta que el programa.
2. Abre el enlace que muestra e inicia sesión en Pixiv.
3. El navegador acabará en una página de error: **copia la URL completa** (la que
   lleva `code=...`) y pégala en la ventana del asistente.
4. El asistente guarda el token solo. **Reinicia Imaginteca.**

Puedes revocar el acceso cerrando sesión en Pixiv.

## Ajustes que puedes cambiar

Cualquier constante en MAYÚSCULAS de `app/config.py` se puede sobrescribir desde
`config_local.py`. Las más útiles:

```python
# Contenido que NO quieres ver nunca (se suma a la lista negra del programa)
PROHIBITED_TAG_TOKENS = ["childporn", "child_porn"]     # etiquetas exactas
PROHIBITED_TAG_PREFIXES = ["pedo"]                      # empiezan por...
BLOCKED_PAID_DOMAINS = ["patreon.com", "onlyfans.com"]  # dominios de pago
EXCLUDED_TAG_TOKENS = ["gore", "vore", "guroli*"]        # tu lista ("*" = empieza por)
EXCLUDED_DOMAINS = ["deviantart.com"]
EXCLUDED_TEXT_TOKENS = ["commission open"]

# Ritmo de las peticiones (segundos entre peticiones al mismo sitio)
MIN_REQUEST_INTERVAL = 1.5

# Carpeta de salida por defecto
# DEFAULT_OUTPUT_DIR = r"C:\MiColeccion"
```

## Filtros que se aplican SIEMPRE

El programa aplica filtros **antes** de mostrarte o guardarte nada, y te dice el
motivo exacto de cada descarte:

- **Lista negra de contenido prohibido** (etiquetas y prefijos).
- **Plataformas de pago** (Patreon, Pixiv Fanbox, OnlyFans, Fansly, Unifans…): se
  descartan los enlaces a contenido exclusivo.
- **Contenido adulto (🔞):** por defecto **no** aparece. Si marcas *Permitir
  contenido adulto* en Opciones, sí.
- **Solo licencia liberada (⚖️):** opcional; solo procesa lo que declare
  CC0 / CC-BY / dominio público.
- **Tus exclusiones** de `config_local.py`.

En la app: **🛡️ Filtros** (o el botón *¿Qué se filtra?*) muestra los arrays tal
como están y la ruta del `config_local.py` en uso.

---

**Siguiente:** [Calidad y mejora](Calidad-y-mejora) ·
**¿Un sitio no responde?** [Problemas frecuentes](Problemas-frecuentes)
