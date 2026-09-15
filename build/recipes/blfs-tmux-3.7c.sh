#!/bin/bash
# https://github.com/tmux/tmux/releases/tag/3.7c
set -e
set -o pipefail
export XORG_PREFIX=/usr
export XORG_CONFIG="--prefix=/usr --sysconfdir=/etc --localstatedir=/var --disable-static"
./configure --prefix=/usr

make

make install
