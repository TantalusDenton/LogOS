#!/bin/bash
# https://www.linuxfromscratch.org/blfs/view/13.1-systemd/x/xorgproto.html
set -e
set -o pipefail
export XORG_PREFIX=/usr
export XORG_CONFIG="--prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-static"
mkdir build &&
cd    build &&

meson setup --prefix=$XORG_PREFIX .. &&
ninja

ninja install &&
mv -v $XORG_PREFIX/share/doc/xorgproto{,-2025.1}
