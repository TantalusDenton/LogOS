#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../build/lib/common.sh"
export LOGOS_CONTAINER LOGOS_IMAGE LOGOS_CPUS LOGOS_MEMORY LOGOS_DISPLAY LOGOS_SCREEN LOGOS_NETWORK LOGOS_STORAGE LOGOS_DISK_SIZE
exec python3 "$REPO/host/control.py" create "$@"
