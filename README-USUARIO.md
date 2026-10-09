# Imaginteca — Guía del usuario

**Versión 0.1.2-beta (fase beta)** · Windows · macOS · Linux

**Imaginteca** es un programa de escritorio para **reunir, ordenar y preparar tu
colección personal de imágenes**: busca en redes sociales, booros y wikis de
fandom, revisa los resultados en una galería, guarda lo que elijas en un formato
único (**WebP**) y, si quieres, **mejóralas de calidad** o **prepara con ellas un
dataset** para entrenar modelos.

> Está pensada para **coleccionar y preparar material**, no para extraerlo de
> nadie: se descarga con **tus credenciales**, con peticiones espaciadas y **sin
> evadir nunca CAPTCHAs ni inicios de sesión**.

> 📖 **Más información, ayuda y foro:**
> **https://github.com/rgomezs2000/extractorfanarts/wiki**
> Ahí está esta guía ampliada, los tableros del **foro** (soporte técnico, fallos,
> ideas, plataformas y datasets) y las respuestas a las dudas más comunes.
> **Contacto privado: Discord `rgomezs2010`.**

> **Programa propietario.** **© 2026 InfoArte** · Todos los derechos
> reservados.
> Puedes usarlo gratis para tu colección personal. No puedes copiarlo,
> redistribuirlo, venderlo ni modificarlo. La **garantía corre por cuenta del
> autor**: ver **Licencia** al final.

---

## Índice

