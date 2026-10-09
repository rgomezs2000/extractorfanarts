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

- `0.1.5-beta.7` es **más nueva** que `0.1.0-beta.1`
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

## Dependencias y consola (mantenimiento)

**Qué te dice y de dónde lo saca.** El informe dice, para cada dependencia
esencial (PySide6, shiboken6, Pillow, httpx, httpcore, h11, anyio, certifi y
curl_cffi), **la versión que está en uso**, **de dónde sale** y cuál es la **última
publicada**:

| Columna | Significa |
|---|---|
| **en uso** | La versión que el programa está usando **de verdad** (la del módulo cargado), no lo que digan los metadatos |
| **de dónde** | `paquete` (viaja dentro del programa), `vendor` (la carpeta del proyecto) o `en uso`/`entorno` (el Python del sistema) |
| **última** | La última publicada en PyPI |
| **estado** | `al día`, `HAY NOVEDAD`, `presente (sin comprobar)` o `NO ENCONTRADO` |

En una copia **empaquetada** las dependencias van **dentro** del ejecutable (no hay
`.dist-info` sueltos), por eso el informe lo comprueba **importando** cada módulo y
leyendo lo que anotó el flujo al empaquetar: así se ve la versión real en lugar de un
«no instalado» engañoso. Al final resume **cuántas están presentes** (por ejemplo
`9 de 9`) y el estado de los **motores de IA**.

Lo mismo está disponible en la consola, en los tres sistemas y en los dos canales:

```powershell
Imaginteca.exe --dependencias     # Windows
```
```bash
./Imaginteca --dependencias       # macOS y Linux
```

En **Ayuda → 🧩 Dependencias del sistema** puedes ver el estado del **intérprete de
Python**, de los **paquetes esenciales** (Qt/PySide6, Pillow, httpx, curl_cffi…) y de
los **motores de IA**, comparado con la **última versión publicada en PyPI**. El
informe sale **en pantalla y en la consola**.

- **Paquete de la release:** no hay nada que actualizar por separado; las
  dependencias (Python incluido) viajan dentro y se actualizan con
  **🔄 Actualizaciones**.
- **Ejecutando desde el código:** desde ese cuadro se **actualizan de una vez**. Se
  abre una **consola propia** que espera a que el programa se cierre, actualiza los
  paquetes, **vuelve a abrir el programa** y **deja la consola abierta** con el
  informe: la consola **no se cierra ni se reinicia**, solo se reinicia el
  programa.

## Desarrollo y producción (canal de la copia)

El programa sabe **de dónde viene** y cambia su comportamiento:

| Copia | Cómo se reconoce | Actualizaciones |
|---|---|---|
| **Desarrollo** | el código fuente (`python main.py`) y **cualquier compilación propia** (un `.exe` hecho con `scripts\build_exe.py` en tu equipo) | **Desactivadas**: ni el programa, ni las dependencias, ni el comando |
| **Producción** | los paquetes que reparte el proyecto: **instalador**, **portable** y la copia usada **desde la consola** | **Activadas**, en la interfaz y por comando |

La diferencia es una **marca de release** (`release.json`) que el flujo de publicación
escribe *dentro* del paquete (`scripts\marcar_release.py`); las copias hechas a mano no
la llevan. Se puede forzar en `config_local.py` con `CANAL = "desarrollo"` o
`CANAL = "produccion"`. En **Ayuda → Acerca de** se ve el canal de la copia que estás
usando.

### Comandos de instalación, por sistema

```powershell
# Windows (asistente; también admite instalación silenciosa)
.\Imaginteca-<versión>-windows-installer.exe
.\Imaginteca-<versión>-windows-installer.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```
```bash
# macOS (montar el .dmg y copiar la aplicación)
hdiutil attach Imaginteca-<versión>-macos-installer.dmg
cp -R "/Volumes/Imaginteca <versión>/Imaginteca.app" /Applications/
hdiutil detach "/Volumes/Imaginteca <versión>"
```
```bash
# Linux (Debian, Ubuntu, Mint…)
sudo apt install ./Imaginteca-<versión>-linux-installer.deb
sudo dpkg -i      ./Imaginteca-<versión>-linux-installer.deb   # alternativa
```

### Comandos de actualización, por sistema

Los tres hacen lo mismo: comprueban, descargan, **verifican la huella**, reemplazan la
copia (conservando tus claves), borran los restos y **vuelven a abrir el programa**,
dejando la consola abierta con el informe.

```powershell
# Windows
Imaginteca.exe --comprobar-actualizacion
Imaginteca.exe --actualizar
```
```bash
# macOS / Linux
./Imaginteca --comprobar-actualizacion
./Imaginteca --actualizar
```

En las copias de **desarrollo** estos comandos están desactivados (`--actualizar`
avisa y no hace nada).

---

## Beta definitiva y releases oficiales

Hasta la `0.1.5-beta.7` las versiones se publicaban como **pre-release**. Desde la
**`0.1.5-beta.7` (beta definitiva)**, los releases se publican como **oficiales**: la
versión sigue llamándose «beta», pero es la **última versión** del proyecto y la
descarga recomendada. El programa sabe que una versión es beta por **su nombre**.

## Saber qué versión tienes

- **Ayuda → Acerca de** (o el botón **ℹ️**): versión instalada, entorno y rutas.
- `Imaginteca.exe --version` en una consola.
- El paquete se llama `Imaginteca-Windows.zip` / `-Linux` / `-macOS`, y el Release
  indica la etiqueta (`v0.1.5-beta.7`).

---

**Siguiente:** [Problemas frecuentes](Problemas-frecuentes) ·
**¿La actualización falla?** [Soporte técnico](Soporte-tecnico)
