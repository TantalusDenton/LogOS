# Building

## Requirements and storage

The bootstrap supports **Ubuntu 24.04 x86_64**. Builds require root for chroot,
private mount namespaces and mounts, plus a normal `logos-lfs` build account.
The host needs a working NVIDIA stack, the Quadro M2000 selected by the launcher,
and initialized LXD with CDI or NVIDIA runtime support before stage 08 can pass.
A local graphical session and Xephyr are needed to run the terminal; they are
not needed to compile the early LFS stages. The exercised server used LXD 6.9.

Start with at least **80 GiB free** in the workspace and retain the configured
**20 GiB reserve**. Source caches, extracted build/test trees, temporary tools,
rootfs and final archives coexist. These checks are lower bounds, not a peak
capacity guarantee. Container creation independently requires at least 16 GiB
free in the selected pool; the model is about 1.12 GB and the measured compressed
image about 2.6 GiB. The uncompressed container and LXD image cache take more.
Even with a pool on another disk, LXD may store imported image archives under its
host data directory, consuming root-disk space.

`JOBS=8` is the example build parallelism; the completed local build used 4.
Reduce it if compiler jobs pressure RAM. The default runtime limits are 8 CPUs
and 16 GiB RAM, not measured minimum requirements. Leave memory/CPU for the host.
A source build with compiler test suites can take many hours or days; there is
no fixed completion-time guarantee.

```bash
df -h / /path/to/build-disk
lxc storage list
lxc network list
nvidia-smi
```

Choose an absolute `LOGOS_BUILD` path without spaces on the larger disk. Do not
assume `/srv` has capacity. The source download cache is `$LOGOS_BUILD/sources`;
extracted trees live at `$LOGOS_BUILD/rootfs/sources`, with `$LOGOS_BUILD/work`
pointing there. Temporary tools are bind-mounted at the book's `/tools` path.
Do not bind a different same-filesystem directory at `/sources`: temporary Bash
cannot reliably resolve its working directory across that mount.

## Configure and compile

```bash
git clone https://github.com/TantalusDenton/LogOS.git
cd LogOS
cp config/logos.conf.example config/logos.conf
# Edit the copied file before running the commands below.
```

Important host configuration keys:

| Key | Example default | Purpose |
| --- | --- | --- |
| `LOGOS_BUILD` | `/srv/logos` | Root of build/cache/artifact storage; choose your disk |
| `JOBS` | `8` | Build parallelism |
| `MIN_FREE_GIB` / `RESERVE_GIB` | `80` / `20` | Initial capacity check / build reserve |
| `LOGOS_STORAGE` / `LOGOS_NETWORK` | `default` / `lxdbr0` | Existing LXD pool and managed network |
| `LOGOS_CONTAINER` / `LOGOS_IMAGE` | `logos-dev` / `logos/0.1` | Instance name / local image alias |
| `LOGOS_CPUS` / `LOGOS_MEMORY` | `8` / `16GiB` | Limits applied on container creation |
| `LOGOS_DISPLAY` / `LOGOS_SCREEN` | `:100` / `1600x900` | Xephyr display and screen |
| `LOGOS_DISK_SIZE` | unset | Optional container root-volume quota; not preallocated |

The file is shell code, sourced by the scripts; explicit assignments override
same-named environment variables. It is ignored by Git. Use identical settings
for root builds and desktop-user launch commands.

```bash
sudo ./build/bootstrap-host.sh
```

Bootstrap installs build-essential, Bison, GNU awk, Texinfo, download/archive
utilities, Python, Git, patch, Perl, file/diff/find tools, util-linux, Xephyr and
X11 utilities. It changes `/bin/sh` to Bash, selects GNU awk and creates
`logos-lfs`. If `lxc` is absent it installs the LXD snap. It does **not** initialize
LXD: on a fresh host run `sudo lxd init` and choose storage/network settings
appropriate to that host. Existing hosts should reuse an appropriate pool and
network. The desktop user and root build session both need LXD access; verify
with `lxc list` in each context.

Bootstrap does not install host CUDA or NVIDIA drivers, partition disks, install
a bootloader, or reboot. The build does create a disposable 512 MiB ext4 loop
image inside its workspace for util-linux tests; no host disk is formatted.
Host `/bin/sh` and awk changes are system-wide, so inspect bootstrap before use.

```bash
make check                            # Host versions, tools, disk, GPU, LXD, Xephyr
make test                             # Local tests and shell syntax
sudo ./build/build-logos.sh --resume   # Full build, validation and packaging
```

