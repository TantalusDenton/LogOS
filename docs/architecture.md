# Architecture

Ubuntu provides only the host kernel, build tools, LXD, Xephyr and NVIDIA kernel driver. LogOS builds its glibc, GCC runtime, binutils, Bash, Python, systemd, core utilities, X libraries, xterm and tmux from the stable LFS/BLFS sources. Linux sources supply API headers only. The image contains no Ubuntu package database or copied Ubuntu base userspace.

Xephyr is a host X server on `:100`, with TCP disabled. LXD binds the host's `/tmp/.X11-unix` read-only at guest `/opt/logos-host-x11`; after boot the launcher links `/tmp/.X11-unix` there so the guest tmpfs cannot hide the socket mount. Xterm uses Xephyr's core `9x15` font and a dedicated tmux socket (`-L logos`); no X server, window manager or desktop is installed inside the container. Xlib/Xt/Xaw provide client font support. This small first preview does not need FreeType/fontconfig or a separate font collection.

LXD's detected NVIDIA CDI support is preferred; older LXD with `nvidia_runtime` uses the runtime injection mechanism and a PCI-selected GPU device. Only NVIDIA driver integration may originate on the host. CUDA toolkit 12.9.1 components come directly from NVIDIA; proprietary CUDA binaries are an explicit exception to the source-built free userspace. There is no guest kernel driver.

`logos-ai.service` runs llama-server as `logos-ai`, with read-only system/model files, video group access and loopback binding. It first runs a real CUDA computation test. The `logos` user owns the normal shell and AI frontend. A stopped AI pane cannot take down Bash.

The Python client uses standard-library HTTP, disables HTTP proxies and redirects, and accepts only `127.0.0.1`. Only explicitly requested terminal capture is included in a prompt. Source/model downloads use the Internet; inference does not.
