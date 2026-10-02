# Validation status

## Completed build and runtime run

On **September 20, 2026 (America/Los_Angeles; September 21 UTC)**, the full build
completed with exit code 0 and all ten stage markers, including CUDA verification,
llama.cpp compilation, rootfs ABI validation and packaging. The approximately
2.6 GiB rootfs was imported into LXD and started as unprivileged `logos-dev` on
the `goldenfir` pool. The host was not rebooted and its NVIDIA driver/kernel/boot
configuration was not changed by these build/run steps.

Observed runtime results after the repairs below:

- systemd, DHCP/network route, gateway ping and DNS passed.
- Xephyr `:100`, the X11 socket, xterm, tmux and `logos-terminal` passed.
- NVIDIA Quadro M2000, CUDA 12.9 runtime and a real CUDA kernel computation passed.
- llama.cpp loaded the pinned model, served local inference and reported **29/29
  layers offloaded**. Live inference samples showed GPU utilization.
- Structured command proposals and the health script's command-pattern checks
  passed. These are smoke checks, not a benchmark of command correctness.

The successful runtime was **not an untouched import**. The host launcher was
repaired to bind X11 at `/opt/logos-host-x11` and link it into the guest `/tmp`,
which systemd mounts separately. The container's failed `console-getty.service`
was masked and its failed state reset. `--verbose` was added to the guest server
launcher to obtain offload logs, and an updated health script was copied in.
The packaged September image predates those guest changes. See
[troubleshooting](troubleshooting.md) for reproducing them; do not describe the
archive alone as having passed the final health run.

On **October 2, 2026**, read-only reinspection confirmed `logos-dev` was still
running, systemd reported `running`, and the inference and terminal services
were active. The complete GPU/inference suite was not rerun for this documentation
update. `make test` passed **23 AI/client tests and 17 build/recovery/model-cache
tests**, plus shell syntax checks.

## Artifact identities

These hashes identify the local September build, not downloadable GitHub release
assets:

| Artifact | SHA-256 |
| --- | --- |
| `logos-rootfs.tar.xz` | `7087ba04b49d04e0ef0512d36914d298f4b7a2c92390000a7bdb5b94c2615e87` |
| `logos-metadata.tar.xz` | `e9fb38fe28fa900dc63b28efbc327ccfbc2d5f6ba7e9dd1fe1c8e34f96e53921` |

LXD imported fingerprint:
`fda7af49b499efd32be4ae327d97ad3ec2a91b14bf73bf78d4091b336407f669`.
Build logs, stage/package markers, manifests, ABI output and checksums are retained
locally under `$LOGOS_BUILD` (this checkout uses ignored `.work/build`). Live
console output is in ignored `reports/build-root-console.log`. Historical tracked
reports may describe earlier failures; they are not current status snapshots.

## Tests and limitations

The LFS build exercised real upstream suites. Diagnosed environmental exceptions
are documented in [LFS deviations](lfs-deviations.md), with preserved summaries
for glibc, Binutils, GCC, ACL, Findutils, Groff, Tar and other packages. Known
upstream failures remain failures; successful stage completion does not turn
those results into PASS. Python's recovered full suite ran 48,271 tests with
2,087 skipped and no failures.

The separate GCC 14 CUDA compatibility build disables libsanitizer. Its full
suite was attempted during development and had sanitizer/plugin/torture failures;
it is not claimed as an all-green compiler qualification. The current stage
skips that full suite by default and reuses an already installed compiler.
The advertised `LOGOS_FULL_GCC_CHECK` switch is not passed through the normal
clean chroot wrapper. Do not infer full GCC coverage from the build's exit code.

llama.cpp CTest initially failed because the build chroot lacks the host's
`libcuda.so.1`. The stage now skips CTest and the version probe in that condition.
Rootfs ABI validation allows this one runtime-injected dependency while rejecting
other unresolved libraries and temporary-toolchain/Ubuntu multiarch paths.
Actual CUDA computation and inference were verified in LXD, but this does not
replace the entire upstream llama.cpp test suite.

The current health check relies on invocation-specific llama.cpp log output. Its
fallback for logs containing only per-layer assignment has not been validated;
the exercised run contained the aggregate `29/29` line. Its semantic checks accept
some command patterns that can still be incorrect (for example, sorting a long
`ls` listing without a size key). Review suggestions manually. GPU success is
limited to the exercised M2000 host; there is no qualification for other cards,
models, driver versions or a fresh end-to-end rebuild of every subsequent edit.
