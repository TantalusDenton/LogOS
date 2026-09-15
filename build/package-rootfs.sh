#!/bin/bash
source "$(dirname "$0")/lib/common.sh"
need_root
space_check "$RESERVE_GIB"
name=logos-rootfs
if [[ ${1:-} = --cuda-check ]]; then name=cuda-check-rootfs; else
 [[ -f $LOGOS_BUILD/state/10-logos.done ]] || fail 'Stage 10 is not complete; refusing to publish a final image'
 python3 "$REPO/build/validate-rootfs.py"
fi
mkdir -p "$LOGOS_BUILD/artifacts"
# Exclude mounts and build-only content. The build tree remains intact for diagnosis.
XZ_OPT='-T4 -3' tar --numeric-owner --xattrs --acls --one-file-system \
 --exclude='./dev/*' --exclude='./proc/*' --exclude='./sys/*' --exclude='./run/*' \
 --exclude='./sources' --exclude='./logos-build' --exclude='./tools' \
 --exclude='./tmp/*' --exclude='./var/tmp/*' --exclude='./var/cache/*' \
 --exclude='./var/log/*' --exclude='./root/.bash_history' \
 --exclude='./usr/lib/libbfd.a' --exclude='./usr/lib/libopcodes.a' \
 --exclude='./usr/lib/*.la' \
 -C "$LFS" -cJf "$LOGOS_BUILD/artifacts/$name.tar.xz.part" .
mv "$LOGOS_BUILD/artifacts/$name.tar.xz.part" "$LOGOS_BUILD/artifacts/$name.tar.xz"
if [[ $name = logos-rootfs ]]; then
 tar -C "$REPO/image" -cJf "$LOGOS_BUILD/artifacts/logos-metadata.tar.xz.part" metadata.yaml templates
 mv "$LOGOS_BUILD/artifacts/logos-metadata.tar.xz.part" "$LOGOS_BUILD/artifacts/logos-metadata.tar.xz"
 sha256sum "$LOGOS_BUILD/artifacts/"logos-*.tar.xz > "$LOGOS_BUILD/artifacts/image-checksums.txt"
fi
