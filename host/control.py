#!/usr/bin/env python3
"""LXD/Xephyr lifecycle; all subprocess arguments are passed without a shell."""
import hashlib, json, os, pathlib, re, subprocess, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
NAME = os.getenv("LOGOS_CONTAINER", "logos-dev")
IMAGE = os.getenv("LOGOS_IMAGE", "logos/0.1")
DISPLAY = os.getenv("LOGOS_DISPLAY", ":100")
SCREEN = os.getenv("LOGOS_SCREEN", "1600x900")
BUILD = pathlib.Path(os.getenv("LOGOS_BUILD", "/srv/logos"))
STATE = (
    pathlib.Path(
        os.environ.get("XDG_STATE_HOME", str(pathlib.Path.home() / ".local/state"))
    )
    / "logos"
)


def cmd(*args, timeout=60, check=True):
    return subprocess.run(
        args, check=check, text=True, capture_output=True, timeout=timeout
    ).stdout.strip()


def lxc(*args, **kw):
    return cmd("lxc", *args, **kw)


def query(path):
    return json.loads(lxc("query", path))


def config():
    return query("/1.0/instances/" + NAME)


def owned():
    c = config()
    if c["config"].get("user.logos.managed") != "0.1":
        raise RuntimeError("Refusing to modify an instance not created by LogOS")
    if c["expanded_config"].get("security.privileged", "false") != "false":
        raise RuntimeError("LogOS requires an unprivileged container")
    return c


def guest(*args, timeout=60, check=True):
    return lxc("exec", NAME, "--", *args, timeout=timeout, check=check)


def gpu():
    text = cmd(
        "nvidia-smi",
        "--query-gpu=index,name,pci.bus_id,memory.total",
        "--format=csv,noheader,nounits",
    )
    candidates = [
        line.split(",") for line in text.splitlines() if "Quadro M2000" in line
    ]
    if len(candidates) != 1:
        raise RuntimeError("Expected one Quadro M2000; NVIDIA host validation failed")
    return [x.strip() for x in candidates[0]]


def configure_gpu():
    c = owned()
    g = gpu()
    api = query("/1.0")
    ext = api["api_extensions"]
    if "gpu_cdi" in ext:
        props = {
            "gputype": "physical",
            "id": "nvidia.com/gpu=" + g[0],
            "gid": "12",
            "mode": "0660",
        }
    elif "nvidia_runtime" in ext:
        lxc(
            "config",
            "set",
            NAME,
            "nvidia.runtime=true",
            "nvidia.driver.capabilities=compute,utility",
        )
        props = {
            "gputype": "physical",
            "pci": g[2][-12:].lower(),
            "gid": "12",
            "mode": "0660",
        }
    else:
        raise RuntimeError("LXD has no supported NVIDIA runtime or CDI capability")
    if "logos-gpu" not in c["devices"]:
        lxc(
            "config",
            "device",
            "add",
            NAME,
            "logos-gpu",
            "gpu",
            *[k + "=" + v for k, v in props.items()],
        )
    elif any(c["devices"]["logos-gpu"].get(k) != v for k, v in props.items()):
        raise RuntimeError("Existing logos-gpu configuration differs from detected GPU")
    return g


def configure_x11():
    current = owned()["devices"].get("logos-x11")
    required = {
        "type": "disk",
        "source": "/tmp/.X11-unix",
        "path": "/tmp/.X11-unix",
        "readonly": "true",
    }
    if current is None:
        lxc(
            "config",
            "device",
            "add",
            NAME,
            "logos-x11",
            "disk",
            *[k + "=" + v for k, v in required.items() if k != "type"],
        )
    elif any(current.get(k) != v for k, v in required.items()):
        raise RuntimeError(
            "Existing logos-x11 device does not match the read-only X socket mount"
        )
    lxc("config", "set", NAME, "environment.DISPLAY=" + DISPLAY)


def image_import():
    for f in ["logos-rootfs.tar.xz", "logos-metadata.tar.xz"]:
        if not (BUILD / "artifacts" / f).is_file():
            raise RuntimeError("Missing artifact " + f)
    print(
        lxc(
            "image",
            "import",
            str(BUILD / "artifacts/logos-metadata.tar.xz"),
            str(BUILD / "artifacts/logos-rootfs.tar.xz"),
            "--alias",
            IMAGE,
            timeout=1200,
        )
    )


