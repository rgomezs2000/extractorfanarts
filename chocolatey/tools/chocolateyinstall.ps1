$ErrorActionPreference = 'Stop'

# Instalador con asistente, en modo silencioso. La comprobación del hash evita que se
# instale un archivo manipulado.
$url      = 'https://github.com/rgomezs2000/extractorfanarts/releases/download/v0.1.5-beta.6/Imaginteca-0.1.5-beta.6-windows-installer.exe'
$checksum = 'f160ae7106dc2b885092d18243c23867ebfce491cd5ba94fd0921c9e985d91bd'

Install-ChocolateyPackage `
  -PackageName   'imaginteca' `
  -FileType      'exe' `
  -SilentArgs    '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-' `
  -Url           $url `
  -Checksum      $checksum `
  -ChecksumType  'sha256' `
  -ValidExitCodes @(0)
