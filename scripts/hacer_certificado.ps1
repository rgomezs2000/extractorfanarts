<#
    Crea un certificado de firma de código AUTOFIRMADO y lo exporta a certs\.

    Úsalo así (sin Python, para evitar el contenedor del Python de la Store):
        powershell -NoProfile -ExecutionPolicy Bypass -File scripts\hacer_certificado.ps1
    o con doble clic en  crear_certificado.bat

    Parámetros:
        -Nombre "Mi Editor"   nombre del certificado
        -Clave  "MiClave123"  contraseña del .pfx (si no se indica, se genera)
        -Confiar              añadirlo también a la raíz de confianza del usuario
                              (muestra un diálogo de Windows pidiendo confirmación)

    ⚠️  Un certificado autofirmado sirve para TU equipo; NO elimina SmartScreen en
        los equipos de otras personas (para eso hace falta un certificado de una CA).
    🔐  certs\ contiene la clave privada: está en .gitignore, no lo subas nunca.
#>
param(
    [string]$Nombre = "Imaginteca (pruebas)",
    [string]$Clave = "",
    [switch]$Confiar
)

$ErrorActionPreference = "Stop"

$raiz = Split-Path -Parent $PSScriptRoot
$certs = Join-Path $raiz "certs"
New-Item -ItemType Directory -Force -Path $certs | Out-Null

if (-not $Clave) {
    $alfabeto = (48..57) + (65..90) + (97..122)
    $Clave = -join ($alfabeto | Get-Random -Count 20 | ForEach-Object { [char]$_ })
}

Write-Host ""
Write-Host "[1/4] Creando el certificado de firma de codigo ..." -ForegroundColor Cyan
$cert = New-SelfSignedCertificate -Type CodeSigningCert `
    -Subject "CN=$Nombre" -FriendlyName $Nombre `
    -KeyUsage DigitalSignature -KeyExportPolicy Exportable `
    -CertStoreLocation Cert:\CurrentUser\My `
    -NotAfter (Get-Date).AddYears(3) `
    -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3")

Write-Host "[2/4] Exportando certs\codigo.pfx y certs\codigo.cer ..." -ForegroundColor Cyan
$segura = ConvertTo-SecureString -String $Clave -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath (Join-Path $certs "codigo.pfx") -Password $segura | Out-Null
Export-Certificate -Cert $cert -FilePath (Join-Path $certs "codigo.cer") | Out-Null
$Clave | Out-File -Encoding ascii -NoNewline (Join-Path $certs "clave.txt")

Write-Host "[3/4] Marcandolo como editor de confianza (solo tu usuario) ..." -ForegroundColor Cyan
try {
    Import-Certificate -FilePath (Join-Path $certs "codigo.cer") `
        -CertStoreLocation Cert:\CurrentUser\TrustedPublisher | Out-Null
    Write-Host "      hecho"
} catch {
    Write-Host "      (omitido: $($_.Exception.Message))" -ForegroundColor Yellow
}

if ($Confiar) {
    Write-Host "[4/4] Anadiendo a la raiz de confianza (acepta el dialogo) ..." -ForegroundColor Cyan
    Import-Certificate -FilePath (Join-Path $certs "codigo.cer") `
        -CertStoreLocation Cert:\CurrentUser\Root | Out-Null
} else {
    Write-Host "[4/4] (omitido: usa -Confiar para anadirlo a la raiz de confianza)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  CERTIFICADO CREADO" -ForegroundColor Green
Write-Host "  Huella         : $($cert.Thumbprint)"
Write-Host "  Archivo .pfx   : $(Join-Path $certs 'codigo.pfx')"
Write-Host "  Clave del .pfx : $Clave"
Write-Host ""
Write-Host "  Para firmar el ejecutable:"
Write-Host "    `$env:EF_CERT_PFX = `"$(Join-Path $certs 'codigo.pfx')`""
Write-Host "    `$env:EF_CERT_PASSWORD = `"$Clave`""
Write-Host "    python scripts\build_exe.py --firmar"
Write-Host ""
