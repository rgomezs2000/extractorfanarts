"""Propiedades de una imagen: todo lo que la plataforma de origen sabe de ella.

Cada adaptador guarda la respuesta **completa** del servicio en `obra.raw`, así que aquí
se sacan de ahí los datos que interesan y se agrupan para poder leerlos de un vistazo:

  - **Imagen**: lo común (título, autor, fecha, rating, licencia, tamaño, enlaces…).
  - **Interacción**: favoritos, reposts, respuestas, vistas, guardados, comentarios…
    (en el fediverso, los totales son los del **servidor de origen** de la publicación,
    que es la copia canónica; cada instancia conoce los suyos).
  - **Del servicio**: lo propio de cada plataforma (boorus: fuentes, etiquetas por
    categoría, quién subió y quién aprobó; wikis: licencia, autor, descripción original…).
  - **Descripción** y **Todo lo demás**: el texto del post y el resto de campos que trae
    el servicio, para no perder nada.
"""
from __future__ import annotations

import datetime
import re

# (etiqueta, claves posibles en el JSON del servicio, en orden de preferencia)
CAMPOS = {
    "favoritos": ("Favoritos", ("favourites_count", "favorite_count", "like_count",
                                "likeCount", "likes_count", "total_bookmarks",
                                "favorites", "fav_count")),
    "reposts": ("Reposts / boosts", ("reblogs_count", "reblog_count", "repost_count",
                                     "repostCount", "retweet_count", "reposts",
                                     "reblog_count")),
    "respuestas": ("Respuestas / comentarios", ("replies_count", "reply_count",
                                                "replyCount", "comment_count",
                                                "comments_count", "comments",
                                                "total_comments", "note_count")),
    "vistas": ("Vistas", ("view_count", "views", "total_view", "impression_count",
                          "viewCount", "stats.views")),
    "guardados": ("Guardados / marcadores", ("bookmark_count", "saves", "save_count",
                                             "pin_count")),
    "citas": ("Citas", ("quote_count", "quoteCount")),
    "renotes": ("Renotes (Misskey)", ("renoteCount",)),
}

# Claves que ya se muestran en «Imagen», «Interacción» o «Del servicio»: no se repiten
# al final en «Todo lo demás».
_YA_MOSTRADAS = {
    "favourites_count", "favorite_count", "like_count", "likeCount", "likes_count",
    "total_bookmarks", "favorites", "fav_count", "reblogs_count", "reblog_count",
    "repost_count", "repostCount", "retweet_count", "reposts", "replies_count",
    "reply_count", "replyCount", "comment_count", "comments_count", "comments",
    "total_comments", "note_count", "view_count", "views", "total_view",
    "impression_count", "viewCount", "bookmark_count", "saves", "save_count",
    "pin_count", "quote_count", "quoteCount", "renoteCount", "url", "uri", "id",
    "created_at", "createdAt", "content", "text", "tags", "media_attachments",
    "sensitive", "visibility", "language", "file_ext", "mime", "file_size", "size",
    "md5", "sha1", "image_width", "image_height", "width", "height", "source",
    "tag_string", "tag_string_artist", "tag_string_character", "tag_string_copyright",
    "tag_string_general", "tag_string_meta", "uploader_id", "approver_id",
    "change_count", "parent_id", "has_children", "has_notes", "is_deleted", "status",
    "score", "up_score", "down_score", "rating", "wiki", "file", "info",
    "extmetadata", "account", "application", "display_name", "acct",
    "followers_count", "following_count", "statuses_count", "note", "illust_type",
    "user", "create_date", "page_count", "x_restrict", "timestamp", "userid",
    "descriptionurl", "description", "caption", "public_metrics", "stats",
    "deviationid", "in_reply_to_id", "edited_at", "preview_url", "page_url",
}


def _valor_legible(valor) -> str:
    """Texto de un valor que puede ser texto, número o un objeto del servicio."""
    if isinstance(valor, dict):
        for clave in ("name", "title", "value", "label", "acct", "id"):
            if valor.get(clave) not in (None, ""):
                return _limpio(valor[clave])
        return ", ".join(f"{k}={_limpio(v, 40)}" for k, v in list(valor.items())[:4])
    if isinstance(valor, list):
        return ", ".join(_limpio(v, 40) for v in valor[:6])
    return _limpio(valor)


