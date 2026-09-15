#!/bin/bash
# Extracted from https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/libxcrypt.html
# Book commands: MIT license; see LICENSE.book-instructions.
set +h
umask 022
set -e
set -o pipefail
sed -i '/strchr/s/const//' lib/crypt-{sm3,gost}-yescrypt.c

./configure --prefix=/usr                \
            --enable-hashes=strong,glibc \
            --enable-obsolete-api=no     \
            --disable-static             \
            --disable-failure-tokens

make

make check

make install

make distclean
./configure --prefix=/usr                \
            --enable-hashes=strong,glibc \
            --enable-obsolete-api=glibc  \
            --disable-static             \
            --disable-failure-tokens
make
cp -av --remove-destination .libs/libcrypt.so.1* /usr/lib
