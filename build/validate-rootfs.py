#!/usr/bin/env python3
import os, pathlib, subprocess

root = pathlib.Path(os.environ["LFS"])
out = []
assert "ID=logos" in (root / "etc/os-release").read_text()
assert not any((root / "boot").glob("*")), "Unexpected kernel or bootloader files"
for binary in [
    "/bin/bash",
    "/usr/bin/python3",
    "/usr/bin/systemctl",
    "/usr/bin/xterm",
    "/usr/bin/tmux",
    "/usr/bin/llama-server",
]:
    result = subprocess.check_output(
        ["chroot", str(root), "/usr/bin/ldd", binary],
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert "not found" not in result, (binary, result)
    assert "/tools/" not in result and "x86_64-linux-gnu" not in result, (
        binary,
        result,
    )
    out.append(binary + "\n" + result)
    subprocess.run(
        ["chroot", str(root), "/usr/bin/readelf", "-l", binary],
        check=True,
        stdout=subprocess.DEVNULL,
    )
assert (
    subprocess.check_output(
        ["chroot", str(root), "readlink", "-f", "/sbin/init"], text=True
    ).strip()
    == "/usr/lib/systemd/systemd"
)
pathlib.Path(os.environ["LOGOS_BUILD"], "artifacts/abi-validation.txt").write_text(
    "\n".join(out)
)
print(
    "LogOS dynamic links resolve inside chroot; no temporary toolchain or Ubuntu multiarch paths"
)
