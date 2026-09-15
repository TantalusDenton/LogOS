"""Conservative warning heuristic, never a shell security sandbox."""
import re, shlex

LEVEL = {"low": 0, "medium": 1, "high": 2}
READ_ONLY = {
    "pwd",
    "ls",
    "cat",
    "grep",
    "head",
    "tail",
    "wc",
    "ps",
    "ss",
    "free",
    "df",
    "du",
    "nvidia-smi",
    "uname",
    "whoami",
    "id",
    "stat",
    "uptime",
    "which",
    "file",
}


def classify(command, hint="medium"):
    risk = "medium"
    try:
        words = shlex.split(command)
    except ValueError:
        return "high"
    if not words:
        return "high"
    executable = words[0].rsplit("/", 1)[-1]
    if executable in READ_ONLY:
        risk = "low"
    if executable == "find":
        risk = (
            "low"
            if not set(words)
            & {
                "-delete",
                "-exec",
                "-execdir",
                "-ok",
                "-okdir",
                "-fprint",
                "-fprintf",
                "-fls",
            }
            else "high"
        )
    if executable in {
        "rm",
        "dd",
        "mkfs",
        "wipefs",
        "shred",
        "userdel",
        "deluser",
        "truncate",
        "fdisk",
        "parted",
        "sfdisk",
        "eval",
        "bash",
        "sh",
        "sudo",
        "su",
        "xargs",
        "python",
        "python3",
        "perl",
        "ruby",
        "awk",
        "gawk",
        "tee",
    } or executable.startswith("mkfs."):
        risk = "high"
    if re.search(r"[;&|><`\n\r]|\$\(|\$\{|\x1b", command):
        risk = "high"
    if re.search(r"\b(chmod|chown|chgrp)\b.*(?:-\w*R|--recursive)", command):
        risk = "high"
    if executable == "nvidia-smi" and any(
        w
        in {
            "-r",
            "--gpu-reset",
            "-pm",
            "--persistence-mode",
            "-pl",
            "--power-limit",
            "-ac",
            "--applications-clocks",
            "-lgc",
            "--lock-gpu-clocks",
        }
        or w.startswith(("--gpu-reset=", "--power-limit=", "--persistence-mode="))
        for w in words[1:]
    ):
        risk = "high"
    if re.search(r"/dev/(?:sd[a-z]|nvme[0-9]|vd[a-z]|mapper/)", command):
        risk = "high"
    # Destructive tokens may occur behind wrappers such as env or command.
    if any(
        w.rsplit("/", 1)[-1] in {"rm", "dd", "mkfs", "userdel", "wipefs", "shred"}
        for w in words
    ):
        risk = "high"
    return max((risk, hint if hint in LEVEL else "high"), key=LEVEL.get)
