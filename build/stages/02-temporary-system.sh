#!/bin/bash
source "$(dirname "$0")/../lib/common.sh"
source "$REPO/build/lib/package.sh"
run_packages 02-temporary-system
