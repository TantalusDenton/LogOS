#!/bin/bash
source "$(dirname "$0")/lib/common.sh"
need_root
[[ ${1:-} = --work-only ]] || fail 'Usage: clean.sh --work-only (keeps rootfs, sources, state and artifacts)'
[[ -f $LOGOS_BUILD/.logos-workspace && $(cat "$LOGOS_BUILD/.logos-workspace") = "$LOGOS_BUILD" ]] || fail 'Not a marked LogOS workspace'
exec 9>"$LOGOS_BUILD/state/build.lock"
flock -n 9 || fail 'Build is active'
find "$LOGOS_BUILD/work" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
