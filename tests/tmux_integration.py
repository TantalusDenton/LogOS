#!/usr/bin/env python3
"""Opt-in real tmux approval test, isolated from any existing tmux server."""
import os, pathlib, shlex, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "logos-ai"))
from logos_ai.commands import Terminal
from logos_ai.main import approve

work = ROOT / ".work/tmux-integration"
work.mkdir(parents=True, exist_ok=True)
os.environ["TMUX_TMPDIR"] = str(work)
os.environ["HISTFILE"] = "/dev/null"


def tmux(*args):
    return subprocess.check_output(["tmux", "-L", "logos", *args], text=True).strip()


def wait_file(path):
    for _ in range(50):
        if path.exists():
            return
        time.sleep(0.05)
    raise AssertionError("Approved command did not execute")


inserted = work / "inserted"
executed = work / "executed"
survived = work / "survived"
for p in [inserted, executed, survived]:
    p.unlink(missing_ok=True)
try:
    pane = tmux(
        "new-session",
        "-d",
        "-s",
        "logos",
        "-P",
        "-F",
        "#{pane_id}",
        "/bin/bash",
        "--noprofile",
        "--norc",
    )
    terminal = Terminal(pane)
    time.sleep(0.2)
    item = {
        "command": "printf insert > " + shlex.quote(str(inserted)),
        "description": "Test insertion",
        "risk": "high",
    }
    approve(item, terminal, lambda _: "i", lambda _: None)
    time.sleep(0.2)
    assert not inserted.exists(), "Insert executed without Enter"
    # Cancel a proposed command without disturbing the existing shell input.
    item["command"] = "printf run > " + shlex.quote(str(executed))
    approve(item, terminal, lambda _: "c", lambda _: None)
    assert not executed.exists()
    inputs = iter(["r", "RUN"])
    approve(item, terminal, lambda _: next(inputs), lambda _: None)
    wait_file(executed)
    assert not inserted.exists(), "Run combined with the pending inserted line"
    tmux("set-option", "-t", "logos", "remain-on-exit", "on")
    ai = tmux(
        "split-window",
        "-h",
        "-t",
        pane,
        "-P",
        "-F",
        "#{pane_id}",
        "/bin/bash",
        "-c",
        "exit 1",
    )
    time.sleep(0.2)
    terminal.send("printf alive > " + shlex.quote(str(survived)), run=True)
    wait_file(survived)
    assert survived.read_text() == "alive"
    print(
        "PASS: real tmux Insert does not execute; Cancel sends nothing; explicit Run executes; Bash survives AI pane exit"
    )
finally:
    subprocess.run(["tmux", "-L", "logos", "kill-server"], capture_output=True)
