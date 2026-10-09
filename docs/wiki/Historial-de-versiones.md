# Historial de versiones

## v0.1.5-beta.4 — 9 de octubre de 2026 · la beta definitiva (4.ª entrega)

**El informe de dependencias ahora dice la verdad**
- Antes, dentro del paquete las dependencias salían como «NO instalado»: van
  **dentro** del ejecutable y no quedan sus metadatos. Ahora se comprueba
  **importando** cada módulo, se lee su versión real y se indica **de dónde sale**
  (`paquete`, `vendor` o el entorno), además de lo que anotó el flujo al empaquetar.
- Resumen final: **cuántas están presentes** (por ejemplo `9 de 9`) y el estado de los
  motores de IA.
- Comando nuevo en los tres sistemas: **`Imaginteca --dependencias`** (Windows:
  `Imaginteca.exe --dependencias`).

---

## v0.1.5-beta.3 — 9 de octubre de 2026 · la beta definitiva (3.ª entrega)

**Contenido y contenido adulto**
- Página nueva **[Qué se descarga](Contenido)**: fanarts, imágenes oficiales, **cómics
  y fancomics**, qué se guarda y qué **nunca** se descarga.
- Dentro, el apartado **NSFW (+18)**: qué significa, los **ratings**, los elementos que
  lo definen (fluidos, partes del cuerpo, atuendo explícito y sugestivo, actividades
  individuales y colectivas), **qué se puede extraer y qué no** y las condiciones de
  acceso.
- **Sin el 🔞 marcado nada se bloquea**: Buscar y Descargar siguen funcionando y el
  contenido adulto (`questionable`/`explicit`) se filtra; la lista negra y el bloqueo
  de plataformas de pago se aplican siempre, marques o no el 🔞.
- **Verificación de edad en el programa**: al marcar «🔞 Contenido adulto» y pulsar
  **Buscar** (o **Descargar**) se pide la **fecha de nacimiento** y se calcula la edad
  contra la fecha actual. Con **menos de 18 años no se busca ni se descarga nada**: se
  avisa y la casilla se desmarca. La fecha **no se guarda ni se envía**.

---

## v0.1.5-beta.2 — 9 de octubre de 2026 · la beta definitiva (2.ª entrega)

**Canal: desarrollo y producción**
- El programa distingue de dónde viene: **desarrollo** (código fuente o compilación
  propia) y **producción** (instalador, portable o consola, con la marca de release
  `release.json` que escribe el flujo).
- En **desarrollo** las actualizaciones quedan **desactivadas**: el programa, sus
  dependencias, la interfaz y el comando `--actualizar`. En **producción** se activan.
- En **Ayuda → Acerca de** se ve el canal de la copia.

**Comandos para los tres sistemas**
- Actualización: `Imaginteca --comprobar-actualizacion` y `Imaginteca --actualizar`
  (Windows y Unix), con la consola visible (Terminal en macOS y el emulador de
  terminal del escritorio en Linux).
- Instalación: instalador `.exe` en Windows (con modo silencioso), `.dmg` + copia a
  Aplicaciones en macOS y `apt install ./…deb` en Linux.

---

## v0.1.5-beta — 9 de octubre de 2026 · **la beta definitiva**

**Release oficial.** Desde esta versión los releases se publican como **oficiales**
(`prerelease: false`): `v0.1.5-beta` es la **última versión** del proyecto y la descarga
recomendada. Las anteriores (`v0.1.0-beta.1` … `v0.1.4-beta`) quedan como pre-release en
el historial. La versión sigue llamándose «beta», y el programa la reconoce por su
nombre.

**Lo que incluye** (todo lo de las betas anteriores, ya estable):
- **Tres modos de instalación**: portátil (`.zip` y `.tar.gz`), **instaladores con
  asistente** para Windows (Inno Setup), macOS (`.dmg`) y Linux (`.deb`), y **consola**.
- **Actualizaciones limpias**: conservan tus claves y borran la versión anterior, los
  temporales y la descarga; comandos `--comprobar-actualizacion` y `--actualizar`.
- **[Requisitos](Requisitos)**, **[Plataformas](Plataformas)** (redes, boorus y
  fandoms), **[Dependencias del sistema](Actualizaciones)** y copyright dinámico
  (`© 2026 InfoArte`).

