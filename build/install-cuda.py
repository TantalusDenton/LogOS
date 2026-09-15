#!/usr/bin/env python3
import json, os, pathlib, subprocess, shutil
from fetch import verify

r = pathlib.Path(__file__).resolve().parents[1]
b = pathlib.Path(os.environ["LOGOS_BUILD"])
dst = b / "rootfs/opt/cuda-12.9"
dst.mkdir(parents=True, exist_ok=True)
for item in json.loads((r / "sources/ai.json").read_text()):
    if "component" not in item and not item["name"].startswith("gcc-"):
        continue
    src = b / "sources" / item["name"]
    verify(src, item["checksum"])
    if item["name"].startswith("gcc-"):
        work = b / "work/gcc-14.3.0"
        if work.exists():
            shutil.rmtree(work)
        subprocess.run(["tar", "-xf", str(src), "-C", str(b / "work")], check=True)
    else:
        subprocess.run(
            ["tar", "--strip-components=1", "-xf", str(src), "-C", str(dst)], check=True
        )
