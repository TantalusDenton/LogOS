#!/bin/bash
# Extracted from https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/automake.html
# Book commands: MIT license; see LICENSE.book-instructions.
set +h
umask 022
set -e
set -o pipefail
./configure --prefix=/usr --docdir=/usr/share/doc/automake-1.18.1

make

make -j$(($(nproc)>4?$(nproc):4)) check

make install
