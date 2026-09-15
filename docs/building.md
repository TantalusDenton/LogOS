# Building

## Requirements and storage

Ubuntu 24.04 x86_64, working sudo/root, >=80 GiB initially free, 20 GiB reserve, LXD initialized with an appropriate pool/network. Default workspace is `/srv/logos`, configurable in `config/logos.conf`. Rootfs, sources, temporary tools, logs, artifacts, state and extracted work trees are separate. The tools directory is bind-mounted at `$LFS/tools` so the book's paths are preserved.

Bootstrap changes `/bin/sh` to Bash, selects GNU awk, installs host build dependencies, and creates `logos-lfs`. It does not initialize or reconfigure existing LXD pools, touch partitions, install CUDA on the host, reboot, or replace NVIDIA drivers.

## Recipe provenance

`build/recipes/chapter*.sh` are extracted command blocks from the frozen LFS 13.1 systemd HTML book, not a hand-invented cross toolchain. `build/lfs-plan.json` preserves the table of contents order. BLFS recipes use the 13.1 book; the X library list is reduced to xterm dependencies. Book instruction licensing is in `LICENSE.book-instructions`.

Official source lists/checksums are under `sources/`. LFS/BLFS MD5 values are used exactly as published; CUDA uses NVIDIA SHA256; GCC 14 uses upstream SHA512; tmux uses its GitHub release asset digest; the model uses its repository LFS SHA256; Git inputs use upstream commit/blob object IDs. Downloads are cached, verified again before use, and any checksum mismatch stops execution. MD5 is the historical book integrity mechanism, not a modern authenticity signature.

`source-manifest.txt` lists verified cached inputs. `package-manifest.txt` is appended only after successful package installation. Package markers contain recipe/source fingerprints. Stage markers are created only after all stage commands succeed.

## Resume

```bash
sudo ./build/build-logos.sh --resume
sudo ./build/build-logos.sh --from 08-cuda
```

`--from` requires every earlier stage marker; it never skips missing dependencies. Completed stages are reused. Changed inputs invalidate a resumed workspace and require a fresh configurable workspace, preventing accidental mixtures of incompatible toolchains. A failed package is extracted afresh. Failure after partially installing a package can need diagnosis or a fresh workspace: there is no transactional package manager or rollback snapshot.

Book tests run with their prescribed users. Nonzero results stop the build, including upstream expected-failure situations requiring review. Do not globally disable tests. Log output and the specific failing test before adapting a recipe. The private mount namespace cleans up bind/proc/sys mounts automatically on exit.

Stages 01/02 use the isolated LFS environment as `logos-lfs`. Stage 03 builds chapters 7/8 in chroot, including systemd in book order. Stage 04 configures that systemd for LXD. Stage 05 builds network/build support; 06 X11; 07 terminal; 08 CUDA plus GCC 14 and actual GPU computation in a temporary unprivileged LXD instance; 09 llama.cpp; 10 LogOS software and ABI checks.

The CUDA diagnostic runs before llama.cpp is built. It requires the host driver to work. Final GPU inference and visible desktop verification happen after image import/start, not during an offline chroot build.

## Artifacts

`artifacts/logos-rootfs.tar.xz`, `logos-metadata.tar.xz`, `source-manifest.txt`, `package-manifest.txt`, `build-report.txt`, image checksums and ABI logs. Packaging excludes build trees, temporary tools, pseudofilesystems, caches/logs and unnecessary binutils static archives and libtool metadata (compiler support archives are retained), preserving runtime shared libraries. The source-built build root is retained for diagnosis. The model is installed once into `/var/lib/logos/models` on first startup and verified on later starts.

## Sharing an existing root terminal with the build session

When normal sudo authentication is confined to another terminal, this development
session also provides `host/root-console.sh`. Run it from that root terminal. It
creates a dedicated root tmux server, grants the workspace owner explicit tmux
write access, and restricts its UNIX socket to that user's private workspace
subdirectory. This intentionally lets the agent execute root commands. It does
not alter sudoers. Close the channel with `./host/root-console.sh close` when the
build is finished. The current session has built tmux/libevent locally for this
helper; other hosts can use an already-installed tmux.
