#!/bin/sh
# Instalador típico de macOS: un .dmg con la aplicación y un acceso a Aplicaciones.
#
# Lo llama el flujo de compilación en macOS:
#     sh scripts/instaladores/crear_instalador_macos.sh <version> <dist> <salida>
#
# El usuario abre el .dmg, arrastra Imaginteca a Aplicaciones y ya está (es el gesto
# habitual en macOS). La versión portátil (.zip / .tar.gz) sigue existiendo.
set -e

VERSION="${1:?falta la versión}"
DIST="${2:?falta la carpeta del paquete}"
SALIDA="${3:?falta la carpeta de salida}"

NOMBRE="Imaginteca"
DMG="$SALIDA/$NOMBRE-$VERSION-macos-installer.dmg"
MONTAJE="$(mktemp -d)/$NOMBRE"

mkdir -p "$SALIDA" "$MONTAJE"

echo "[info] copiando la aplicación al volumen del instalador…"
# La app puede venir como .app (si se compiló con --windowed en macOS) o como
# carpeta con el binario dentro.
if [ -d "$DIST/$NOMBRE.app" ]; then
  cp -a "$DIST/$NOMBRE.app" "$MONTAJE/"
else
  cp -a "$DIST" "$MONTAJE/$NOMBRE"
fi
cp -a "$DIST"/*.txt "$MONTAJE/" 2>/dev/null || true

echo "[info] añadiendo el enlace a Aplicaciones…"
ln -s /Applications "$MONTAJE/Aplicaciones"

echo "[info] creando el .dmg…"
rm -f "$DMG"
hdiutil create -volname "$NOMBRE $VERSION" -srcfolder "$MONTAJE" -ov -format UDZO "$DMG"

echo "[ok] instalador: $DMG ($(du -h "$DMG" | cut -f1))"
