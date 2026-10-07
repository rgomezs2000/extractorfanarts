@echo off
REM ============================================================
REM  Firma ExtractorFanarts.exe con el certificado de certs\
REM
REM  Se hace SIN Python: el Python de la Microsoft Store lanza
REM  sus procesos hijos en un contenedor que no puede usar el
REM  almacen de claves/certificados (fallaria con "Acceso denegado").
REM
REM  Requisitos:
REM    - certs\codigo.pfx   (crealo con: crear_certificado.bat)
REM    - su clave (se lee de certs\clave.txt o la pides por pantalla)
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "EXE=dist\ExtractorFanarts\ExtractorFanarts.exe"
set "PFX=%~dp0certs\codigo.pfx"

if not exist "%EXE%" (
  echo [ERROR] No hay ejecutable. Compila primero con: compilar.bat
  echo.
  pause
  exit /b 1
)

if not exist "%PFX%" (
  echo [ERROR] No existe el certificado: %PFX%
  echo         Crealo primero con: crear_certificado.bat
  echo.
  pause
  exit /b 1
)

REM Localizar signtool (Windows SDK)
set "SIGNTOOL="
for /f "delims=" %%i in ('dir /b /s "C:\Program Files (x86)\Windows Kits\10\bin\signtool.exe" 2^>nul') do set "SIGNTOOL=%%i"
if not defined SIGNTOOL (
  for /f "delims=" %%i in ('dir /b /s "C:\Program Files\Windows Kits\10\bin\signtool.exe" 2^>nul') do set "SIGNTOOL=%%i"
)
if not defined SIGNTOOL (
  echo [ERROR] No se encontro signtool.exe. Instala el Windows SDK.
  echo.
  pause
  exit /b 1
)

REM Clave del .pfx: variable de entorno o certs\clave.txt
if "%EF_CERT_PASSWORD%"=="" (
  if exist "certs\clave.txt" (
    set /p EF_CERT_PASSWORD=<certs\clave.txt
  ) else (
    set /p EF_CERT_PASSWORD=Escribe la clave del .pfx: 
  )
)

echo ============================================================
echo   Firmando %EXE%
echo   Con: %PFX%
echo ============================================================
echo.

"%SIGNTOOL%" sign /f "%PFX%" /p "%EF_CERT_PASSWORD%" /fd sha256 /td sha256 /tr http://timestamp.digicert.com "%EXE%"
if errorlevel 1 goto error

echo.
echo Verificando la firma...
"%SIGNTOOL%" verify /pa /v "%EXE%" | findstr /i "Successfully Issued Subject Issued to"
echo.
echo ============================================================
echo   LISTO: el ejecutable esta firmado.
echo ============================================================
echo.
pause
exit /b 0

:error
echo.
echo [ERROR] No se pudo firmar.
echo   - Comprueba la clave del .pfx (certs\clave.txt)
echo   - Si dice "Acceso denegado", ejecuta este .bat con doble clic
echo     desde el Explorador (no desde una consola restringida)
echo.
pause
exit /b 1
