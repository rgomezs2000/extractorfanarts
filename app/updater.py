"""Actualizaciones: consulta los Releases de GitHub, descarga y aplica la nueva versión.

Por qué existe: al publicar una versión nueva (una etiqueta `vX.Y.Z` en GitHub) la
aplicación debe poder **avisar, descargar e instalar** esa versión sin que el usuario
toque nada. Aquí vive toda esa lógica, separada de la ventana para poder probarla.

Cómo funciona el reemplazo (Windows):
  1. Se descarga el `.zip` del sistema y se comprueba su SHA-256 contra el que
     publica el Release.
  2. Se genera un pequeño `.bat` que espera a que ESTE proceso termine (no se puede
     sobrescribir un `.exe` en ejecución), descomprime encima y vuelve a abrir.
  3. La aplicación se cierra y el `.bat` hace el resto.

En macOS y Linux se descarga y se abre la carpeta con el paquete, porque reemplazar
una aplicación en marcha allí depende de cómo la tenga instalada cada usuario.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from . import canal, config

logger = logging.getLogger("imaginteca")

API = "https://api.github.com"
_CABECERAS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": f"{config.APP_NAME}-actualizador",
}
_SISTEMAS = {"win32": "Windows", "darwin": "macOS", "linux": "Linux"}


# ------------------------------------------------------------------ versiones
def clave_version(texto: str) -> tuple[int, int, int, int, int]:
    """Clave comparable: (mayor, menor, parche, es_final, número de beta).

    Así `0.1.5-beta.6 > 0.1.0-beta.1` y cualquier beta queda ANTES de la versión
    final (`0.1.0-beta.9 < 0.1.0`), que es el orden correcto al publicar.
    """
    texto = (texto or "").strip().lstrip("vV")
    coincidencia = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:[-+.]?([A-Za-z]+)\.?(\d+)?)?", texto)
    if not coincidencia:
        return (0, 0, 0, 1, 0)
    mayor, menor, parche, etiqueta, numero = coincidencia.groups()
    return (int(mayor), int(menor), int(parche), 0 if etiqueta else 1, int(numero or 0))


def version_actual() -> str:
    return str(config.APP_VERSION)


def hay_novedad(actual: str, nueva: str) -> bool:
    """¿La versión publicada es más nueva que la que se está ejecutando?"""
    return clave_version(nueva) > clave_version(actual)


def sistema_actual() -> str:
    return _SISTEMAS.get(sys.platform, "Linux")


# ------------------------------------------------------------------ consulta
def _pedir_json(url: str, timeout: int) -> object:
    peticion = urllib.request.Request(url, headers=_CABECERAS)
    with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


def _repositorios() -> list[str]:
    """Repositorio principal y, si el proyecto se renombró, el nombre anterior.

    GitHub redirige las llamadas de un repositorio renombrado, así que teniendo los
    dos la comprobación funciona antes y después de un cambio de nombre.
    """
    repos: list[str] = []
    for candidato in (getattr(config, "UPDATE_REPO", ""),
                      getattr(config, "UPDATE_REPO_ALTERNATIVO", "")):
        candidato = str(candidato or "").strip()
        if candidato and candidato not in repos:
            repos.append(candidato)
    return repos


def consultar_ultima(incluir_betas: bool | None = None,
                     timeout: int | None = None) -> dict:
    """Devuelve la última versión publicada, o lanza OSError con el motivo.

    Se miran los Releases (no las etiquetas sueltas) porque ahí están los paquetes.
    Si `incluir_betas` está activo se aceptan las pre-release: este proyecto publica
    versiones beta, que son justo las que interesan.
    """
    if incluir_betas is None:
        incluir_betas = bool(getattr(config, "UPDATE_INCLUIR_BETAS", True))
    if timeout is None:
        timeout = int(getattr(config, "UPDATE_TIMEOUT", 15))
    repos = _repositorios()
    if not repos:
        raise OSError("no hay repositorio configurado para las actualizaciones "
                      "(config.UPDATE_REPO)")

    publicados = None
    problemas: list[str] = []
    for repo in repos:
        try:
            publicados = _pedir_json(f"{API}/repos/{repo}/releases?per_page=20", timeout)
            logger.info("versiones leídas del repositorio %s", repo)
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                raise OSError(
                    "GitHub ha limitado las consultas desde tu conexión (HTTP 403).\n"
                    "Suele ser temporal: espera unos minutos y vuelve a intentarlo."
                ) from exc
            problemas.append(f"{repo}: HTTP {exc.code}")
        except Exception as exc:  # noqa: BLE001
            problemas.append(f"{repo}: {exc}")
    if publicados is None:
        raise OSError("no se pudo consultar GitHub (" + "; ".join(problemas) + ")")

    candidatos: list[dict] = []
    for release in publicados if isinstance(publicados, list) else []:
        if release.get("draft"):
            continue
        if release.get("prerelease") and not incluir_betas:
            continue
        candidatos.append(release)
    if not candidatos:
        raise OSError("no hay ninguna versión publicada todavía")

    candidatos.sort(key=lambda r: clave_version(r.get("tag_name") or ""), reverse=True)
    elegido = candidatos[0]
    etiqueta = elegido.get("tag_name") or ""
    return {
        "etiqueta": etiqueta,
        "version": etiqueta.lstrip("vV"),
        "nombre": elegido.get("name") or etiqueta,
        "notas": elegido.get("body") or "",
        "publicado": elegido.get("published_at") or "",
        "url": elegido.get("html_url") or "",
        # «beta» se deduce del NOMBRE de la versión (0.1.5-beta.6), no de la marca
        # pre-release de GitHub: desde la beta definitiva los releases son oficiales
        # y, aun así, la versión sigue siendo una beta.
        "beta": bool(elegido.get("prerelease"))
        or "beta" in str(elegido.get("tag_name") or "").lower(),
        "activos": elegido.get("assets") or [],
    }


def elegir_paquete(activos: list[dict], sistema: str | None = None) -> dict | None:
    """El `.zip` de este sistema (por ejemplo «Imaginteca-Windows.zip»)."""
    sistema = (sistema or sistema_actual()).lower()
    for activo in activos:
        nombre = str(activo.get("name") or "")
        if nombre.lower().endswith(".zip") and sistema in nombre.lower():
            return activo
    return None


def elegir_huella(activos: list[dict], paquete: dict) -> dict | None:
    """El `.sha256` que acompaña al paquete (para comprobar la descarga)."""
    esperado = f"{paquete.get('name') or ''}.sha256"
    for activo in activos:
        if str(activo.get("name") or "") == esperado:
            return activo
    return None


# ------------------------------------------------------------------ descarga
def sha256_de(archivo: Path) -> str:
    resumen = hashlib.sha256()
    with archivo.open("rb") as manejador:
        for bloque in iter(lambda: manejador.read(1024 * 1024), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def descargar(url: str, destino: Path, progreso=None, timeout: int = 60) -> Path:
    """Descarga con progreso. `progreso(descargado, total)` puede ser None."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    peticion = urllib.request.Request(url, headers=_CABECERAS)
    with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
        total = int(respuesta.headers.get("Content-Length") or 0)
        recibido = 0
        with destino.open("wb") as salida:
            while True:
                bloque = respuesta.read(256 * 1024)
                if not bloque:
                    break
                salida.write(bloque)
                recibido += len(bloque)
                if progreso is not None:
                    progreso(recibido, total)
    return destino


