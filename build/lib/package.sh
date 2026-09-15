#!/bin/bash
run_packages() { python3 "$REPO/build/run-packages.py" "$1"; }
in_root() { chroot "$LFS" /usr/bin/env -i HOME=/root TERM=xterm PATH=/usr/bin:/usr/sbin LC_ALL=POSIX MAKEFLAGS="-j$JOBS" "$@"; }
