#!/bin/bash
# https://www.linuxfromscratch.org/blfs/view/13.1-systemd/postlfs/make-ca.html
set -e
set -o pipefail
export XORG_PREFIX=/usr
export XORG_CONFIG="--prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-static"
sed '/mktemp/s/-t //' -i make-ca

make install &&
install -vdm755 /etc/ssl/local
