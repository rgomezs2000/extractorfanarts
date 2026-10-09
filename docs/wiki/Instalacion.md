# Instalación

> **Antes de empezar:** comprueba los **[Requisitos](Requisitos)** (sistema,
> espacio, pantalla y el modo IA). Se tarda un minuto.

**Imaginteca no se instala**: se descomprime y se ejecuta. No hay que pagar nada,
no hay que registrarse y no se recogen datos.

## 1. Descarga

Ve a **[Releases](https://github.com/rgomezs2000/extractorfanarts/releases)** y
baja el paquete de tu sistema:

| Sistema | Archivo | Tamaño aproximado |
|---|---|---|
| Windows | `Imaginteca-Windows.zip` | ~147 MB |
| Linux | `Imaginteca-Linux.zip` | ~240 MB |
| macOS | `Imaginteca-macOS.zip` | ~557 MB |

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
  - La primera vez puede salir el aviso azul *«Windows protegió su PC»*. Es
    normal: el programa no está firmado digitalmente (un certificado de firma es
    de pago), no es un virus. Pulsa **Más información → Ejecutar de todas
    formas**.
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

## 4. Primer arranque

Al abrirlo por primera vez se crea la carpeta de datos:

| Sistema | Carpeta |
|---|---|
| Windows | `%USERPROFILE%\.imaginteca` |
| Linux / macOS | `~/.imaginteca` |

Ahí viven tus **registros** (`logs`), tu **historial** (`historial.db`) y,
si quieres, tus **claves** (`config_local.py`).

Las imágenes se guardan en la **carpeta de Imágenes** del sistema, subcarpeta
`Imaginteca` (la puedes cambiar con el botón **📂 Carpeta** o el atajo `Ctrl+O`).

## 5. Comprueba que todo está bien

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
