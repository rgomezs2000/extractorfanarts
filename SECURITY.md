# Seguridad de Imaginteca

Este documento describe las medidas de **integridad del sistema** aplicadas al programa
(no tiene que ver con inicios de sesión ni con credenciales de las plataformas).

Se pueden comprobar en cualquier momento con:

```bat
Imaginteca.exe --seguridad
```

## Qué se protege

| Superficie | Riesgo | Medida |
|---|---|---|
| **Imágenes descargadas** | bomba de descompresión (pocos KB → gigapíxeles) | `Image.MAX_IMAGE_PIXELS` = **120 MP**; se rechazan las que lo superan antes de decodificar |
| **ZIP de ugoira (Pixiv)** | bomba de descompresión, zip-slip | máximo **5000** entradas, **60 MB** por entrada, **400 MB** total; rutas con `..` o absolutas rechazadas |
| **Paquete de actualización** | instalar un ZIP ajeno o con rutas que escapan | mismas validaciones + comprobación de que contiene la aplicación |
| **Nombres de archivo** | path traversal al guardar | se sanean separadores, `..`, caracteres prohibidos y nombres reservados de Windows (`CON`, `NUL`, `COM1`…) |
| **Procesos externos** | inyección de comandos | **nunca** `shell=True`; listas de argumentos, rutas absolutas y `timeout` |
| **Descargas HTTP** | respuestas gigantes | tope de bytes por petición (`max_bytes`) |
| **TLS** | interceptación | verificación de certificados **activa** (no se usa `verify=False`) |
| **Registros** | filtración de claves | las claves se enmascaran (`_SECRET_KEYS`) |
| **Configuración** | publicar claves | los `config_local.py` con claves no se versionan ni se empaquetan |

## Lo que NO se hace

- No se ejecuta código de los sitios (`eval`, `exec`, `pickle`, `marshal`): verificado, no hay
  ninguna llamada de ese tipo en el código.
- No se desactiva la verificación TLS.
- No se usa `shell=True` ni `os.system`.
- No se guardan credenciales en el registro ni en los paquetes publicados.

## Qué hacer si encuentras un problema

Abre un *issue* en el repositorio describiendo el caso **sin incluir claves**. Si afecta a la
integridad del sistema (por ejemplo, que una imagen o un ZIP pudiera escribir fuera de la
carpeta de salida), indícalo como **seguridad** para que se atienda primero.

## Dependencias

El programa usa un conjunto acotado de dependencias empaquetadas (PySide6, Pillow, httpx,
curl_cffi). Los avisos de seguridad de esas librerías se atienden actualizando las versiones
fijadas en `dependencies.json` y publicando una versión nueva.
