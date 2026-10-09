@echo off
REM ---------------------------------------------------------------------------
REM  Publica las paginas de docs\wiki\ en la Wiki de GitHub del repositorio.
REM
REM  Se puede ejecutar las veces que haga falta:
REM    - la DOCUMENTACION se actualiza desde docs\wiki\ (manda el repositorio);
REM    - las paginas del FORO NO se sobrescriben si ya existen, porque pueden
REM      tener mensajes de usuarios.
REM ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0"

echo ======================================================================
echo   Publicar la wiki de Imaginteca
echo ======================================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo   [error] No se encuentra Python en el PATH.
  echo           Ejecutalo a mano desde una consola:
  echo               python scripts\publicar_wiki.py --esperar
  goto :fin
)

echo   La wiki de GitHub NO existe hasta que se guarda UNA pagina desde la
echo   web (GitHub no lo permite por git). Si todavia no existe, este
echo   programa ESPERA y publica solo en cuanto la crees.
echo.
echo   Abre esto en el navegador:
echo.
echo       https://github.com/rgomezs2000/extractorfanarts/wiki
echo.
echo   Pulsa "Create the first page", guarda cualquier titulo (por ejemplo
echo   "Inicio") y ya esta: aqui se publicaran las 24 paginas.
echo.
echo ----------------------------------------------------------------------
python scripts\publicar_wiki.py --esperar
echo ----------------------------------------------------------------------
echo.

:fin
echo ======================================================================
echo   Pulsa una tecla para cerrar esta ventana.
echo ======================================================================
pause >nul
