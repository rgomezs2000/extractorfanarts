# Datasets para IA (LoRA, LyCORIS, checkpoints)

Imaginteca también sirve para **preparar las imágenes con las que se entrena un
modelo**: un **LoRA** de tu personaje, un **LyCORIS** (LoCon, LoHa) de estilo, un
**embedding** o un **checkpoint / DreamBooth**.

## Por qué sirve para esto

| Lo que necesita un dataset | Cómo te lo da el programa |
|---|---|
| Imágenes **del concepto correcto** | Búsqueda por **etiqueta exacta** en 14 booros (el mejor etiquetado que existe para arte), por `@usuario` en redes y por personaje o franquicia en wikis |
| **Sin repetidas** | Deduplicación por hash: el mismo archivo no entra dos veces en una misma búsqueda |
| **Un solo formato** | Todo se guarda en `.webp`, con la calidad que elijas |
| **Tamaños coherentes** | Reescala automáticamente las imágenes pequeñas (hasta 4×) para que el dataset no mezcle 300 px con 3000 px |
| **Más definición** | ✨ *Mejorar calidad*, y con 🤖 *Modo IA* recupera detalle de originales pequeños |
| **Etiquetas para las captions** | Con **🏷️ Guardar metadatos .json** obtienes un `.json` por imagen con **tags**, artista, licencia, origen, rating y fecha |
| **Dataset limpio** | Filtros de contenido prohibido, plataformas de pago, contenido adulto y licencias |
| **Revisar antes de descargar** | La galería te deja ver y descartar **antes** de bajarte 300 archivos |
| **Saber de dónde salió cada imagen** | Los nombres son `Plataforma_id_hash.webp` y el `.json` guarda el enlace original |

## Paso a paso

1. **Tipo: Booru** → **Plataforma: Danbooru o Gelbooru** (tienen el etiquetado más
   completo).
2. En **Tags**, escribe el personaje o el concepto y afina con etiquetas de
   calidad y encuadre: `solo`, `1girl`, `highres`. Excluye lo que no quieras con un
   guion delante: `-comic`, `-text`, `-sketch`.
3. Marca **✨ Mejorar calidad** (y **🤖 Modo IA** si el arte original es pequeño)
   para que todas las imágenes queden con una definición parecida.
4. Marca **🏷️ Guardar metadatos .json**: tendrás las etiquetas de cada imagen
   listas para convertirlas en captions.
5. **⬇️ Descargar** con un límite razonable: para un personaje suelen bastar
   **100–200 imágenes**; para un estilo, **30–50**.
6. **Revisa en la galería** y quédate con las buenas: variedad de poses, fondos y
   expresiones. Fuera las de cuerpo cortado, con marcas de agua o borrosas.
7. Usa las **etiquetas** del `.json` para escribir los archivos de caption (`.txt`)
   y entrena con tu herramienta habitual (kohya-ss, OneTrainer, ai-toolkit…).

## Consejos para que salga bien

- **Variedad antes que cantidad:** 40 imágenes distintas entrenan mejor que 200
  casi iguales.
- **Elige un tamaño objetivo:** decide si entrenas a 512, 768 o 1024 y quédate en
  esa franja. El programa reescala **hacia arriba**.
- **El programa no recorta:** si necesitas encuadres concretos, recórtalos con tu
  editor antes de entrenar.
- **¿Tu entrenador no acepta WebP?** Convierte la carpeta por lotes a PNG o JPG.
- **Entre sesiones puede repetir alguna imagen:** evita repetidos dentro de una
  misma búsqueda, pero si vuelves a buscar lo mismo otro día puede bajar algo que
  ya tenías.
- **Respeta a los artistas:** usa los campos `licencia` y `artista` del `.json` y
  ten en cuenta las listas de «no entrenar» de algunos autores. Si quieres quedarte
  solo con obras de licencia abierta, activa **⚖️ Solo licencia liberada**.

## Qué NO hace

- No recorta, no rota ni reencuadra.
- No separa automáticamente por carpetas de concepto ni genera los `.txt` de
  caption (te da las etiquetas para que los escribas como quieras).
- No entrena modelos: prepara el material.

---

**Siguiente:** [Actualizaciones](Actualizaciones) ·
**Dudas:** [Preguntas frecuentes](Preguntas-frecuentes)
