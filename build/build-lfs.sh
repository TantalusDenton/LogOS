#!/bin/bash
exec "$(dirname "$0")/build-logos.sh" --resume --until 04-systemd "$@"
