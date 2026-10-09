# 🍫 Chocolatey

Paquete para instalar Imaginteca con **Chocolatey** (Windows), generado por
`scripts\empaquetadores\generar_manifiestos.py`. Sirve para que el usuario instale
**con una orden** y **sin el aviso azul** de Windows (Chocolatey descarga sin la marca
de internet que dispara SmartScreen).

```powershell
choco install imaginteca
```

## Qué hay aquí

| Archivo | Para qué |
|---|---|
| `imaginteca.nuspec` | Ficha del paquete (nombre, versión, autor, licencia, descripción) |
| `tools\chocolateyinstall.ps1` | Descarga el **instalador** y lo ejecuta en modo silencioso, **comprobando el hash SHA-256** |
| `tools\chocolateyuninstall.ps1` | Desinstala con el desinstalador que deja el instalador |

## Publicarlo en la comunidad (una vez por versión)

1. Regenera los manifiestos (o espera al flujo: se publican en cada release):

   ```powershell
   python scripts\empaquetadores\generar_manifiestos.py
   ```

2. Empaqueta y sube (necesita cuenta en [community.chocolatey.org](https://community.chocolatey.org)
   y su **API key**):

   ```powershell
   choco pack chocolatey\imaginteca.nuspec
   choco apikey --key <TU_API_KEY> --source https://push.chocolatey.org/
   choco push imaginteca.<versión>.nupkg --source https://push.chocolatey.org/
   ```

3. La comunidad lo revisa (suele tardar **de uno a varios días**) y, cuando lo acepta,
   aparece en `choco install imaginteca`.

> La revisión es humana y pueden pedir cambios (por ejemplo, la licencia propietaria
> debe quedar clara). Hasta que lo acepten, el paquete de este repositorio ya es válido:
> cualquiera puede instalarlo desde la carpeta con `choco install imaginteca.nuspec`.
