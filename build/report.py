#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys

r = pathlib.Path(__file__).resolve().parents[1]
b = pathlib.Path(os.environ["LOGOS_BUILD"])
a = b / "artifacts"
a.mkdir(exist_ok=True)
history = b / "state/history.tsv"
cuda = b / "state/cuda-compute.pass"
text = [
    "LogOS Developer Preview 0.1 — build report",
    "Last build exit code: " + sys.argv[1],
    "Completed stages: "
    + ", ".join(p.stem for p in sorted((b / "state").glob("*.done"))),
    "CUDA: 12.9.1 selected; compute "
    + ("TESTED PASS" if cuda.exists() else "NOT VERIFIED"),
    "GPU inference: NOT VERIFIED by build; run make health on the actual LXD instance",
    "llama.cpp: "
    + next(
        x["checksum"]
        for x in json.loads((r / "sources/ai.json").read_text())
        if x["name"] == "llama.cpp.git"
    ),
    "Model: " + json.loads((r / "sources/model.json").read_text())["name"],
    "Rootfs disk usage: "
    + subprocess.check_output(
        [
            "du",
            "-shx",
            "--exclude=logos-build",
            "--exclude=sources",
            "--exclude=tools",
            "--exclude=dev",
            "--exclude=proc",
            "--exclude=sys",
            "--exclude=run",
            str(b / "rootfs"),
        ],
        text=True,
    ).strip(),
    "Test results and failed/retried packages:\n"
    + (history.read_text() if history.exists() else "No package tests executed"),
    "Deliberate deviations:\n" + (r / "docs/lfs-deviations.md").read_text(),
]
(a / "build-report.txt").write_text("\n".join(text) + "\n")