def leer_huella_publicada(activo_huella: dict | None, timeout: int = 30) -> str:
    """Primer campo del `.sha256` publicado (o cadena vacía si no se pudo leer)."""
    if not activo_huella:
        return ""
    url = activo_huella.get("browser_download_url") or ""
    if not url:
        return ""
    try:
        peticion = urllib.request.Request(url, headers=_CABECERAS)
        with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
            texto = respuesta.read().decode("utf-8", "replace").strip()
        return (texto.split() or [""])[0].lower()
    except Exception:  # noqa: BLE001
        logger.warning("no se pudo leer la huella publicada", exc_info=True)
        return ""


def comprobar_paquete(archivo: Path) -> bool:
    """¿El `.zip` trae de verdad la aplicación? (evita instalar un paquete ajeno)."""
    try:
        with zipfile.ZipFile(archivo) as comprimido:
            nombres = comprimido.namelist()
    except Exception:  # noqa: BLE001
        return False
    prefijos = (f"{config.APP_NAME}/", f"{config.APP_NAME}.app/")
    return any(nombre.startswith(prefijos) for nombre in nombres)


# ------------------------------------------------------------------ instalación
def carpeta_aplicacion() -> Path:
    """Carpeta donde vive la aplicación (junto al ejecutable o el propio proyecto)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def escribir_actualizador(paquete: Path, carpeta: Path | None = None) -> Path:
    """Crea el script que espera a que la app cierre, instala **limpio** y la reabre.

    Actualización LIMPIA: la versión nueva se descomprime aparte, se **conserva tu
    `config_local.py`**, se reemplaza la carpeta entera (la anterior se borra) y al
    final se retiran los restos: la versión anterior, los temporales y **el paquete
    descargado**. Así no queda nada viejo ni a medias.

    Devuelve la ruta del script. NO lo ejecuta: de eso se encarga la ventana tras
    cerrarse, para que el reemplazo ocurra cuando el ejecutable ya no está en uso.
    """
    carpeta = (carpeta or carpeta_aplicacion()).resolve()
    padre = carpeta.parent                        # el .zip trae la carpeta de la app
    temporal = Path(tempfile.mkdtemp(prefix=f"{config.APP_NAME}-actualizar-"))
    ejecutable = carpeta / f"{config.APP_NAME}.exe"
    if not ejecutable.is_file():
        candidatos = sorted(carpeta.glob(f"{config.APP_NAME}*"))
        ejecutable = candidatos[0] if candidatos else ejecutable

    if sys.platform.startswith("win"):
        guion = temporal / "actualizar.bat"
        guion.write_text(
            "@echo off\r\n"
            "chcp 65001 >nul\r\n"
            f"title {config.APP_NAME} - actualizacion limpia\r\n"
            "setlocal\r\n"
            f'set "PADRE={padre}"\r\n'
            f'set "CARPETA={carpeta}"\r\n'
            f'set "PAQUETE={paquete}"\r\n'
            'set "BAJADA=%PADRE%\\.imaginteca-tmp"\r\n'
            'set "NUEVA=%PADRE%\\.imaginteca-nueva"\r\n'
            'set "VIEJA=%PADRE%\\.imaginteca-anterior"\r\n'
            "echo ======================================================================\r\n"
            f"echo   {config.APP_NAME} - actualizacion limpia\r\n"
            "echo ======================================================================\r\n"
            "echo.\r\n"
            "echo   Esperando a que se cierre la aplicacion...\r\n"
            ":espera\r\n"
            f'tasklist /FI "PID eq {os.getpid()}" | find "{os.getpid()}" >nul 2>&1\r\n'
            "if not errorlevel 1 (\r\n"
            "  timeout /t 1 /nobreak >nul\r\n"
            "  goto espera\r\n"
            ")\r\n"
            "echo   [1/5] Descomprimiendo la version nueva...\r\n"
            'rmdir /s /q "%BAJADA%" 2>nul\r\n'
            'rmdir /s /q "%NUEVA%" 2>nul\r\n'
            "powershell -NoProfile -ExecutionPolicy Bypass -Command "
            "\"Expand-Archive -LiteralPath '%PAQUETE%' -DestinationPath '%BAJADA%' -Force\"\r\n"
            f'move "%BAJADA%\\{config.APP_NAME}" "%NUEVA%" >nul 2>&1\r\n'
            'if not exist "%NUEVA%\\' + f'{config.APP_NAME}.exe" (\r\n'
            "  echo   [ERROR] no se pudo preparar la version nueva. No se toca nada.\r\n"
            "  goto :final\r\n"
            ")\r\n"
            "echo   [2/5] Conservando tu config_local.py...\r\n"
            'if exist "%CARPETA%\\config_local.py" copy /y "%CARPETA%\\config_local.py" '
            '"%NUEVA%\\config_local.py" >nul\r\n'
            "echo   [3/5] Reemplazando la version anterior...\r\n"
            'rmdir /s /q "%VIEJA%" 2>nul\r\n'
            'move "%CARPETA%" "%VIEJA%" >nul 2>&1\r\n'
            'move "%NUEVA%" "%CARPETA%" >nul 2>&1\r\n'
            'if not exist "%CARPETA%\\' + f'{config.APP_NAME}.exe" (\r\n'
            "  echo   [ERROR] no se pudo mover la version nueva: restaurando la anterior.\r\n"
            '  move "%VIEJA%" "%CARPETA%" >nul 2>&1\r\n'
            "  goto :final\r\n"
            ")\r\n"
            "echo   [4/5] Abriendo la aplicacion...\r\n"
            f'start "" "{ejecutable}"\r\n'
            "echo   [5/5] Limpiando restos (version anterior, temporales y descarga)...\r\n"
            'rmdir /s /q "%VIEJA%" 2>nul\r\n'
            'rmdir /s /q "%BAJADA%" 2>nul\r\n'
            'rmdir /s /q "%NUEVA%" 2>nul\r\n'
            'del /q "%PAQUETE%" 2>nul\r\n'
            ":final\r\n"
            "echo.\r\n"
            "echo ======================================================================\r\n"
            "echo   Listo. ESTA CONSOLA NO SE CIERRA NI SE REINICIA:\r\n"
            "echo   el programa se ha reiniciado por su cuenta, todo quedo limpio\r\n"
            "echo   (sin version anterior, sin temporales y sin la descarga) y la\r\n"
            "echo   consola se queda para que leas el informe.\r\n"
            "echo ======================================================================\r\n"
            f'start "" cmd /c rmdir /s /q "{temporal}"\r\n',
            encoding="utf-8",
        )
        return guion

    guion = temporal / "actualizar.sh"
    guion.write_text(
        "#!/bin/sh\n"
        f'echo "== {config.APP_NAME} · actualización limpia =="\n'
        f'echo "Esperando a que se cierre {config.APP_NAME}..."\n'
        f"while kill -0 {os.getpid()} 2>/dev/null; do sleep 1; done\n"
        f'PADRE="{padre}"\n'
        f'CARPETA="{carpeta}"\n'
        f'EXE="{ejecutable}"\n'
        'BAJADA="$PADRE/.imaginteca-tmp"\n'
        'NUEVA="$PADRE/.imaginteca-nueva"\n'
        'VIEJA="$PADRE/.imaginteca-anterior"\n'
        'echo "[1/5] Descomprimiendo la versión nueva..."\n'
        'rm -rf "$BAJADA" "$NUEVA"\n'
        f'mkdir -p "$BAJADA" && unzip -oq "{paquete}" -d "$BAJADA"\n'
        f'mv "$BAJADA/{config.APP_NAME}" "$NUEVA" 2>/dev/null || true\n'
        'if [ ! -e "$NUEVA" ]; then\n'
        '  echo "[ERROR] no se pudo preparar la versión nueva. No se toca nada."\n'
        '  exit 1\n'
        'fi\n'
        'echo "[2/5] Conservando tu config_local.py..."\n'
        '[ -f "$CARPETA/config_local.py" ] && cp -f "$CARPETA/config_local.py" "$NUEVA/config_local.py"\n'
        'echo "[3/5] Reemplazando la versión anterior..."\n'
        'rm -rf "$VIEJA"; mv "$CARPETA" "$VIEJA"; mv "$NUEVA" "$CARPETA"\n'
        'echo "[4/5] Abriendo la aplicación..."\n'
        'if [ -d "$EXE" ]; then open "$EXE" 2>/dev/null || true; else "$EXE" & fi\n'
        'echo "[5/5] Limpiando restos (versión anterior, temporales y descarga)..."\n'
        'rm -rf "$VIEJA" "$BAJADA" "$NUEVA"\n'
        f'rm -f "{paquete}"\n'
        f'rm -rf "{temporal}"\n'
        'echo "Listo: el programa se ha reiniciado y todo quedó limpio."\n'
        'echo.\n'
        'echo "ESTA CONSOLA NO SE CIERRA NI SE REINICIA: el programa se ha"\n'
        'echo "reiniciado por su cuenta. Dejala abierta para leer el informe."\n'
        'printf "Pulsa Intro para cerrar esta consola... "\n'
        'read -r _ || true\n',
        encoding="utf-8",
    )
    if sys.platform == "darwin":
        # En macOS el escritorio lanza los «.command» con doble clic y Terminal los
        # abre; así la consola se ve y se queda abierta al terminar.
        destino = guion.with_suffix(".command")
        guion.rename(destino)
        guion = destino
        guion.chmod(0o755)
    return guion


def lanzar_actualizador(guion: Path) -> None:
    """Arranca el script en una **consola visible** que no se cierra al terminar.

    Vale para los tres sistemas:

      - **Windows**: una ventana de `cmd` (`cmd /k`) con el informe.
      - **macOS**: el script se guarda como `.command` y se abre con Terminal.
      - **Linux**: se busca un emulador de terminal (el del escritorio, y si no,
        `xterm`); si no hay ninguno, se ejecuta en segundo plano sin ventana.
    """
    if sys.platform.startswith("win"):
        subprocess.Popen(["cmd", "/c", "start", f"{config.APP_NAME} - actualizacion",
                          "cmd", "/k", str(guion)], close_fds=True)
        return
    if sys.platform == "darwin":
        for orden in (["open", "-a", "Terminal", str(guion)],
                      ["open", str(guion)]):
            try:
                subprocess.Popen(orden, close_fds=True)
                return
            except OSError:
                continue
    else:
        for terminal, argumentos in (
            ("x-terminal-emulator", ["-e"]),
            ("gnome-terminal", ["--"]),
            ("konsole", ["-e"]),
            ("xfce4-terminal", ["-e"]),
            ("mate-terminal", ["-e"]),
            ("lxterminal", ["-e"]),
            ("xterm", ["-e"]),
        ):
            if shutil.which(terminal):
                try:
                    subprocess.Popen([terminal, *argumentos, "/bin/sh", str(guion)],
                                     close_fds=True, start_new_session=True)
                    return
                except OSError:
                    continue
    # Sin terminal gráfico: se ejecuta igualmente (el informe queda en el registro)
    logger.info("sin emulador de terminal: ejecutando el actualizador en segundo plano")
    subprocess.Popen(["/bin/sh", str(guion)], close_fds=True, start_new_session=True)


def actualizar_desde_consola(solo_comprobar: bool = False, decir=print) -> int:
    """Actualiza el sistema desde la consola (o solo informa).

    Es lo que usan `Imaginteca --actualizar` y `--comprobar-actualizacion`: muestra
    paso a paso lo que hace (versión, paquete, descarga, huella) y, al instalar,
    lanza el instalador **limpio** que reemplaza esta copia y vuelve a abrirla.
    Devuelve el código de salida (0 = bien).
    """
    decir("")
    decir("=" * 70)
    decir(f"  {config.APP_NAME} · actualización desde la consola")
    decir("=" * 70)
    decir(f"  canal     : {canal.descripcion()}")
    decir(f"  instalada : {version_actual()}")
    decir(f"  sistema   : {sistema_actual()}")
    if not solo_comprobar and not canal.actualizaciones_activas():
        # Copia de DESARROLLO: el comando de actualización está desactivado a propósito.
        decir("")
        decir("  [desactivado] " + canal.motivo_desactivado().replace("**", ""))
        decir("")
        return 0
    if canal.es_desarrollo():
        decir("  [aviso] copia de desarrollo: solo se comprueba, no se instala nada")
    try:
        version = consultar_ultima()
    except OSError as exc:
        decir(f"  [error] {exc}")
        return 1
    decir(f"  publicada : {version['version']}"
          f"{' (beta)' if version.get('beta') else ''}")
    if not hay_novedad(version_actual(), version.get("version", "")):
        decir("  [ok] estás al día: no hay nada que instalar")
        return 0
    paquete = elegir_paquete(version.get("activos") or [])
    if paquete is None:
        decir(f"  [error] la versión nueva no trae paquete para {sistema_actual()}")
        return 1
    megas = int(paquete.get("size") or 0) / 1024 / 1024
    decir(f"  paquete   : {paquete.get('name')} ({megas:.0f} MB)")
    if solo_comprobar:
        decir("  [ok] hay una versión nueva (modo comprobación: no se instala nada)")
        return 0

    decir("")
    decir("  descargando…")
    ultimo = [-10]

    def progreso(descargado: int, total: int) -> None:
        if not total:
            return
        porcentaje = int(descargado * 100 / total)
        if porcentaje >= ultimo[0] + 10 or porcentaje == 100:
            ultimo[0] = porcentaje
            decir(f"    {porcentaje:3d} %   ({descargado / 1024 / 1024:.0f} de "
                  f"{total / 1024 / 1024:.0f} MB)")

    try:
        archivo, huella_ok = descargar_version(version, progreso)
    except OSError as exc:
        decir(f"  [error] {exc}")
        return 1
    if not huella_ok:
        decir("  [error] la huella SHA-256 NO coincide: no se instala nada")
        try:
            archivo.unlink()
        except OSError:
            pass
        return 1
    decir("  [ok] descarga verificada (SHA-256)")

    try:
        guion = escribir_actualizador(archivo)
    except Exception as exc:  # noqa: BLE001
        decir(f"  [error] no se pudo preparar la instalación: {exc}")
        return 1
    decir("  [ok] instalador preparado (reemplazo limpio: conserva tu config_local.py)")
    try:
        lanzar_actualizador(guion)
    except Exception as exc:  # noqa: BLE001
        decir(f"  [error] no se pudo abrir el instalador: {exc}")
        return 1
    decir("")
    decir("  La ventana de instalación esperará, reemplazará esta copia y volverá a")
    decir("  abrir el programa. Al terminar no queda nada viejo: se borran la versión")
    decir("  anterior, los temporales y el paquete descargado.")
    decir("")
    return 0


def descargar_version(version: dict, progreso=None) -> tuple[Path, bool]:
    """Descarga el paquete de esta versión y comprueba su huella.

    Devuelve (ruta_del_zip, huella_correcta). Lanza OSError si no hay paquete para
    este sistema o si la descarga falla.
    """
    activos = version.get("activos") or []
    paquete = elegir_paquete(activos)
    if paquete is None:
        raise OSError(f"la versión {version.get('version')} no trae paquete para "
                      f"{sistema_actual()}")
    destino = Path(tempfile.mkdtemp(prefix=f"{config.APP_NAME}-descarga-")) / \
        str(paquete.get("name"))
    descargar(str(paquete.get("browser_download_url") or ""), destino, progreso)
    if not comprobar_paquete(destino):
        raise OSError("el paquete descargado no contiene la aplicación "
                      "(¿es el archivo correcto?)")
    publicada = leer_huella_publicada(elegir_huella(activos, paquete))
    if not publicada:
        logger.warning("el Release no publica .sha256: no se puede comprobar la descarga")
        return destino, True
    return destino, sha256_de(destino) == publicada
