#!/bin/bash
source "$(dirname "$0")/lib/common.sh"
source "$REPO/build/lib/logging.sh"
need_root
resume=0; from=''; until='10-logos'; accept_changes=0
while (( $# )); do
 case $1 in
  --resume) resume=1; shift;;
  --from) from=${2:?stage required}; resume=1; shift 2;;
  --until) until=${2:?stage required}; shift 2;;
  --accept-input-changes) accept_changes=1; shift;;
  --inside-mount-namespace) shift;;
  *) fail "Unknown argument $1";;
 esac
done
stages=(01-toolchain 02-temporary-system 03-chroot-base 04-systemd 05-network 06-x11 07-terminal 08-cuda 09-llama-cpp 10-logos)
[[ " ${stages[*]} " == *" $until "* ]] || fail "Unknown --until $until"
[[ -z $from || " ${stages[*]} " == *" $from "* ]] || fail "Unknown --from $from"
if [[ ${LOGOS_MOUNT_NAMESPACE:-0} != 1 ]]; then
 args=(--until "$until"); ((resume)) && args+=(--resume); [[ -n $from ]] && args+=(--from "$from")
 ((accept_changes)) && args+=(--accept-input-changes)
 exec unshare --mount --propagation private env LOGOS_MOUNT_NAMESPACE=1 "$0" "${args[@]}"
fi
space_check "$RESERVE_GIB"
workspace
exec 9>"$LOGOS_BUILD/state/build.lock"
flock -n 9 || fail 'Another build owns this workspace'
prepare_worktree
log_to "build-$(date -u +%Y%m%dT%H%M%SZ)"
trap 'code=$?; python3 "$REPO/build/report.py" "$code"; exit "$code"' EXIT
if (( ! resume )) && compgen -G "$LOGOS_BUILD/state/*.done" >/dev/null; then fail 'Existing build; use --resume'; fi
if [[ ! -f $LOGOS_BUILD/state/01-toolchain.done ]]; then "$REPO/build/check-host.sh" --build-only; fi
# A separate private mount namespace guarantees mount cleanup on exit.
mkdir -p "$LFS"/{dev,proc,sys,run,sources,logos-build,tools}
# Desktop-mounted workspaces may be nodev/nosuid. LFS tests need normal Unix
# semantics. Change only this private namespace's rootfs mount, not the disk.
mount --bind "$LFS" "$LFS"
mount -o remount,bind,rw,suid,dev "$LFS"
# The workspace root can have been created by the invoking user before the
# chroot exists. Systemd's safe-path tests require the chroot's / boundary to
# be owned by root, like the rest of the installed tree.
chown root:root "$LFS"
mount --bind "$LOGOS_BUILD/tools" "$LFS/tools"
mount --bind "$REPO" "$LFS/logos-build"
mount -o remount,bind,ro "$LFS/logos-build"
mount --rbind /dev "$LFS/dev"; mount --make-rslave "$LFS/dev"
mount -t proc proc "$LFS/proc"
mount -t sysfs sysfs "$LFS/sys"
mount -t tmpfs tmpfs "$LFS/run"
# The chroot shares the host network, including its local DNS stub. Keep the
# build resolver in volatile /run; the booted container supplies its own.
mkdir -p "$LFS/run/systemd/resolve" "$LFS/etc"
cat /etc/resolv.conf > "$LFS/run/systemd/resolve/stub-resolv.conf"
if [[ ! -e $LFS/etc/resolv.conf && ! -L $LFS/etc/resolv.conf ]]; then
 ln -s /run/systemd/resolve/stub-resolv.conf "$LFS/etc/resolv.conf"
fi
if [[ -L $LFS/dev/shm ]]; then mkdir -p "$LFS/$(readlink /dev/shm)"; else mount -t tmpfs -o nosuid,nodev tmpfs "$LFS/dev/shm"; fi
fingerprint=$(cd "$REPO"; find build sources rootfs-overlay logos-ai/logos_ai -type f ! -name '*.pyc' -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)
# A reviewed runner/layout repair may resume only with unchanged completed inputs.
if [[ -f $LOGOS_BUILD/state/build.fingerprint ]]; then
 if [[ $(cat "$LOGOS_BUILD/state/build.fingerprint") != "$fingerprint" ]]; then
  ((accept_changes)) || fail 'Build inputs changed; review them and use --accept-input-changes for a safe repair, or a fresh workspace.'
  python3 "$REPO/build/check-resume.py" --accept
 fi
fi
python3 "$REPO/build/check-resume.py" --snapshot
printf '%s\n' "$fingerprint" > "$LOGOS_BUILD/state/build.fingerprint"
reached=0
for stage in "${stages[@]}"; do
 [[ -z $from || $stage = "$from" ]] && reached=1
 if (( ! reached )); then [[ -f $LOGOS_BUILD/state/$stage.done ]] || fail "Prerequisite $stage missing"; continue; fi
 if [[ -f $LOGOS_BUILD/state/$stage.done ]]; then
  echo "CACHED $stage"
 else
  space_check "$RESERVE_GIB"
  printf '%s\t%s\tSTART\n' "$(date -u +%FT%TZ)" "$stage" >> "$LOGOS_BUILD/state/history.tsv"
  bash "$REPO/build/stages/$stage.sh"
  printf '%s\n' "$fingerprint" > "$LOGOS_BUILD/state/$stage.done"
  printf '%s\t%s\tPASS\n' "$(date -u +%FT%TZ)" "$stage" >> "$LOGOS_BUILD/state/history.tsv"
 fi
 [[ $stage = "$until" ]] && break
done
if [[ $until = 10-logos ]]; then "$REPO/build/package-rootfs.sh"; fi
