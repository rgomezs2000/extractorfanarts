# Soporte técnico

Aquí se atiende **cualquier duda o fallo**, gratis, y es también la forma de hacer
valer la **garantía del autor**: los defectos que se reportan **se corrigen sin
coste** y se publica la versión corregida.

## Dónde contar tu caso

| Canal | Para qué | Enlace |
|---|---|---|
| 💬 **Foro (en la wiki)** | Dudas de uso, cómo hacer algo, preguntas abiertas y **asistencia técnica** | [Foro](https://github.com/rgomezs2000/extractorfanarts/wiki/Foro) |
| 🐞 **Fallos (en la wiki)** | Fallos con seguimiento y peticiones de mejora | [Fallos](https://github.com/rgomezs2000/extractorfanarts/wiki/Foro-Fallos) |
| 📖 **Wiki** | Consultar antes de preguntar | [Wiki](https://github.com/rgomezs2000/extractorfanarts/wiki) |
| ✉️ **Contacto directo** | Lo que prefieras tratar en privado | `rogergomezs2003@gmail.com` |

Puedes **comentar en el foro o en la wiki**: todo se lee y se
contesta.

## Qué incluir (esto hace que te ayuden a la primera)

1. **Qué intentabas hacer** y qué esperabas que pasara.
2. **Qué pasó de verdad** (mensaje exacto, si lo hay).
3. **Pasos para reproducirlo**, si puedes.
4. **Tu versión**: la ves en **Ayuda → Acerca de** (o `Imaginteca.exe --version`).
5. **Tu sistema**: Windows / Linux / macOS y la versión.
6. **Dos archivos que valen oro:**

   ```powershell
   # 1) Informe del entorno (genera selftest.txt junto al programa)
   Imaginteca.exe --selftest
   ```

   | Archivo | Dónde está |
   |---|---|
   | **`selftest.txt`** | junto al programa, después de ejecutar `--selftest` |
   | **Registro del día** | `%USERPROFILE%\.imaginteca\logs\app-AAAA-MM-DD.log` (Linux/macOS: `~/.imaginteca/logs/...`) |

   > 🔐 **Revisa antes lo que compartes**: quita de tus capturas o archivos las
   > claves que aparezcan (en el registro se ocultan, pero mejor comprobar).

7. **Una captura o un recorte** de la imagen si el problema es de calidad (halos,
   artefactos, colores). Basta un recorte al 100 % de la zona afectada.

## Qué garantiza el autor

- **Corregir sin coste** los defectos que se reporten y publicar la versión
  corregida (el programa puede instalártela: ver [Actualizaciones](Actualizaciones)).
- **Atender** los avisos y las consultas.
- **Responder de los daños directos** que un defecto del programa cause en tus
  archivos o en tu equipo.
- Contestar y trabajar en ello **en un plazo razonable**, sin coste alguno.

**No cubre**: el contenido que descargues ni el uso que hagas de él, el uso
ilícito o contra las condiciones de una plataforma, los cambios que hagas en tu
equipo o en tus claves, ni que un servicio de terceros cambie su API o cierre (en
ese caso se avisa y se adapta en cuanto se puede). El texto completo está en la
[Licencia](Licencia).

## Antes de escribir

- Mira **[Problemas frecuentes](Problemas-frecuentes)**: la mayoría de los avisos
  están explicados.
- Si el problema apareció **después de actualizar**, dilo: es el dato más útil.
- Si es un fallo de **una plataforma concreta**, indica cuál y el término buscado.

---

Gracias por tomarte un minuto en reportar bien: eso es lo que hace que la
siguiente versión salga mejor.
