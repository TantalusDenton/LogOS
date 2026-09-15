import getpass, os, platform, subprocess
from pathlib import Path


def snapshot(terminal=None):
    data = {
        "logos_version": "Developer Preview 0.1",
        "hostname": platform.node(),
        "username": getpass.getuser(),
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "working_directory": os.getcwd(),
    }
    if terminal:
        try:
            data["working_directory"] = terminal.info("#{pane_current_path}")
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        data["memory"] = next(
            x
            for x in Path("/proc/meminfo").read_text().splitlines()
            if x.startswith("MemTotal:")
        )
    except (OSError, StopIteration):
        pass
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            data["gpu"] = result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return data