The scripts fetch and verify missing sources themselves. Optional prefetch:
`./build/download-sources.sh` and `./build/download-model.sh` (use the appropriate
workspace permissions). Source-built stages compile inside the isolated LFS
build environment; proprietary NVIDIA CUDA redistributables are the exception.
Do not run concurrent builds against one workspace; a lock enforces this.

To stop after early stages, use for example:

```bash
sudo ./build/build-logos.sh --resume --until 07-terminal
```

A full build must proceed through `10-logos`; it packages automatically. Stage 08
imports a temporary image into LXD and executes the CUDA kernel diagnostic.
This is why an offline chroot alone cannot complete the full GPU build.

## Import and run the result

From the local graphical desktop, as the LXD-enabled desktop user:

```bash
./host/create-container.sh
./host/start-logos.sh
./host/status.sh
./host/health.sh
```

Creation imports both generated archives automatically if the configured image
alias does not exist, and creates an unprivileged container without inherited
profiles. `./host/import-image.sh` performs import separately when desired.
Neither creation nor import replaces an existing container with a new image.
Use a new name and image alias in the configuration for a separate build; do not
delete user data to resolve an alias mismatch. See [using LogOS](using.md) and
[first-start troubleshooting](troubleshooting.md) before interpreting health.

## Recipe provenance

`build/recipes/chapter*.sh` are extracted command blocks from the frozen LFS 13.1 systemd HTML book, not a hand-invented cross toolchain. `build/lfs-plan.json` preserves the table of contents order. BLFS recipes use the 13.1 book; the X library list is reduced to xterm dependencies. Book instruction licensing is in `LICENSE.book-instructions`.

Official source lists/checksums are under `sources/`. LFS/BLFS MD5 values are used exactly as published; CUDA uses NVIDIA SHA256; GCC 14 uses upstream SHA512; tmux uses its GitHub release asset digest; the model uses its repository LFS SHA256; Git inputs use upstream commit/blob object IDs. Downloads are cached, verified again before use, and any checksum mismatch stops execution. MD5 is the historical book integrity mechanism, not a modern authenticity signature.

`source-manifest.txt` lists verified cached inputs. `package-manifest.txt` is appended only after successful package installation. Package markers contain recipe/source fingerprints. Stage markers are created only after all stage commands succeed.

## Resume

```bash
sudo ./build/build-logos.sh --resume
sudo ./build/build-logos.sh --from 08-cuda
```

`--from` requires every earlier stage marker; it never skips missing dependencies. Completed stages are reused. Changed inputs stop a resume by default. After diagnosing and reviewing a runner or unfinished-recipe repair, `--resume --accept-input-changes` audits the previous input snapshot and completed package hashes. It rejects changes to completed recipes, source locks, package plans, completed stage scripts and installed overlays; those require a fresh workspace. Accepted repairs are recorded in `state/history.tsv`. A legacy workspace without an input snapshot cannot automatically accept changes. A failed package is extracted afresh. Failure after partially installing a package can need diagnosis or a fresh workspace: there is no transactional package manager or rollback snapshot.

LFS book tests run with their prescribed users. Unexpected nonzero results stop those package builds. Diagnosed glibc lchmod, Binutils gprofng and ACL cp failures are handled individually according to LFS 13.1; fresh complete summaries and the exact expected diagnostics are required. Test summaries and failure output are retained under `logs/tests`. Do not globally disable LFS tests. The separate GCC 14 compatibility stage currently skips its full suite by default, and llama.cpp CTest/version probing are skipped when the chroot lacks host-injected `libcuda.so.1`; these skips are not passing test results. The `LOGOS_FULL_GCC_CHECK` branch in stage 08 is not currently forwarded through the clean chroot environment by the normal wrapper, so merely exporting it on the host does not enable the suite. See [validation](validation.md). Log output and the specific failing test before adapting a recipe. The private mount namespace cleans up bind/proc/sys mounts automatically on exit.

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

## Default model cache

`./build/download-model.sh` optionally caches and verifies the single pinned GGUF under `$LOGOS_BUILD/models`. First startup verifies that cached file and transfers it into the container before `logos-model install-default` verifies it again. Without a host cache, the same guest command downloads and verifies the model normally. Existing guest model files are not overwritten. The runtime AI remains loopback-only.

## Reclaiming build space

`sudo make clean` removes extracted package work trees only after checking the
workspace identity and build lock. It retains downloads, rootfs, state and
artifacts, but discards useful diagnostic build files. Preserve needed test logs
first. It does not clean LXD images, container data or model caches. Avoid deleting
stage markers or rootfs contents to manufacture a successful resume.
