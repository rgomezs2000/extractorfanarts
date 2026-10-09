#!/bin/sh
# Instalador típico de Linux: un paquete .deb (Debian, Ubuntu, Mint, Pop!_OS…).
#
# Lo llama el flujo de compilación en Linux:
#     sh scripts/instaladores/crear_instalador_linux.sh <version> <dist> <salida>
#
# Deja el programa en /opt/imaginteca, un lanzador en /usr/bin/imaginteca, el icono
# y una entrada de menú. Se instala con:
#     sudo apt install ./Imaginteca-<versión>-linux-installer.deb
#     sudo dpkg -i  ./Imaginteca-<versión>-linux-installer.deb
#
# La versión portátil (.zip / .tar.gz) sigue existiendo para cualquier distribución.
set -e

VERSION="${1:?falta la versión}"
DIST="${2:?falta la carpeta del paquete}"
SALIDA="${3:?falta la carpeta de salida}"
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"

NOMBRE="Imaginteca"
# Debian no admite «-» como parte de la versión: las pre-versiones se escriben con «~».
VERSION_DEB="$(printf '%s' "$VERSION" | sed 's/-/~/')"
PAQUETE="imaginteca_${VERSION_DEB}_amd64"
DEB="$SALIDA/$NOMBRE-$VERSION-linux-installer.deb"

mkdir -p "$SALIDA"
rm -rf "$PAQUETE"
mkdir -p "$PAQUETE/DEBIAN" \
         "$PAQUETE/opt/imaginteca" \
         "$PAQUETE/usr/bin" \
         "$PAQUETE/usr/share/applications" \
         "$PAQUETE/usr/share/icons/hicolor/256x256/apps" \
         "$PAQUETE/usr/share/doc/imaginteca"

echo "[info] copiando el programa a /opt/imaginteca…"
cp -a "$DIST"/. "$PAQUETE/opt/imaginteca/"
cp -a "$RAIZ/LICENSE" "$RAIZ/LEEME-PRIMERO.txt" "$RAIZ/THIRD-PARTY-NOTICES.txt" \
      "$PAQUETE/usr/share/doc/imaginteca/" 2>/dev/null || true
[ -f "$RAIZ/assets/icon_256.png" ] && \
  cp -a "$RAIZ/assets/icon_256.png" "$PAQUETE/usr/share/icons/hicolor/256x256/apps/imaginteca.png"

cat > "$PAQUETE/usr/bin/imaginteca" <<'LANZADOR'
#!/bin/sh
exec /opt/imaginteca/Imaginteca "$@"
LANZADOR
chmod +x "$PAQUETE/usr/bin/imaginteca"

cat > "$PAQUETE/usr/share/applications/imaginteca.desktop" <<ESCRITORIO
[Desktop Entry]
Type=Application
Name=$NOMBRE
Comment=Tu colección de imágenes y datasets para IA
Exec=/opt/imaginteca/Imaginteca
Icon=imaginteca
Terminal=false
Categories=Graphics;2DGraphics;
StartupWMClass=$NOMBRE
ESCRITORIO

cat > "$PAQUETE/DEBIAN/control" <<CONTROL
Package: imaginteca
Version: $VERSION_DEB
Section: graphics
Priority: optional
Architecture: amd64
Maintainer: $(printf '%s' "InfoArte")
Installed-Size: $(du -sk "$PAQUETE" | cut -f1)
Description: Imaginteca - tu coleccion de imagenes y datasets para IA
 Aplicacion de escritorio para reunir, ordenar y preparar una coleccion personal
 de imagenes: busca en redes sociales, booros y wikis, guarda en WebP y prepara
 datasets para entrenar modelos.
CONTROL

cat > "$PAQUETE/DEBIAN/postinst" <<'POSTINST'
#!/bin/sh
set -e
# Refresca las bases de datos del escritorio para que aparezca el icono.
command -v update-desktop-database >/dev/null 2>&1 && \
  update-desktop-database -q /usr/share/applications || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
  gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
exit 0
POSTINST
chmod 755 "$PAQUETE/DEBIAN/postinst"

cat > "$PAQUETE/DEBIAN/postrm" <<'POSTRM'
#!/bin/sh
set -e
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
  rm -rf /opt/imaginteca
fi
exit 0
POSTRM
chmod 755 "$PAQUETE/DEBIAN/postrm"

echo "[info] construyendo el .deb…"
dpkg-deb --build --root-owner-group "$PAQUETE" "$DEB"
rm -rf "$PAQUETE"

echo "[ok] instalador: $DEB ($(du -h "$DEB" | cut -f1))"
