$ErrorActionPreference = 'Stop'

Uninstall-ChocolateyPackage `
  -PackageName  'imaginteca' `
  -FileType     'exe' `
  -SilentArgs   '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' `
  -ValidExitCodes @(0)
