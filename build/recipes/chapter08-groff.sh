#!/bin/bash
# Extracted from https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/groff.html
# Book commands: MIT license; see LICENSE.book-instructions.
set +h
umask 022
set -e
set -o pipefail
PAGE=A4 ./configure --prefix=/usr

make -j1

test_started=$(date +%s)
if ! make check; then
 python3 /logos-build/build/verify-groff-tests.py . "$test_started"
fi

make install
