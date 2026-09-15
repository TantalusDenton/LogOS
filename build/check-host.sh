#!/bin/bash
source "$(dirname "$0")/lib/common.sh"
status=0
check() { local label=$1; shift; if ( "$@" ); then printf '%-24s PASS\n' "$label"; else printf '%-24s FAIL\n' "$label"; status=1; fi; }
check 'x86_64' test "$(uname -m)" = x86_64
check 'Workspace capacity' space_check
for c in bash gcc g++ make bison gawk texi2any patch tar xz bzip2 gzip sed grep diff find perl python3 wget curl git chroot mount unshare readelf flock; do
 check "$c" command -v "$c"
done
check 'sh is Bash' bash -c 'test "$(readlink -f /bin/sh)" = "$(readlink -f /bin/bash)"'
check 'awk is GNU awk' bash -c 'awk --version 2>/dev/null | head -1 | grep -q "GNU Awk"'
check 'yacc is Bison' bash -c 'yacc --version 2>/dev/null | head -1 | grep -qi bison'
# Version requirements are checked by the exact LFS 13.1 script.
check 'LFS version requirements' bash "$REPO/build/host-version-check.sh"
if [[ ${1:-} != --build-only ]]; then
 check 'NVIDIA host runtime' nvidia-smi
 check 'LXD server' lxc version
 check 'Xephyr' command -v Xephyr
fi
exit "$status"
