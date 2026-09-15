#!/bin/bash
exec "$(dirname "$0")/build-logos.sh" --resume --until 10-logos "$@"
