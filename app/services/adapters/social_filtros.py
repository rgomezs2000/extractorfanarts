"""Filtros de búsqueda social: usuario + varias palabras clave + varios hashtags.

La UI tiene tres campos (usuario, palabras clave y hashtags) y las APIs del fediverso
y de Bluesky **no** saben combinarlos (ni aceptan varios valores): si pides la timeline
de un usuario, te devuelve *todo* lo suyo. Aquí se resuelve con una **intersección
local** con estas reglas:

  - `@usuario`      → solo publicaciones de esa cuenta (si se indica).
  - palabras clave  → deben aparecer **todas** en el texto (varias = más preciso).
  - hashtags        → deben aparecer **todos** en el texto o en las etiquetas.
  - los campos que no se rellenen, simplemente no se exigen.

Los valores se pueden separar con comas, espacios o almohadillas, así que
`#lola_loud #the_loud_house`, `#lola_loud,#the_loud_house` y `#lola_loud#the_loud_house`
se interpretan igual. Las comillas permiten frases exactas: `"lola loud"`.

El campo más «selectivo» decide de qué fuente se tiran los candidatos (usuario >
primer hashtag > primera palabra) y después se aplican **todos** los filtros.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence

_SEPARADORES = re.compile(r"[#,\s]+")
_ENTRECOMILLADO = re.compile(r'("[^"]*")')
_ESPACIOS = re.compile(r"\s+")
# Separadores admitidos en el campo de palabras clave (varias palabras clave/frases):
# coma (lo recomendado), punto y coma, barra vertical y salto de línea.
_SEPARADORES_PALABRAS = re.compile(r"[,;|\n]+")


def _norm(texto: str) -> str:
    return _ESPACIOS.sub(" ", (texto or "").strip().lower())


def _modo_alguno() -> bool:
    """¿Con varios valores dentro de un campo basta con que aparezca alguno?

    Se configura con `SOCIAL_VARIOS_EN_CAMPO` en `app/config_local.py`:
      - `"todos"` (por defecto): intersección, más preciso.
      - `"alguno"`: unión, más resultados (cualquiera de los valores vale).
    """
    from ... import config

    valor = str(getattr(config, "SOCIAL_VARIOS_EN_CAMPO", "todos") or "todos").strip().lower()
    return valor in ("alguno", "algunos", "cualquiera", "o", "or", "any")


def _modo_texto() -> str:
    return "alguno de los valores de cada campo" if _modo_alguno() \
        else "todos los valores indicados"


def separar_hashtags(texto: str) -> list[str]:
    """'#lola_loud #the_loud_house' → ['lola_loud', 'the_loud_house'] (sin repetir).

    Se admite cualquier mezcla de espacios, comas y almohadillas, así que
    '#lola_loud #the_loud_house', '#lola_loud,#the_loud_house' y
    '#lola_loud#the_loud_house' se interpretan igual.
    """
    vistos: list[str] = []
    for parte in _SEPARADORES.split(texto or ""):
        limpio = parte.strip().lstrip("#").strip()
        if limpio and limpio.lower() not in [v.lower() for v in vistos]:
            vistos.append(limpio)
    return vistos


def separar_palabras(texto: str) -> list[str]:
    """'lola loud, lincoln loud' → ['lola loud', 'lincoln loud'] (sin repetir).

    Cada valor (separado por **comas**, punto y coma, barra vertical o salto de línea)
    es una palabra clave o frase: sus palabras deben aparecer todas, en cualquier orden.
    Con comillas se busca la frase exacta. Un único valor con espacios ('Lola Loud') es
    una sola frase, así que si quieres varias, sepáralas con comas:
    'Lola Loud, Lincoln Loud, The Loud House'.
    """
    frases: list[str] = []

    def anadir(valor: str) -> None:
        limpio = _norm(valor)
        if limpio and limpio not in frases:
            frases.append(limpio)

    for trozo in _ENTRECOMILLADO.split(texto or ""):
        if not trozo:
            continue
        if trozo.startswith('"') and trozo.endswith('"') and len(trozo) > 2:
            anadir(trozo[1:-1])
            continue
        for parte in _SEPARADORES_PALABRAS.split(trozo):
            anadir(parte)
    return frases


def partes_handle(usuario: str) -> tuple[str, str]:
    """'@Mysterbox@baraag.net' → ('mysterbox', 'baraag.net')."""
    limpio = (usuario or "").strip().lstrip("@")
    if "@" in limpio:
        nombre, host = limpio.split("@", 1)
        return nombre.strip().lower(), host.strip().lower()
    return limpio.lower(), ""


@dataclass
class Criterios:
    """Los filtros que pidió el usuario, ya normalizados."""

    usuario: str = ""
    palabras: tuple[str, ...] = ()
    hashtags: tuple[str, ...] = ()
    consulta: str = ""          # texto tal cual lo escribió el usuario (para mensajes)
    _descripcion: str = field(default="", repr=False)

    # ------------------------------------------------------------------ construcción
    @classmethod
    def desde_query(cls, query) -> "Criterios":
        return cls(
            usuario=(getattr(query, "usuario", "") or "").strip(),
            palabras=tuple(separar_palabras(getattr(query, "keyword", "") or "")),
            hashtags=tuple(separar_hashtags(getattr(query, "hashtag", "") or "")),
            consulta=" · ".join(
                p for p in (
                    (getattr(query, "usuario", "") or "").strip(),
                    (getattr(query, "keyword", "") or "").strip(),
                    (getattr(query, "hashtag", "") or "").strip(),
                ) if p
            ),
        )

    # ------------------------------------------------------------------ propiedades
    @property
    def vacio(self) -> bool:
        return not (self.usuario or self.palabras or self.hashtags)

    @property
    def fuente(self) -> str:
        """De dónde se piden los candidatos: usuario > hashtag > palabra."""
        if self.usuario:
            return "usuario"
        if self.hashtags:
            return "hashtag"
        if self.palabras:
            return "palabra"
        return ""

    def descripcion(self) -> str:
        partes = []
        if self.usuario:
            partes.append(self.usuario)
        for palabra in self.palabras:
            partes.append(f"«{palabra}»")
        for tag in self.hashtags:
            partes.append(f"#{tag}")
        return " + ".join(partes)

    def detalle(self) -> str:
        """Cómo se han interpretado los campos (para la línea de estado y el log)."""
        trozos = []
        if self.usuario:
            trozos.append(f"usuario={self.usuario}")
        if self.palabras:
            trozos.append("palabras=[" + " · ".join(self.palabras) + "]")
        if self.hashtags:
            trozos.append("hashtags=[" + " · ".join('#' + t for t in self.hashtags) + "]")
        if not trozos:
            return "sin filtros"
        return " ; ".join(trozos) + f"  (se exigen {_modo_texto()})"

    def _cumplen(self, valores: list[bool]) -> bool:
        """¿Se cumplen los valores exigidos? (alguno, o todos según la configuración)."""
        if not valores:
            return True
        if _modo_alguno():
            return any(valores)
        return all(valores)

    @property
    def exigir_todos(self) -> bool:
        """True si con varios valores dentro de un campo se exigen todos (intersección)."""
        return not _modo_alguno()

    def consulta_para(self, hallar: str = "palabra") -> str:
        """Término con el que consultar la API cuando la fuente es palabra/hashtag."""
        if self.hashtags:
            return self.hashtags[0]
        return self.palabras[0] if self.palabras else ""

    def como_etiquetas(self) -> "Criterios":
        """Copia en la que cada palabra clave se exige como **etiqueta** derivada.

        Sirve de respaldo en instancias que no permiten buscar por texto sin cuenta:
        «Lola Loud» se busca como la etiqueta `#lola_loud` (las etiquetas del fediverso
        no llevan espacios), y así la búsqueda por palabras sigue dando resultados.
        """
        derivadas = list(self.hashtags)
        for palabra in self.palabras:
            etiqueta = palabra.replace(" ", "_").replace("-", "_")
            if etiqueta and etiqueta.lower() not in [d.lower() for d in derivadas]:
                derivadas.append(etiqueta)
        return Criterios(usuario=self.usuario, palabras=(), hashtags=tuple(derivadas),
                         consulta=self.consulta)

    def etiquetas_derivadas(self) -> list[str]:
        """Etiquetas equivalentes a las palabras clave («Lola Loud» → lola_loud)."""
        return [p.replace(" ", "_").replace("-", "_") for p in self.palabras if p]

    # ------------------------------------------------------------------ aplicación
    def cumple(self, *, texto: str = "", etiquetas: Iterable[str] = (),
               autor: str = "") -> bool:
        """¿La publicación pasa TODOS los filtros indicados?

        Entre campos siempre se exige todo (usuario **y** palabras **y** hashtags).
        Dentro de un campo, con varios valores: por defecto se exigen todos
        (`SOCIAL_VARIOS_EN_CAMPO = "todos"`); con `"alguno"` basta con que aparezca
        cualquiera de ellos.
        """
        if self.usuario and not _autor_coincide(autor, self.usuario):
            return False
        cuerpo = _norm(texto)
        nombres = {_norm(e).lstrip("#") for e in etiquetas if e}
        if self.palabras and not self._cumplen([p in cuerpo for p in self.palabras if p]):
            return False
        if self.hashtags:
            if not self._cumplen([_norm(t) in nombres or f"#{_norm(t)}" in cuerpo
                                  for t in self.hashtags]):
                return False
        return True

    def explica(self, *, texto: str = "", etiquetas: Iterable[str] = (),
                autor: str = "") -> str:
        """Motivo por el que NO pasa los filtros ('' si los pasa). Útil para el log."""
        if self.usuario and not _autor_coincide(autor, self.usuario):
            return f"autor {autor or '?'} ≠ {self.usuario}"
        cuerpo = _norm(texto)
        nombres = {_norm(e).lstrip("#") for e in etiquetas if e}
        faltan = [f"«{p}»" for p in self.palabras if p and p not in cuerpo]
        faltan += [f"#{t}" for t in self.hashtags
                   if _norm(t) not in nombres and f"#{_norm(t)}" not in cuerpo]
        return "falta " + ", ".join(faltan) if faltan else ""


def _autor_coincide(autor: str, criterio: str) -> bool:
    """Compara '@usuario@host' / '@usuario' con el autor de una publicación.

    Acepta también el formato con puntos ('usuario.host'), que es como se escriben los
    handles en Bluesky, para que un `@usuario@host` del fediverso encuentre a la misma
    persona si allí se llama `usuario.host`.
    """
    if not criterio:
        return True
    if not autor:
        return False
    nombre, host = partes_handle(criterio)
    autor_limpio = (autor or "").strip().lstrip("@").lower()
    if autor_limpio == nombre:
        return True
    if host and autor_limpio in (f"{nombre}.{host}", f"{nombre}@{host}"):
        return True
    autor_nombre, autor_host = partes_handle(autor_limpio)
    if nombre != autor_nombre:
        return False
    if not host:
        return True                      # basta con el nombre de usuario
    return not autor_host or autor_host == host


def resumen_filtros(criterios: Criterios) -> str:
    """Texto corto para el log/estatus: qué filtros se están aplicando."""
    partes = []
    if criterios.usuario:
        partes.append(criterios.usuario)
    if criterios.palabras:
        partes.append(f"{len(criterios.palabras)} palabra(s) clave")
    if criterios.hashtags:
        partes.append(f"{len(criterios.hashtags)} hashtag(s)")
    return " + ".join(partes) if partes else "sin filtros"


def etiquetas_de(*listas: Sequence[str]) -> list[str]:
    """Une etiquetas quitando vacíos y repetidos (conservando el orden)."""
    vistas: list[str] = []
    for lista in listas:
        for etiqueta in lista or ():
            limpio = (etiqueta or "").strip()
            if limpio and limpio.lower() not in [v.lower() for v in vistas]:
                vistas.append(limpio)
    return vistas


def repartir_en_lotes(valores: Sequence[str], longitud_max: int,
                      separador: str = " ") -> list[list[str]]:
    """Reparte los valores en lotes que quepan en `longitud_max` **sin perder ninguno**.

    Se usa cuando la API limita la longitud de la consulta (X, Bluesky): en lugar de
    descartar los valores que no caben, se hacen varias consultas (una por lote) y sus
    resultados se unen. Un valor que por sí solo supere el límite va en su propio lote.
    """
    lotes: list[list[str]] = []
    actual: list[str] = []
    longitud = 0
    for valor in valores:
        extra = len(valor) + (len(separador) if actual else 0)
        if actual and longitud + extra > longitud_max:
            lotes.append(actual)
            actual, longitud = [], 0
            extra = len(valor)
        actual.append(valor)
        longitud += extra
    if actual:
        lotes.append(actual)
    return lotes or [[]]
