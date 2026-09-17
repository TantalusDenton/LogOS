#!/usr/bin/env python3
"""LFS's temporary Coreutils cannot yet preserve ACLs with cp -p."""
from pathlib import Path
import re
import sys


def verify(directory, started):
    directory = Path(directory)
    summary = directory / 'test-suite.log'
    if summary.stat().st_mtime < started:
        raise ValueError('Stale ACL test summary')
    text = summary.read_text()
    stats = {k: int(v) for k, v in re.findall(r'^# (\w+):\s+(\d+)$', text, re.M)}
    if stats != {'TOTAL': 16, 'PASS': 13, 'SKIP': 0, 'XFAIL': 2, 'FAIL': 1, 'XPASS': 0, 'ERROR': 0}:
        raise ValueError('Unexpected ACL test results: ' + repr(stats))
    if re.findall(r'^FAIL: (.+)$', text, re.M) != ['test/cp']:
        raise ValueError('Unexpected failing ACL test')
    cp = (directory / 'test/cp.log').read_text()
    if '22 commands (20 passed, 2 failed)' not in cp or 'cp -p f g -- ok' not in cp:
        raise ValueError('ACL cp failure differs from the diagnosed preservation failure')
    print('KNOWN LFS FAILURE (not PASS): test/cp; temporary Coreutils lacks ACL support')
    print('Reference: https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/acl.html')


if __name__ == '__main__':
    verify(sys.argv[1], int(sys.argv[2]))
