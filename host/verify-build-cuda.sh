#!/bin/bash
source "$(dirname "$0")/../build/lib/common.sh"
# Export a temporary source-built rootfs into LXD to test the real NVIDIA integration.
name="logos-cuda-check-$$"
alias="logos/cuda-check-$$"
metadata=$(mktemp -d "$LOGOS_BUILD/work/cuda-meta.XXXXXX")
cleanup() {
 lxc delete "$name" --force >/dev/null 2>&1 || true
 lxc image delete "$alias" >/dev/null 2>&1 || true
 rm -rf "$metadata"
 rm -f "$LOGOS_BUILD/artifacts/cuda-check-rootfs.tar.xz" "$LOGOS_BUILD/artifacts/cuda-check-metadata.tar.xz"
}
trap cleanup EXIT
cp "$REPO/image/metadata.yaml" "$metadata/metadata.yaml"
tar -C "$metadata" -cJf "$LOGOS_BUILD/artifacts/cuda-check-metadata.tar.xz" metadata.yaml
"$REPO/build/package-rootfs.sh" --cuda-check
lxc image import "$LOGOS_BUILD/artifacts/cuda-check-metadata.tar.xz" "$LOGOS_BUILD/artifacts/cuda-check-rootfs.tar.xz" --alias "$alias"
export LOGOS_CONTAINER=$name LOGOS_IMAGE=$alias
# Honor the same configured pool/network/limits as the normal host wrappers.
export LOGOS_STORAGE LOGOS_NETWORK LOGOS_CPUS LOGOS_MEMORY LOGOS_DISPLAY LOGOS_SCREEN LOGOS_DISK_SIZE
python3 "$REPO/host/control.py" create
lxc start "$name"
lxc exec "$name" -- ldconfig
lxc exec "$name" -- nvidia-smi
lxc exec "$name" -- /usr/libexec/logos/cuda-test | tee "$LOGOS_BUILD/artifacts/cuda-compute.txt"
date -u +%FT%TZ > "$LOGOS_BUILD/state/cuda-compute.pass"
