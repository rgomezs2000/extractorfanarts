"""Empaqueta Imaginteca en un ejecutable con PyInstaller.

Uso:
    python scripts\\build_exe.py              # carpeta dist/Imaginteca/ (onedir)
    python scripts\\build_exe.py --onefile    # un único archivo
    python scripts\\build_exe.py --consola    # conserva la ventana de consola
    python scripts\\build_exe.py --probar     # además ejecuta --selftest del resultado

IMPORTANTE (PyInstaller NO compila cruzado):
    - el .exe se genera en Windows,
    - el binario/.app de macOS se genera en macOS,
    - el binario de Linux se genera en Linux.
Para los tres de una vez usa el workflow de GitHub Actions incluido
(.github/workflows/build.yml), que compila en los tres sistemas.

Requisitos en la máquina que compila:
    pip install PySide6 httpx Pillow curl_cffi pyinstaller
    (o:  python scripts\\setup_vendor.py vendor  &&  python scripts\\setup_vendor.py vendor --ai)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
NOMBRE = "Imaginteca"

# Permite usar el PyInstaller instalado en ./vendor (sin instalación global)
if VENDOR.is_dir() and str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

# Módulos de Qt que la app no usa (slim del paquete)
EXCLUIR = [
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.QtQuick3D", "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets", "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.QtDesigner", "PySide6.QtHelp",
    "PySide6.QtUiTools", "PySide6.QtTest", "PySide6.QtSql", "PySide6.QtBluetooth",
    "PySide6.QtNfc", "PySide6.QtPositioning", "PySide6.QtSensors", "PySide6.QtSerialPort",
    "PySide6.QtWebSockets", "PySide6.QtWebChannel", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
    "tkinter", "matplotlib", "numpy", "pandas", "scipy", "IPython", "pytest",
]

PLANTILLA_CONFIG = '''# PLANTILLA-VACIA: este archivo solo es un ejemplo, sin claves.
# Escribe aquí tus credenciales, o ejecuta ejecutar.bat (copia las tuyas).
"""Ajustes y credenciales locales de Imaginteca.

Este archivo vive JUNTO AL EJECUTABLE (o en ~/.imaginteca/config_local.py).
Cualquier constante en MAYÚSCULAS sobreescribe app/config.py.

Ejemplos:
    RULE34_API_KEY = "..."
    RULE34_USER_ID = "..."
    CF_CLEARANCE = "..."
    CF_USER_AGENT = "..."
    X_BEARER_TOKEN = "..."
    PIXIV_REFRESH_TOKEN = "..."
    WEBP_QUALITY_DEFAULT = 92
    ALLOW_ADULT_RATINGS = ["general", "sensitive", "questionable", "explicit"]
