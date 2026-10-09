<#
.SYNOPSIS
    Firma digitalmente los archivos indicados (Windows).

.DESCRIPTION
    **Sin certificado no se firma nada** y el aviso azul de SmartScreen seguirá
    apareciendo: eso solo lo quita un certificado emitido por una autoridad de
    certificación (o Microsoft Trusted Signing). Un certificado **autofirmado no
    sirve** para eso.

    Se configura por variables de entorno (en el flujo de compilación, por secretos):

      WINDOWS_CERT_PFX_BASE64 + WINDOWS_CERT_PASSWORD   certificado .pfx en base64
      WINDOWS_CERT_THUMBPRINT                           certificado ya instalado
      TRUSTED_SIGNING_DLIB + TRUSTED_SIGNING_METADATA   Microsoft Trusted Signing

.EXAMPLE
    pwsh -File scripts\firmar_windows.ps1 dist\Imaginteca\Imaginteca.exe
#>
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $Archivos
)

$ErrorActionPreference = "Continue"

if (-not $Archivos -or $Archivos.Count -eq 0) {
    Write-Host "No se indicó ningún archivo que firmar."
    exit 0
}

$signtool = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe" -ErrorAction SilentlyContinue |
            Sort-Object FullName | Select-Object -Last 1
if (-not $signtool) {
    Write-Host "::warning::no se encontró signtool.exe (Windows SDK)"
    exit 0
}

$extra = @()
if ($env:WINDOWS_CERT_PFX_BASE64) {
    $pfx = Join-Path $env:RUNNER_TEMP "certificado.pfx"
    if (-not $env:RUNNER_TEMP) { $pfx = Join-Path ([IO.Path]::GetTempPath()) "certificado.pfx" }
    [IO.File]::WriteAllBytes($pfx, [Convert]::FromBase64String($env:WINDOWS_CERT_PFX_BASE64))
    $extra = @("/f", $pfx)
    if ($env:WINDOWS_CERT_PASSWORD) { $extra += @("/p", $env:WINDOWS_CERT_PASSWORD) }
} elseif ($env:WINDOWS_CERT_THUMBPRINT) {
    $extra = @("/sha1", $env:WINDOWS_CERT_THUMBPRINT)
} elseif ($env:TRUSTED_SIGNING_DLIB) {
    $extra = @("/dlib", $env:TRUSTED_SIGNING_DLIB, "/dmdf", $env:TRUSTED_SIGNING_METADATA)
} else {
    Write-Host "Sin certificado configurado: NO se firma."
    Write-Host "  · WINDOWS_CERT_PFX_BASE64 (+ WINDOWS_CERT_PASSWORD)  (certificado .pfx)"
    Write-Host "  · WINDOWS_CERT_THUMBPRINT                            (certificado instalado)"
    Write-Host "  · TRUSTED_SIGNING_DLIB + TRUSTED_SIGNING_METADATA    (Microsoft Trusted Signing)"
    Write-Host "El aviso azul de SmartScreen seguirá apareciendo hasta que haya uno."
    exit 0
}

$fallos = 0
foreach ($archivo in $Archivos) {
    if (-not (Test-Path $archivo)) {
        Write-Host "::warning::no existe: $archivo"
        continue
    }
    Write-Host "Firmando $archivo"
    & $signtool.FullName sign @extra /fd sha256 /td sha256 /tr http://timestamp.digicert.com "$archivo"
    if ($LASTEXITCODE -ne 0) { $fallos++ }
    & $signtool.FullName verify /pa "$archivo"
}
if ($pfx) { Remove-Item $pfx -Force -ErrorAction SilentlyContinue }
Write-Host "Archivos firmados: $($Archivos.Count - $fallos) de $($Archivos.Count)"
exit 0
