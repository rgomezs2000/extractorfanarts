# 📦 Instalación sin la ventana azul (va dentro del proyecto y del release)

Windows muestra el aviso azul *«Windows protegió su PC»* a los programas descargados
del navegador que **no están firmados** con un certificado de una autoridad. Ese
certificado **cuesta dinero** y **no hay ninguno gratuito** para software propietario
([opciones de firma de Microsoft](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options));
uno autofirmado **no sirve**.

La vía **gratuita** que sí funciona es **Scoop**, que descarga el paquete **sin la marca
de internet** que dispara SmartScreen. Este manifiesto **viaja con el proyecto y con el
release**: no hay que crear ningún repositorio aparte ni publicar nada a mano.

## Cómo lo instala el usuario final (una sola orden)

```powershell
scoop install https://github.com/rgomezs2000/extractorfanarts/releases/latest/download/imaginteca.json
```

…y el programa se abre **sin ningún aviso**. Se actualiza con `scoop update imaginteca`
(el manifiesto ya trae `checkver` y `autoupdate`, así que Scoop lo hace solo).

> **Scoop se instala una vez** en el equipo del usuario (es su gestor de paquetes, dos
> órdenes en PowerShell):
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> irm get.scoop.sh | iex
> ```
> Quien no quiera Scoop sigue teniendo el **instalador** y el **portátil** de siempre
> (con el aviso azul, porque no hay certificado).

## Cómo se mantiene (automático)

El flujo de publicación genera el manifiesto **en cada versión**, a partir del propio
`.zip` ya construido, y lo publica junto al resto de adjuntos (`imaginteca.json` y su
`.sha256`). No hay que tocar nada.

Para generarlo a mano (por ejemplo, tras publicar algo):

```powershell
python scripts\scoop\generar_manifiesto.py                 # toma la última release oficial
python scripts\scoop\generar_manifiesto.py --zip dist\Imaginteca-Windows.zip --version 0.1.5-beta.8
```

## La firma: automática en cada compilación

`scripts\build_exe.py` **firma solo** cuando hay certificado configurado, así que cada
compilación sale firmada sin pedir nada:

```powershell
$env:EF_CERT_PFX = "C:\ruta\certificado.pfx"; $env:EF_CERT_PASSWORD = "…"
python scripts\build_exe.py            # compila y firma
```

En el flujo de compilación se firman **el ejecutable, el asistente de Pixiv y el
instalador** en cuanto existan los secretos (`WINDOWS_CERT_PFX_BASE64`,
`WINDOWS_CERT_THUMBPRINT` o `TRUSTED_SIGNING_DLIB` + `TRUSTED_SIGNING_METADATA`).
Sin certificado, la compilación avisa de que sale **sin firmar** y no finge nada.

## Otras vías gratis

| Vía | Estado | Notas |
|---|---|---|
| **Scoop** | ✅ dentro del release | Una orden, sin bucket aparte, sin aviso |
| **Chocolatey** | 🟡 posible | Gratis, con moderación de la comunidad |
| **winget** | 🟡 posible | Gratis; puede que exijan el instalador firmado |
| **Reputación** | ✅ automático | Con el tiempo y descargas, SmartScreen deja de avisar |
| **Microsoft Store** | ❌ no encaja | Lo firma Microsoft, pero choca con el contenido para adultos |