def _numero(valor) -> str:
    """Número con separador de millares (o el valor tal cual si no es número)."""
    try:
        return f"{int(valor):,}".replace(",", " ")
    except (TypeError, ValueError):
        return str(valor)


def _fecha(valor) -> str:
    """Fecha legible a partir de ISO 8601 (o el texto original si no se entiende)."""
    if not valor:
        return ""
    texto = str(valor)
    try:
        limpio = texto.replace("Z", "+00:00")
        momento = datetime.datetime.fromisoformat(limpio)
        try:
            momento = momento.astimezone()
        except (ValueError, OSError):
            pass
        return momento.strftime("%d/%m/%Y a las %H:%M")
    except ValueError:
        return texto


def _limpio(valor, ancho: int = 220) -> str:
    """Texto de una línea, sin etiquetas HTML y recortado si es larguísimo."""
    texto = re.sub(r"<[^>]+>", " ", str(valor))
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto if len(texto) <= ancho else texto[: ancho - 1] + "…"


def _buscar(datos: dict, claves) -> tuple[str, object] | None:
    """Primer (clave, valor) que exista en el diccionario, siguiendo el orden dado."""
    for clave in claves:
        if "." in clave:                     # ruta simple: stats.views
            partes = clave.split(".")
            valor = datos
            for parte in partes:
                if isinstance(valor, dict) and parte in valor:
                    valor = valor[parte]
                else:
                    valor = None
                    break
            if valor not in (None, "", [], {}):
                return clave, valor
            continue
        valor = datos.get(clave)
        if valor not in (None, "", [], {}):
            return clave, valor
    return None


def familia(obra) -> str:
    """Qué familia de servicio es, mirando los datos crudos (no el nombre)."""
    datos = obra.raw if isinstance(obra.raw, dict) else {}
    claves = set(datos)
    if {"favourites_count", "reblogs_count", "replies_count"} & claves:
        return "fediverso"
    if {"likeCount", "repostCount", "replyCount"} & claves:
        return "bluesky"
    if "renoteCount" in claves or "reactions" in claves and "createdAt" in claves:
        return "fediverso"
    if "note_count" in claves:
        return "tumblr"
    if {"total_view", "total_bookmarks"} & claves:
        return "pixiv"
    if "public_metrics" in claves:
        return "twitter"
    if "stats" in claves or "deviationid" in claves:
        return "deviantart"
    if {"wiki", "file"} <= claves:
        return "wiki"
    if {"score", "fav_count"} & claves or {"tag_string", "file_url"} & claves:
        return "booru"
    if "pin" in claves or {"link", "saves"} <= claves:
        return "pinterest"
    return "generico"


def _ancho_alto(obra) -> tuple[object, object]:
    """Resolución: del propio objeto o de los datos del servicio."""
    ancho = getattr(obra, "width", None)
    alto = getattr(obra, "height", None)
    datos = obra.raw if isinstance(obra.raw, dict) else {}
    if not (ancho and alto):
        info = datos.get("info") if isinstance(datos.get("info"), dict) else {}
        for clave_a, clave_b in (("image_width", "image_height"), ("width", "height")):
            ancho = ancho or datos.get(clave_a) or info.get(clave_a)
            alto = alto or datos.get(clave_b) or info.get(clave_b)
    return ancho, alto


