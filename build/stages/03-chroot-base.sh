#!/bin/bash
source "$(dirname "$0")/../lib/common.sh"
source "$REPO/build/lib/package.sh"
chown -R root:root "$LFS"/{usr,etc,var,lib64,sources} "$LOGOS_BUILD/tools"
run_packages 03-chroot-base
