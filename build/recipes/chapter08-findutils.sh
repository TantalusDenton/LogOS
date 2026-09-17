#!/bin/bash
# Extracted from https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/findutils.html
# Book commands: MIT license; see LICENSE.book-instructions.
set +h
umask 022
set -e
set -o pipefail
./configure --prefix=/usr --localstatedir=/var/lib/locate

make

chown -R tester .
test_started=$(date +%s)
if ! su tester -c "PATH=$PATH make check -k"; then
 python3 /logos-build/build/verify-findutils-tests.py . "$test_started"
fi

make install
