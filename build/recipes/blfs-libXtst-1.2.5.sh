#!/bin/bash
# https://www.linuxfromscratch.org/blfs/view/13.1-systemd/x/x7lib.html
set -e
set -o pipefail
./configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-static
make
make check
make install
