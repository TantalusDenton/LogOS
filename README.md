# LogOS Developer Preview 0.1

LogOS is a Linux From Scratch **13.1 systemd** userspace that runs in an
**unprivileged LXD container**. Its main interface is an AI terminal: Bash and a
local assistant side by side in xterm/tmux. Inference uses llama.cpp, CUDA 12.9.1,
and the pinned Qwen2.5-Coder-1.5B-Instruct Q4_K_M model.

A complete image was built and run on the development machine on **September 20,
2026**. CUDA computation and inference with **29/29 layers offloaded** to a Quadro
M2000 were observed. The running container required the fixes documented in
[troubleshooting](docs/troubleshooting.md); these are not all baked into that
image. See [validation status](docs/validation.md) for evidence and limitations.

## Available features

- Source-built LFS/BLFS userspace, systemd, networking, Bash, Python, xterm and tmux.
- A persistent Bash pane (70%) and an AI pane (30%) in a host Xephyr window.
- Local command suggestions and explanations, with **Run, Insert, or Cancel** for
  each proposed command. High-risk Run also requires typing `RUN`.
- Explicit `Explain terminal` action shares at most the last 40 lines of the Bash
  pane with the local model; ordinary requests include system/working-directory
  context, not a continuous terminal recording.
- NVIDIA GPU access through LXD CDI or its NVIDIA runtime, and a real CUDA kernel
  diagnostic. Inference binds to container loopback, with no remote AI fallback.
- Pinned sources and model, verified downloads, resumable build stages, package
  manifests, ABI checks and runtime health checks.

This preview targets **Ubuntu 24.04 x86_64 and one Quadro M2000 (4 GiB VRAM)**.
The launcher explicitly checks that GPU. It is not a general GPU installer or a
bootable OS: no kernel image, bootloader, ISO, desktop environment, package
manager, or CPU-only inference mode is provided. AI suggestions can be wrong;
risk labels and health checks do not prove that a command is correct or safe.

## Requirements at a glance

| Resource | Requirement / default |
| --- | --- |
| Host | Ubuntu 24.04 x86_64; root/sudo for building; LXD access for runtime |
| GPU | Working host NVIDIA driver for the M2000; `nvidia-smi` must succeed |
| LXD | Initialized server with NVIDIA CDI or runtime support, a managed network and storage pool; LXD 6.9/CDI was exercised |
| Display | Local X11 desktop (or working Xwayland), Xephyr, valid `DISPLAY` and desktop authorization |
| Disk | At least 80 GiB initially free in the build workspace; 20 GiB build reserve; at least 16 GiB free in the selected LXD pool |
| CPU / RAM | Example build uses 8 jobs; runtime defaults to 8 CPUs and a 16 GiB memory limit; leave resources for the host and reduce jobs if needed |
| Downloads | Internet for pinned sources and the approximately 1.12 GB model; inference itself is local |

The disk checks are floors, not guaranteed peak-use estimates. LXD's image cache
can consume the host root filesystem even when the container uses another pool.
Read the [build guide](docs/building.md) before installing prerequisites.

## Build and start

From a checkout on a disk with enough capacity:

```bash
git clone https://github.com/TantalusDenton/LogOS.git
cd LogOS
cp config/logos.conf.example config/logos.conf
# Edit LOGOS_BUILD (absolute path), LOGOS_STORAGE and LOGOS_NETWORK first.
sudo ./build/bootstrap-host.sh
# Initialize LXD if this is a new installation; confirm the chosen pool/network.
make check
sudo ./build/build-logos.sh --resume
./host/create-container.sh
./host/start-logos.sh
```

Bootstrap installs dependencies, changes `/bin/sh` to Bash and selects GNU awk.
It can install LXD when absent but does not initialize its pools/network. It does
not install NVIDIA drivers or configure host boot. Start the runtime scripts as
your desktop user, with access to LXD. Startup imports no image by itself: run
`create-container.sh` first. Creation imports the built image if its alias is
absent; an existing alias or container is reused, not upgraded.

The last packaged preview may need the [first-start repairs](docs/troubleshooting.md)
for its console getty and inference logging before every health check can pass.

## Daily commands

```bash
make start       # Start container, display, terminal, model and AI checks
make status      # Container, GPU, inference service and display information
make health      # Runtime checks; nonzero means at least one check failed
make shell       # LogOS user shell through LXD
make stop        # Stop the container and managed Xephyr display
make test        # Local Python tests and shell syntax checks; no full OS build
```

Use `Ctrl+b`, then an arrow key to move between terminal panes. Ask the AI pane
`show me GPU usage`, review its suggestion, then choose Run, Insert, or Cancel.
See [using LogOS](docs/using.md) for controls, configuration, lifecycle and recovery.

## Documentation

- [Using LogOS](docs/using.md)
- [Requirements, compilation, resume and artifacts](docs/building.md)
- [Troubleshooting and first-start repairs](docs/troubleshooting.md)
- [Architecture](docs/architecture.md)
- [Validation evidence and known limitations](docs/validation.md)
- [CUDA and Maxwell](docs/cuda-maxwell.md)
- [GPU passthrough](docs/gpu-passthrough.md)
- [LFS/BLFS deviations](docs/lfs-deviations.md)
- [Source locks and provenance](sources/README.md)

The repository's MIT license does not replace the licenses of bundled or built
components. LFS book excerpts have [their own license](LICENSE.book-instructions);
CUDA components are proprietary, and the model/source manifests record their
respective licenses. Build artifacts and downloaded models are not Git content.
