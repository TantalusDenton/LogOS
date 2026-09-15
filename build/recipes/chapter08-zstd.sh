#!/bin/bash
# Extracted from https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/zstd.html
# Book commands: MIT license; see LICENSE.book-instructions.
set +h
umask 022
set -e
set -o pipefail
make prefix=/usr

make check

make prefix=/usr install

rm -v /usr/lib/libzstd.a
