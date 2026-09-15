#!/bin/bash
# Extracted from https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/acl.html
# Book commands: MIT license; see LICENSE.book-instructions.
set +h
umask 022
set -e
set -o pipefail
./configure --prefix=/usr    \
            --disable-static \
            --docdir=/usr/share/doc/acl-2.4.0

make

make check

make install
