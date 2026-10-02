#!/bin/bash
# Optional development helper: expose a deliberately authorized root tmux console.
# This is host tooling, never installed in the LogOS image.
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd -P)
console_dir="$REPO/.work/root-console"
socket="$console_dir/control.sock"
local_prefix="$REPO/.work/session/host-test-prefix"
if command -v tmux >/dev/null; then
 tmux_bin=$(command -v tmux)
elif [[ -x $local_prefix/bin/tmux ]]; then
 tmux_bin="$local_prefix/bin/tmux"
 export LD_LIBRARY_PATH="$local_prefix/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
else
 echo 'tmux is unavailable. This session has a source-built copy under .work/session/host-test-prefix.' >&2
 exit 1
fi
case ${1:-open} in
 close)
  "$tmux_bin" -S "$socket" kill-server
  echo 'LogOS root console closed; its command channel is gone.'
  exit;;
 status)
  exec "$tmux_bin" -S "$socket" list-sessions;;
 open) ;;
 *) echo 'Usage: root-console.sh [open|status|close]' >&2; exit 2;;
esac
if (( EUID != 0 )); then
 echo 'Run this helper from your existing root terminal to authorize a shared root console.' >&2
 exit 1
fi
console_user=${SUDO_USER:-$(stat -c '%U' "$REPO")}
[[ $console_user != root ]] || { echo 'Cannot determine the normal workspace owner' >&2; exit 1; }
console_group=$(id -gn "$console_user")
install -d -o "$console_user" -g "$console_group" -m 0700 "$console_dir"
# tmux leaves its UNIX socket behind when a server is killed unexpectedly.
# Verify that the socket has a live server before treating it as reusable.
if [[ -S $socket ]] && ! "$tmux_bin" -S "$socket" list-sessions >/dev/null 2>&1; then
 rm -f -- "$socket"
fi
if [[ ! -S $socket ]]; then
 "$tmux_bin" -f /dev/null -S "$socket" new-session -d -s logos-root -c "$REPO" \
   /usr/bin/env -u LD_LIBRARY_PATH HOME=/root HISTFILE=/dev/null /bin/bash --noprofile --norc
 "$tmux_bin" -S "$socket" set-option -g history-limit 10000
elif ! "$tmux_bin" -S "$socket" has-session -t logos-root 2>/dev/null; then
 "$tmux_bin" -S "$socket" new-session -d -s logos-root -c "$REPO" \
   /usr/bin/env -u LD_LIBRARY_PATH HOME=/root HISTFILE=/dev/null /bin/bash --noprofile --norc
fi
# Both UNIX-socket access and tmux's explicit per-user ACL are required.
"$tmux_bin" -S "$socket" server-access -w "$console_user"
chown root:"$console_group" "$socket"
chmod 0660 "$socket"
printf 'Root console ready. Authorized user: %s.\n' "$console_user"
echo 'Codex can now send root commands through this dedicated console.'
echo 'Close it with: ./host/root-console.sh close'
exec "$tmux_bin" -S "$socket" attach-session -t logos-root
