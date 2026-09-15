# Troubleshooting

- **Host NVML driver/library mismatch:** inspect `/proc/driver/nvidia/version`, `nvidia-smi`, installed NVIDIA package versions and `ldconfig -p`. On the inspected server the loaded module is 535.309.01 but NVML is 580.178.04. A root administrator must reconcile the installed and loaded versions; the appropriate action depends on whether an upgrade is pending. LogOS does not replace drivers or reboot the active desktop automatically.
- **Insufficient space:** `/srv` was on a filesystem with only 7.1 GiB free. Point `LOGOS_BUILD` at the larger workspace disk; changing paths does not magically move existing build state. LXD's storage pool must also have adequate space.
- **Root-owned repository / sudo requires password:** this session cannot bootstrap/chroot or write the requested root-owned directory. Use an accessible checkout and root-enabled build session. Never use LXD access to bypass a denied sudo operation.
- **Book tests fail:** inspect `logs/build-*.log` and `state/history.tsv`. Preserve the original error. Known upstream expected failures still require review; do not mark a stage complete manually.
- **Resume reports changed inputs:** a completed package's recipe/source or build configuration changed. Use a fresh workspace until a compatible migration has been reviewed. There is no package rollback mechanism.
- **X11:** confirm local desktop DISPLAY/XAUTHORITY, Xephyr socket, LXD bind mount, and run `DISPLAY=:100 xdpyinfo` inside LogOS. Xephyr always disables TCP. `-ac` applies only to this developer display; other local users can connect. No `xhost +` is used.
- **AI unavailable:** Bash remains usable while `logos-ai.service` loads/restarts. Check its journal and model checksum. Download errors cannot trigger remote inference or execution of malformed output.
- **Unexpected systemd degraded state:** inspect `systemctl --failed`; startup fails until each cause is understood. No unreviewed degraded state is treated as healthy.
- **Busy Bash pane:** return to a Bash prompt before approving an AI command. Run cancels a partial input line; Insert appends literal text without Enter. Complex shell syntax is conservatively high risk.
