import json, os, subprocess, unittest
from unittest.mock import Mock, patch
from logos_ai.inference import parse, validate_command, Client, Unavailable, visible
from logos_ai.commands import Terminal
from logos_ai.main import approve
from logos_ai.risk import classify
from logos_ai.config import DEFAULTS


def reply(command="nvidia-smi", risk="low"):
    return {
        "message": "GPU usage",
        "commands": [
            {"command": command, "description": "Show GPU usage", "risk": risk}
        ],
    }


class Protocol(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(parse(json.dumps(reply())), reply())

    def test_reject_bad_schema(self):
        for content in [
            "```json\n" + json.dumps(reply()) + "\n```",
            "nvidia-smi",
            "[]",
            "{}",
            '{"message":"a","message":"b","commands":[]}',
            json.dumps(reply()).replace('"low"', '"safe"'),
        ]:
            with self.subTest(content=content), self.assertRaises(ValueError):
                parse(content)

    def test_no_controls_or_newlines(self):
        for command in [
            "echo ok\nrm -rf ~",
            "ls\r",
            "\x1b[200~ls",
            "ls\x00",
            "echo\u2028oops",
            "\u202eecho",
        ]:
            with self.subTest(command=command), self.assertRaises(ValueError):
                parse(json.dumps(reply(command)))

    def test_literal_shell_syntax_allowed_for_approval(self):
        self.assertEqual(
            parse(
                json.dumps(
                    reply('find ~ -type f -printf "%s %p\\n" | sort -nr | head -n 10')
                )
            )["commands"][0]["risk"],
            "low",
        )

    def test_terminal_escape_output(self):
        self.assertNotIn("\x1b", visible("\x1b]52;c;secret\x07"))

    def test_remote_rejected(self):
        with self.assertRaises(ValueError):
            Client({**DEFAULTS, "LLAMA_HOST": "example.com"})

    def test_unknown_route(self):
        with self.assertRaises(ValueError):
            Client(DEFAULTS).request("http://example.com")


class Risks(unittest.TestCase):
    def test_low(self):
        for c in ["pwd", "ls -la", "nvidia-smi", "find ~ -type f"]:
            self.assertEqual(classify(c, "low"), "low")

    def test_high(self):
        for c in [
            "rm -rf /tmp/a",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda",
            "userdel user",
            "find ~ -delete",
            "ls $(touch /tmp/pwn)",
            "cat x > ~/.bashrc",
            "env rm x",
            "chmod -R 777 ~",
            "bash -c whoami",
        ]:
            with self.subTest(c=c):
                self.assertEqual(classify(c, "low"), "high")

    def test_model_can_raise_risk(self):
        self.assertEqual(classify("pwd", "high"), "high")

    def test_medium(self):
        self.assertEqual(classify("systemctl restart logos-ai", "low"), "medium")


class Approval(unittest.TestCase):
    def test_cancel_and_invalid_choices_never_send(self):
        for choice in ["c", "", "yes", "run"]:
            terminal = Mock()
            approve(reply()["commands"][0], terminal, lambda _: choice, lambda _: None)
            terminal.send.assert_not_called()

    def test_insert_never_enters(self):
        t = Mock()
        approve(reply()["commands"][0], t, lambda _: "i", lambda _: None)
        t.send.assert_called_once_with("nvidia-smi", run=False)

    def test_high_requires_exact_run(self):
        for confirmation in ["", "run", "yes", " RUN"]:
            inputs = iter(["r", confirmation])
            t = Mock()
            approve(
                reply("rm -rf ~/test")["commands"][0],
                t,
                lambda _: next(inputs),
                lambda _: None,
            )
            t.send.assert_not_called()

    def test_high_confirmed(self):
        inputs = iter(["r", "RUN"])
        t = Mock()
        approve(
            reply("rm -rf ~/test")["commands"][0],
            t,
            lambda _: next(inputs),
            lambda _: None,
        )
        t.send.assert_called_once()

    def test_send_literal_without_second_shell(self):
        t = Terminal("%1")
        t.tmux = Mock(side_effect=["bash", "", ""])
        t.send("ls $(touch /tmp/test)", run=False)
        self.assertEqual(
            t.tmux.call_args_list[-1].args,
            ("send-keys", "-t", "%1", "-l", "--", "ls $(touch /tmp/test)"),
        )
        self.assertFalse(any("Enter" in x.args for x in t.tmux.call_args_list))

    def test_run_clears_partial_line(self):
        t = Terminal("%1")
        t.tmux = Mock(return_value="bash")
        t.send("pwd", run=True)
        self.assertEqual(
            t.tmux.call_args_list[1].args, ("send-keys", "-t", "%1", "C-c")
        )
        self.assertEqual(
            t.tmux.call_args_list[-1].args, ("send-keys", "-t", "%1", "Enter")
        )

    def test_busy_pane_rejected(self):
        t = Terminal("%1")
        t.tmux = Mock(return_value="vim")
        with self.assertRaises(ValueError):
            t.send("pwd", run=True)
        self.assertEqual(t.tmux.call_count, 1)

    def test_bad_pane_rejected(self):
        for name in ["", "logos:0", "%1; rm"]:
            with self.assertRaises(ValueError):
                Terminal(name)

    def test_capture_sends_at_most_forty_lines(self):
        terminal = Terminal("%1")
        terminal.tmux = Mock(return_value="\n".join(str(i) for i in range(100)))
        self.assertEqual(
            terminal.capture().splitlines(), [str(i) for i in range(60, 100)]
        )

    def test_context_capture_explicit(self):
        t = Terminal("%1")
        t.tmux = Mock(return_value="last lines")
        self.assertEqual(t.capture(), "last lines")
        t.tmux.assert_called_once_with("capture-pane", "-p", "-t", "%1", "-S", "-40")


if __name__ == "__main__":
    unittest.main()
