# 📦 Instalación sin la ventana azul (gratis)

Windows muestra el aviso azul *«Windows protegió su PC»* a los programas descargados
del navegador que **no están firmados** con un certificado de una autoridad. Ese
certificado **cuesta dinero** y **no hay ninguno gratuito** para software propietario
([opciones de firma de Microsoft](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options));
uno autofirmado **no sirve** (no es de confianza para otros equipos).

Pero hay una vía **gratuita** para que tus usuarios no lo vean: **instalar con Scoop**.
Scoop descarga los paquetes con su propio descargador, **sin la marca de internet** que
dispara SmartScreen, así que el programa se abre sin ningún aviso.

## Publicar el bucket (una sola vez)

1. Crea un repositorio en tu cuenta llamado **`scoop-bucket`** (público).
2. Sube **`imaginteca.json`** (esta carpeta) a la raíz de ese repositorio.
3. Cuando saques una versión nueva, regenera el manifiesto y súbelo:

   ```powershell
   python scripts\scoop\generar_manifiesto.py     # toma la última release oficial
   ```

   Scoop también puede actualizarlo solo (`checkver` + `autoupdate` ya están puestos).

## Cómo lo instalan los usuarios

```powershell
scoop bucket add rgomezs2000 https://github.com/rgomezs2000/scoop-bucket
scoop install imaginteca
```

…y **no aparece la ventana azul**. Se actualiza con `scoop update imaginteca`.

## Otras vías gratis

| Vía | Estado | Notas |
|---|---|---|
| **Scoop** | ✅ listo (este manifiesto) | No necesita revisión de nadie: el bucket es tuyo |
| **Chocolatey** | 🟡 posible | Gratis, pero el paquete pasa por moderación de la comunidad |
| **winget** | 🟡 posible | Gratis; se envía un PR a `microsoft/winget-pkgs` y **pueden exigir el instalador firmado** |
| **Reputación** | ✅ automático | Con el tiempo y descargas, SmartScreen deja de avisar aunque no esté firmado |
| **Microsoft Store** | ❌ no encaja | Lo firma Microsoft, pero el contenido para adultos de la app choca con sus políticas |

## Y si algún día hay certificado

El proyecto ya tiene la firma cableada (`scripts\firmar_windows.ps1`): ejecutable,
asistente de Pixiv e instalador se firman solos en cuanto existan los secretos
(`WINDOWS_CERT_PFX_BASE64`, `WINDOWS_CERT_THUMBPRINT` o Trusted Signing).
