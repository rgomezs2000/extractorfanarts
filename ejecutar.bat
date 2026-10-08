@echo off
REM ============================================================
REM  Ejecuta ExtractorFanarts (el compilado de dist\)
REM  Copia tu config_local.py automaticamente si falta.
REM ============================================================
setlocal
cd /d "%~dp0"

set "EXE=dist\ExtractorFanarts\ExtractorFanarts.exe"

if not exist "%EXE%" (
  echo [ERROR] No hay ejecutable compilado.
  echo         Ejecuta primero:  compilar.bat
  echo.
  pause
  exit /b 1
)

REM Tus claves: se leen desde aqui (nunca van dentro del .exe).
REM Se copian si falta el archivo O si lo que hay es la plantilla vacia
REM (cada recompilacion borra dist\ y deja la plantilla).
set "COPIAR="
if not exist "dist\ExtractorFanarts\config_local.py" set "COPIAR=1"
if exist "dist\ExtractorFanarts\config_local.py" (
  findstr /C:"PLANTILLA-VACIA" "dist\ExtractorFanarts\config_local.py" >nul 2>&1
  if not errorlevel 1 set "COPIAR=1"
)
if defined COPIAR (
  if exist "app\config_local.py" (
    copy /y "app\config_local.py" "dist\ExtractorFanarts\config_local.py" >nul
    echo [ok] tus claves copiadas junto al ejecutable
  ) else (
    echo [aviso] no tienes app\config_local.py; la app arrancara sin claves
  )
)

REM Etiqueta de integridad "Media": si el paquete se compilo dentro de un entorno
REM restringido (sandbox), sus archivos quedan con etiqueta baja y Windows abre la
REM app en modo restringido: arranca pero NO puede escribir en tus carpetas
REM (Imagenes, Descargas, ~). Esto lo corrige (rapido, sin permisos de admin).
icacls "dist\ExtractorFanarts" /setintegritylevel Medium /T >nul 2>&1

echo Iniciando ExtractorFanarts...
start "" "%EXE%"
exit /b 0
