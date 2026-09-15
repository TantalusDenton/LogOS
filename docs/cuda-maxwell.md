# CUDA and Maxwell

Quadro M2000: compute capability 5.2, 4 GiB VRAM. CUDA 13 cannot compile Maxwell. Use pinned CUDA **12.9.1** redistribution components; `CMAKE_CUDA_ARCHITECTURES=52` emits Maxwell code. The upstream llama.cpp CUDA CMake file at the pinned commit explicitly includes Maxwell support for CUDA <13.

CUDA's GCC support range does not cover LFS 13.1 GCC 16. GCC 14.3.0 is built from upstream source inside LogOS for NVCC and llama.cpp; it does not replace `/usr/bin/gcc`. GCC 14/new-glibc/CUDA header interoperability remains untested; do not add `--allow-unsupported-compiler` or conceal errors if this combination fails.

The selected Qwen2.5-Coder-1.5B-Instruct Q4_K_M file is about 1.12 GB. Default context is 4096, parallelism 1, batch 128 and microbatch 64, with 99 GPU layers requested (all available layers). Actual fit and offload must be verified on this host, which shares GPU memory with the graphical desktop. If allocation fails, measure free VRAM, reduce context/batch or GPU_LAYERS, and repeat health; GPU_LAYERS=0 is rejected.

`cuda-test` verifies GPU name/compute capability, allocates CUDA memory, runs a 128-thread kernel, copies the results back and checks every value. Device nodes alone never pass. Health requires positive offloaded-layer counts and CUDA model buffers from the current systemd service invocation plus a successful structured inference response, and samples `nvidia-smi` during inference.

References: [NVIDIA CUDA 12.9 installation guide](https://docs.nvidia.com/cuda/archive/12.9.1/cuda-installation-guide-linux/index.html), [NVIDIA redistribution manifest](https://developer.download.nvidia.com/compute/cuda/redist/redistrib_12.9.1.json), [pinned llama.cpp CUDA CMake](https://github.com/ggml-org/llama.cpp/blob/38a5b42d9a3e82e0a586bcd1caed121f36c87a73/ggml/src/ggml-cuda/CMakeLists.txt).
