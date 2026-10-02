#!/bin/bash
# Extracted from https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/systemd.html
# Book commands: MIT license; see LICENSE.book-instructions.
set +h
umask 022
set -e
set -o pipefail
sed -e 's/GROUP="render"/GROUP="video"/' \
    -e 's/GROUP="sgx", //'               \
    -i rules.d/50-udev-default.rules.in
patch -Np1 -i /logos-build/build/patches/systemd-userns-map-skip.patch

mkdir -p build
cd       build

meson setup ..                \
      --prefix=/usr           \
      --buildtype=release     \
      -D default-dnssec=no    \
      -D firstboot=false      \
      -D install-tests=false  \
      -D ldconfig=false       \
      -D sysusers=false       \
      -D rpmmacrosdir=no      \
      -D homed=disabled       \
      -D man=disabled         \
      -D mode=release         \
      -D pamconfdir=no        \
      -D dev-kvm-mode=0660    \
      -D nobody-group=nogroup \
      -D sysupdate=disabled   \
      -D ukify=disabled       \
      -D docdir=/usr/share/doc/systemd-261.2

ninja

echo 'NAME="Linux From Scratch"' > /etc/os-release
# The suite byte-compares UTF-8 table ellipses and measures help output in
# characters. Keep the LFS build locale, but run these Unicode-aware tests in
# the UTF-8 locale that systemd declares for its test environment. A one-UID
# user namespace lets Systemd skip the UID-1 mapping case unavailable in the
# unprivileged build container. The test patch accepts only that capability
# denial; all other test failures still stop the build.
LC_ALL=C.UTF-8 unshare -m ninja test

ninja install

tar -xf ../../systemd-man-pages-261.2.tar.xz \
    --no-same-owner --strip-components=1     \
    -C /usr/share/man

: > /etc/machine-id

systemctl preset-all
