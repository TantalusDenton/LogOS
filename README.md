# LogOS Developer Preview 0.1

Independent LFS **13.1 systemd** userspace for an **unprivileged LXD system container**. No kernel, bootloader, initramfs or ISO. The only application is an xterm + tmux AI Terminal using a local Qwen2.5-Coder 1.5B Q4_K_M model and CUDA llama.cpp.

**Status: implemented build/runtime repository; not a completed or GPU-verified distribution.** Read [the actual validation report](docs/validation.md). Do not treat generated scripts as proof that a complete rootfs has compiled or booted.

## Build and run

Choose a filesystem with at least 80 GiB free, retaining a 20 GiB reserve. On the inspected server `/srv` is on a nearly full filesystem; set `LOGOS_BUILD` on the larger workspace disk.

```bash
cp config/logos.conf.example config/logos.conf
# Edit LOGOS_BUILD and LOGOS_STORAGE for this machine.
sudo ./build/bootstrap-host.sh
sudo ./build/build-logos.sh --resume
./host/create-container.sh
./host/start-logos.sh
```

Container creation imports the generated image automatically when its alias is absent.

Host bootstrap installs build tools and Xephyr, sets `/bin/sh` to Bash and the awk alternative to GNU awk as LFS requires. It never installs or replaces NVIDIA drivers. LXD must have a configured storage pool and managed network. Container startup checks the host GPU first and fails if NVIDIA libraries do not match the loaded kernel module.

`make test` runs local software tests. `make check` inspects build/host prerequisites. `make health` performs real container, X11, CUDA computation, inference and offload checks; it returns nonzero on any failed requirement.

The terminal has a normal Bash pane (70%) and an AI pane (30%). Each AI command requires Run, Insert, or Cancel. Insert never sends Enter; Run clears a partially typed Bash line before sending the approved command. High risk execution additionally requires `RUN`. Risk labels are conservative heuristics, not a shell sandbox. `Explain terminal` alone captures recent terminal output. No continuous recording, telemetry, or remote inference.

[Build guide](docs/building.md) · [Architecture](docs/architecture.md) · [LFS deviations](docs/lfs-deviations.md) · [CUDA/Maxwell](docs/cuda-maxwell.md) · [GPU passthrough](docs/gpu-passthrough.md) · [Troubleshooting](docs/troubleshooting.md)
