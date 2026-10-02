# Using LogOS

## Start an existing installation

Run these from the repository as the local desktop user who has LXD access:

```bash
./host/start-logos.sh
./host/status.sh
```

For a new installation, first follow [building](building.md) and run
`./host/create-container.sh`. The default container is `logos-dev`, image alias
`logos/0.1`, display `:100`, and window size `1600x900`. Set these in the host's
`config/logos.conf`. That file is trusted shell configuration and is ignored by
Git; its assignments override environment values when the wrappers source it.

Startup checks the host GPU, starts the unprivileged container and Xephyr, checks
systemd/network/CUDA, opens the terminal, installs or verifies the pinned model,
starts inference and runs health checks. The model can take time to download and
load. A failed health check can leave the container and window running: inspect
the failure rather than assuming startup rolled everything back.

## Terminal controls

The left pane is a regular Bash shell; the right pane has the `AI>` prompt.
Use tmux's default prefix `Ctrl+b`, release it, then press an arrow key to switch
panes. `Ctrl+b`, then `o` cycles panes. There is no desktop or window manager
inside LogOS; the window is displayed by the host's Xephyr.

Try `show me GPU usage` or ask for an explanation of a Linux command. Each
suggestion shows the command, description and risk label:

| Choice | Effect |
| --- | --- |
| `r` (Run) | Clears a partially typed Bash line and executes the approved command; high-risk commands additionally require exact `RUN` |
| `i` (Insert) | Inserts literal command text into Bash without Enter; review/edit the line yourself |
| `c` (Cancel), or another response | Sends nothing to Bash |

Return Bash to a prompt before approving a suggestion. If a foreground program
is running, command delivery is refused. `/quit` or `/exit` leaves the AI frontend;
Bash remains available. `Ctrl+c` cancels the current frontend interaction.
AI pane failure does not shut down Bash.

Type **`Explain terminal`** at `AI>` to include up to the last 40 lines of Bash
output (also bounded to 16 KiB). Normal requests include context such as username,
hostname, working directory, architecture, memory and GPU. Terminal output is
included only by that explicit action. Inference is local at
`127.0.0.1:8080` inside the container; there is no OpenAI key or cloud service to
configure. Downloading sources/models still needs Internet access.

Generated commands are proposals, not executed results. A small model can give an
incorrect pipeline or a misleading explanation. Read commands before approving;
risk classification is a heuristic, not a shell sandbox. The health check's
proposal tests check response structure and command patterns, not general shell
correctness.

## Shell access and lifecycle

```bash
make shell                         # Login shell as logos
lxc exec logos-dev -- /bin/bash     # Container root shell for administration
make status
make health
make stop
make start
```

Replace `logos-dev` in direct `lxc` commands if configured differently. LXD exec
does not need a guest password; account passwords are locked. Stopping retains
the container filesystem and home directory. Starting again restores the
interface, although processes/tmux state do not survive a container stop.
Changing host CPU/memory defaults does not resize an existing container; inspect
its configuration with `lxc config show logos-dev` before making resource changes.

`./host/destroy-container.sh --yes` permanently deletes the managed container and
its files. It is not needed for ordinary shutdown. Back up home/model data before
deletion or replacing an instance. There is no in-place image upgrade command:
`create-container.sh` reuses existing containers and image aliases.

## Model and inference settings

Inside the guest, `/etc/logos/logos.conf` contains:

| Setting | Default | Meaning |
| --- | --- | --- |
| `MODEL` | `/var/lib/logos/models/default.gguf` | Model file read by llama-server |
| `LLAMA_HOST` | `127.0.0.1` | Only loopback is accepted |
| `LLAMA_PORT` | `8080` | Local port; allowed range 1024–65535 |
| `CONTEXT_SIZE` | `4096` | Context tokens; allowed range 512–8192 |
| `GPU_LAYERS` | `99` | Requested GPU layer count; positive integer or `auto`; zero is rejected |
| `TEMPERATURE` | `0.2` | Client sampling temperature; allowed range 0–2 |

The supported model is pinned in `sources/model.json`. On the host,
`./build/download-model.sh` optionally caches it under `$LOGOS_BUILD/models`.
Startup checks the cache's SHA-256 before transfer, and `logos-model install-default`
verifies the guest copy. Without the cache the guest downloads it. Existing guest
files are verified rather than silently overwritten.

After editing inference settings as container root:

```bash
lxc exec logos-dev -- systemctl restart logos-ai
lxc exec logos-dev -- journalctl -u logos-ai -b --no-pager -n 80
make health
```

Restart the AI frontend to reload its client settings, for example by running
`make start` when it is safe to restart the terminal window. The daemon uses one
slot, batch size 128 and microbatch 64. Those are currently fixed in
`/usr/libexec/logos/server`, not exposed as configuration keys. Other models,
GPUs and context sizes need separate validation; all-layer fit is not guaranteed
when the host desktop also uses VRAM.

## Data locations

| Location | Purpose |
| --- | --- |
| Host `config/logos.conf` | Build and launcher configuration |
| Host `$LOGOS_BUILD` | Source cache, build root, logs, state, artifacts and optional model cache |
| Host `$XDG_STATE_HOME/logos` (normally `~/.local/state/logos`) | Managed Xephyr PID and log |
| Guest `/home/logos` | User files and normal shell environment |
| Guest `/var/lib/logos/models` | Verified model file |
| Guest `/etc/logos/logos.conf` | Inference settings |
| Guest systemd journal | Service diagnostics; volatile, limited to 64 MiB by the image configuration |

There is no package manager, SSH service setup, host-home sharing, or automated
OS upgrade mechanism supplied by this preview. Use LXD shell/file operations and
source builds where needed. See [troubleshooting](troubleshooting.md) for startup
and GPU diagnostics.
