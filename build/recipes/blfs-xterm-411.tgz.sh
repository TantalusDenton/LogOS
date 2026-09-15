#!/bin/bash
# https://www.linuxfromscratch.org/blfs/view/13.1-systemd/x/xterm.html
set -e
set -o pipefail
export XORG_PREFIX=/usr
export XORG_CONFIG="--prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-static"
sed -i '/v0/{n;s/new:/new:kb=^?:/}' termcap &&
printf '\tkbs=\\177,\n' >> terminfo &&

TERMINFO=/usr/share/terminfo \
./configure $XORG_CONFIG     \
            --with-app-defaults=/etc/X11/app-defaults --disable-freetype &&

make

make install &&

mkdir -pv /usr/share/applications &&
cp -v *.desktop /usr/share/applications/
