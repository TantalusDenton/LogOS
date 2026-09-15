import argparse, subprocess
from .config import read_config
from .inference import Client, Unavailable, visible
from .commands import Terminal
from .context import snapshot
from .risk import classify


def approve(item, terminal, input_fn=input, print_fn=print):
    risk = classify(item["command"], item["risk"])
    print_fn(
        "\nCOMMAND\n"
        + visible(item["command"])
        + "\n"
        + visible(item["description"])
        + "\nRisk: "
        + risk.upper()
    )
    action = input_fn("[R]un  [I]nsert  [C]ancel: ").strip().lower()
    if action not in ("r", "i"):
        return False
    if action == "r" and risk == "high" and input_fn("Type RUN to execute: ") != "RUN":
        return False
    if terminal is None:
        raise ValueError("No Bash pane connected; nothing was sent")
    terminal.send(item["command"], run=action == "r")
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--interactive", action="store_true")
    p.parse_args()
    try:
        client = Client(read_config())
    except ValueError as e:
        print(e)
        return 1
    try:
        terminal = Terminal()
    except ValueError:
        terminal = None
    print(
        "LogOS AI\nLocal inference · Every command needs approval\nType Explain terminal to share the last 40 lines; /quit to exit."
    )
    try:
        client.request("/health", timeout=2)
    except Unavailable:
        print(
            "Local AI unavailable (server stopped or model loading). Bash remains available."
        )
    while True:
        try:
            question = input("\nAI> ").strip()
            if question in ("/quit", "/exit"):
                return 0
            if not question:
                continue
            if len(question) > 8192:
                print("Request too long")
                continue
            ctx = snapshot(terminal)
            if question.lower() == "explain terminal":
                if terminal is None:
                    raise ValueError("No terminal pane to capture")
                ctx["terminal_output_untrusted"] = terminal.capture()
            reply = client.ask(question, ctx)
            print(visible(reply["message"]))
            for item in reply["commands"]:
                approve(item, terminal)
        except EOFError:
            return 0
        except KeyboardInterrupt:
            print("\nCancelled")
        except (ValueError, Unavailable, OSError, subprocess.SubprocessError) as e:
            print(visible(str(e)))


if __name__ == "__main__":
    raise SystemExit(main())