"""
'''


def _pyinstaller_disponible() -> bool:
    try:
        import PyInstaller  # noqa: F401
        return True
    except ImportError:
        return False


def _rutas_datos_ia() -> list[tuple[Path, str]]:
    """(origen, destino dentro del paquete) para los motores IA y sus modelos."""
    entradas: list[tuple[Path, str]] = []
    if not VENDOR.is_dir():
        return entradas
    nombres = ("realesrgan-ncnn-vulkan", "waifu2x-ncnn-vulkan")
    for elemento in sorted(VENDOR.iterdir()):
        if elemento.name == "models" and elemento.is_dir():
            entradas.append((elemento, "vendor/models"))
            continue
        if not elemento.name.startswith(nombres):
            continue
        if elemento.is_file() and elemento.suffix.lower() == ".exe":
            entradas.append((elemento, "vendor"))
        elif elemento.is_dir():
            entradas.append((elemento, f"vendor/{elemento.name}"))
    return entradas


def _icono_para_empaquetar() -> Path | None:
    """Icono del ejecutable: .ico en Windows, .png en macOS/Linux."""
    preferidos = (("icon.ico", "icon.png") if sys.platform.startswith("win")
                  else ("icon.png", "icon.ico"))
    for nombre in preferidos:
        ruta = ROOT / "assets" / nombre
        if ruta.is_file():
            return ruta
    return None


def _argumentos(onefile: bool, consola: bool, limpiar: bool) -> list[str]:
    separador = ";" if sys.platform.startswith("win") else ":"
    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--name", NOMBRE,
        "--onefile" if onefile else "--onedir",
        "--paths", str(ROOT),
    ]
    if limpiar:
        args.append("--clean")

    if VENDOR.is_dir():
        args += ["--paths", str(VENDOR)]
    # El transporte con huella de navegador trae su propia DLL/libcurl
    args += ["--collect-all", "curl_cffi"]
    args += ["--collect-all", "certifi"]
    for modulo in EXCLUIR:
        args += ["--exclude-module", modulo]
    for origen, destino in _rutas_datos_ia():
        args += ["--add-data", f"{origen}{separador}{destino}"]
    # Icono del ejecutable (y de la barra de tareas/ventana en tiempo de ejecución)
    icono = _icono_para_empaquetar()
    if icono is not None:
        args += ["--icon", str(icono)]
    assets = ROOT / "assets"
    if assets.is_dir():
        args += ["--add-data", f"{assets}{separador}assets"]
    # El archivo de credenciales del usuario NO se empaqueta (se lee de fuera)
    args += ["--exclude-module", "app.config_local"]

    if sys.platform.startswith("win") and not consola:
        args.append("--windowed")
    elif sys.platform == "darwin" and not consola:
        args.append("--windowed")
    args.append(str(ROOT / "main.py"))
    return args


def _arreglar_etiqueta_integridad(carpeta: Path) -> None:
    """Devuelve la etiqueta de integridad del paquete a «Media» (Windows).

    Si la compilación se hace desde una consola restringida (sandbox de un agente/IDE),
    los archivos generados heredan la etiqueta **baja** de integridad y Windows lanza
    el .exe en modo restringido: la app arranca, pero **no puede escribir** en Imágenes,
    Descargas ni en `~` (da «Permiso denegado» aunque los permisos de las carpetas sean
    correctos, y el Explorador no lo arregla, porque la etiqueta viaja con el archivo).
    Este paso lo evita: es rápido, idempotente y no necesita permisos de administrador.
    """
    if not sys.platform.startswith("win"):
        return
    if not carpeta.is_dir():
        return
    icacls = shutil.which("icacls")
    if not icacls:
        print("[aviso] no se encontró icacls: revisa la etiqueta de integridad del paquete")
        return
    print("[info] revisando la etiqueta de integridad del paquete (para que no se abra "
          "en modo restringido)…")
    try:
        resultado = subprocess.run(
            [icacls, str(carpeta), "/setintegritylevel", "Medium", "/T"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
    except OSError as exc:
        print(f"[aviso] no se pudo revisar la etiqueta de integridad: {exc}")
        return
    if resultado.returncode == 0:
        print("[ok] etiqueta de integridad del paquete: Media (se abre con permisos normales)")
    else:
        detalle = (resultado.stderr or resultado.stdout or "").strip().splitlines()
        print(f"[aviso] no se pudo ajustar la etiqueta de integridad "
              f"({detalle[-1] if detalle else resultado.returncode}): si la app no puede "
              "guardar en tus carpetas, ejecuta:\n"
              f"        icacls \"{carpeta}\" /setintegritylevel Medium /T")


def _crear_plantilla(destino: Path) -> None:
    try:
        destino.mkdir(parents=True, exist_ok=True)
        archivo = destino / "config_local.py"
        if not archivo.exists():
            archivo.write_text(PLANTILLA_CONFIG, encoding="utf-8")
            print(f"[ok] plantilla de configuración: {archivo}")
    except OSError as exc:
        print(f"[aviso] no se pudo crear la plantilla: {exc}")


def _copiar_config_usuario(destino: Path) -> None:
    """Copia TUS claves (app/config_local.py) junto al ejecutable para poder probarlo.

    ⚠️ Ese archivo NO debe viajar en el .zip del release: `scripts/release.py` lo
    sustituye por la plantilla limpia antes de comprimir (y lo restaura después).
    """
    origen = ROOT / "app" / "config_local.py"
    if not origen.is_file():
        return
    try:
        destino.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origen, destino / "config_local.py")
        print("[ok] tus claves copiadas junto al ejecutable (dist\\...\\config_local.py)")
        print("     ⚠️  no compartas ese archivo: el release usa la plantilla vacía")
    except OSError as exc:
        print(f"[aviso] no se pudo copiar tu config_local.py: {exc}")


def _signtool() -> Path | None:
    """Localiza signtool.exe (viene con el Windows SDK)."""
    encontrado = shutil.which("signtool")
    if encontrado:
        return Path(encontrado)
    for base in (Path(r"C:\Program Files (x86)\Windows Kits\10\bin"),
                 Path(r"C:\Program Files\Windows Kits\10\bin")):
        if base.is_dir():
            candidatos = sorted(base.glob("*/x64/signtool.exe"))
            if candidatos:
                return candidatos[-1]
    return None


def _firmar(ejecutable: Path) -> int:
    """Firma el .exe para que Windows deje de mostrar SmartScreen.

    Necesita un certificado de firma de código (se compra a una CA; los
    autofirmados NO quitan SmartScreen). Configúralo con variables de entorno:
        EF_CERT_PFX          ruta al archivo .pfx
        EF_CERT_PASSWORD     contraseña del .pfx
      o bien
        EF_CERT_THUMBPRINT   huella SHA-1 de un certificado instalado en Windows
    """
    if not sys.platform.startswith("win"):
        print("[aviso] la firma solo aplica en Windows")
        return 1
    herramienta = _signtool()
    if herramienta is None:
        print("[error] no se encontró signtool.exe (instala el Windows SDK)")
        return 1

    base = [str(herramienta), "sign", "/fd", "sha256", "/td", "sha256",
            "/tr", "http://timestamp.digicert.com"]
    pfx = os.environ.get("EF_CERT_PFX", "").strip()
    clave = os.environ.get("EF_CERT_PASSWORD", "")
    huella = os.environ.get("EF_CERT_THUMBPRINT", "").strip()
    if pfx:
        extra = ["/f", pfx] + (["/p", clave] if clave else [])
    elif huella:
        extra = ["/sha1", huella]
    else:
        print("[error] define EF_CERT_PFX (+ EF_CERT_PASSWORD) o EF_CERT_THUMBPRINT")
        print("        (un certificado autofirmado NO elimina el aviso de SmartScreen)")
        return 1

    print(f"[info] firmando {ejecutable.name} …")
    return subprocess.call(base + extra + [str(ejecutable)], cwd=str(ROOT))


def _ruta_ejecutable(destino: Path) -> Path:
    """Ruta del ejecutable dentro de una carpeta dist (o del .app en macOS)."""
    if sys.platform.startswith("win"):
        return destino / f"{NOMBRE}.exe"
    if sys.platform == "darwin":
        app = destino / f"{NOMBRE}.app" / "Contents" / "MacOS" / NOMBRE
        return app if app.exists() else destino / NOMBRE
    return destino / NOMBRE


def _probar(destino: Path) -> int:
    ejecutable = _ruta_ejecutable(destino)
    if not ejecutable.exists():
        print(f"[aviso] no se encontró el ejecutable para probar en {destino}")
        return 1
    print(f"\n[prueba] {ejecutable} --selftest")
    try:
        return subprocess.call([str(ejecutable), "--selftest"], cwd=str(destino))
    except OSError as exc:
        print(f"[aviso] no se pudo ejecutar: {exc}")
        return 1


def main() -> int:
    onefile = "--onefile" in sys.argv
    consola = "--consola" in sys.argv
    probar = "--probar" in sys.argv
    firmar = "--firmar" in sys.argv

    if not _pyinstaller_disponible():
        print("[error] falta PyInstaller. Instálalo con:")
        print("        python -m pip install pyinstaller   (o)   "
              "python scripts\\setup_vendor.py vendor --only=pyinstaller,...")
        return 1

    print(f"[info] compilando para {sys.platform} / {os.environ.get('PROCESSOR_ARCHITECTURE', '')}")
    print(f"[info] modo: {'onefile' if onefile else 'onedir'} · "
          f"consola: {'sí' if consola else 'no'}")

    # Visibilidad: sin esto, un paquete sin motores IA parecía correcto hasta que el
    # usuario marcaba "Modo IA" y la app caía a Lanczos sin explicación.
    datos_ia = _rutas_datos_ia()
    if datos_ia:
        print("[info] motores IA incluidos: "
              + ", ".join(str(origen.name) for origen, _ in datos_ia))
    else:
        print("[aviso] NO se incluyen motores IA (el modo IA usará Lanczos + afilado). "
              "Para tenerlos:  python scripts\\setup_vendor.py vendor --solo-ia")

    entorno = dict(os.environ)
    if VENDOR.is_dir():
        previo = entorno.get("PYTHONPATH", "")
        entorno["PYTHONPATH"] = str(VENDOR) + (os.pathsep + previo if previo else "")

    codigo = subprocess.call(_argumentos(onefile, consola, limpiar=True),
                             cwd=str(ROOT), env=entorno)
    if codigo != 0:
        print(f"[error] PyInstaller terminó con código {codigo}")
        return codigo

    destino = ROOT / "dist" / (NOMBRE if not onefile else "")
    carpeta_dist = ROOT / "dist" / NOMBRE if not onefile else ROOT / "dist"
    _crear_plantilla(carpeta_dist)
    # Cada compilación borra dist\: se vuelven a copiar tus claves para poder probar
    _copiar_config_usuario(carpeta_dist)
    # Que el paquete NO quede con etiqueta de integridad baja (app en modo restringido)
    _arreglar_etiqueta_integridad(carpeta_dist)

    # La carpeta build/ contiene un ejecutable INTERMEDIO e incompleto: si alguien
    # lo ejecuta por error falla con "Failed to load Python DLL ... _internal\python312.dll".
    # Se elimina para que nadie pueda confundirse (y para no ocupar espacio).
    intermedio = ROOT / "build"
    if intermedio.is_dir():
        shutil.rmtree(intermedio, ignore_errors=True)
        print("[ok] carpeta intermedia build/ eliminada")

    ejecutable = _ruta_ejecutable(carpeta_dist)
    print()
    print("=" * 74)
    print(f"  LISTO -> {ejecutable}")
    print()
    print("  Ejecuta SIEMPRE ese archivo (el de dist\\).")
    print("  NUNCA ejecutes build\\Imaginteca\\Imaginteca.exe:")
    print("  es un paso intermedio incompleto y da error de 'Python DLL'.")
    print("=" * 74)

    if probar:
        return _probar(carpeta_dist)
    if firmar:
        return _firmar(ejecutable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
