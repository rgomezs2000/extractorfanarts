# Instalación

> **Antes de empezar:** comprueba los **[Requisitos](Requisitos)** (sistema,
> espacio, pantalla y el modo IA). Se tarda un minuto.

**Hay tres formas de tenerlo**, las tres con el mismo programa y sin pagar nada,
sin registrarse y sin recoger datos:

| Forma | Archivo | Para quién |
|---|---|---|
| **1. Portátil** | `Imaginteca-Windows.zip`, `Imaginteca-Linux.tar.gz`, `Imaginteca-macOS.tar.gz` (y los `.zip`) | Probar sin tocar el sistema |
| **2. Instalador** | `…-windows-installer.exe`, `…-macos-installer.dmg`, `…-linux-installer.deb` | El día a día: asistente, accesos directos y desinstalador |
| **3. Consola** | `Imaginteca --actualizar` | Terminal y automatización |

## 1. Descarga

Ve a **[Releases](https://github.com/rgomezs2000/extractorfanarts/releases)** y
baja el paquete de tu sistema:

| Sistema | Portátil | Instalador |
|---|---|---|
| Windows | `Imaginteca-Windows.zip` | `Imaginteca-<versión>-windows-installer.exe` |
| Linux | `Imaginteca-Linux.zip` · `Imaginteca-Linux.tar.gz` | `Imaginteca-<versión>-linux-installer.deb` |
| macOS | `Imaginteca-macOS.zip` · `Imaginteca-macOS.tar.gz` | `Imaginteca-<versión>-macos-installer.dmg` |

Junto a cada paquete hay un `.sha256`. **Comprueba la descarga** (es lo que
garantiza que el archivo llegó íntegro y no manipulado):

```powershell
# Windows (PowerShell)
Get-FileHash .\Imaginteca-Windows.zip -Algorithm SHA256
```

```bash
# Linux / macOS
shasum -a 256 Imaginteca-*.zip
```

El resultado tiene que coincidir con el contenido del `.sha256`.

## 2. Descomprime

Descomprime el `.zip` **completo** en una carpeta tuya, por ejemplo
`C:\Imaginteca` o `~/Imaginteca`.

> ⚠️ **No lo ejecutes desde dentro del archivo comprimido**: el programa necesita
> la carpeta `_internal` que va a su lado.

## 3. Ábrelo

- **Windows:** doble clic en **`Imaginteca.exe`**.
  - La primera vez puede salir el aviso azul *«Windows protegió su PC»*. Si el
    paquete viene **firmado**, no aparece; si no, es normal (un certificado de firma
    es de pago), y no es un virus. Pulsa **Más información → Ejecutar de todas
    formas**. El proyecto tiene la **firma cableada** para cuando haya certificado.
  - Si sigue bloqueado: clic derecho en el `.exe` → **Propiedades** → marca
    **Desbloquear** → **Aceptar**.
- **macOS:** si dice *«no se puede abrir»*, clic derecho en la aplicación →
  **Abrir**. Si se resiste:
  ```bash
  xattr -dr com.apple.quarantine Imaginteca.app
  ```
- **Linux:** da permisos de ejecución la primera vez:
  ```bash
  chmod +x Imaginteca
  ./Imaginteca
  ```

## 4. Sin la ventana azul (gratis)

El aviso azul no se puede quitar con código: hace falta un certificado de una
autoridad, y **no hay ninguno gratuito**. La vía **gratuita** que funciona es
**Scoop**, que descarga el paquete sin la marca de internet que dispara SmartScreen:

```powershell
scoop bucket add rgomezs2000 https://github.com/rgomezs2000/scoop-bucket
scoop install imaginteca      # sin aviso; se actualiza con «scoop update imaginteca»
```

También sirven **Chocolatey** y **winget** (gratis, con revisión), y con el tiempo la
**reputación** hace que SmartScreen deje de avisar. Los detalles, en el repositorio
([`scoop/README.md`](https://github.com/rgomezs2000/extractorfanarts/blob/main/scoop/README.md)).

## 5. O instálalo con el asistente

Si prefieres instalarlo como cualquier otro programa (con accesos directos y
desinstalador), usa el **instalador** de tu sistema:

- **Windows** (`…-windows-installer.exe`): doble clic y sigue el **asistente**
  (idioma, licencia, carpeta, accesos directos). Se instala **por usuario** en
  `%LOCALAPPDATA%\Programs\Imaginteca` (sin pedir administrador), deja acceso en el
  menú Inicio y, si quieres, en el Escritorio. Al instalar encima de una versión
  anterior, **tus claves se conservan**.
- **macOS** (`…-macos-installer.dmg`): ábrelo y **arrastra Imaginteca a
  Aplicaciones**.
- **Linux** (`…-linux-installer.deb`):
  ```bash
  sudo apt install ./Imaginteca-<versión>-linux-installer.deb
  ```
  Queda en `/opt/imaginteca` con el lanzador `imaginteca`, su icono y su entrada de
  menú. Se desinstala con `sudo apt remove imaginteca`.

## 6. Desde la consola

```bash
Imaginteca --selftest                 # estado del entorno → selftest.txt
Imaginteca --version                  # versión instalada
Imaginteca --comprobar-actualizacion  # ¿hay versión nueva? (no instala)
Imaginteca --actualizar               # descarga, verifica e instala (limpio) y reinicia
```

`--actualizar` muestra el proceso paso a paso y hace un **reemplazo limpio**:
conserva tus claves, borra la versión anterior, los temporales y el paquete
descargado, y vuelve a abrir el programa (la consola se queda abierta).

## 7. Primer arranque

Al abrirlo por primera vez se crea la carpeta de datos:

| Sistema | Carpeta |
|---|---|
| Windows | `%USERPROFILE%\.imaginteca` |
| Linux / macOS | `~/.imaginteca` |

Ahí viven tus **registros** (`logs`), tu **historial** (`historial.db`) y,
si quieres, tus **claves** (`config_local.py`).

Las imágenes se guardan en la **carpeta de Imágenes** del sistema, subcarpeta
`Imaginteca` (la puedes cambiar con el botón **📂 Carpeta** o el atajo `Ctrl+O`).

## 8. Comprueba que todo está bien

En una consola, dentro de la carpeta del programa:

```powershell
Imaginteca.exe --selftest
```

Genera un archivo **`selftest.txt`** con el estado de bibliotecas, carpetas,
permisos, motores de IA y si la ventana cabe en tu pantalla. Es lo primero que se
pide cuando pides ayuda (ver [Soporte técnico](Soporte-tecnico)).

---

## Qué hay en la carpeta

| Archivo | Para qué sirve |
|---|---|
| `Imaginteca.exe` | **El programa.** Es lo único que tienes que abrir |
| `pixiv-token.exe` | Asistente para conseguir tu token de Pixiv (opcional) |
| `config_local.py` | Tus claves y ajustes (viene como plantilla vacía) |
| `README.md` | La guía del usuario completa (también dentro del programa, con `F1`) |
| `LEEME-PRIMERO.txt` | Los primeros pasos, en texto plano |
| `LICENSE` | Las condiciones de uso |
| `THIRD-PARTY-NOTICES.txt` | Licencias de las bibliotecas incluidas |
| `_internal/` | Biblioteca del programa. **No la borres ni la muevas** |

Puedes mover la carpeta entera donde quieras, pero mantén esos archivos **juntos**.

---

**Siguiente:** [Guía rápida](Guia-rapida) · **Si algo falla:**
[Problemas frecuentes](Problemas-frecuentes)
