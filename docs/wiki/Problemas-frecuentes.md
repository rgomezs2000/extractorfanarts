# Problemas frecuentes

Antes de preguntar, mira aquí: la mayoría de los avisos tienen explicación.

## Al abrir el programa

| Síntoma | Qué pasa y qué hacer |
|---|---|
| Aviso azul de Windows *«Windows protegió su PC»* | Es normal: no está firmado digitalmente. **Más información → Ejecutar de todas formas** |
| «Python DLL» u error al abrir | Estás ejecutando el `.exe` de la carpeta `build\`, que es un paso intermedio **incompleto**. Ejecuta siempre el de `dist\Imaginteca\` o el que descomprimiste |
| No arranca en Linux | Da permisos: `chmod +x Imaginteca` |
| macOS dice «no se puede abrir» | Clic derecho → **Abrir**, o `xattr -dr com.apple.quarantine Imaginteca.app` |

## Búsquedas

| Síntoma | Qué pasa y qué hacer |
|---|---|
| **0 resultados** pero la conexión va bien | En Rule34.xxx y Rule34 Paheal casi todo es adulto: marca **Permitir contenido adulto** en Opciones |
| Búsqueda **muy lenta** | Se espacian las peticiones a propósito (cortesía con los sitios). Con muchos hashtags o palabras clave tarda más |
| Una wiki o un sitio devuelve **403** | Suele ser una defensa contra programas. Anótalo y avísalo en el [foro](https://github.com/rgomezs2000/extractorfanarts/discussions) |
| **Cloudflare pide un CAPTCHA** (Rule34.xxx) | Ábrelo en tu navegador, resuélvelo y copia en `config_local.py` la cookie `cf_clearance` y tu `User-Agent` (F12 → Red → la primera petición → Cabeceras). **El programa nunca evade CAPTCHAs** |
| Las palabras clave del fediverso no encuentran nada | Si la instancia no permite buscar por texto sin cuenta, se buscan como etiqueta equivalente (`Lola Loud` → `#lola_loud`) |
| Pixiv no funciona | Necesita tu token: usa `pixiv-token.exe` (ver [Claves y configuración](Claves-y-configuracion)) y reinicia |

## Guardado y calidad

| Síntoma | Qué pasa y qué hacer |
|---|---|
| **Acceso denegado** al guardar en Imágenes o Descargas | Abre el programa **con doble clic desde el Explorador** (no desde una terminal restringida). Si sigue igual, ejecuta `Imaginteca.exe --selftest` y mira `selftest.txt` |
| El programa **no guarda donde quiero** | Puede que la carpeta no sea escribible: al arrancar avisa y, al descargar, prueba alternativas (Descargas, `~/.imaginteca/descargas`, una carpeta junto al programa) y dice cuál usó |
| Quiero el **archivo original** | No se conserva: todo se guarda en `.webp` procesado (ver [Calidad y mejora](Calidad-y-mejora)) |
| **El 🤖 Modo IA no mejora nada** (sigue con Lanczos) | Los motores pueden traer una etiqueta de Windows que les impide escribir su salida (en el registro verás `encode image … failed`). En la carpeta del programa: `icacls _internal\vendor /setintegritylevel Medium /T`. Si no, usa **✨ Mejorar calidad** sin modo IA |
| Veo **halos blancos** alrededor de las líneas | Actualiza a la última versión: el afilado está calibrado para no producirlos (se eliminó más del 90 % midiéndolo). Si los ves, mándanos un recorte por el foro |
| Una imagen sale **borrosa** tras mejorarla | Si el original era diminuto (menos de 300 px), el programa te avisa: **agrandar no crea detalle real** |

## Datos y privacidad

| Síntoma | Qué pasa y qué hacer |
|---|---|
| ¿Se envían mis claves o mis búsquedas a algún sitio? | **No.** No hay servidor propio ni telemetría: cada petición va directamente a la plataforma que consultas |
| ¿Qué se guarda en mi equipo? | Imágenes en tu carpeta de salida, y en `~/.imaginteca`: registro del día, historial y (si quieres) tus claves |
| ¿Puedo borrar el historial? | Sí: cierra el programa y borra `~/.imaginteca/historial.db` (y los `.log` que quieras) |
| Quiero empezar de cero | Borra `~/.imaginteca` y la carpeta de salida. El programa las vuelve a crear |

## Cualquier error raro

Mira el **registro del día**: ahí está exactamente qué respondió cada servidor.

- Windows: `%USERPROFILE%\.imaginteca\logs\app-AAAA-MM-DD.log`
- Linux/macOS: `~/.imaginteca/logs/app-AAAA-MM-DD.log`

Y si vas a pedir ayuda, incluye ese archivo y el `selftest.txt`: ver
**[Soporte técnico](Soporte-tecnico)**.

---

**¿No está tu caso?** Pregúntalo en el
**[foro](https://github.com/rgomezs2000/extractorfanarts/discussions)** o abre una
**[incidencia](https://github.com/rgomezs2000/extractorfanarts/issues)**.
