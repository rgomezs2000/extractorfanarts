# 📣 Foro · Anuncios

**Para qué:** avisos del proyecto: **versiones nuevas**, cambios importantes,
plataformas que se caen y arreglos.

> **Solo lectura para el resto:** esta página la actualiza el autor. Si quieres
> comentar algo de un anuncio, hazlo en el tablero que corresponda —normalmente
> [Soporte técnico](Foro-Soporte-tecnico) o [Ideas](Foro-Ideas)— mencionando el
> anuncio.

## Cómo enterarte de las versiones nuevas

- **Dentro del programa:** 🔄 **Actualizaciones** (o **Ayuda → Actualizaciones**).
  Detecta la versión nueva, la descarga, **verifica el SHA-256** y la instala
  reiniciándose sola. Ver [Actualizaciones](Actualizaciones).
- **En el repositorio:** [Releases](https://github.com/rgomezs2000/extractorfanarts/releases).
- **Aquí:** en esta página.

---

## Anuncios

### 2026-10-09 · v0.1.5-beta.7 — la beta definitiva (7.ª entrega)

- **Chocolatey y winget** se suman a Scoop: los tres manifiestos viajan en el release.
- **Instalando con el asistente no aparece el aviso azul**: el instalador quita la marca
  de internet de los ejecutables que deja.

### 2026-10-09 · v0.1.5-beta.6 — la beta definitiva (6.ª entrega)

- **Scoop va dentro del release**: `imaginteca.json` se publica como adjunto de cada
  versión, así que instalar sin el aviso de Windows es **una sola orden** (sin crear
  ningún repositorio aparte).
- **La firma es automática**: cada compilación firma el ejecutable si hay certificado.

### 2026-10-09 · v0.1.5-beta.5 — la beta definitiva (5.ª entrega)

- **Informe de dependencias completo**: se corrigió el nombre de importación
  (`Pillow` → `PIL`) y se anota lo que va dentro al compilar. Ahora dice **9 de 9** en
  desarrollo y en la copia empaquetada.
- **Firma digital cableada**: ejecutable, asistente e instalador se firman solos en
  cuanto haya certificado (incluido Microsoft Trusted Signing). Sin certificado no se
  firma nada: el aviso de SmartScreen solo lo quita un certificado de una autoridad.

### 2026-10-09 · v0.1.5-beta.4 — la beta definitiva (4.ª entrega)

- **Informe de dependencias arreglado**: ya distingue la versión **en uso** de cada
  paquete y **de dónde sale** (paquete, vendor o entorno). Antes, en la copia
  empaquetada, aparecía «NO instalado» aunque las dependencias van dentro.
- **Comando nuevo**: `Imaginteca --dependencias` (también en macOS y Linux).

### 2026-10-09 · v0.1.5-beta.3 — la beta definitiva (3.ª entrega)

- **Nueva página [Qué se descarga](Contenido)**: fanarts, imágenes oficiales, cómics y
  fancomics, y el apartado **NSFW (+18)** completo (ratings, qué lo define, qué se
  extrae y qué no).
- **Verificación de edad**: con el 🔞 marcado, al **Buscar** o **Descargar** se pide la
  fecha de nacimiento; **menores de 18 no buscan ni descargan** contenido adulto. Tu
  fecha no se guarda ni se envía a ningún sitio.

### 2026-10-09 · v0.1.5-beta.2 — la beta definitiva (2.ª entrega)

- **Desarrollo vs producción**: las copias de desarrollo (código fuente o
  compilaciones propias) tienen las **actualizaciones desactivadas**; las de
  producción (instalador, portable y consola) las tienen **activadas**.
- **Comandos para Windows, macOS y Linux**: `--comprobar-actualizacion` y
  `--actualizar`, más los comandos de instalación de cada sistema.

### 2026-10-09 · v0.1.5-beta — la beta definitiva

- **`v0.1.5-beta` se publica como release OFICIAL** (ya no como pre-release): es la
  última versión del proyecto y la descarga recomendada.
- Reúne todo lo de las betas anteriores: tres modos de instalación, actualizaciones
  limpias, requisitos, dependencias del sistema, plataformas documentadas y copyright
  dinámico.

### 2026-10-09 · v0.1.4-beta

- **Tres modos de instalación**: portátil (`.zip` y `.tar.gz`), **instalador con
  asistente** para Windows, macOS y Linux, y **consola**.
- **Actualizaciones limpias**: al actualizar no queda nada viejo (se borran la
  versión anterior, los temporales y la descarga) y **tus claves se conservan**.
- Nuevo comando de consola: `Imaginteca --comprobar-actualizacion` y
  `Imaginteca --actualizar`.

### 2026-10-09 · v0.1.3-beta

- **[Requisitos](Requisitos)**, la página nueva: qué necesitas para usarlo y qué
  para compilarlo (y que el modo IA es opcional).
- **Ayuda → 🧩 Dependencias del sistema**: estado de Python, de los paquetes
  esenciales y de los motores de IA, con opción de **actualizarlos de una vez**.
- **La consola de mantenimiento ya no se cierra**: al actualizar el programa o sus
  dependencias se abre una consola con el informe que permanece abierta (el
  programa sí se reinicia).

### 2026-10-09 · v0.1.2-beta

- Nueva **versión 0.1.2-beta**.
- El **ejecutable muestra su versión y su copyright** en las propiedades del
  archivo (Detalles).
- **Copyright dinámico**: «© 2026 InfoArte» y, al cambiar el año,
  «© 2026-2027 InfoArte».

### 2026-10-09 · v0.1.0-beta.4

- **«Acerca de» sin datos personales**: **InfoArte** y **Discord `rgomezs2010`**,
  sin nombre propio, sin correo y sin el repositorio.
- **Nueva ventana de licencia** dentro del programa («📜 Ver licencia completa»).
- El autor pasa a ser **InfoArte** en la documentación y en la licencia.
- **Copyright dinámico**: el aviso pasa solo de «© 2026 InfoArte» a
  «© 2026-2027 InfoArte» cuando cambie el año; no hay que tocar nada.
- **Soporte de plataformas documentado**: [redes sociales](Redes-sociales),
  [boorus](Boorus) y [fandoms](Fandoms) **uno por uno**, con lo que busca cada una,
  sus claves, sus límites y las que vendrán. También en la ayuda del programa
  (`F1`) y resumido en las [preguntas frecuentes](Preguntas-frecuentes).

### 2026-10-09 · v0.1.0-beta.3

- **Documentación reescrita y al día**: guía del usuario, `LEEME-PRIMERO.txt` y
  README técnico, con la versión nueva y enlazados con esta wiki.
- **El foro ya está abierto** (estás en él): soporte técnico, fallos, ideas,
  plataformas, datasets, presentaciones y anuncios.
- **Contacto privado: Discord `rgomezs2010`**.
- El publicador de la wiki **protege los mensajes del foro** al actualizar la
  documentación.

### 2026-10-09 · v0.1.0-beta.2

- **Barra de herramientas** con lo esencial y lo de apoyo, menús **Archivo** y
  **Ayuda**, y atajos (`Ctrl+B`, `Ctrl+D`, `Ctrl+L`, `Ctrl+O`, `F1`).
- **Ayuda dentro del programa** con `F1`: el manual completo, con **índice** y
  buscador.
- **Acerca de**: tu versión, el autor, la licencia y dónde queda todo.
- **Actualizador**: busca la versión nueva, la descarga, comprueba la huella y la
  instala reiniciando.
- **Licencia v2**: la **garantía corre por cuenta del autor**.
- **Este foro**: la comunidad pasa a vivir en la wiki.
- El proyecto se llama **Imaginteca** (antes «ExtractorFanarts»).

### 2026-10-08 · v0.1.0-beta.1 — primera versión pública

- Búsqueda y descarga desde **8 redes sociales, 14 booros y wikis de fandom**.
- Galería con visor y guardado individual por clic derecho.
- Todo en **WebP**, con **mejora de calidad** por tramos y **modo IA**
  (Real-ESRGAN / waifu2x).
- Filtros legales y éticos en el núcleo.
- Paquetes para **Windows, macOS y Linux** con huella `.sha256`.

*El detalle completo está en [Historial de versiones](Historial-de-versiones).*

---

**[← Volver al foro](Foro)** · [Historial de versiones](Historial-de-versiones) ·
[Actualizaciones](Actualizaciones)
