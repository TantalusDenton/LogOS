#!/usr/bin/env python3
"""Accept only the diagnosed LFS 13.1 lchmod chroot test exception."""
from pathlib import Path
import sys


def verify(summary, started):
    summary = Path(summary)
    if summary.stat().st_mtime < started:
        raise ValueError('Test summary is stale; make check did not finish')
    lines = summary.read_text().splitlines()
    bad = [line for line in lines if line.startswith(('FAIL:', 'XPASS:', 'ERROR:'))]
    if bad != ['FAIL: io/tst-lchmod'] or sum(s.startswith('PASS:') for s in lines) < 6000:
        raise ValueError('Unexpected/incomplete glibc test results: ' + repr(bad))
    output = (summary.parent / 'io/tst-lchmod.out').read_text()
    if 'error: descriptor 1 changed from "/sources/' not in output or 'error: 1 test failures' not in output:
        raise ValueError('lchmod failure differs from the diagnosed chroot path change')
    print('KNOWN LFS CHROOT FAILURE (not PASS): io/tst-lchmod; descriptor path changes after leaving chroot')
    print('Reference: https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/glibc.html')


if __name__ == '__main__':
    verify(sys.argv[1], int(sys.argv[2]))