---

## v0.1.4-beta — 9 de octubre de 2026

**Instaladores y modos de instalación**
- **Tres modos**: **portátil** (`.zip` y `.tar.gz`), **instalador con asistente**
  (`…-windows-installer.exe` con Inno Setup, `…-macos-installer.dmg` con acceso a
  Aplicaciones y `…-linux-installer.deb`) y **consola**.
- Los instaladores se generan en cada sistema dentro del flujo de compilación y se
  publican junto a los paquetes portátiles, con su `.sha256`.
- El instalador de Windows instala **por usuario** (sin administrador), deja accesos
  directos y desinstalador, y **conserva `config_local.py`** al actualizar.

**Actualizaciones limpias y comando de consola**
- `--comprobar-actualizacion` y `--actualizar`: mantenimiento desde la consola, con
  el proceso paso a paso (versión, paquete, descarga y huella SHA-256).
- La actualización ahora es **limpia**: descomprime aparte, conserva tus claves,
  reemplaza la carpeta entera y **borra la versión anterior, los temporales y el
  paquete descargado**.

---

## v0.1.3-beta — 9 de octubre de 2026

**Requisitos y dependencias**
- Página nueva **[Requisitos](Requisitos)** (en la wiki y en la ayuda del programa,
  **antes** de Instalación): qué hace falta para usarlo, qué hace falta para
  compilarlo y qué es opcional (el modo IA).
- **Ayuda → 🧩 Dependencias del sistema**: comprueba el **intérprete de Python**,
  los **paquetes esenciales** (frente a la última versión de PyPI) y los **motores
  de IA**; el informe sale **en pantalla y en la consola** y se pueden
  **actualizar de una vez**.

**Consola de mantenimiento**
- Al actualizar el programa **o sus dependencias** se abre una **consola propia**
  con el proceso y el informe, y **no se cierra ni se reinicia**: el programa se
  reinicia solo y la consola se queda para leerla.

---

## v0.1.2-beta — 9 de octubre de 2026

**Versión y propiedades del ejecutable**
- La versión pasa a **0.1.2-beta**.
- El ejecutable lleva **recurso de versión**: en «Propiedades → Detalles» se ven el
  **producto**, la **versión** y el **copyright** («{© 2026 InfoArte} · Todos los
  derechos reservados»), calculado con el año en curso al compilar.

**Copyright dinámico**
- El aviso es «© 2026 InfoArte» y pasa solo a «© 2026-2027 InfoArte» cuando cambia
  el año: en el programa, en la ayuda `F1` y en la documentación
  (`scripts\actualizar_copyright.py`).

---

## v0.1.0-beta.4 — 9 de octubre de 2026

**Sin datos personales**
- **El cuadro «Acerca de» ya no muestra nada personal**: ni nombre propio, ni
  correo, ni el repositorio. Aparece **InfoArte** y el contacto privado
  (**Discord `rgomezs2010`**).
- **El autor pasa a ser InfoArte** en todos los documentos y en la licencia, con
  el aviso **«© 2026 InfoArte · Todos los derechos reservados»**.
- Las rutas de «Acerca de» se muestran como `%USERPROFILE%…`, así que no aparece
  el nombre de usuario del equipo.
- **Nueva ventana de licencia**: «📜 Ver licencia completa» abre el texto entero
  dentro del programa (con botón para copiarlo), en vez de remitir a un archivo.
- **Aviso de copyright dinámico**: «© 2026 InfoArte» mientras el año en curso sea
  el de creación, y «© 2026-2027 InfoArte» en cuanto cambie el año. Lo calcula el
  programa en cada arranque (y `scripts\actualizar_copyright.py` lo pone al día en
  los documentos).

**Soporte de plataformas**
- Páginas nuevas en la wiki: **[Soporte de plataformas](Plataformas)**,
  **[Redes sociales](Redes-sociales)**, **[Boorus](Boorus)** y
  **[Fandoms](Fandoms)**: cada plataforma explicada —qué busca, qué claves pide,
  qué límites tiene y de qué va— y **las que vendrán**.
- La **guía del usuario** (y por tanto la ayuda `F1` del programa) incluye el mismo
  detalle, plataforma por plataforma.
