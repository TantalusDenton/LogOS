#!/usr/bin/env python3
"""Fetch locked upstream inputs; never accept a checksum computed from an untrusted download."""
import argparse, hashlib, json, os, pathlib, shutil, sys, urllib.request, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = pathlib.Path(__file__).resolve().parents[1]


def verify(path, spec):
    algorithm, expected = spec.split(":", 1)
    if algorithm == "git":
        subprocess.run(
            ["git", "--git-dir=" + str(path), "fsck", "--full"],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        actual = subprocess.check_output(
            ["git", "--git-dir=" + str(path), "rev-parse", "HEAD"], text=True
        ).strip()
        if actual != expected:
            raise ValueError("Git commit mismatch")
        return
    h = (
        hashlib.sha1(("blob " + str(path.stat().st_size) + "\0").encode())
        if algorithm == "git-blob"
        else hashlib.new(algorithm)
    )
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    if h.hexdigest() != expected:
        raise ValueError(f"CHECKSUM MISMATCH: {path}")


def fetch(item, cache):
    path = cache / item["name"]
    if path.exists():
        verify(path, item["checksum"])
        return path
    if item["checksum"].startswith("git:"):
        commit = item["checksum"].split(":")[1]
        part = path.with_name(path.name + ".part")
        if part.exists():
            shutil.rmtree(part)
        subprocess.run(
            ["git", "init", "--bare", str(part)], check=True, stdout=subprocess.DEVNULL
        )
        subprocess.run(
            [
                "git",
                "--git-dir=" + str(part),
                "fetch",
                "--depth=1",
                item["url"],
                commit,
            ],
            check=True,
        )
        subprocess.run(
            ["git", "--git-dir=" + str(part), "update-ref", "HEAD", commit], check=True
        )
        verify(part, item["checksum"])
        os.replace(part, path)
        return path
    part = path.with_name(path.name + ".part")
    req = urllib.request.Request(
        item["url"], headers={"User-Agent": "LogOS/0.1 source builder"}
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as src, open(part, "wb") as dst:
            reserve = int(os.environ.get("RESERVE_GIB", "20")) * 1024**3
            while chunk := src.read(1024 * 1024):
                if shutil.disk_usage(cache).free < reserve + len(chunk):
                    raise OSError("Source download would exhaust workspace reserve")
                dst.write(chunk)
        verify(part, item["checksum"])
        os.replace(part, path)
    except BaseException:
        part.unlink(missing_ok=True)
        raise
    return path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--group", choices=["all", "lfs", "blfs", "ai"], default="all")
    p.add_argument("--verify-only", action="store_true")
    a = p.parse_args()
    build = pathlib.Path(os.environ.get("LOGOS_BUILD", "/srv/logos"))
    cache = build / "sources"
    cache.mkdir(parents=True, exist_ok=True)
    (build / "artifacts").mkdir(exist_ok=True)
    items = []
    for name in ["lfs", "blfs", "ai"] if a.group == "all" else [a.group]:
        items += json.loads((ROOT / "sources" / f"{name}.json").read_text())
    errors = []

    def obtain(item):
        print(("VERIFY " if a.verify_only else "SOURCE ") + item["name"], flush=True)
        if a.verify_only:
            verify(cache / item["name"], item["checksum"])
        else:
            fetch(item, cache)

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(obtain, item): item for item in items}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as error:
                errors.append(futures[future]["name"] + ": " + str(error))
    # Even an incomplete download batch leaves a manifest of verified inputs.
    # Manifest lists only verified, present sources, including previously cached groups.
    lines = ["package/version\tURL\tchecksum\tlicense"]
    for name in ["lfs", "blfs", "ai"]:
        for item in json.loads((ROOT / "sources" / f"{name}.json").read_text()):
            if (cache / item["name"]).exists():
                verify(cache / item["name"], item["checksum"])
                lines.append(
                    "\t".join(
                        [
                            item["name"],
                            item["url"],
                            item["checksum"],
                            item.get("license", "See upstream source"),
                        ]
                    )
                )
    model = json.loads((ROOT / 'sources/model.json').read_text())
    model_path = build / 'models' / model['name']
    if model_path.is_file():
        verify(model_path, model['checksum'])
        lines.append('\t'.join([model['name'], model['url'], model['checksum'], model['license']]))
    (build / "artifacts/source-manifest.txt").write_text("\n".join(lines) + "\n")
    if errors:
        raise RuntimeError("Source download failures:\n" + "\n".join(errors))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
