#!/bin/bash
# https://www.linuxfromscratch.org/blfs/view/13.1-systemd/basicnet/libevent.html
set -e
set -o pipefail
export XORG_PREFIX=/usr
export XORG_CONFIG="--prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-static"
sed -i 's/python/&3/' event_rpcgen.py

./configure --prefix=/usr --disable-static &&
make

make install
