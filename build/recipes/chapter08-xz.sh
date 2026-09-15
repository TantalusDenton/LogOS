#!/bin/bash
# Extracted from https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/xz.html
# Book commands: MIT license; see LICENSE.book-instructions.
set +h
umask 022
set -e
set -o pipefail
./configure --prefix=/usr    \
            --disable-static \
            --docdir=/usr/share/doc/xz-5.8.3

make

make check

make install
