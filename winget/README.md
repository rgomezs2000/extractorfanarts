# 🪟 winget

Manifiestos para instalar Imaginteca con **winget** (el gestor de paquetes de Windows),
generados por `scripts\empaquetadores\generar_manifiestos.py`.

```powershell
winget install InfoArte.Imaginteca
```

## Qué hay aquí

| Archivo | Para qué |
|---|---|
| `InfoArte.Imaginteca.yaml` | Manifiesto de **versión** |
| `InfoArte.Imaginteca.installer.yaml` | Manifiesto del **instalador** (URL, SHA-256 y los interruptores silenciosos del `.exe` de Inno Setup) |
| `InfoArte.Imaginteca.locale.es-ES.yaml` | Textos en **español** (autor, descripción, etiquetas, licencia) |

## Publicarlo (una vez por versión)

1. Regenera los manifiestos (o cógelos del release, que se publican en cada versión):

   ```powershell
   python scripts\empaquetadores\generar_manifiestos.py
   ```

2. Envía un **PR a [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs)**
   con los tres archivos en esta ruta (la estructura que exige winget):

   ```
   manifests/i/InfoArte/Imaginteca/<versión>/
   ```

   Lo más cómodo es `wingetcreate`:

   ```powershell
   winget install wingetcreate
   wingetcreate update InfoArte.Imaginteca --version <versión> `
       --urls https://github.com/rgomezs2000/extractorfanarts/releases/download/v<versión>/Imaginteca-<versión>-windows-installer.exe `
       --submit
   ```

3. Un revisor lo valida y, cuando se aprueba, aparece en `winget install InfoArte.Imaginteca`.

> ⚠️ **Aviso importante:** la validación de winget **puede exigir que el instalador esté
> firmado** con un certificado de una autoridad. Como no hay certificado gratuito para
> software propietario, es posible que no lo acepten hasta que exista uno. Por eso
> **Scoop** es la vía que funciona hoy sin gastar nada (su manifiesto va en
> `scoop/imaginteca.json` y se instala con una orden desde el propio release).
