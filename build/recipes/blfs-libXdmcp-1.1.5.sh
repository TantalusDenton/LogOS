#!/bin/bash
# https://www.linuxfromscratch.org/blfs/view/13.1-systemd/x/libXdmcp.html
set -e
set -o pipefail
export XORG_PREFIX=/usr
export XORG_CONFIG="--prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-static"
./configure $XORG_CONFIG --docdir='${datadir}'/doc/libXdmcp-1.1.5 &&
make

make install
