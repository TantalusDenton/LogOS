import os, re, subprocess
from .inference import validate_command


class Terminal:
    def __init__(self, pane=None):
        self.pane = pane or os.environ.get("LOGOS_SHELL_PANE", "")
        if not re.fullmatch(r"%[0-9]+", self.pane):
            raise ValueError("No dedicated LogOS Bash pane; start logos-session")

    def tmux(self, *args):
        return subprocess.run(
            ["tmux", "-L", "logos", *args],
            check=True,
            text=True,
            capture_output=True,
            timeout=5,
        ).stdout.rstrip("\n")

    def info(self, fmt):
        return self.tmux("display-message", "-p", "-t", self.pane, fmt)

    def send(self, command, run=False):
        validate_command(command)
        if self.info("#{pane_current_command}") != "bash":
            raise ValueError("Bash pane is busy; return it to a prompt first")
        if run:
            # Clear any partially typed command before sending the separately approved command.
            self.tmux("send-keys", "-t", self.pane, "C-c")
        self.tmux("send-keys", "-t", self.pane, "-l", "--", command)
        if run:
            self.tmux("send-keys", "-t", self.pane, "Enter")

    def capture(self):
        raw = self.tmux("capture-pane", "-p", "-t", self.pane, "-S", "-40")
        # tmux -S -40 includes history plus the visible pane; limit the payload itself.
        return "\n".join(raw.splitlines()[-40:])[-16384:]