- Las **[preguntas frecuentes](Preguntas-frecuentes)** responden de un vistazo qué
  **redes**, qué **boorus** y qué **fandoms** son compatibles.

---

## v0.1.0-beta.3 — 9 de octubre de 2026

**Documentación**
- **Redacción limpia y actualizada** de los tres documentos: la guía del usuario,
  el `LEEME-PRIMERO.txt` y el README técnico, con la versión al día.
- **La wiki con su foro es la fuente de más información**: los tres documentos
  enlazan con ella desde el principio.
- **Contacto privado unificado: Discord `rgomezs2010`** (fallos de seguridad y
  asuntos que no deban ser públicos). No se publica ningún correo.

**Wiki y foro**
- La **wiki está publicada**: documentación y **9 tableros de foro**, con índice,
  barra lateral y pie.
- El publicador de la wiki **protege las páginas del foro**: actualizar la
  documentación **ya no puede borrar los mensajes** de nadie.

---

## v0.1.0-beta.2 — 9 de octubre de 2026

**Interfaz y ayuda**
- **Barra de herramientas** con todas las funciones clave: Buscar (`Ctrl+B`),
  Descargar/Cancelar (`Ctrl+D`), Limpiar (`Ctrl+L`), Carpeta (`Ctrl+O`), Filtros,
  Ayuda (`F1`), Actualizaciones y Acerca de. Refleja el estado del formulario: no
  se puede pulsar nada que esté bloqueado.
- **Menús** Archivo y Ayuda, con los mismos accesos y sus atajos.
- **Ayuda dentro del programa (`F1`)**: el manual completo con **índice**,
  **buscador** y formato; lee la guía que viaja con la aplicación.
- **Acerca de**: versión instalada, autor, licencia, repositorio y **dónde queda
  todo** (registros, historial, claves, carpeta de salida).
- **Actualizador**: consulta las versiones publicadas, muestra **cuál tienes y
  cuál hay** (con fecha, peso y notas), descarga con progreso, **verifica el
  SHA-256**, se instala y **se reinicia solo**.

**Licencia**
- **Licencia v2**: la **garantía corre por cuenta del autor** (se corrigen sin
  coste los defectos reportados, se atienden los avisos y se responde de los daños
  directos causados por un defecto del programa). Se puede hacer valer por el foro
  de la wiki.

**Nombre del proyecto**
- El proyecto pasa a llamarse **Imaginteca** (antes «ExtractorFanarts»): imágenes,
  colección y preparación de datasets. El ejecutable, las carpetas de datos y los
  paquetes usan el nombre nuevo. Tus claves anteriores se siguen leyendo.

**Comunidad**
- **El foro vive en la wiki** (no en el repositorio): tableros de soporte técnico,
  fallos, ideas, plataformas y datasets, más las normas de convivencia. Se publica
  un mensaje editando la página, y todo queda junto a la documentación.
- La **garantía del autor** se hace valer dejando el reporte en el foro de la wiki.

**Calidad y limpieza**
- El modo IA ya no deja registros ni archivos temporales: el proceso queda limpio.
- Se garantiza que la IA **no cambie la paleta** de la obra.
- Se documenta el orden de reescalado y el tope de 8K con afilado calibrado
  (sin halos).

## v0.1.0-beta.1 — 8 de octubre de 2026

Primera versión pública (beta).

- Búsqueda y descarga desde **8 redes sociales, 14 booros y wikis de fandom**.
- Galería con visor, menú contextual (copiar, guardar, guardar como…).
- Conversión obligatoria a **WebP** con calidad ajustable.
- **Mejora de calidad** por tramos (hasta 699 px ×4, 700–799 px ×3, 800 px o más
  ×2, tope 8K) y **modo IA** con Real-ESRGAN / waifu2x.
- Filtros legales y éticos en el núcleo (lista negra, plataformas de pago,
  contenido adulto, licencias).
- Paquetes para **Windows, macOS y Linux** con huellas `.sha256`.
- **Licencia propietaria** (todos los derechos reservados).

---

*¿Falta algo en el historial? Dilo en el
[foro](https://github.com/rgomezs2000/extractorfanarts/wiki/Foro).*
