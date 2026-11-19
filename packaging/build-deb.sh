#!/bin/sh
# Run from the checkout root: sh packaging/build-deb.sh VERSION OUTPUT.deb
set -eu
umask 022
version=${1:?Supply a Debian package version}
output=${2:?Supply the output .deb path}
dpkg --validate-version "$version"
stage=$(mktemp -d)
trap 'rm -rf -- "$stage"' EXIT
chmod 755 "$stage"
modules="$stage/usr/lib/python3/dist-packages/xquasar"
mkdir -p "$stage/DEBIAN" "$modules"
install -m 644 xquasar/*.py "$modules/"
install -Dm755 packaging/xquasar "$stage/usr/bin/xquasar"
install -Dm644 packaging/xquasar.desktop "$stage/usr/share/applications/xquasar.desktop"
cat > "$stage/DEBIAN/control" <<EOF
Package: xquasar
Version: $version
Architecture: all
Maintainer: XQuasar project <217289399+glitchykid@users.noreply.github.com>
Depends: python3 (>= 3.12), python3-gi, gir1.2-gtk-3.0
Suggests: flatpak
Section: utils
Priority: optional
Homepage: https://github.com/glitchykid/xquasar
Description: Interactive Linux home folder cleaner
 Preview thumbnail and font caches and profiles left by uninstalled Flatpak
 apps, then confirm cleanup. Personal folders and recovery copies are kept.
EOF
dpkg-deb --root-owner-group --build "$stage" "$output"
