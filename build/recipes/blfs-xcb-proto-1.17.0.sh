#!/bin/bash
# https://www.linuxfromscratch.org/blfs/view/13.1-systemd/x/xcb-proto.html
set -e
set -o pipefail
export XORG_PREFIX=/usr
export XORG_CONFIG="--prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-static"
PYTHON=python3 ./configure $XORG_CONFIG

make install

rm -f $XORG_PREFIX/lib/pkgconfig/xcb-proto.pc
