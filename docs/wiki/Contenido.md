# 🖼️ Qué se descarga

Lo que Imaginteca guarda de cada plataforma: **fanarts** e **imágenes oficiales**, y
también **páginas de cómic y de fancomic** cuando el sitio las sirve.

## Fanarts, arte oficial, cómics y fancomics

| Tipo | Qué es | Dónde aparece |
|---|---|---|
| **Fanart** | Arte hecho por la comunidad. Es lo más abundante y lo que mejor etiquetado está | Boorus, redes sociales y wikis de fandom |
| **Imagen oficial** | Promocionales, portadas, ilustraciones de producción, arte de manual | Wikis de fandom y boorus (aparece etiquetado) |
| **Cómic y fancomic** | Páginas o viñetas completas; llegan **página a página** como una imagen más | Wikis, boorus y algunas redes |
| **Otros** | Fondos, wallpapers, sprites, *fan comics* de una franquicia | Según la plataforma y sus etiquetas |

- Todo se guarda en **WebP**: más ligero y más versátil para un dataset o para tu
  galería. La **subida de calidad** (Real-ESRGAN / waifu2x) es opcional y llega hasta
  8K, respetando las reglas por resolución (≤699 px → ×4, 700–799 → ×3, 800–1599 → ×2).
- Los **cómics** llegan como imágenes sueltas: si quieres unirlos después, el orden de
  descarga sigue el de la plataforma. Para entrenar un dataset suelen descartarse las
  páginas con bocadillos de texto (puedes excluirlas con tu lista de etiquetas).
- **Nunca** se descarga: contenido prohibido (ver más abajo), material de **pago o
  exclusivo** (Patreon, Pixiv Fanbox, OnlyFans, Fansly, Unifans, Gumroad…) ni nada que
  la plataforma no entregue por su API pública. El programa **no salta muros de pago ni
  inicios de sesión**.

## NSFW: contenido adulto (+18)

### Qué significa

**NSFW** viene de *«Not Safe For Work»*: contenido que **no es apto** para verse en un
entorno laboral o delante de menores. En la práctica, hablamos de material **sexual o
explícito**. Los sitios lo clasifican con **ratings**, y el programa los respeta:

| Rating | Qué significa | ¿Aparece sin marcar el 🔞? |
|---|---|---|
| `general` | Apto para todos | Sí |
| `sensitive` | Sensible, pero **no** sexual (sangre leve, temas duros) | Sí |
| `questionable` | **Sugestivo**: insinuación, poca ropa, poses | **No** |
| `explicit` | **Explícito**: actos sexuales o desnudo | **No** |

**Sin el 🔞 marcado** (o si lo desmarcas), **Buscar y Descargar funcionan con total
normalidad**: simplemente el **contenido adulto se filtra** y no aparece
(`questionable` y `explicit` se descartan antes de mostrarse). No hay ningún bloqueo:
la búsqueda sigue igual, solo que «limpia». Lo que **sí** se aplica siempre, marques o
no el 🔞, es la **lista negra de contenido prohibido** y el **bloqueo de plataformas de
pago**.

### Alcance: qué elementos lo definen

| Elemento | Ejemplos | Nivel habitual |
|---|---|---|
| **Fluidos** | Semen, lubricación, saliva abundante, sudor | Explícito |
| **Partes del cuerpo** | Genitales, pechos con pezón, nalgas | Sugestivo o explícito, según el contexto |
| **Atuendo explícito** | Desnudo, ropa transparente, lencería sin más, *bondage* | Explícito |
| **Atuendo sugestivo** | Ropa muy ajustada, escotes, bañador, ropa interior | Sugestivo |
| **Actividades individuales** | Masturbación, uso de juguetes | Explícito |
| **Actividades colectivas** | Sexo entre dos o más personas | Explícito |

También hay **fetiches** (pies, latex, *vore*, etc.): cada booru los etiqueta a su
manera y suelen caer en `questionable` o `explicit`.

### Qué se puede extraer y qué no

| | |
|---|---|
| **Sí** | Lo que la plataforma sirve **públicamente** y pasa los filtros. Con el 🔞 marcado se admiten `questionable` y `explicit`; **sin marcarlo, la búsqueda y la descarga funcionan igual y esas dos categorías se filtran** |
| **No, nunca** | Contenido con **menores**: la lista negra lo bloquea siempre (etiquetas `childporn`, `child_porn` y todo lo que empiece por `pedo`), marques lo que marques |
| **No, nunca** | Material de **pago o exclusivo**, y lo que la API no entregue |
| **Tampoco** | Contenido **ilegal** o no consentido: la lista negra se aplica **aunque** tengas el 🔞 activado |
| **Además** | Tu **lista de exclusión** propia (etiquetas, dominios o palabras) se respeta siempre |

### Condiciones para acceder al contenido +18

1. Marca **🔞 Contenido adulto** en Opciones (junto a *Buscar*).
2. Al pulsar **Buscar** o **Descargar**, el programa pide **verificar la edad**: escribes
   tu **fecha de nacimiento** y la calcula **contra la fecha actual** del equipo.
3. **Menos de 18 años**: **no se busca ni se descarga nada**, se muestra el aviso de que
   hay que ser mayor de 18 y la casilla 🔞 **se desmarca sola** (puedes buscar sin ella).
4. **18 años o más**: la búsqueda o la descarga continúa, ya con contenido adulto.
5. **Privacidad**: la fecha se compara **en tu equipo** y **no se guarda ni se envía** a
   ningún sitio; no queda en el registro. Solo se recuerda —mientras el programa esté
   abierto— que verificaste la edad, y únicamente si dejas marcada la casilla *«Recordar
   durante esta sesión»*. Si la desmarcas, **preguntará en cada búsqueda**.
6. **Es tu responsabilidad** cumplir la ley de tu país o región sobre este contenido, y
   las condiciones de uso de cada plataforma.

> ⚠️ En **[Rule34.xxx](https://rule34.xxx)** y **[Rule34 Paheal](https://rule34.paheal.net)**
> casi todo el contenido es adulto: si **no** marcas el 🔞 verás **0 resultados** aunque
> la conexión funcione bien. Y al revés: con el 🔞 marcado, recuerda que la lista negra
> de contenido prohibido **se sigue aplicando**.

---

## Ver las propiedades de una imagen

Con el **clic derecho** sobre una imagen (o `Ctrl+I`) se abre **📋 Propiedades de la
imagen**: todo lo que la plataforma sabe de ella, agrupado y listo para copiar.

| Grupo | Qué trae |
|---|---|
| **Imagen** | Autor, plataforma, fecha, resolución, clasificación, licencia, formato, tamaño, hashes y enlaces |
| **Interacción** | Favoritos, reposts/boosts, respuestas, vistas, guardados, citas y la puntuación de los boorus |
| **Del servicio** | Boorus: fuentes y etiquetas por categoría, quién la subió y quién la aprobó. Wikis: descripción y licencia originales, autor, subida. Fediverso: cuenta, seguidores, visibilidad, idioma |
| **Descripción** | El texto del post o de la ficha |
| **Todo lo demás** | El resto de datos que trae el servicio, sin perder nada |

Con **`F3`** se abre **ampliada** la imagen de ejemplo sobre la que esté el ratón, sin
tener que seleccionarla antes.

> En el **fediverso**, los totales (favoritos, reposts, respuestas) son los del
> **servidor de origen** de la publicación, que es la copia canónica; cada instancia
> conoce los suyos.

**[← Plataformas](Plataformas)** · **[Boorus](Boorus)** · **[Fandoms](Fandoms)** ·
**[Calidad y mejora](Calidad-y-mejora)**
