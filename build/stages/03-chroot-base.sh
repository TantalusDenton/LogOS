#!/bin/bash
source "$(dirname "$0")/../lib/common.sh"
source "$REPO/build/lib/package.sh"
chown -R root:root "$LFS"/{usr,etc,var,lib64} "$LOGOS_BUILD"/{tools,work}
run_packages 03-chroot-base
