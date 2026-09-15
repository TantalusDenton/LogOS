#!/bin/bash
source "$(dirname "$0")/../lib/common.sh"
source "$REPO/build/lib/package.sh"
getent passwd logos-lfs >/dev/null || fail 'Run bootstrap-host.sh to create the build user'
python3 "$REPO/build/fetch.py" --group lfs
mkdir -p "$LFS"/{etc,var,usr/{bin,lib,sbin},lib64}
for i in bin lib sbin; do [[ -e $LFS/$i ]] || ln -s "usr/$i" "$LFS/$i"; done
chown logos-lfs:logos-lfs "$LFS"/{usr,etc,var,lib64} "$LOGOS_BUILD"/{tools,work}
chown -R logos-lfs:logos-lfs "$LFS/usr"
run_packages 01-toolchain
