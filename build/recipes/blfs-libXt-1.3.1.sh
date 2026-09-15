#!/bin/bash
# https://www.linuxfromscratch.org/blfs/view/13.1-systemd/x/x7lib.html
set -e
set -o pipefail
export XORG_PREFIX=/usr
export XORG_CONFIG="--prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-static"
./configure $XORG_CONFIG --with-appdefaultdir=/etc/X11/app-defaults

make

make check

make install
