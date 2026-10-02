# NVIDIA passthrough

The host must pass `nvidia-smi` before any LogOS container is created or started. `host/control.py` detects the M2000 index and PCI address and queries the LXD API extension list.

For `gpu_cdi`, use a physical GPU device with `id=nvidia.com/gpu=<detected index>`. CDI injects matching NVIDIA driver userspace/device configuration. For older versions advertising `nvidia_runtime`, use a PCI-selected physical GPU plus `nvidia.runtime=true`, `nvidia.driver.capabilities=compute,utility`. If neither is supported, fail. Never set `security.privileged=true`.

The guest video group is GID 12 (LFS), with device mode 0660. Both logos and logos-ai join video. There is no `PrivateDevices=true` restriction on the CUDA service. The container runs its own glibc/ldconfig. No hand-picked Ubuntu general-purpose library tree is copied.

LXD 6.9 on the inspected server advertises both `gpu_cdi` and `nvidia_runtime`; CDI is selected. The September 20, 2026 run verified NVIDIA access, a real CUDA kernel and llama.cpp inference with 29/29 layers offloaded on the M2000. This is evidence for that host configuration, not all LXD/driver versions. Check inside with `nvidia-smi`, then `/usr/libexec/logos/cuda-test`, then `make health`. An injection/linker failure must be diagnosed, never replaced with CPU inference.

[Canonical LXD GPU device documentation](https://canonical.com/lxd/docs/latest/reference/devices_gpu/) documents physical/CDI device syntax and supported properties.
