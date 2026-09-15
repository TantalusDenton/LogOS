from pathlib import Path

DEFAULTS = {
    "MODEL": "/var/lib/logos/models/default.gguf",
    "LLAMA_HOST": "127.0.0.1",
    "LLAMA_PORT": "8080",
    "CONTEXT_SIZE": "4096",
    "GPU_LAYERS": "99",
    "TEMPERATURE": "0.2",
}


def read_config(path="/etc/logos/logos.conf"):
    config = DEFAULTS.copy()
    if Path(path).exists():
        for line in Path(path).read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            key, sep, value = line.partition("=")
            if not sep or key.strip() not in DEFAULTS:
                raise ValueError("Invalid LogOS configuration key")
            config[key.strip()] = value.strip().strip("\"'")
    if config["LLAMA_HOST"] != "127.0.0.1":
        raise ValueError("AI endpoint must be 127.0.0.1")
    if not 1024 <= int(config["LLAMA_PORT"]) <= 65535:
        raise ValueError("Invalid local port")
    if not 512 <= int(config["CONTEXT_SIZE"]) <= 8192:
        raise ValueError("Invalid context size")
    if not 0 <= float(config["TEMPERATURE"]) <= 2:
        raise ValueError("Invalid temperature")
    return config
