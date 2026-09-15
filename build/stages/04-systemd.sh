#!/bin/bash
source "$(dirname "$0")/../lib/common.sh"
source "$REPO/build/lib/package.sh"
cp -a "$REPO/rootfs-overlay/etc/." "$LFS/etc/"
in_root /bin/bash -e <<'INNER'
ln -sf ../lib/systemd/systemd /usr/sbin/init
ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
ln -sf /usr/share/zoneinfo/UTC /etc/localtime
: > /etc/machine-id
: > /etc/fstab
systemctl enable systemd-networkd systemd-resolved
systemctl set-default multi-user.target
# The host controls the wall clock, kernel modules and virtual consoles.
systemctl mask systemd-timesyncd.service systemd-modules-load.service getty@tty1.service
install -d /etc/systemd/journald.conf.d
printf '[Journal]\nStorage=volatile\nRuntimeMaxUse=64M\n' > /etc/systemd/journald.conf.d/logos.conf
INNER
