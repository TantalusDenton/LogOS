#!/bin/bash
source "$(dirname "$0")/lib/common.sh"
source "$REPO/build/lib/logging.sh"
space_check
workspace
exec 8>"$LOGOS_BUILD/state/sources.lock"
flock 8
log_to sources
python3 "$REPO/build/fetch.py" "$@"
