@echo off
REM ============================================================
REM  Compila Imaginteca en un .exe para Windows
REM  NO usa pip: las dependencias se instalan en .\vendor
REM  (asi se evita el error de rutas largas de la Microsoft Store)
REM ============================================================
setlocal
cd /d "%~dp0"

echo ============================================================
echo   Imaginteca - compilacion para Windows
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] No se encontro Python en el PATH.
  echo         Instala Python desde https://www.python.org/downloads/
  echo         y marca la casilla "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

echo [1/4] Dependencias de la aplicacion (PySide6, httpx, Pillow, curl_cffi)...
if exist "vendor\PySide6" (
  echo       ya estan en .\vendor
) else (
  python scripts\setup_vendor.py vendor
  if errorlevel 1 goto error
)

echo [2/4] PyInstaller (para empaquetar)...
if exist "vendor\PyInstaller" (
  echo       ya esta en .\vendor
) else (
  python scripts\setup_vendor.py vendor --only=pyinstaller,pyinstaller-hooks-contrib,altgraph,packaging,setuptools,pefile,pywin32-ctypes
  if errorlevel 1 goto error
)

echo [3/4] Compilando el ejecutable...
echo.
REM --consola: el .exe abre una ventana de consola con los registros (ver el .log
REM del dia en vivo). Si prefieres compilarlo sin consola, quita ese argumento.
python scripts\build_exe.py --consola
if errorlevel 1 goto error

echo [4/4] Asistente de token de Pixiv (se entrega dentro del paquete)...
python scripts\build_token_exe.py
if errorlevel 1 goto error

echo.
echo ============================================================
echo   LISTO
echo   Ejecutable: dist\Imaginteca\Imaginteca.exe
echo   Asistente : dist\Imaginteca\pixiv-token.exe
echo.
echo   Al abrirlo se abre tambien una consola con los registros
echo   (los mismos que el .log del dia, en .imaginteca\logs).
echo.
echo   Antes de ejecutarlo, copia tu app\config_local.py a
echo   dist\Imaginteca\config_local.py (tus claves van ahi,
echo   nunca dentro del .exe).
echo ============================================================
echo.
pause
exit /b 0

:error
echo.
echo [ERROR] La compilacion fallo. Revisa el mensaje de arriba.
echo.
pause
exit /b 1
