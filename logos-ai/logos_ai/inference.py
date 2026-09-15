import json, urllib.request, urllib.error, unicodedata
from .prompts import SYSTEM, SCHEMA


class Unavailable(Exception):
    pass


def visible(text):
    return "".join(
        c if not unicodedata.category(c).startswith("C") else "\\u%04x" % ord(c)
        for c in text
    )


def validate_command(command):
    if not isinstance(command, str) or not command.strip() or len(command) > 4096:
        raise ValueError("Invalid command length")
    if any(
        unicodedata.category(c).startswith("C") or c in "\u2028\u2029" for c in command
    ):
        raise ValueError("Control characters or multiline commands rejected")
    return command


def parse(text):
    def pairs(items):
        d = {}
        for k, v in items:
            if k in d:
                raise ValueError("Duplicate JSON key")
            d[k] = v
        return d

    if len(text) > 65536:
        raise ValueError("Response too large")
    data = json.loads(text, object_pairs_hook=pairs)
    if not isinstance(data, dict) or set(data) != {"message", "commands"}:
        raise ValueError("Invalid response schema")
    if not isinstance(data["message"], str) or len(data["message"]) > 8192:
        raise ValueError("Invalid explanation")
    if not isinstance(data["commands"], list) or len(data["commands"]) > 5:
        raise ValueError("Invalid command list")
    for item in data["commands"]:
        if not isinstance(item, dict) or set(item) != {
            "command",
            "description",
            "risk",
        }:
            raise ValueError("Invalid command schema")
        validate_command(item["command"])
        if (
            not isinstance(item["description"], str)
            or len(item["description"]) > 8192
            or item["risk"] not in ("low", "medium", "high")
        ):
            raise ValueError("Invalid command metadata")
    return data


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise Unavailable("Local endpoint attempted a redirect")


class Client:
    def __init__(self, config):
        if config["LLAMA_HOST"] != "127.0.0.1":
            raise ValueError("Only loopback inference is permitted")
        self.config = config
        self.base = f"http://127.0.0.1:{int(config['LLAMA_PORT'])}"
        self.http = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect()
        )

    def request(self, path, payload=None, timeout=120):
        if path not in ("/health", "/v1/chat/completions", "/props"):
            raise ValueError("Invalid local route")
        body = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(
            self.base + path, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with self.http.open(req, timeout=timeout) as response:
                raw = response.read(262145)
            if len(raw) > 262144:
                raise ValueError("Server response too large")
            return json.loads(raw)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as e:
            raise Unavailable(
                "Local AI unavailable (server stopped or model loading)"
            ) from e

    def ask(self, question, context):
        payload = {
            "messages": [
                {"role": "system", "content": SYSTEM},
                {
                    "role": "user",
                    "content": json.dumps({"context": context, "request": question}),
                },
            ],
            "temperature": float(self.config["TEMPERATURE"]),
            "max_tokens": 512,
            "stream": False,
            "response_format": {"type": "json_object", "schema": SCHEMA},
        }
        response = self.request("/v1/chat/completions", payload)
        try:
            return parse(response["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as e:
            raise ValueError(
                "Invalid llama-server response; nothing was executed"
            ) from e
