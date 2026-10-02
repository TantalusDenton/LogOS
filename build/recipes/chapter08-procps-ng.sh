#!/bin/bash
# Extracted from https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/procps-ng.html
# Book commands: MIT license; see LICENSE.book-instructions.
set +h
umask 022
set -e
set -o pipefail
./configure --prefix=/usr                           \
            --docdir=/usr/share/doc/procps-ng-4.0.7 \
            --disable-static                        \
            --disable-kill                          \
            --enable-watch8bit                      \
            --with-systemd

make

chown -R tester .
# DejaGNU determines the terminal name before spawning background test
# processes. Give the tester a dedicated controlling PTY so pgrep's tty
# selector checks the same terminal the processes inherit.
su tester -c "PATH=$PATH script -q -e -c 'make check' /dev/null"

make install
