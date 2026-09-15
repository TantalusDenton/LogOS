#!/bin/bash
# Extracted from https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/bc.html
# Book commands: MIT license; see LICENSE.book-instructions.
set +h
umask 022
set -e
set -o pipefail
CC='gcc -std=c99' ./configure --prefix=/usr -G -O3 -r

make

make test

make install
