# Troubleshooting

Commands below assume the default `logos-dev` container name. Replace it when
using another name. Start with `make status`, `lxc list` and `df -h /` plus the
build/pool filesystems. A failed launcher command may leave services running.

## First-start repairs for the September 2026 image

The recorded successful run needed three guest adjustments after import. The
archive does not yet include all of them; the repository launcher includes the
X11 mount correction.

### X11 hidden by the guest's /tmp mount

The launcher binds the host socket directory read-only at `/opt/logos-host-x11`
and creates `/tmp/.X11-unix` as a symlink after boot. This avoids the guest tmpfs
hiding a mount made directly under `/tmp`. Use the current `host/control.py`,
then rerun `make start` from the local desktop. Check:

```bash
lxc exec logos-dev -- ls -ld /tmp/.X11-unix /opt/logos-host-x11
lxc exec logos-dev -- env DISPLAY=:100 xdpyinfo
```

Confirm the host's `DISPLAY`/`XAUTHORITY`, the Xephyr process and socket, and
`~/.local/state/logos/xephyr.log` (or the configured XDG state directory). The
LogOS display may differ from the host desktop display. Xephyr disables TCP;
`-ac` permits other local users to connect to this developer display. The
launcher does not use `xhost +`.

### Degraded systemd: console-getty

```bash
lxc exec logos-dev -- systemctl --failed
lxc exec logos-dev -- journalctl -u console-getty.service -b --no-pager
```

The tested container's only failure was the unused console getty. If inspection
confirms that same cause and no console login is needed, apply the recorded
container-only repair:

```bash
lxc exec logos-dev -- systemctl mask --now console-getty.service
lxc exec logos-dev -- systemctl reset-failed console-getty.service
lxc exec logos-dev -- systemctl is-system-running
```

Do not mask arbitrary failed services. The launcher requires systemd `running`;
other failed units need their own diagnosis.

### GPU works but offload evidence is missing

The pinned llama.cpp default log level did not emit the layer/buffer evidence
required by health. The running development container uses `--verbose` in
`/usr/libexec/logos/server`. For the original image, add it idempotently inside
the guest and restart only the guest inference service:

```bash
lxc exec logos-dev -- python3 - <<'PY'
from pathlib import Path
p = Path('/usr/libexec/logos/server')
s = p.read_text()
if '"--verbose"' not in s:
    needle = '        "--no-warmup",'
    if s.count(needle) != 1:
        raise SystemExit('Unexpected server launcher; inspect it before editing')
    p.write_text(s.replace(needle, needle + '\n        "--verbose",'))
PY
lxc exec logos-dev -- systemctl restart logos-ai
lxc exec logos-dev -- journalctl -u logos-ai -b --no-pager -n 100
```

Verbose logs include detailed inference/prompt information. The image's guest
journal is volatile and bounded to 64 MiB. The repository health script also
recognizes more proposal patterns than the original archive. To use that version:

```bash
lxc file push rootfs-overlay/usr/libexec/logos/health logos-dev/usr/libexec/logos/health
lxc exec logos-dev -- chown root:root /usr/libexec/logos/health
lxc exec logos-dev -- chmod 0755 /usr/libexec/logos/health
make health
```

These are runtime repairs; they do not rewrite the original image or its hashes.
See [validation](validation.md) for remaining test limitations. Never mark GPU
success solely because the device node exists or a command was proposed.

## Host NVIDIA errors

`nvidia-smi` must work before creation/start. Inspect
`/proc/driver/nvidia/version`, installed driver libraries and `ldconfig -p` if it
reports an NVML driver/library mismatch. A mismatch was an earlier development
blocker; it was no longer present at the successful September run. Reconcile a
host driver problem through normal host administration. LogOS scripts do not
replace drivers, install a guest kernel module or reboot the host.

Inside the guest, diagnose in order:

```bash
lxc exec logos-dev -- nvidia-smi
lxc exec logos-dev -- /usr/libexec/logos/cuda-test
lxc exec logos-dev -- journalctl -u logos-ai -b --no-pager -n 100
```

If VRAM is exhausted, inspect desktop/GPU usage and reduce `CONTEXT_SIZE` or the
positive `GPU_LAYERS` setting in the guest config. Repeat health. CUDA 12.9.1 and
architecture 52 are pinned for this preview; do not substitute CUDA 13.

## Disk space or memory pressure

Set `LOGOS_BUILD` to a spacious filesystem **before** a new build. Editing the
path does not move an existing workspace. Watch the build disk, LXD pool and
host root: the LXD image cache can use root even with a separate container pool.
The development host root remains close to capacity; do not assume free space
on the build disk solves that. See [build cleanup](building.md#reclaiming-build-space)
for the scoped cleanup command. Do not remove state markers or unrelated host
files to get around disk checks.

Lower `JOBS` for a new/resumed build if compiler processes exhaust memory. Review
build fingerprint changes when changing configuration; do not bypass resume
checks blindly. Compilation/test runs can take hours with little terminal output;
inspect the current log and processes before starting another build.

## Build/test failure and resume

Inspect `$LOGOS_BUILD/logs/build-*.log`, `logs/tests` and `state/history.tsv`.
Preserve the original error. After an ordinary interruption use
`sudo ./build/build-logos.sh --resume`. Changed inputs are rejected by default.
Only after reviewing a compatible repair use `--resume --accept-input-changes`;
completed recipes/overlays require a fresh workspace when the audit rejects
changes. Do not mark stages complete manually or treat skipped suites as passed.

A `libcuda.so.1` error inside the offline build chroot differs from the same
error in a running GPU-enabled container. The former is expected before LXD
injects the host driver; the latter requires injection/linker diagnosis.

## No server on root-console/control.sock

The optional root-console helper needs a live, explicitly authorized root tmux
server. Run `sudo ./host/root-console.sh open` in a real terminal (or run the
helper from an existing root shell), then check `./host/root-console.sh status`.
The helper handles stale sockets. Close with `./host/root-console.sh close` when
finished. It grants root command access to the workspace owner; it is not needed
when builds already have normal sudo access. See [building](building.md).

## Slow import or stale image

Materializing the CUDA image on btrfs took several minutes in the verified run;
creation allows 900 seconds. If a client times out, inspect `lxc operation list`
and `lxc list` before retrying. A server-side operation can continue after the
client exits. An existing `logos-dev` or `logos/0.1` is reused; changing build
artifacts does not update it. Use a separate container name/image alias to test
another build while preserving existing home data.

## AI or terminal unavailable

Bash remains usable while the model loads or the AI service restarts. Check
`journalctl -u logos-ai`, model checksum and guest configuration. Downloads do
not cause a remote-inference fallback. If the AI pane exited, rerun `logos-ai
--interactive` from that pane when possible, or recreate the dedicated tmux
session after saving shell work. `make start` restarts the terminal window but
reuses an existing tmux session, including exited panes.

A busy Bash pane rejects command delivery: return it to a prompt. Insert does
not clear existing input or press Enter; Run cancels partial input first. Treat
an incorrect suggestion as a model limitation, cancel it, and use Bash directly.
