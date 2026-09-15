#!/bin/bash
source "$(dirname "$0")/lib/common.sh"
need_root
space_check
source /etc/os-release
[[ $ID = ubuntu && $VERSION_ID = 24.04 ]] || fail 'Host bootstrap is for Ubuntu 24.04 only.'
# Inspect before installing anything. No NVIDIA or CUDA package is installed here.
nvidia-smi || true
command -v nvcc >/dev/null && nvcc --version || true
ldconfig -p | grep -i nvidia || true
apt-get update
apt-get install -y build-essential bison gawk texinfo wget curl tar xz-utils bzip2 gzip python3 git patch perl file diffutils findutils util-linux xserver-xephyr x11-utils
# These are required by the LFS host requirements (documented host changes).
ln -sf bash /bin/sh
update-alternatives --set awk /usr/bin/gawk
command -v lxc >/dev/null || snap install lxd --channel=5.21/stable
workspace
getent passwd logos-lfs >/dev/null || useradd --system --user-group --home-dir "$LOGOS_BUILD/lfs-home" --create-home --shell /bin/bash logos-lfs
"$REPO/build/check-host.sh" --build-only
