# 🔔 Notificaciones

El programa avisa de lo importante y lo cuenta:

| Cuándo | Qué dice |
|---|---|
| Termina una **búsqueda** | «Búsqueda completada — N imágenes encontradas» |
| Una búsqueda **no trae nada** | «La búsqueda no trajo resultados» (y el motivo) |
| Termina una **descarga** | «Descarga completada — N imágenes guardadas» (o con fallos) |
| Hay un **error** | «Se produjo un error» con el resumen |
| Sale una **versión nueva** | «Versión nueva disponible: …» al arrancar |
| **Plataformas caídas** | «Servicios con problemas: …» (comprobación del menú Ayuda) |

## Dónde se ven

- **Campana 🔔** de la barra de herramientas: número sin leer; al pulsarla, la lista y las
  opciones de marcar como leídas o borrar.
- **Barra de estado**: el último aviso.
- **Ventana minimizada**: notificación del **sistema operativo** (Windows, macOS, Linux) y
  **insignia con el número** en el icono de la barra de tareas / Dock. El icono es el mismo
  de la aplicación.

## Estado de las redes sociales

En **Ayuda › 📡 Estado de las redes sociales** se comprueba, una por una, **todas las
plataformas del programa**:

- **Redes sociales (7):** X, Pinterest, DeviantArt, Tumblr, Pixiv, Bluesky y Mastodon.
- **Boorus (14):** los que tengas configurados, incluidos los que añadas en
  config_local.py (salen de la lista real del programa, no de una copia).
- **Wiki de fandom:** la plataforma con la que se leen los fandoms.

Con su estado, latencia y enlace a su página de estado (doble clic en la fila). Los
estados posibles:

| Estado | Significa |
|---|---|
| **operativo** | El servicio responde con normalidad |
| **operativo (bloquea robots)** | Está en pie, pero filtra a los programas (403/429) |
| **con problemas** | Responde con errores del servidor (5xx) |
| **sin respuesta** | No contesta a tiempo o el dominio no resuelve |

> Es una foto del **servicio**, no de tus permisos: que una red esté «operativa» no
> significa que funcione sin identificarte.

Para silenciar los avisos: `NOTIFICACIONES = False` en `config_local.py`.

---

**[← Calidad y mejora](Calidad-y-mejora)** · **[Actualizaciones →](Actualizaciones)**