def create():
    gpu()
    query("/1.0")
    # Explicit devices avoid accidentally inheriting privileged or unrelated profile devices.
    existing = query("/1.0/instances")
    if "/1.0/instances/" + NAME in existing:
        owned()
        configure_gpu()
        configure_x11()
        return
    aliases = json.loads(lxc("image", "alias", "list", "--format=json"))
    if not any(a["name"] == IMAGE for a in aliases):
        image_import()
    network = os.getenv("LOGOS_NETWORK", "lxdbr0")
    pool = os.getenv("LOGOS_STORAGE", "default")
    query("/1.0/networks/" + network)
    query("/1.0/storage-pools/" + pool)
    space = query("/1.0/storage-pools/" + pool + "/resources")["space"]
    if space["total"] - space["used"] < 16 * 1024**3:
        raise RuntimeError("Selected LXD pool has less than 16 GiB free")
    args = [
        "init",
        IMAGE,
        NAME,
        "--no-profiles",
        "--storage",
        pool,
        "--network",
        network,
        "-c",
        "security.privileged=false",
        "-c",
        "user.logos.managed=0.1",
        "-c",
        "limits.cpu=" + os.getenv("LOGOS_CPUS", "8"),
        "-c",
        "limits.memory=" + os.getenv("LOGOS_MEMORY", "16GiB"),
    ]
    lxc(*args, timeout=300)
    if os.getenv("LOGOS_DISK_SIZE"):
        lxc(
            "config",
            "device",
            "set",
            NAME,
            "root",
            "size=" + os.environ["LOGOS_DISK_SIZE"],
        )
    configure_gpu()
    configure_x11()
    print("Created unprivileged " + NAME)