def propiedades(obra) -> list[tuple[str, list[tuple[str, str]]]]:
    """[(grupo, [(campo, valor), …]), …] para mostrar en la ventana de propiedades."""
    datos = obra.raw if isinstance(obra.raw, dict) else {}
    familia_obra = familia(obra)
    grupos: list[tuple[str, list[tuple[str, str]]]] = []

    # ---------------------------------------------------------------- imagen
    imagen: list[tuple[str, str]] = []
    if obra.author:
        imagen.append(("Autor", str(obra.author)))
    if obra.site:
        imagen.append(("Plataforma", str(obra.site)))
    if obra.created_at:
        imagen.append(("Fecha de publicación", _fecha(obra.created_at)))
    elif datos.get("created_at") or datos.get("createdAt") or datos.get("timestamp"):
        imagen.append(("Fecha de publicación",
                       _fecha(datos.get("created_at") or datos.get("createdAt")
                              or datos.get("timestamp"))))
    ancho, alto = _ancho_alto(obra)
    if ancho and alto:
        try:
            proporcion = f" ({float(ancho) / float(alto):.2f}:1)"
        except (TypeError, ValueError, ZeroDivisionError):
            proporcion = ""
        imagen.append(("Resolución", f"{ancho} × {alto} px{proporcion}"))
    if obra.rating:
        imagen.append(("Clasificación", str(obra.rating)))
    if obra.license:
        imagen.append(("Licencia", str(obra.license)))
    if datos.get("sensitive") is not None:
        imagen.append(("Marcada como sensible", "sí" if datos["sensitive"] else "no"))
    for clave, etiqueta in (("visibility", "Visibilidad"), ("language", "Idioma"),
                            ("file_ext", "Formato"), ("mime", "Tipo"),
                            ("file_size", "Tamaño (bytes)"), ("size", "Tamaño (bytes)"),
                            ("md5", "Hash MD5"), ("sha1", "Hash SHA-1"),
                            ("image_width", "Ancho (px)"), ("image_height", "Alto (px)")):
        if datos.get(clave) not in (None, "", [], {}):
            valor = datos[clave]
            imagen.append((etiqueta, _numero(valor) if clave.endswith("size")
                           else _limpio(valor)))
    if obra.url:
        imagen.append(("Enlace de la imagen", str(obra.url)))
    if obra.page_url:
        imagen.append(("Página de la obra", str(obra.page_url)))
    if obra.animacion:
        imagen.append(("Animación", f"sí ({obra.animacion.get('tipo', 'ugoira')})"))
    grupos.append(("Imagen", imagen))

    # ---------------------------------------------------------------- interacción
    interaccion: list[tuple[str, str]] = []
    for clave in ("favoritos", "reposts", "respuestas", "vistas", "guardados", "citas",
                  "renotes"):
        etiqueta, claves = CAMPOS[clave]
        encontrado = _buscar(datos, claves)
        if encontrado:
            interaccion.append((etiqueta, _numero(encontrado[1])))
    if familia_obra == "fediverso" and interaccion:
        interaccion.append(("Nota", "totales del servidor de origen de la publicación "
                                    "(la copia canónica del fediverso)"))
    if familia_obra == "booru":
        for clave, etiqueta in (("score", "Puntuación"), ("up_score", "Votos a favor"),
                                ("down_score", "Votos en contra")):
            if datos.get(clave) not in (None, ""):
                interaccion.append((etiqueta, _numero(datos[clave])))
    if interaccion:
        grupos.append(("Interacción", interaccion))

    # ---------------------------------------------------------------- del servicio
    servicio: list[tuple[str, str]] = []
    if familia_obra == "booru":
        fuentes = datos.get("source")
        if fuentes:
            for numero, fuente in enumerate(str(fuentes).split(), start=1):
                servicio.append((f"Fuente {numero}" if numero > 1 else "Fuente",
                                 _limpio(fuente, 300)))
        for clave, etiqueta in (("tag_string_artist", "Etiquetas · artista"),
                                ("tag_string_character", "Etiquetas · personaje"),
                                ("tag_string_copyright", "Etiquetas · franquicia"),
                                ("tag_string_general", "Etiquetas · generales"),
                                ("tag_string_meta", "Etiquetas · meta"),
                                ("tag_string", "Etiquetas")):
            if datos.get(clave):
                cuantas = len(str(datos[clave]).split())
                servicio.append((etiqueta, f"{cuantas} etiqueta"
                                           f"{'s' if cuantas != 1 else ''}: "
                                           + _limpio(datos[clave], 400)))
        for clave, etiqueta in (("uploader_id", "Subida por (id)"),
                                ("approver_id", "Aprobada por (id)"),
                                ("change_count", "Cambios"),
                                ("parent_id", "Obra de la que deriva"),
                                ("has_children", "Tiene variantes"),
                                ("has_notes", "Tiene notas"),
                                ("is_deleted", "Borrada en el sitio"),
                                ("status", "Estado")):
            if datos.get(clave) not in (None, "", [], {}):
                servicio.append((etiqueta, _limpio(datos[clave])))
    elif familia_obra == "wiki":
        for clave, etiqueta in (("wiki", "Wiki"), ("file", "Archivo")):
            if datos.get(clave):
                servicio.append((etiqueta, _limpio(datos[clave])))
        info = datos.get("info") if isinstance(datos.get("info"), dict) else {}
        ext = info.get("extmetadata") if isinstance(info.get("extmetadata"), dict) else {}
        for clave, etiqueta in (("ImageDescription", "Descripción original"),
                                ("Artist", "Autor (según la wiki)"),
                                ("LicenseShortName", "Licencia"),
                                ("UsageTerms", "Condiciones de uso"),
                                ("DateTimeOriginal", "Fecha original"),
                                ("Categories", "Categorías"),
                                ("Credit", "Crédito"),
                                ("Attribution", "Atribución")):
            valor = (ext.get(clave) or {}).get("value") if isinstance(ext.get(clave), dict) \
                else ext.get(clave)
            if valor:
                servicio.append((etiqueta, _limpio(valor, 300)))
        for clave, etiqueta in (("user", "Subida por"), ("timestamp", "Subida el"),
                                ("descriptionurl", "Página del archivo"),
                                ("sha1", "Hash SHA-1"), ("mime", "Tipo"),
                                ("width", "Ancho"), ("height", "Alto"),
                                ("size", "Tamaño (bytes)")):
            if info.get(clave) not in (None, "", [], {}):
                valor = info[clave]
                servicio.append((etiqueta, _fecha(valor) if clave == "timestamp"
                                 else _limpio(valor)))
    elif familia_obra in ("fediverso", "bluesky"):
        cuenta = datos.get("account") or datos.get("author") or {}
        if isinstance(cuenta, dict):
            for clave, etiqueta in (("display_name", "Nombre de la cuenta"),
                                    ("acct", "Cuenta"),
                                    ("followers_count", "Seguidores"),
                                    ("following_count", "Siguiendo a"),
                                    ("statuses_count", "Publicaciones"),
                                    ("note", "Biografía")):
                if cuenta.get(clave) not in (None, "", [], {}):
                    valor = cuenta[clave]
                    servicio.append((etiqueta, _numero(valor)
                                     if clave.endswith("count") else _limpio(valor)))
        for clave, etiqueta in (("uri", "URI (identificador federado)"),
                                ("application", "Aplicación de origen"),
                                ("in_reply_to_id", "Responde a"),
                                ("edited_at", "Editada el")):
            if datos.get(clave) not in (None, "", [], {}):
                servicio.append((etiqueta, _valor_legible(datos[clave])))
    elif familia_obra == "pixiv":
        for clave, etiqueta in (("illust_type", "Tipo de obra"),
                                ("user", "Autor"), ("create_date", "Creada el"),
                                ("page_count", "Páginas"), ("x_restrict", "Restricción"),
                                ("width", "Ancho"), ("height", "Alto")):
            if datos.get(clave) not in (None, "", [], {}):
                servicio.append((etiqueta, _limpio(datos[clave])))
    if servicio:
        grupos.append(("Del servicio", servicio))

    # ---------------------------------------------------------------- descripción
    descripcion = obra.content_text or datos.get("content") or datos.get("text") \
        or datos.get("description") or datos.get("caption")
    if descripcion:
        grupos.append(("Descripción", [("Texto", _limpio(descripcion, 1200))]))

    # ---------------------------------------------------------------- etiquetas
    if obra.tags:
        grupos.append(("Etiquetas", [(f"{len(obra.tags)} etiquetas",
                                      ", ".join(str(t) for t in obra.tags[:80]))]))

    # ---------------------------------------------------------------- lo demás
    resto: list[tuple[str, str]] = []
    for clave, valor in datos.items():
        if clave in _YA_MOSTRADAS or valor in (None, "", [], {}):
            continue
        if isinstance(valor, (dict, list)):
            texto = f"{len(valor)} elemento(s): {_valor_legible(valor)}"
        else:
            texto = _valor_legible(valor)
        resto.append((str(clave), texto[:220]))
    if resto:
        grupos.append(("Todo lo demás (datos del servicio)", resto[:60]))

    return [(grupo, [(campo, valor) for campo, valor in campos if valor not in ("", None)])
            for grupo, campos in grupos if campos]


def como_texto(obra) -> str:
    """Las mismas propiedades en texto plano (para copiar o pegar)."""
    lineas = [f"{obra.summary()}", "=" * 60]
    for grupo, campos in propiedades(obra):
        lineas.append("")
        lineas.append(f"— {grupo} —")
        for campo, valor in campos:
            lineas.append(f"  {campo}: {valor}")
    return "\n".join(lineas) + "\n"
