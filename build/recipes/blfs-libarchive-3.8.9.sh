#!/bin/bash
# https://www.linuxfromscratch.org/blfs/view/13.1-systemd/general/libarchive.html
set -e
set -o pipefail
export XORG_PREFIX=/usr
export XORG_CONFIG="--prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-static"
./configure --prefix=/usr --disable-static &&
make

make install