def xephyr():
    if not re.fullmatch(r":[1-9][0-9]*", DISPLAY) or not re.fullmatch(
        r"[1-9][0-9]{2,3}x[1-9][0-9]{2,3}", SCREEN
    ):
        raise RuntimeError("Invalid Xephyr display or screen size")
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    socket = pathlib.Path("/tmp/.X11-unix/X" + DISPLAY[1:])
    pidfile = STATE / ("xephyr-" + DISPLAY[1:] + ".pid")
    if socket.exists():
        if not pidfile.exists():
            raise RuntimeError("Display is occupied by an unmanaged X server")
        pid = int(pidfile.read_text())
        args = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
        if (
            b"Xephyr" not in [pathlib.Path(x.decode()).name.encode() for x in args if x]
            or DISPLAY.encode() not in args
        ):
            raise RuntimeError("Stale Xephyr ownership record")
        return
    if not os.environ.get("DISPLAY"):
        raise RuntimeError(
            "Start from the local graphical desktop; host DISPLAY is missing"
        )
    helptext = subprocess.run(
        ["Xephyr", "-help"], capture_output=True, text=True
    ).stderr
    for flag in ["-screen", "-resizeable", "-noreset", "-nolisten", "-ac"]:
        if flag not in helptext:
            raise RuntimeError("Xephyr does not advertise " + flag)
    with open(STATE / "xephyr.log", "a") as log:
        proc = subprocess.Popen(
            [
                "Xephyr",
                DISPLAY,
                "-screen",
                SCREEN,
                "-resizeable",
                "-noreset",
                "-nolisten",
                "tcp",
                "-ac",
            ],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    pidfile.write_text(str(proc.pid))
    for _ in range(100):
        if proc.poll() is not None:
            raise RuntimeError("Xephyr exited; inspect " + str(STATE / "xephyr.log"))
        if socket.exists():
            return
        time.sleep(0.1)
    raise RuntimeError("Xephyr socket did not appear")


def seed_cached_model():
    lock = json.loads((ROOT / 'sources/model.json').read_text())
    cached = BUILD / 'models' / lock['name']
    if not cached.is_file():
        return
    digest = hashlib.sha256()
    with cached.open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            digest.update(chunk)
    if 'sha256:' + digest.hexdigest() != lock['checksum']:
        raise RuntimeError('Cached model checksum mismatch')
    target = '/var/lib/logos/models/default.gguf'
    exists = subprocess.run(['lxc', 'exec', NAME, '--', 'test', '-e', target], capture_output=True)
    if exists.returncode == 0:
        return  # logos-model verifies the installed file below.
    if exists.returncode != 1:
        raise RuntimeError('Cannot inspect container model path')
    guest('install', '-d', '-m', '755', '/var/lib/logos/models')
    part = target + '.preseed-' + str(os.getpid())
    try:
        lxc('file', 'push', str(cached), NAME + part, timeout=300)
        guest('chmod', '0644', part)
        guest('mv', '-n', part, target)
    finally:
        guest('rm', '-f', part, check=False)


def start():
    gpu()
    owned()
    configure_gpu()
    configure_x11()
    c = config()
    if c["status"] != "Running":
        lxc("start", NAME, timeout=120)
    xephyr()
    guest("ldconfig")
    state = guest("systemctl", "is-system-running", "--wait", check=False, timeout=90)
    if state != "running":
        failures = guest("systemctl", "--failed", "--no-legend", "--plain", check=False)
        raise RuntimeError(
            "systemd " + state + "; unreviewed failed units:\n" + failures
        )
    guest(
        "/usr/lib/systemd/systemd-networkd-wait-online",
        "--interface=eth0",
        "--ipv4",
        "--timeout=60",
        timeout=70,
    )
    guest("ip", "-4", "addr", "show", "dev", "eth0")
    guest("ip", "route", "get", "1.1.1.1")
    gateway = json.loads(guest("ip", "-j", "route", "show", "default"))[0]["gateway"]
    guest("ping", "-c", "1", "-W", "3", gateway)
    guest("getent", "ahosts", "www.linuxfromscratch.org")
    guest("nvidia-smi")
    print(guest("/usr/libexec/logos/cuda-test"))
    # Starting the terminal does not wait for AI loading; Bash is immediately usable.
    guest("systemctl", "stop", "logos-terminal", check=False)
    guest(
        "systemd-run",
        "--unit=logos-terminal",
        "--collect",
        "--uid=logos",
        "--gid=logos",
        "--setenv=HOME=/home/logos",
        "--setenv=DISPLAY=" + DISPLAY,
        "/usr/bin/logos-session",
    )
    seed_cached_model()
    guest("logos-model", "install-default", timeout=1800)
    guest("systemctl", "start", "logos-ai")
    for _ in range(180):
        result = subprocess.run(
            [
                "lxc",
                "exec",
                NAME,
                "--",
                "systemctl",
                "is-active",
                "--quiet",
                "logos-ai",
            ],
            capture_output=True,
        )
        if result.returncode == 0:
            probe = subprocess.run(
                [
                    "lxc",
                    "exec",
                    NAME,
                    "--",
                    "python3",
                    "-c",
                    'from logos_ai.config import read_config; from logos_ai.inference import Client; Client(read_config()).request("/health",timeout=2)',
                ],
                capture_output=True,
            )
            if probe.returncode == 0:
                break
        time.sleep(1)
    health_check()


def health_check():
    c = owned()
    if c["status"] != "Running":
        raise RuntimeError("LXD container FAIL: stopped")
    print("LXD container             PASS")
    result = subprocess.run(
        [
            "lxc",
            "exec",
            NAME,
            "--",
            "env",
            "DISPLAY=" + DISPLAY,
            "/usr/libexec/logos/health",
        ],
        text=True,
        timeout=300,
    )
    if result.returncode:
        raise RuntimeError("Health checks failed; see results above")


def stop():
    owned()
    lxc("stop", NAME, timeout=120)
    pidfile = STATE / ("xephyr-" + DISPLAY[1:] + ".pid")
    if pidfile.exists():
        pid = int(pidfile.read_text())
        try:
            args = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
            if DISPLAY.encode() in args and any(x.endswith(b"Xephyr") for x in args):
                os.kill(pid, 15)
        except (FileNotFoundError, ProcessLookupError):
            pass
        pidfile.unlink()


def status():
    c = owned()
    print("LogOS Developer Preview 0.1")
    print(
        "Container:",
        c["status"],
        "\nDisplay:",
        c["expanded_config"].get("environment.DISPLAY", "unset"),
    )
    for key in ["limits.cpu", "limits.memory"]:
        print(key + ":", c["expanded_config"].get(key, "unlimited"))
    if c["status"] == "Running":
        for label, args in [
            (
                "GPU",
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,utilization.gpu",
                    "--format=csv,noheader",
                ],
            ),
            ("CUDA toolkit", ["/opt/cuda-12.9/bin/nvcc", "--version"]),
            (
                "llama.cpp",
                ["systemctl", "show", "logos-ai", "-p", "ActiveState", "-p", "MainPID"],
            ),
            ("AI settings", ["cat", "/etc/logos/logos.conf"]),
            (
                "GPU layers (observed)",
                ["journalctl", "-u", "logos-ai", "-b", "--no-pager", "-n", "80"],
            ),
            ("AI Terminal", ["systemctl", "is-active", "logos-terminal"]),
        ]:
            print("\n" + label + ":\n" + guest(*args, check=False))
        print(
            "X11:",
            guest("env", "DISPLAY=" + DISPLAY, "xdpyinfo", check=False)[:200]
            or "UNAVAILABLE",
        )


def main():
    action = sys.argv[1]
    if action == "import":
        image_import()
    elif action == "create":
        create()
    elif action == "start":
        start()
    elif action == "stop":
        stop()
    elif action == "status":
        status()
    elif action == "health":
        health_check()
    elif action == "shell":
        owned()
        os.execvp("lxc", ["lxc", "exec", NAME, "--", "su", "-", "logos"])
    elif action == "destroy":
        owned()
        if sys.argv[2:] != ["--yes"]:
            raise RuntimeError(
                "Destructive: use destroy-container.sh --yes to delete this LogOS container and its data"
            )
        lxc("delete", NAME, "--force", timeout=300)
    else:
        raise RuntimeError("Unknown action")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as e:
        print("ERROR:", e, file=sys.stderr)
        if isinstance(e, subprocess.CalledProcessError):
            print(e.stderr or e.stdout, file=sys.stderr)
        sys.exit(1)
