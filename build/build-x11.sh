#!/bin/bash
exec "$(dirname "$0")/build-logos.sh" --resume --until 06-x11 "$@"
