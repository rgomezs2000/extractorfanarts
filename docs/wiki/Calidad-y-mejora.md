# Calidad y mejora

## Todo se guarda en WebP

- **El formato es siempre `.webp`**, con la calidad que elijas en el deslizador
  (1–100; por defecto 90).
- **El archivo original no se conserva**: se guarda el resultado procesado.
- **La transparencia se respeta** (los PNG con alfa siguen teniendo alfa).
- **Los nombres** son `Plataforma_id_hash.webp`, así que no se pisan entre sí.

## Mejorar calidad (✨)

Cuando marcas **✨ Mejorar calidad**, el reescalado depende del tamaño de partida:

| Tamaño original | Aumento |
|---|---|
| hasta **699 px** | **×4** |
| **700 – 799 px** | **×3** |
| **800 px o más** | **×2** |
| por encima de **7679 px** | solo se convierte a WebP |

El tope es **8K** (7680 px de lado), y se aplica un **afilado suave y calibrado**
en lugar de un enfoque agresivo: así las líneas no ganan halos blancos.

**Siempre verás lo que se ha hecho:** al guardar o copiar, la barra de estado
indica el tamaño de partida y el resultado real:

```
153x153 → 612x612 · Lanczos 4x
```

Si el origen era **muy pequeño** (menos de 300 px) te avisa, porque **agrandar una
imagen diminuta no crea detalle real** — conviene saberlo antes de entrenar un
modelo con ella.

## Modo IA (🤖)

- Usa los motores **Real-ESRGAN** y **waifu2x** (ncnn-vulkan), que van incluidos
  en el paquete y aprovechan tu tarjeta gráfica.
- Da **más detalle real**, sobre todo en dibujos y en originales pequeños.
- Si los motores no están disponibles o fallan, **te lo dice** y usa el reescalado
  clásico: **nunca** guarda una imagen corrupta ni a medias.
- El programa comprueba que la salida de la IA se parezca al original
  (si saliera un mosaico o un desplazamiento, la descarta) y **devuelve la paleta
  a la del original** si un modelo cambia el color más de la cuenta.

> **Si el modo IA «no mejora nada»** (y en el registro aparece
> `encode image … failed`), los motores pueden haber heredado una etiqueta de
> integridad baja de Windows que les impide escribir su resultado. Se arregla en
> la carpeta del programa con:
> ```powershell
> icacls _internal\vendor /setintegritylevel Medium /T
> ```
> Si no, desmarca *Modo IA*: con **✨ Mejorar calidad** sigue mejorando (Lanczos).

## Cuándo usar cada cosa

| Situación | Recomendación |
|---|---|
| Arte con líneas limpias, tamaño decente | **✨ Mejorar calidad** sin IA |
| Dibujo pequeño, boceto, mucho detalle perdido | **✨ Mejorar calidad + 🤖 Modo IA** |
| Imagen ya enorme (más de 1600 px) | Sin mejora o solo WebP: no gana nada |
| Fotos o ilustraciones realistas | **Modo IA** (Real-ESRGAN) |
| Preparar un [dataset](Datasets-IA) | Mejora **uniforme**: mismas casillas para todo |

## Sin sorpresas

- Si algo falla al guardar, el archivo **no queda a medias**: se descarta y se
  registra el motivo.
- El proceso **no deja basura**: ni carpetas temporales, ni PNG intermedios, ni
  registros del motor en tu carpeta de salida.
- Cada archivo se comprueba al guardarlo: si la conversión saliera corrupta, se
  detecta y se descarta.

---

**Siguiente:** [Datasets para IA](Datasets-IA) ·
**¿Ves artefactos o halos?** [Problemas frecuentes](Problemas-frecuentes)
