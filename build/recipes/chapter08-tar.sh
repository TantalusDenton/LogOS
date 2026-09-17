#!/bin/bash
# Extracted from https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/tar.html
# Book commands: MIT license; see LICENSE.book-instructions.
set +h
umask 022
set -e
set -o pipefail
patch -Np1 -i ../tar-1.35-acl_fix-1.patch

FORCE_UNSAFE_CONFIGURE=1  \
./configure --prefix=/usr

make

test_started=$(date +%s)
if ! make check; then
 python3 /logos-build/build/verify-tar-tests.py . "$test_started"
fi

make install
make -C doc install-html docdir=/usr/share/doc/tar-1.35
