#!/bin/bash
set -Eeuo pipefail
REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
if [[ -f $REPO/config/logos.conf ]]; then source "$REPO/config/logos.conf"; fi
: "${LOGOS_BUILD:=/srv/logos}"
: "${JOBS:=8}"
: "${MIN_FREE_GIB:=80}"
: "${RESERVE_GIB:=20}"
[[ $LOGOS_BUILD = /* && $LOGOS_BUILD != / && $LOGOS_BUILD != /usr && $LOGOS_BUILD != /home && $LOGOS_BUILD != *[[:space:]]* ]] || { echo 'Unsafe LOGOS_BUILD path' >&2; exit 2; }
LOGOS_BUILD=$(realpath -m "$LOGOS_BUILD")
export LOGOS_BUILD LFS="$LOGOS_BUILD/rootfs" JOBS RESERVE_GIB
export PATH=/usr/bin:/usr/sbin:/bin:/sbin:/snap/bin
export LC_ALL=C.UTF-8
fail() { echo "ERROR: $*" >&2; exit 1; }
need_root() { (( EUID == 0 )) || fail 'This operation requires root (sudo).'; }
space_check() {
 local target=$LOGOS_BUILD avail need=${1:-$MIN_FREE_GIB}
 while [[ ! -e $target ]]; do target=$(dirname "$target"); done
 avail=$(df -B1 --output=avail "$target" | tail -1)
 (( avail >= need * 1024 * 1024 * 1024 )) || fail "$target has less than ${need} GiB free; choose LOGOS_BUILD on another filesystem."
}
workspace() {
 mkdir -p "$LOGOS_BUILD"/{rootfs,sources,tools,logs,artifacts,state}
 [[ ! -L $LFS && $LFS != / ]] || fail 'Rootfs must be a real directory.'
 if [[ -e $LOGOS_BUILD/.logos-workspace ]]; then
  [[ $(cat "$LOGOS_BUILD/.logos-workspace") == "$LOGOS_BUILD" ]] || fail 'Workspace identity mismatch'
 else
  [[ -z $(ls -A "$LFS") ]] || fail 'Refusing to adopt a populated rootfs'
  printf '%s\n' "$LOGOS_BUILD" > "$LOGOS_BUILD/.logos-workspace"
 fi
}
prepare_worktree() {
 # Call only while holding the build lock.
 # Keep the build tree at the book's physical /sources path. A same-filesystem
 # bind mount breaks the temporary Bash getcwd fallback (readdir inode mismatch).
 # The download cache remains separate at LOGOS_BUILD/sources.
 if [[ -d $LOGOS_BUILD/work && ! -L $LOGOS_BUILD/work ]]; then
  [[ ! -d $LFS/sources || -z $(ls -A "$LFS/sources") ]] || fail 'Cannot migrate two populated source work directories'
  mountpoint -q "$LFS/sources" && fail 'Cannot migrate a mounted source work directory'
  [[ ! -d $LFS/sources ]] || rmdir "$LFS/sources"
  mv "$LOGOS_BUILD/work" "$LFS/sources"
 fi
 mkdir -p "$LFS/sources"
 if [[ -L $LOGOS_BUILD/work ]]; then
  [[ $(realpath "$LOGOS_BUILD/work") == "$LFS/sources" ]] || fail 'Unexpected work symlink'
 else
  ln -s rootfs/sources "$LOGOS_BUILD/work"
 fi
}
