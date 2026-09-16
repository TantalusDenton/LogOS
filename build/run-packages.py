#!/usr/bin/env python3
"""Run pinned book recipes in book order; package markers bind to recipe+source."""
import hashlib, json, os, pathlib, shutil, subprocess, sys, tarfile, time
from fetch import verify

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD = pathlib.Path(os.environ["LOGOS_BUILD"])
LFS = BUILD / "rootfs"


def call(args, **kw):
    subprocess.run(args, check=True, **kw)


def save_test_results(package_dir, package_id):
    target = BUILD / 'logs' / 'tests' / package_id
    for path in package_dir.rglob('*'):
        if not path.is_file() or not (path.suffix == '.sum' or path.name in
                ('test-suite.log', 'testlog.txt', 'LastTest.log')):
            continue
        dest = target / path.relative_to(package_dir)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        if path.name == 'tests.sum':
            for line in path.read_text().splitlines():
                if line.startswith(('FAIL:', 'XPASS:', 'ERROR:')):
                    name = line.split(':', 1)[1].strip() + '.out'
                    src = path.parent / name
                    if src.is_file() and '..' not in pathlib.PurePosixPath(name).parts:
                        out = dest.parent / name
                        out.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, out)


def chroot(args):
    return [
        "chroot",
        str(LFS),
        "/usr/bin/env",
        "-i",
        "HOME=/root",
        "TERM=xterm",
        "PATH=/usr/bin:/usr/sbin",
        "LC_ALL=POSIX",
        "MAKEFLAGS=-j" + os.environ.get("JOBS", "8"),
        "NINJAJOBS=" + os.environ.get("JOBS", "8"),
        *args,
    ]


def main(stage):
    items = {
        p["name"]: p
        for group in ["lfs", "blfs", "ai"]
        for p in json.loads((ROOT / "sources" / f"{group}.json").read_text())
    }
    plans = sum(
        [
            json.loads((ROOT / "build" / f"{name}-plan.json").read_text())
            for name in ["lfs", "blfs"]
        ],
        [],
    )
    state = BUILD / "state/packages"
    state.mkdir(exist_ok=True)
    work = BUILD / "work"
    # All supplemental patches/tarballs are alongside extracted directories as in the books.
    for item in items.values():
        source = BUILD / "sources" / item["name"]
        if not source.is_file():
            continue
        dest = work / item["name"]
        if not dest.exists():
            os.link(source, dest)
    for p in plans:
        if p["stage"] != stage:
            continue
        source = p["source"]
        recipe = ROOT / p["recipe"]
        fingerprint = hashlib.sha256(
            recipe.read_bytes() + json.dumps(items.get(source), sort_keys=True).encode()
        ).hexdigest()
        marker = state / (p["id"] + ".done")
        if marker.exists():
            if marker.read_text().strip() != fingerprint:
                raise RuntimeError(
                    "Completed package changed: "
                    + p["id"]
                    + "; rebuild in a new workspace"
                )
            print("CACHED", p["id"], flush=True)
            continue
        if (
            shutil.disk_usage(BUILD).free
            < int(os.environ.get("RESERVE_GIB", "20")) * 1024**3
        ):
            raise RuntimeError("Disk reserve reached")
        package_dir = work
        if source:
            verify(BUILD / "sources" / source, items[source]["checksum"])
            with tarfile.open(BUILD / "sources" / source) as tar:
                roots = set()
                for member in tar.getmembers():
                    name = pathlib.PurePosixPath(member.name)
                    if name.is_absolute() or ".." in name.parts:
                        raise RuntimeError("Unsafe archive member: " + member.name)
                    if name.parts:
                        roots.add(name.parts[0])
                if len(roots) != 1 or roots.intersection({"", ".", ".."}):
                    raise RuntimeError(
                        "Archive must have one source directory: " + source
                    )
                package_dir = work / roots.pop()
            if package_dir.exists():
                shutil.rmtree(package_dir)
            call(
                [
                    "tar",
                    "--no-same-owner",
                    "-xf",
                    str(BUILD / "sources" / source),
                    "-C",
                    str(work),
                ]
            )
        cross = stage in ("01-toolchain", "02-temporary-system")
        if cross:
            call(
                ["chown", "-R", "logos-lfs:logos-lfs", str(package_dir)]
                if source
                else ["true"]
            )
            env = [
                "HOME=" + str(BUILD / "lfs-home"),
                "LC_ALL=POSIX",
                "LFS=" + str(LFS),
                "LFS_TGT=x86_64-lfs-linux-gnu",
                "CONFIG_SITE=" + str(LFS) + "/usr/share/config.site",
                "PATH=" + str(LFS) + "/tools/bin:/usr/bin:/bin",
                "MAKEFLAGS=-j" + os.environ.get("JOBS", "8"),
            ]
            # Exact LFS environment; /bin/sh and awk are validated before reaching here.
            args = [
                "runuser",
                "-u",
                "logos-lfs",
                "--",
                "env",
                "-i",
                *env,
                "bash",
                "--noprofile",
                "--norc",
                str(recipe),
            ]
        else:
            inside = (
                "/sources"
                if package_dir == work
                else "/sources/" + str(package_dir.relative_to(work))
            )
            args = chroot(
                [
                    "/bin/bash",
                    "-c",
                    'cd "$1"; exec /bin/bash "$2"',
                    "logos",
                    inside,
                    "/logos-build/" + p["recipe"],
                ]
            )
        print("BUILD", p["id"], flush=True)
        start = time.time()
        try:
            call(args, cwd=package_dir)
        except BaseException:
            with open(BUILD / "state/history.tsv", "a") as f:
                f.write(f'{time.time()}\t{p["id"]}\tFAILED\n')
            raise
        finally:
            if source:
                save_test_results(package_dir, p['id'])
        marker.write_text(fingerprint + "\n")
        with open(BUILD / "state/history.tsv", "a") as f:
            f.write(f'{time.time()}\t{p["id"]}\tPASS\t{time.time()-start:.0f}s\n')
        if source:
            with open(BUILD / "artifacts/package-manifest.txt", "a") as f:
                f.write(p["id"] + "\t" + source + "\t" + p["book_url"] + "\n")
            shutil.rmtree(package_dir)


if __name__ == "__main__":
    main(sys.argv[1])