1. [Qué es y para qué sirve](#1-qué-es-y-para-qué-sirve)
2. [Instalar y abrir](#2-instalar-y-abrir)
3. [Qué hay en esta carpeta](#3-qué-hay-en-esta-carpeta)
4. [Tus claves (opcional)](#4-tus-claves-opcional)
5. [Buscar y descargar, paso a paso](#5-buscar-y-descargar-paso-a-paso)
6. [Plataformas compatibles](#6-plataformas-compatibles)
7. [La galería y el visor](#7-la-galería-y-el-visor)
8. [Menú contextual (clic derecho)](#8-menú-contextual-clic-derecho)
9. [Barra de herramientas, menús y atajos](#9-barra-de-herramientas-menús-y-atajos)
10. [La ayuda dentro del programa (F1) y «Acerca de»](#10-la-ayuda-dentro-del-programa-f1-y-acerca-de)
11. [Dónde se guarda todo](#11-dónde-se-guarda-todo)
12. [Calidad y mejora de imagen](#12-calidad-y-mejora-de-imagen)
13. [Preparar datasets para IA (LoRA, LyCORIS, checkpoints)](#13-preparar-datasets-para-ia-lora-lycoris-checkpoints)
14. [Qué se filtra](#14-qué-se-filtra)
15. [Actualizaciones](#15-actualizaciones)
16. [Si algo va mal](#16-si-algo-va-mal)
17. [Más información, foro y contacto](#17-más-información-foro-y-contacto)
18. [Licencia y uso responsable](#18-licencia-y-uso-responsable)

---

## 1. Qué es y para qué sirve

Imaginteca reúne en una sola ventana lo que normalmente se hace con cinco
programas:

- **Buscar** imágenes en **8 redes sociales, 14 booros y wikis de fandom**.
- **Revisarlas** antes de descargar nada, en una galería con visor.
- **Guardarlas** siempre en **`.webp`**, con la calidad que elijas.
- **Mejorar su calidad** (reescalado clásico o con **IA**, Real-ESRGAN / waifu2x).
- **Prepararlas para entrenar**: metadatos `.json` con las etiquetas de cada
  imagen, tamaños homogéneos y sin repetidas.

Y lo hace con **filtros legales y éticos en el núcleo**: lista negra de contenido
prohibido, bloqueo de plataformas de pago, control de contenido adulto y opción de
quedarse solo con licencias liberadas.

---

## 2. Instalar y abrir

**El programa no se instala**: se descomprime y se ejecuta. No hay que pagar nada,
no hay que registrarse y no se recogen datos.

1. **Descarga** el paquete de tu sistema desde
   **[Releases](https://github.com/rgomezs2000/extractorfanarts/releases)**:

   | Sistema | Archivo |
   |---|---|
   | Windows | `Imaginteca-Windows.zip` |
   | Linux | `Imaginteca-Linux.zip` |
   | macOS | `Imaginteca-macOS.zip` |

2. **Comprueba la descarga** con el `.sha256` que acompaña al paquete:

   ```powershell
   # Windows (PowerShell)
   Get-FileHash .\Imaginteca-*.zip -Algorithm SHA256
   ```
   ```bash
   # Linux / macOS
   shasum -a 256 Imaginteca-*.zip
   ```

   El resultado debe coincidir con el contenido del `.sha256`.

3. **Descomprime el `.zip` completo** en una carpeta tuya (por ejemplo
   `C:\Imaginteca`). No lo ejecutes desde dentro del archivo comprimido: necesita
   la carpeta `_internal` que va a su lado.

4. **Ábrelo**:
   - **Windows:** doble clic en **`Imaginteca.exe`**. La primera vez puede salir
     el aviso azul *«Windows protegió su PC»*: es normal (el programa no está
     firmado digitalmente; un certificado de firma es de pago). Pulsa **Más
     información → Ejecutar de todas formas**. Si sigue bloqueado: clic derecho en
     el `.exe` → **Propiedades** → marca **Desbloquear** → **Aceptar**.
   - **macOS:** si dice *«no se puede abrir»*, clic derecho en la aplicación →
     **Abrir**. Si se resiste: `xattr -dr com.apple.quarantine Imaginteca.app`
   - **Linux:** `chmod +x Imaginteca` la primera vez y luego ejecútalo.

5. **Comprueba que todo está bien** (opcional pero recomendable). En una consola,
   dentro de la carpeta del programa:

   ```powershell
   Imaginteca.exe --selftest
   ```

   Genera **`selftest.txt`** con el estado de bibliotecas, carpetas, permisos,
   motores de IA y si la ventana cabe en tu pantalla. Es lo primero que se pide
   cuando pides ayuda.

Al abrirlo por primera vez se crea la carpeta de datos
(`%USERPROFILE%\.imaginteca` en Windows, `~/.imaginteca` en Linux/macOS), donde
viven tus registros, tu historial y —si quieres— tus claves.

---

## 3. Qué hay en esta carpeta

| Archivo | Para qué sirve |
|---|---|
| `Imaginteca.exe` | **El programa.** Es lo único que tienes que abrir |
| `pixiv-token.exe` | Asistente para conseguir tu token de Pixiv (opcional) |
| `config_local.py` | Tus claves y ajustes (viene como plantilla vacía) |
| `README.md` | Esta guía (también dentro del programa, con `F1`) |
| `LEEME-PRIMERO.txt` | Los primeros pasos, en texto plano |
| `LICENSE` | Las condiciones de uso |
| `THIRD-PARTY-NOTICES.txt` | Licencias de las bibliotecas incluidas |
| `_internal/` | Biblioteca del programa. **No la borres ni la muevas** |

Puedes mover la carpeta entera donde quieras, pero mantén esos archivos **juntos**.

---

## 4. Tus claves (opcional)

El programa funciona **sin configurar nada** en varias plataformas. Para las que
piden credenciales, edita el archivo **`config_local.py`** que está **junto al
ejecutable** y escribe dentro tus claves, una por línea:

```python
RULE34_API_KEY = "tu_clave"
RULE34_USER_ID = "tu_id"
GELBOORU_API_KEY = "tu_clave"
GELBOORU_USER_ID = "tu_id"
DEVIANTART_CLIENT_ID = "tu_id"
DEVIANTART_CLIENT_SECRET = "tu_secreto"
TUMBLR_API_KEY = "tu_clave"
CF_CLEARANCE = "valor_de_la_cookie"
CF_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
```

**Dónde se busca ese archivo** (por este orden):

1. junto al ejecutable (lo más cómodo),
2. dentro de la carpeta del programa,
3. en `%USERPROFILE%\.imaginteca\config_local.py` (Windows) o
   `~/.imaginteca/config_local.py` (Linux/macOS) — **la mejor opción si quieres
   que sobreviva a las actualizaciones**.

**Reinicia el programa** después de cambiar el archivo. El botón **🛡️ Filtros** te
dice qué archivo se está usando.

| Plataforma | Clave que necesita | Dónde se consigue |
|---|---|---|
| Safebooru, Danbooru, wikis, Fediverso, Bluesky, Newgrounds | **ninguna** | — |
| Rule34.xxx | `RULE34_API_KEY` + `RULE34_USER_ID` | Opciones de tu cuenta → *API Access Credentials* |
| Gelbooru | `GELBOORU_API_KEY` + `GELBOORU_USER_ID` | Opciones de tu cuenta → *API Access Credentials* |
| DeviantArt | `DEVIANTART_CLIENT_ID` + `DEVIANTART_CLIENT_SECRET` | deviantart.com/developers |
| Tumblr | `TUMBLR_API_KEY` | tumblr.com/oauth/apps |
| Pixiv | `PIXIV_REFRESH_TOKEN` | Ver *Pixiv*, abajo |
| X (Twitter) | `X_BEARER_TOKEN` | App de desarrollador **de pago** |
| Pinterest | `PINTEREST_ACCESS_TOKEN` | App aprobada + permiso del usuario |

**Pixiv.** No permite el acceso anónimo: hay que usar **tu cuenta** con un
*refresh token* (el programa **no guarda tu contraseña**). En la **misma carpeta**
que el programa tienes un asistente: haz **doble clic en `pixiv-token.exe`** (o
`pixiv-token` en Linux/macOS) y sigue lo que te diga. Te dará un enlace para
iniciar sesión en Pixiv, le pegarás la dirección final (la que lleva `code=...`) y
**el token se guarda solo**. Después, **reinicia Imaginteca**.

> 🔐 Guarda tus claves en `config_local.py`. Ese archivo queda en tu equipo: el
> programa no envía nada a ningún servidor propio y no incluye ninguna clave.

---

## 5. Buscar y descargar, paso a paso

1. **Tipo:** elige *Red social*, *Booru* o *Wiki*.
2. **Plataforma:** el sitio concreto (la lista cambia según el tipo).
3. **Escribe lo que buscas**, según el tipo:
   - *Red social:* `@usuario`, palabras clave y/o `#hashtags`. Puedes
     combinarlos y poner **varios valores** en un mismo campo (separados por
     espacios o comas): se busca todo a la vez.
   - *Booru:* las etiquetas que quieras, separadas por espacios o comas
     (`lola_loud 1girl solo`). También valen los operadores del sitio
     (`-etiqueta` para excluir, `rating:general`, `score:>10`).
   - *Wiki:* el fandom, el personaje y/o la URL de la wiki.
4. Pulsa **🔍 Buscar** (`Ctrl+B`, o `Enter` en cualquier campo). Aparecerán los
   resultados en una **galería** para que los revises antes de descargar nada.
5. Ajusta lo que quieras (cantidad, calidad, mejora, metadatos, carpeta de
   destino) y pulsa **⬇️ Descargar** (`Ctrl+D`, o `Shift+Enter`). Te pedirá
   confirmación y te dirá al terminar **cuántos archivos guardó y dónde**.
6. **⏹️ Cancelar** (`Esc`) detiene la operación en cualquier momento y **no deja
   archivos a medias**. **🧹 Limpiar** (`Ctrl+L`) vacía el formulario.

Puedes lanzar una búsqueda y, sin descargar nada, usar el **clic derecho** sobre
una imagen para guardar solo esa (ver más abajo).

---

## 6. Plataformas compatibles

El detalle completo, plataforma por plataforma, está en la wiki:
**[Soporte de plataformas](https://github.com/rgomezs2000/extractorfanarts/wiki/Plataformas)**
([redes](https://github.com/rgomezs2000/extractorfanarts/wiki/Redes-sociales) ·
[boorus](https://github.com/rgomezs2000/extractorfanarts/wiki/Boorus) ·
[fandoms](https://github.com/rgomezs2000/extractorfanarts/wiki/Fandoms)). Aquí
tienes el resumen y lo esencial de cada una.

### 6.1 ¿Qué es compatible? (resumen)

| Familia | Cuántas | Cuáles |
|---|---|---|
| 🌐 **Redes sociales** | **8** | Fediverso, Bluesky, DeviantArt, Tumblr, Pixiv, X (Twitter), Pinterest, Newgrounds |
| 🧩 **Boorus** | **14** (en 5 familias de API) | Safebooru, Gelbooru, Rule34.xxx, The Big ImageBoard, Xbooru, Hypnohub, Danbooru, Safebooru (Donmai), Yande.re, Konachan, Konachan (SFW), Derpibooru, ATF Booru, Rule34 Paheal |
| 📚 **Fandoms y wikis** | **todas** | Cualquier wiki de **Fandom.com** y cualquier **MediaWiki** (por franquicia, personaje o concepto) |

**Sin configurar nada** funcionan: Fediverso, Bluesky, Newgrounds, todas las wikis
y **12 de los 14 booros**. Solo **Gelbooru** y **Rule34.xxx** aceptan una clave
gratuita (y también funcionan sin ella).

### 6.2 Redes sociales, una por una

| Red | Qué se busca | 🔑 Claves | Notas |
|---|---|---|---|
| **Fediverso** (Mastodon / Misskey / CherryPick) | `@usuario`, `@usuario@servidor`, `#hashtags`, palabras | No | Cualquier instancia: detecta el software solo |
| **Bluesky** | palabras clave y `#hashtags` | No | API pública (atproto) |
| **DeviantArt** | palabras clave + **licencia** | Sí (app propia, gratis) | Permite filtrar por licencia |
| **Tumblr** | etiquetas de post | Sí (consumer key, gratis) | Solo publicaciones públicas |
| **Pixiv** | obras de un autor, etiquetas | Sí (tu cuenta) | También animaciones *ugoira* |
| **X / Twitter** | palabras y `#hashtags` | Sí (**de pago**) | No hay plan gratuito |
| **Pinterest** | pines y tableros | Sí (app aprobada) | Solo contenido al que tengas acceso |
| **Newgrounds** | arte público del sitio | No | La más frágil ante cambios del sitio |

- **Fediverso:** escribe `@usuario@servidor` (por ejemplo `@alguien@baraag.net`) y
  se consulta **su** servidor; o `@usuario` y rellena el campo *Instancia*. En
  Misskey, el texto se busca como su etiqueta equivalente.
- **DeviantArt, Tumblr, X y Pinterest** necesitan que crees **tu propia app** en la
  plataforma y pegues las credenciales en `config_local.py` (ver el punto 4).
- **Pixiv** necesita tu cuenta: se resuelve con el asistente `pixiv-token.exe`, y
  **el programa no guarda tu contraseña**.

**Próximamente:** Reddit (viable), ArtStation (viable), Instagram/Threads (difícil:
exige app revisada y tu token), FurAffinity/Inkbunny (frágil: sin API oficial).

### 6.3 Boorus, uno por uno

Los booros son la mejor fuente para un [dataset](#13-preparar-datasets-para-ia-lora-lycoris-checkpoints):
su **etiquetado** es el más completo que existe para arte. Se agrupan en **5
familias de API** (gelbooru, danbooru, moebooru, philomena y shimmie), así que
muchos comparten comportamiento.

| Booru | Familia | 🔑 Claves | De qué va |
|---|---|---|---|
| **Safebooru** | Gelbooru | No | Solo contenido **SFW**; ideal para empezar |
| **Gelbooru** | Gelbooru | Gratis (opcional) | Enorme y variado, con `rating:` para filtrar |
| **Rule34.xxx** | Gelbooru | Gratis (opcional) | **Adulto** casi al 100 % |
| **The Big ImageBoard** | Gelbooru | No | Generalista y ordenado |
| **Xbooru** | Gelbooru | No | **Adulto**, con mucho arte *furry* |
| **Hypnohub** | Gelbooru | No | **Adulto**, temática concreta |
| **Danbooru** | Danbooru | No | **El mejor etiquetado para anime/fanart**; sin clave, **2 etiquetas** por búsqueda |
| **Safebooru (Donmai)** | Danbooru | No | La parte **SFW** de Danbooru, mismo etiquetado |
| **Yande.re** | Moebooru | No | Alta resolución; mezcla SFW y adulto |
| **Konachan** | Moebooru | No | Fondos y arte en gran tamaño |
| **Konachan (SFW)** | Moebooru | No | El mismo sitio, solo **SFW** |
| **Derpibooru** | Philomena | No | **My Little Pony** y su comunidad |
| **ATF Booru** | Danbooru | No | **Adulto** (se aplican los filtros de contenido prohibido) |
| **Rule34 Paheal** | Shimmie | No | **Adulto** |

- **Cómo buscar:** etiquetas separadas por espacios (`lola_loud 1girl solo`),
  excluir con guion (`-comic -text`) y operadores del sitio (`rating:general`,
  `score:>10`, `order:score`).
- **Aviso adulto:** en Rule34.xxx, Rule34 Paheal, Xbooru, Hypnohub y ATF Booru casi
  todo es adulto: sin marcar **«Permitir contenido adulto»** verás **0 resultados**.

**Próximamente:** e621 (viable), Rule34.us y Realbooru (familia Gelbooru),
Sakugabooru (familia Moebooru), Zerochan (sin API pública). Además, **cualquier
booru de una familia soportada se puede añadir ya** desde `config_local.py`.

### 6.4 Fandoms y wikis

No hay lista cerrada: se conecta a **cualquier wiki de Fandom.com** y a cualquier
**MediaWiki**. Son cientos de miles de wikis.

| | |
|---|---|
| **Qué se busca** | Por **franquicia**, por **personaje** y/o por **concepto** (`fanart`, `anime`, `wallpaper`) |
| **De dónde salen las imágenes** | De las imágenes que la propia wiki tiene subidas |
| **Claves** | **Ninguna** (API pública de MediaWiki) |
| **Cómo se elige la wiki** | Por el nombre del fandom o pegando directamente su **URL** |

**Fandoms más buscados, por categoría** (todos funcionan, y cualquier otro de
Fandom también):

- **Anime y manga:** Naruto, One Piece, Dragon Ball, My Hero Academia, Jujutsu
  Kaisen, Demon Slayer, Attack on Titan, Bleach, Fairy Tail, Black Clover, Sailor
  Moon, Cardcaptor Sakura, Inuyasha, Tokyo Ghoul, Sword Art Online, Hunter x
  Hunter, JoJo's Bizarre Adventure, Chainsaw Man, Spy x Family, One Punch Man,
  Evangelion, Dandadan.
- **Videojuegos:** Pokémon, Minecraft, The Legend of Zelda, Genshin Impact, Honkai:
  Star Rail, League of Legends, Valorant, Overwatch, Fortnite, The Elder Scrolls /
  Skyrim, Dark Souls, Elden Ring, Hollow Knight, Undertale, Stardew Valley, Five
  Nights at Freddy's, Sonic, Super Mario, Resident Evil, Silent Hill, Animal
  Crossing.
- **Animación occidental · Nickelodeon:** The Loud House, The Casagrandes,
  SpongeBob (Bob Esponja), Fairly OddParents (Los padrinos mágicos), Danny
  Phantom, Avatar: la leyenda de Aang y La leyenda de Korra, Rugrats, Hey
  Arnold!, Invader Zim, Jimmy Neutron, My Life as a Teenage Robot, The Wild
  Thornberrys, Rocko's Modern Life, CatDog, Teenage Mutant Ninja Turtles,
  Wylde Pak, Harvey Beaks, Welcome to the Wayne.
- **Animación occidental · Cartoon Network:** The Powerpuff Girls, Foster's Home
  for Imaginary Friends, The Amazing World of Gumball, Adventure Time, Steven
  Universe, Regular Show, We Bare Bears (Somos osos), Ben 10, Teen Titans y Teen
  Titans Go!, Dexter's Laboratory, Samurai Jack, Courage the Cowardly Dog, Ed,
  Edd n Eddy, Codename: Kids Next Door, The Grim Adventures of Billy & Mandy,
  Over the Garden Wall, Infinity Train, Craig of the Creek, OK K.O.! Let's Be
  Heroes, Mao Mao, Victor and Valentino, Summer Camp Island, Generator Rex,
  Sym-Bionic Titan, The Secret Saturdays.
- **Animación occidental · Disney:** Gravity Falls, Amphibia, The Owl House, Star
  vs. the Forces of Evil, The Ghost and Molly McGee, Phineas and Ferb (y Milo
  Murphy's Law), Kim Possible, DuckTales (2017), Wander Over Yonder, Big City
  Greens, Kiff, Hailey's on It!, Moon Girl and Devil Dinosaur, Hamster & Gretel,
  Recess, The Proud Family, Lilo & Stitch: The Series, American Dragon: Jake
  Long, Dave the Barbarian, Brandy & Mr. Whiskers, Little Einsteins.
- **Animación occidental · Streaming y web:** Hilda, The Amazing Digital Circus,
  Murder Drones, Hazbin Hotel, Helluva Boss, Kipo and the Age of Wonderbeasts,
  Carmen Sandiego, Centaurworld, The Dragon Prince, Voltron: Legendary Defender,
  Trollhunters, She-Ra and the Princesses of Power, Arcane, Castlevania, Battle
  for Dream Island (BFDI), Inanimate Insanity, Gameoverse, Planetonika,
  Lackadaisy, Eddsworld.
- **Animación occidental · clásicos y para adultos:** My Little Pony, Bluey,
  Miraculous, Looney Tunes, Tom and Jerry, Scooby-Doo, Los Simpson, South Park,
  Family Guy, Futurama, Bob's Burgers, American Dad, Rick and Morty, Total Drama,
  6teen, Detentionaire, Winx Club.
- **Cómics y superhéroes:** Marvel, DC, Spider-Man, Batman, X-Men, The Boys,
  Invincible.
- **Cine, TV y libros:** Star Wars, Harry Potter, El Señor de los Anillos, Juego de
  Tronos, Stranger Things, Marvel Cinematic Universe, The Witcher, Dune, Percy
  Jackson.
- **Música, mascotas y otros:** Vocaloid / Hatsune Miku, K-pop, Sanrio, Warrior
  Cats, furry, Creepypasta, SCP Foundation.

> **Consejo:** si conoces la wiki, pega su URL (por ejemplo
> `https://naruto.fandom.com/es`) y busca ahí directamente. La calidad depende de
> la wiki: algunas tienen arte en alta resolución y otras casi solo texto.

---

## 7. La galería y el visor

- Los resultados aparecen en un **carrusel**: contador, imagen grande y una tira
  de miniaturas. Hay **una casilla por cada resultado**.
- **Clic en la imagen grande** → se abre un **visor** dentro de la misma ventana:
  - **rueda del ratón**: acercar y alejar (del 10 % al 800 %),
  - **arrastrar**: mover la imagen,
  - **doble clic** o tecla `0`: ajustar a la ventana,
  - `←` / `→`: imagen anterior y siguiente,
  - `+` / `-`: zoom, **`Esc`**: cerrar.
- Las imágenes se preparan a partir del **original**, así que se ven nítidas al
  ampliarlas, y se cargan **de una en una con cortesía** hacia los sitios (por eso
  la tira se va llenando poco a poco).

---

## 8. Menú contextual (clic derecho)

Con **clic derecho** sobre cualquier imagen (la grande, una miniatura o dentro
del visor):

| Opción | Qué hace | Atajo |
|---|---|---|
| 📋 Copiar imagen | Copia la imagen ya procesada para pegarla en otro programa | `Ctrl+C` |
| 💾 Guardar imagen | Guarda **solo esa** imagen en la carpeta de salida | `Ctrl+S` |
| 🗂️ Guardar como… | Igual, pero eligiendo carpeta y nombre | `Ctrl+Shift+S` |
| 🌐 Abrir imagen original en el navegador | Abre la página original | — |
| 🔗 Copiar enlace de la imagen original | Copia esa dirección web | `Ctrl+Shift+C` |

La calidad es **la misma** que en la descarga completa, y funciona **aunque solo
hayas pulsado Buscar**.

---

## 9. Barra de herramientas, menús y atajos

Arriba tienes los accesos directos a todo lo importante, primero lo esencial y
luego lo de apoyo:

| Botón | Atajo | Qué hace |
|---|---|---|
| 🔍 **Buscar** | `Ctrl+B` | busca con el criterio del formulario |
| ⬇️ **Descargar** / ⏹️ **Cancelar** | `Ctrl+D` | descarga lo encontrado; mientras trabaja, cancela |
| 🧹 **Limpiar** | `Ctrl+L` | vacía el formulario |
| 📂 **Carpeta** | `Ctrl+O` | elige la carpeta de salida |
| 🛡️ **Filtros** | — | explica qué se filtra y por qué |
| 📖 **Ayuda** | `F1` | abre esta guía dentro del programa |
| 🔄 **Actualizaciones** | — | busca e instala la versión nueva |
| ℹ️ **Acerca de** | — | versión, licencia, autor y rutas |

Los botones de la barra se apagan y se encienden **a la vez** que los del
formulario: si algo no se puede pulsar, en la barra tampoco. En los menús
**Archivo** y **Ayuda** tienes lo mismo, además del foro y la wiki.

| Tecla | Dónde | Qué hace |
|---|---|---|
| `Enter` | en cualquier campo o control de búsqueda | **Buscar** |
| `Shift+Enter` | igual | **Descargar** |
| `Enter` | en el campo **Salida** | elegir carpeta |
| `Enter` | sobre un botón enfocado | pulsarlo |
| `Enter` o `Esc` | mientras busca o descarga | **cancelar** |
| `Esc` | con el visor abierto | cerrarlo |
| `Ctrl+B` · `Ctrl+D` · `Ctrl+L` | en cualquier parte | buscar · descargar · limpiar |
| `Ctrl+O` | en cualquier parte | elegir la carpeta de salida |
| `F1` | en cualquier parte | abrir la ayuda |
| `Alt+F4` o `Ctrl+Q` | en cualquier parte | cerrar el programa |

Si hay una descarga en curso y cierras, te preguntará antes y no dejará archivos a
medias.

---

## 10. La ayuda dentro del programa (F1) y «Acerca de»

- **`F1`** (o **Ayuda → Ayuda**) abre esta guía **dentro del programa**: a la
  izquierda el **índice** con todas las secciones y un **buscador** para dar con la
  tuya; a la derecha el texto. El botón **🗂️ Abrir el manual completo** lo abre con
  tu programa de textos, por si prefieres leerlo entero o imprimirlo.
- **Ayuda → Acerca de** (o el botón **ℹ️**) te dice **qué versión tienes
  instalada**, quién la hizo, la licencia y **dónde queda todo**: registros,
  historial, tus claves y la carpeta de salida. Desde ahí mismo puedes buscar
  actualizaciones.

---

## 11. Dónde se guarda todo

| Qué | Dónde |
|---|---|
| **Imágenes** | Carpeta de **Imágenes** del sistema, subcarpeta `Imaginteca`, con una subcarpeta por plataforma |
| **Registros** | `%USERPROFILE%\.imaginteca\logs\app-AAAA-MM-DD.log` (un archivo por día) |
| **Historial** | `%USERPROFILE%\.imaginteca\historial.db` |
| **Tus claves** | `config_local.py` (junto al programa o en `~/.imaginteca`) |

- Puedes cambiar la carpeta de salida con **📂 Carpeta** (`Ctrl+O`).
- Si esa carpeta no se puede escribir (permisos, protección contra ransomware…),
  el programa **te avisa al arrancar** y, al descargar, prueba alternativas
  (Descargas, `~/.imaginteca/descargas`, una carpeta junto al programa) y te dice
  cuál ha usado.
- Las descargas **nunca** van a Documentos.
- Junto a cada imagen se puede guardar un archivo `.json` con sus datos, si marcas
  **«Guardar metadatos .json»** en Opciones (desactivado por defecto).

---

## 12. Calidad y mejora de imagen

- **Todo se guarda en `.webp`**, con la calidad que elijas en el deslizador
  (1–100). El archivo original no se conserva.
- **✨ Mejorar calidad** aumenta la resolución según el tamaño de partida:
  **hasta 699 px → ×4** · **700–799 px → ×3** · **800 px o más → ×2**, con un tope
  de 8K, y aplica un afilado suave y calibrado. Por encima de 7679 px solo se
  convierte a WebP.
- **Siempre verás lo que se ha hecho:** al guardar o copiar, la barra de estado
  indica el tamaño de partida y el resultado real
  (`153x153 → 612x612 · Lanczos 4x`). Si el origen era muy pequeño (menos de
  300 px) te avisa, porque **agrandar una imagen diminuta no crea detalle real**:
  para preparar un dataset conviene saberlo antes de entrenar.
- **🤖 Modo IA** usa los motores **Real-ESRGAN / waifu2x** que van incluidos en el
  paquete (dan más detalle, sobre todo en dibujos). Si no están disponibles, el
  programa lo dice y usa el reescalado clásico: **nunca** guarda una imagen
  corrupta ni a medias.
- **Sin dejar basura:** el proceso no deja carpetas temporales, ni PNG
  intermedios, ni registros del motor en tu carpeta de salida. Cada archivo se
  comprueba al guardarlo.
- **🔢 Limitar cantidad**: descarga solo el número que indiques (1–1000). Sin
  marcar, descarga todo lo encontrado.

> **Si el modo IA «no mejora nada»:** casi siempre es la etiqueta de integridad de
> Windows sobre los motores, y se arregla en un paso. Lo explica
> **[Problemas frecuentes](https://github.com/rgomezs2000/extractorfanarts/wiki/Problemas-frecuentes)**.

---

## 13. Preparar datasets para IA (LoRA, LyCORIS, checkpoints)

Este programa también sirve para **preparar las imágenes con las que se entrena un
modelo**: un **LoRA** de tu personaje, un **LyCORIS** (LoCon, LoHa) de estilo, un
**embedding** o un **checkpoint / DreamBooth**.

| Lo que necesita un dataset | Cómo te lo da el programa |
|---|---|
| Imágenes **del concepto correcto** | Búsqueda por **etiqueta exacta** en 14 booros (el mejor etiquetado que existe para arte), por `@usuario` en redes y por personaje o franquicia en wikis |
| **Sin repetidas** | Deduplicación por hash: el mismo archivo no entra dos veces en una misma búsqueda |
| **Un solo formato** | Todo se guarda en `.webp`, con la calidad que elijas |
| **Tamaños coherentes** | Reescala automáticamente las imágenes pequeñas (hasta ×4) para que el dataset no mezcle 300 px con 3000 px |
| **Más definición** | ✨ *Mejorar calidad*, y con 🤖 *Modo IA* recupera detalle de originales pequeños |
| **Etiquetas para las captions** | Marcando **🏷️ Guardar metadatos .json** obtienes un `.json` por imagen con sus **tags**, artista, licencia, origen, rating y fecha |
| **Dataset limpio** | Filtros de contenido prohibido, plataformas de pago, contenido adulto y licencias |
| **Revisar antes de descargar** | La galería te deja ver y descartar **antes** de bajarte 300 archivos |

**Paso a paso:** Booru → Danbooru o Gelbooru → escribe el personaje o concepto
(afina con `solo`, `1girl`, `highres`; excluye con `-comic`, `-text`, `-sketch`) →
marca **✨ Mejorar calidad** (+ **🤖 Modo IA** si el original es pequeño) y
**🏷️ Guardar metadatos .json** → descarga **100–200 imágenes** para un personaje o
**30–50** para un estilo → revisa en la galería → usa las etiquetas del `.json`
para las captions y entrena con tu herramienta habitual.

**Consejos:** variedad antes que cantidad (40 distintas entrenan mejor que 200 casi
iguales) · elige un tamaño objetivo (512, 768, 1024) y sé constante · el programa
**no recorta** · respeta a los artistas y sus listas de «no entrenar» (con
**⚖️ Solo licencia liberada** te quedas solo con obras de licencia abierta).

> Guía ampliada: **[Datasets para IA](https://github.com/rgomezs2000/extractorfanarts/wiki/Datasets-IA)**.

---

## 14. Qué se filtra

El programa aplica **siempre** unos filtros antes de mostrarte o guardarte nada, y
te dice el motivo exacto de cada descarte:

- **Lista negra de contenido prohibido** (etiquetas y prefijos).
- **Plataformas de pago** (Patreon, Pixiv Fanbox, OnlyFans, Fansly, Unifans…): se
  descartan los enlaces a contenido exclusivo.
- **Contenido adulto (🔞):** por defecto **no** aparece. Si marcas «Permitir
  contenido adulto» en Opciones, sí.
- **Solo licencia liberada (⚖️):** opcional; solo procesa lo que declare
  CC0 / CC-BY / dominio público.
- **Tu propia lista de exclusiones** (etiquetas, dominios o palabras) que puedes
  añadir en `config_local.py`.

Puedes ver y ajustar todo esto en **🛡️ Filtros**.

> ⚠️ En **Rule34.xxx** y **Rule34 Paheal** casi todo el contenido es adulto: si no
> marcas «Permitir contenido adulto» verás **0 resultados** aunque la conexión
> funcione bien.

---

## 15. Actualizaciones

Pulsa **🔄 Actualizaciones** y el programa mirará si hay una versión más nueva
publicada. Te dirá **cuál tienes y cuál hay**, con la fecha, el peso de la descarga
y lo que trae de nuevo.

- Si **no hay nada nuevo**, te lo dice y ya está.
- Si **hay una versión nueva**, pulsa **⬇️ Descargar e instalar**: se descarga
  (verás el progreso), se **comprueba que la descarga llegó íntegra** (SHA-256) y,
  cuando aceptes, el programa **se cierra, se instala y se vuelve a abrir solo**
  con la versión nueva. **No pierdes nada**: tus imágenes, tus claves y tu
  historial se quedan como están.
- Si la descarga viniera dañada, **no se instala**: te avisa y puedes repetirlo.

Las **versiones beta** cuentan como versión nueva, que es lo que se publica por
ahora. Si no tienes internet, o GitHub te limita las consultas, te lo dirá sin
más.

> En **Windows** el reemplazo y el reinicio son automáticos. En **macOS y Linux**
> la descarga se hace igual y se verifica igual, pero te avisará para que
> sustituyas la aplicación a mano, porque depende de cómo la tengas instalada.

---

## 16. Si algo va mal

| Síntoma | Qué pasa y qué hacer |
|---|---|
| Aviso azul de Windows al abrir | Normal (no está firmado): *Más información → Ejecutar de todas formas* |
| «Python DLL» u error al abrir | Estás ejecutando el `.exe` de la carpeta `build\`, que es un paso intermedio incompleto. Usa siempre el de la carpeta que descomprimiste |
| «0 resultados» pero la conexión va bien | El contenido es adulto: marca **Permitir contenido adulto** en Opciones |
| **Acceso denegado** al guardar en Imágenes o Descargas | Abre el programa **con doble clic desde el Explorador** (no desde una terminal restringida). Si sigue igual, ejecuta `Imaginteca.exe --selftest` y revisa `selftest.txt` |
| Cloudflare pide un CAPTCHA (p. ej. Rule34.xxx) | Abre el sitio en tu navegador, resuélvelo, y copia en `config_local.py` la cookie `cf_clearance` y tu `User-Agent`. El programa **nunca** evade CAPTCHAs |
| Una wiki o un sitio devuelve error 403 | Suele ser una defensa contra programas. Anótalo y avísalo en el foro |
| **El 🤖 Modo IA no mejora nada** (sigue usando Lanczos) | Los motores pueden traer una etiqueta de Windows que les impide escribir su resultado (en el registro verás `encode image … failed`). Se arregla en la carpeta del programa con `icacls _internal\vendor /setintegritylevel Medium /T`. Si no, usa **✨ Mejorar calidad** sin modo IA |
| Una imagen sale borrosa tras mejorarla | Si el original era diminuto (menos de 300 px), el programa te avisa: **agrandar no crea detalle real** |
| Búsqueda muy lenta | Se espacian las peticiones a propósito (cortesía con los sitios). Con muchos hashtags o palabras clave tarda más |
| Cualquier error raro | Mira el `.log` del día: ahí está exactamente qué respondió cada servidor |

**Diagnóstico:** ejecuta `Imaginteca.exe --selftest` y se genera **`selftest.txt`**
con el estado de todo: bibliotecas, carpetas, permisos y si la ventana cabe en tu
pantalla. Es lo más útil que puedes adjuntar si pides ayuda.

---

## 17. Más información, foro y contacto

La documentación ampliada y el **foro** viven en la **wiki del proyecto**:

**https://github.com/rgomezs2000/extractorfanarts/wiki**

| Dónde | Para qué |
|---|---|
| 📖 **[Wiki](https://github.com/rgomezs2000/extractorfanarts/wiki)** | esta guía ampliada, instalación, claves, calidad, datasets, actualizaciones… |
| 🆘 **[Foro · Soporte técnico](https://github.com/rgomezs2000/extractorfanarts/wiki/Foro-Soporte-tecnico)** | dudas de uso y **asistencia técnica** |
| 🐞 **[Foro · Fallos](https://github.com/rgomezs2000/extractorfanarts/wiki/Foro-Fallos)** | algo no funciona como debería |
| 💡 **[Foro · Ideas](https://github.com/rgomezs2000/extractorfanarts/wiki/Foro-Ideas)** | propuestas y mejoras |
| 🛠️ **[Problemas frecuentes](https://github.com/rgomezs2000/extractorfanarts/wiki/Problemas-frecuentes)** | la mayoría de los avisos, explicados |
| 🔒 **Contacto privado** | **Discord `rgomezs2010`** (fallos de seguridad y asuntos que no deban ser públicos) |

**Para publicar en el foro**: abre el tablero, pulsa **✏️ Edit**, copia la
plantilla al final de «Mensajes» y guarda. Solo hace falta una cuenta de GitHub
(gratis).

Todo esto está también **dentro del programa**: menú **Ayuda** y la ventana que se
abre con **`F1`**.

Si vas a contar un fallo, incluye la **versión** (Ayuda → Acerca de), tu
**sistema**, los **pasos**, el **`selftest.txt`** y el **registro del día**.
**Borra tus claves** de lo que compartas.

---

## 18. Licencia y uso responsable

### Licencia del programa

**Imaginteca es un programa propietario.**
**© 2026 InfoArte · Todos los derechos reservados.** · **Licencia v2** (revisada el 9 de octubre de
2026).

> El **aviso de copyright es dinámico**: mientras el año en curso sea el de
> creación verás **«© 2026 InfoArte»**, y en cuanto cambie el año pasará solo a
> **«© 2026-2027 InfoArte»** (el programa lo calcula en cada arranque).

- **Sí puedes:** ejecutarlo y usarlo **gratis**, para tu colección personal, en tus
  equipos, y hacerte una copia de seguridad.
- **No puedes:** copiarlo, publicarlo, compartirlo, subirlo a ningún sitio,
  venderlo, alquilarlo, modificarlo, descompilarlo ni reutilizar su código
  fuente. Tampoco puedes quitar los avisos de autor de este paquete.
- **El código fuente es propiedad del autor** y no se licencia.

El texto legal completo está en el archivo **`LICENSE`** que acompaña al
ejecutable. Para cualquier permiso distinto (uso comercial, redistribución,
integración en otro producto…), pídelo por escrito al autor **desde el foro de la
wiki**, indicando qué necesitas.

### Garantía: responde el autor

El programa se entrega **«tal cual»** (no hay instalador, ni registro, ni coste),
pero eso es la **forma de entrega**, no una renuncia a responder: **la garantía
corre por cuenta del autor**.

- Si algo **no hace lo que dice esta guía**, es un defecto del programa: el autor
  lo **corrige sin coste** y publica la versión corregida (la propia aplicación
  puede instalártela: mira *Actualizaciones*).
- **Se atienden los avisos.** Deja tu comentario o reporte en el **foro de la
  wiki**; para asuntos que no deban ser públicos, escribe por
  **Discord `rgomezs2010`**. Incluye el **registro del día** y el archivo
  **`selftest.txt`**. Se contesta y se trabaja en ello en un plazo razonable, sin
  coste alguno.
- **Daños directos por un defecto del programa** (por ejemplo, que sobrescriba un
  archivo que no debía): responde el autor.
- **Qué no cubre:** el contenido que descargues y el uso que hagas de él, el uso
  ilícito o contra las condiciones de una plataforma, los cambios que hagas en tu
  equipo o en tus claves, y que un servicio de terceros cambie su API o cierre.

### Componentes de terceros

El programa incluye bibliotecas de terceros (Qt/PySide6, Pillow, httpx, curl_cffi
y los motores de IA Real-ESRGAN / waifu2x) que conservan **sus propias licencias**,
detalladas en **`THIRD-PARTY-NOTICES.txt`**.

### Uso responsable

- Es una herramienta para **archivo personal** de contenido al que tengas acceso
  legítimo.
- **Respeta a los artistas** y las condiciones de uso de cada plataforma.
- No redistribuyas el material que descargues: la mayoría del fanart **no** tiene
  licencia liberada.
- El programa **no evade** CAPTCHAs, inicios de sesión ni bloqueos, y espacia sus
  peticiones a propósito.
- **No se recogen datos**: no hay telemetría, no hay servidor propio y tus claves
  no salen de tu ordenador.

---

*Imaginteca 0.1.2-beta · fase beta: si encuentras un fallo, el registro del día
(`.imaginteca\logs`) y el `selftest.txt` son lo más útil para reportarlo.*
