#!/bin/bash
# Extracted from https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/openssl.html
# Book commands: MIT license; see LICENSE.book-instructions.
set +h
umask 022
set -e
set -o pipefail
./config --prefix=/usr         \
         --openssldir=/etc/ssl \
         --libdir=lib          \
         shared                \
         zlib-dynamic

make

make test

make INSTALL_LIBS= MANSUFFIX=ssl install

mv -v /usr/share/doc/openssl /usr/share/doc/openssl-4.0.1

cp -vfr doc/* /usr/share/doc/openssl-4.0.1
