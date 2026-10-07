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

REM Tus claves: se leen desde aqui (nunca van dentro del .exe)
if not exist "dist\ExtractorFanarts\config_local.py" (
  if exist "app\config_local.py" (
    copy /y "app\config_local.py" "dist\ExtractorFanarts\config_local.py" >nul
    echo [ok] config_local.py copiado junto al ejecutable
  ) else (
    echo [aviso] no tienes app\config_local.py; la app arrancara sin claves
  )
)

echo Iniciando ExtractorFanarts...
start "" "%EXE%"
exit /b 0
