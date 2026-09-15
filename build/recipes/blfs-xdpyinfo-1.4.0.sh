#!/bin/bash
# https://www.linuxfromscratch.org/blfs/view/13.1-systemd/x/x7app.html
set -e
set -o pipefail
export XORG_PREFIX=/usr
export XORG_CONFIG="--prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-static"
./configure $XORG_CONFIG

make

make install
