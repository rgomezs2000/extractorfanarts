# Seguridad de Imaginteca

Este documento describe las medidas de **integridad del sistema** aplicadas al programa
(no tiene que ver con inicios de sesión ni con credenciales de las plataformas).

**Se aplican en Windows, macOS y Linux.** Se pueden comprobar en cualquier sistema con:

```bat
Imaginteca.exe --seguridad        :: Windows
./Imaginteca --seguridad          # macOS / Linux
```

La propia comprobación indica el sistema en el que se ejecuta y los límites activos.

## Qué se protege (común a los tres sistemas)

| Superficie | Riesgo | Medida |
|---|---|---|
| **Imágenes descargadas** | bomba de descompresión (pocos KB → gigapíxeles) | `Image.MAX_IMAGE_PIXELS` = **120 MP**; se rechazan antes de decodificar |
| **ZIP de ugoira (Pixiv)** | bomba de descompresión, zip-slip | máx. **5000** entradas, **60 MB** por entrada, **400 MB** total; rutas con `..` o absolutas rechazadas |
| **Paquete de actualización** | instalar un ZIP ajeno o con rutas que escapan | mismas validaciones + comprobar que contiene la aplicación |
| **Nombres de archivo** | path traversal al guardar | se sanean separadores (`/` y `\`), `..`, caracteres prohibidos y nombres reservados de Windows |
| **Procesos externos** | inyección de comandos | **nunca** `shell=True`; listas de argumentos, rutas absolutas y `timeout` |
| **Descargas HTTP** | respuestas gigantes | tope de bytes por petición (`max_bytes`) |
| **TLS** | interceptación | verificación de certificados **activa** |
| **Registros** | filtración de claves | las claves se enmascaran |

## Medidas por sistema

| Medida | Windows | macOS | Linux |
|---|---|---|---|
| Tope de píxeles y validación de ZIP | ✅ | ✅ | ✅ |
| Nombres saneados (incluye reglas de Windows, inocuas en Unix) | ✅ | ✅ | ✅ |
| Archivos con claves a **0600** (solo su dueño) | — (ACL del perfil) | ✅ `chmod` | ✅ `chmod` |
| Carpeta `~/.imaginteca` a **0700** | — (ACL del perfil) | ✅ `chmod` | ✅ `chmod` |

En Windows los permisos POSIX no existen con esa semántica: el archivo vive en el perfil del
usuario y hereda las ACL de Windows. En macOS y Linux se aplica además `chmod` restrictivo
al archivo de configuración con claves y a la carpeta privada.

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
