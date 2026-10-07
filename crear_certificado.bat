@echo off
REM ============================================================
REM  Crea el certificado de firma AUTOFIRMADO (gratis)
REM
REM  Se hace SIN Python a proposito: el Python de la Microsoft
REM  Store lanza PowerShell dentro de un contenedor restringido
REM  que no puede leer el almacen de certificados (por eso falla
REM  con "No existe ninguna unidad con el nombre 'Cert'").
REM ============================================================
setlocal
cd /d "%~dp0"

echo ============================================================
echo   Creando certificado de firma de codigo (autofirmado)
echo ============================================================
echo.

where powershell >nul 2>&1
if errorlevel 1 (
  echo [ERROR] No se encontro PowerShell.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\hacer_certificado.ps1" %*
if errorlevel 1 goto error

echo.
echo ============================================================
echo   Listo. Ahora firma el ejecutable con:
echo     set EF_CERT_PFX=%%CD%%\certs\codigo.pfx
echo     set EF_CERT_PASSWORD=(la clave que se muestra arriba)
echo     python scripts\build_exe.py --firmar
echo ============================================================
echo.
pause
exit /b 0

:error
echo.
echo [ERROR] No se pudo crear el certificado.
echo.
echo   Que hacer:
echo     1) Abre PowerShell desde el menu Inicio (NO desde Python ni desde
echo        la terminal de un IDE que herede restricciones).
echo     2) Comprueba el almacen:  Test-Path Cert:\CurrentUser\My
echo        Debe responder:  True
echo     3) Ejecuta a mano (desde la carpeta del proyecto):
echo          powershell -NoProfile -ExecutionPolicy Bypass -File scripts\hacer_certificado.ps1
echo.
echo   Si Test-Path responde False en una consola normal, tu equipo tiene una
echo   politica (WDAC/AppLocker) que bloquea el almacen de certificados: en ese
echo   caso firma desde otro equipo o usa un servicio en la nube (Azure Trusted
echo   Signing, DigiCert KeyLocker, SSL.com eSigner).
echo.
pause
exit /b 1
