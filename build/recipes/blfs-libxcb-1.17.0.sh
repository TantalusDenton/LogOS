#!/bin/bash
# https://www.linuxfromscratch.org/blfs/view/13.1-systemd/x/libxcb.html
set -e
set -o pipefail
export XORG_PREFIX=/usr
export XORG_CONFIG="--prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-static"
./configure $XORG_CONFIG      \
            --without-doxygen \
            --docdir='${datadir}'/doc/libxcb-1.17.0 &&
LC_ALL=en_US.UTF-8 make

make install

chown -Rv root:root $XORG_PREFIX/share/doc/libxcb-1.17.0
