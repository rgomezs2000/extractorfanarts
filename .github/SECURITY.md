# Política de seguridad

## Cómo reportar un problema de seguridad

Si encuentras un fallo que pueda comprometer la seguridad o la privacidad de
quien use Imaginteca —por ejemplo, que **tus claves salgan de tu equipo**, que se
ejecute código no previsto, o que se pueda escribir fuera de las carpetas
permitidas—, **no lo publiques en el foro**: escríbelo en privado a

**rogergomezs2003@gmail.com**

indicando:

1. Qué has encontrado y **por qué es un problema**.
2. **Cómo reproducirlo** (versión, sistema y pasos).
3. Si lo deseas, cómo quieres que se te acredite.

Se contesta **en un plazo razonable** y se trabaja en la corrección **sin coste**.
Si el fallo afecta a datos o a la privacidad, se avisará por el
[foro](https://github.com/rgomezs2000/extractorfanarts/wiki/Foro) una vez
publicada la versión corregida, con el detalle justo para que la gente pueda
protegerse.

## Qué se considera un problema de seguridad

- Que **tus claves o tokens** se envíen a un sitio distinto del que corresponde.
- Que se pueda **ejecutar código** o abrir archivos ajenos por contenido
  descargado (imágenes o metadatos maliciosos).
- Que se pueda **escribir o borrar** fuera de la carpeta de salida y de la carpeta
  de datos.
- Que el **actualizador** acepte un paquete no firmado o con huella incorrecta, o
  que instale algo que no venga del Release oficial.
- Cualquier **telemetría o envío de datos** no documentado (no existe, y si
  apareciera, sería un fallo grave).

## Lo que NO es un problema de seguridad

- Que una plataforma de terceros bloquee, limite o cambie su API.
- Que un booru devuelva contenido que no esperabas: usa los
  [filtros](https://github.com/rgomezs2000/extractorfanarts/wiki/Claves-y-configuracion).
- Que Windows muestre el aviso azul de programa no firmado (está documentado en
  [Instalación](https://github.com/rgomezs2000/extractorfanarts/wiki/Instalacion)).
- Que el programa no evada un CAPTCHA o un inicio de sesión: **es intencionado**.

## Garantía

Este programa es **propietario** y se entrega **«tal cual»**, pero la **garantía
corre por cuenta del autor**: los defectos —de seguridad incluidos— que se
reporten **se corrigen sin coste** y se publica la versión corregida. Ver
[LICENSE](LICENSE).
