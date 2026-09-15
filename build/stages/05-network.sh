#!/bin/bash
source "$(dirname "$0")/../lib/common.sh"
source "$REPO/build/lib/package.sh"
python3 "$REPO/build/fetch.py" --group blfs
run_packages 05-network
# make-ca uses a pinned upstream Mozilla certificate input, not Ubuntu certificates.
in_root /usr/sbin/make-ca -f -C /sources/certdata.txt
