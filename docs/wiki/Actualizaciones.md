# Actualizaciones

Imaginteca **se actualiza sola** desde los Releases del repositorio: detecta la
versión nueva, la descarga, **comprueba que llegó íntegra** y la instala
reiniciándose.

## Cómo se hace

1. Pulsa **🔄 Actualizaciones** en la barra (o **Ayuda → Actualizaciones**).
2. El programa consulta las versiones publicadas y compara con la instalada.
3. Te dice **cuál tienes y cuál hay**, con la fecha, el peso de la descarga y las
   **notas de la versión**.
4. Si hay una nueva, pulsa **⬇️ Descargar e instalar**:
   - se descarga con **barra de progreso**;
   - se **comprueba el SHA-256** contra el que publica el Release: si no coincide,
     **no se instala nada** y te avisa;
   - se comprueba que el paquete **es de verdad la aplicación**;
   - al aceptar, el programa **se cierra, se instala y se vuelve a abrir solo**
     con la versión nueva.
5. Si **no hay nada nuevo**, te lo dice y ya está.

## Qué se conserva

**Todo lo tuyo**: tus imágenes, tus claves (`config_local.py`), tu historial y tus
registros. La actualización reemplaza **el programa**, no tus datos.

## Orden de versiones

Se comparan correctamente, incluidas las betas:

- `0.1.2-beta` es **más nueva** que `0.1.0-beta.1`
- `0.1.0` (final) es **más nueva** que cualquier `0.1.0-beta.x`

Las versiones **beta cuentan como versión nueva**, porque es lo que se publica por
ahora.

## Si algo impide actualizar

| Situación | Qué pasa |
|---|---|
| Sin conexión | Se avisa; no ocurre nada más |
| GitHub limita las consultas (HTTP 403) | Aviso claro: suele ser temporal (límite por conexión); espera unos minutos |
| El programa está en una carpeta protegida (`Program Files`, por ejemplo) | El reemplazo falla: el aviso lo explica y **el paquete queda descargado** para que lo hagas a mano |
| La descarga se corta | Se descarta: **nunca** se instala un archivo incompleto |
| **macOS / Linux** | Se descarga y se verifica igual, pero el reemplazo depende de cómo tengas instalada la aplicación: avisa para hacerlo a mano |

## Actualizar a mano

Siempre puedes bajar el paquete nuevo desde
**[Releases](https://github.com/rgomezs2000/extractorfanarts/releases)**,
descomprimirlo **encima** de la carpeta del programa (o en una carpeta nueva y
copiar tu `config_local.py`) y abrirlo. Verifica el `.sha256` como se explica en
[Instalación](Instalacion).

## Saber qué versión tienes

- **Ayuda → Acerca de** (o el botón **ℹ️**): versión instalada, entorno y rutas.
- `Imaginteca.exe --version` en una consola.
- El paquete se llama `Imaginteca-Windows.zip` / `-Linux` / `-macOS`, y el Release
  indica la etiqueta (`v0.1.2-beta`).

---

**Siguiente:** [Problemas frecuentes](Problemas-frecuentes) ·
**¿La actualización falla?** [Soporte técnico](Soporte-tecnico)
