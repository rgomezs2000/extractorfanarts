# ✅ Requisitos

Lo que hace falta para **usar** Imaginteca y lo que hace falta para **compilarla**
(no es lo mismo). Si solo quieres usarla, con un sistema moderno y 1 GB libre vas
sobrado: **el programa ya trae todo lo que necesita dentro**.

## Para usarlo (paquete de la release)

| | Mínimo | Recomendado |
|---|---|---|
| **Sistema** | Windows 10 · macOS 11 · cualquier Linux de escritorio | Windows 11 · macOS 13+ · Ubuntu 22.04+ |
| **Arquitectura** | 64 bits (x86-64; Apple Silicon con Rosetta o binario nativo) | 64 bits nativo |
| **Espacio en disco** | ~1,5 GB (el paquete ocupa entre 150 y 560 MB al descomprimirlo) | 5 GB o más para tu colección |
| **Memoria** | 4 GB | 8 GB o más |
| **Pantalla** | 1024×768; la ventana funciona desde 728×695 | 1920×1080 |
| **Conexión** | Necesaria para buscar y descargar (y para las actualizaciones) | Banda ancha |
| **Python** | **No hace falta instalarlo**: va incluido en el paquete | — |
| **Tarjeta gráfica** | **Opcional**: solo para el **🤖 Modo IA** (Vulkan) | GPU Intel/AMD/NVIDIA con Vulkan |

**Nada más**: no hay que instalar dependencias, ni registrarse, ni tener una cuenta
en ninguna plataforma (salvo las claves que quieras poner para Rule34, Gelbooru,
Pixiv…, que son **opcionales**).

### El 🤖 Modo IA (opcional)

- Necesita **Vulkan**. Funciona en GPUs integradas Intel, AMD y NVIDIA recientes.
- Si no hay GPU compatible, el programa **lo dice y usa el reescalado clásico**:
  todo lo demás funciona igual.
- Los motores (Real-ESRGAN y waifu2x) **ya vienen en el paquete**.
- Si el motor se queda sin poder escribir su resultado en Windows (etiqueta de
  integridad), mira **[Problemas frecuentes](Problemas-frecuentes)**.

### Permisos y carpetas

- Escritura en la carpeta donde descomprimas el programa y en tu carpeta de
  **Imágenes** (o en la que elijas como salida).
- Si el programa está en una carpeta protegida (`Program Files`), las
  **actualizaciones** no podrán reemplazarlo: el aviso lo explica y el paquete
  queda descargado para hacerlo a mano.

## Para compilarlo desde el código

| | Necesitas |
|---|---|
| **Python** | **3.11 o superior** (probado con 3.12) |
| **Paquetes** | PySide6, Pillow, httpx, curl_cffi y certifi (el proyecto los instala en `vendor/` con `scripts\setup_vendor.py`) |
| **Empaquetado** | PyInstaller (también en `vendor/`) |
| **Sistema** | **PyInstaller no compila cruzado**: cada paquete se genera en su sistema |
| **Motores de IA** | Opcionales al compilar: `python scripts\setup_vendor.py vendor --solo-ia` |

Los tres paquetes (Windows, macOS y Linux) los genera el flujo incluido en
`.github/workflows/build.yml` en cada etiqueta.

### Comprobar las dependencias desde el programa

El menú **Ayuda → 🧩 Dependencias del sistema** muestra el estado de:

- el **intérprete de Python** que se está usando,
- los **paquetes esenciales** (Qt/PySide6, Pillow, httpx, curl_cffi y sus
  dependencias), comparando la versión instalada con la **última publicada en
  PyPI**,
- los **motores de IA** presentes.

El informe sale **en pantalla y en la consola**, y desde ahí mismo se pueden
**actualizar de una vez** (cuando se ejecuta desde el código). Al actualizar:

1. Se abre una **consola propia** que muestra el proceso.
2. El programa **se cierra** (si no, Windows no deja reemplazar las DLL de Qt).
3. La consola espera, **actualiza los paquetes** y **vuelve a abrir el programa**.
4. La consola **no se cierra ni se reinicia**: queda con el informe para leerlo.
   Solo se reinicia el programa.

> Si usas el **paquete de la release**, no hay nada que actualizar por separado:
> las dependencias (incluido Python) viajan dentro y se actualizan con
> **[🔄 Actualizaciones](Actualizaciones)**.

---

**Siguiente:** [Instalación](Instalacion) · [Primeros pasos](Guia-rapida)
