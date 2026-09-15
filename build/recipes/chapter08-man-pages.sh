#!/bin/bash
# Extracted from https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/man-pages.html
# Book commands: MIT license; see LICENSE.book-instructions.
set +h
umask 022
set -e
set -o pipefail
rm -v man3/crypt*

make -R GIT=false prefix=/usr install
