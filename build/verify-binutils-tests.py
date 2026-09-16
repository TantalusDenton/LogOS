#!/usr/bin/env python3
"""Account for the diagnosed gprofng exception documented by LFS 13.1."""
from pathlib import Path
import sys


def verify(directory, started, status):
    directory = Path(directory)
    required = {'binutils/binutils.sum', 'libsframe/libsframe.sum',
                'gas/testsuite/gas.sum', 'gprofng/gprofng.sum',
                'libctf/libctf.sum', 'ld/ld.sum'}
    summaries = {str(p.relative_to(directory)): p for p in directory.rglob('*.sum')}
    if not required <= summaries.keys():
        raise ValueError('Incomplete Binutils test suite')
    failures = []
    for name, path in summaries.items():
        text = path.read_text()
        if path.stat().st_mtime < started or 'Summary ===' not in text or '# of expected passes' not in text:
            raise ValueError('Stale/incomplete test summary: ' + name)
        failures += [(name, line) for line in text.splitlines()
                     if line.startswith(('FAIL:', 'XPASS:', 'ERROR:'))]
    if not failures and status == 0:
        return
    log = (directory / 'gprofng/gprofng.log').read_text()
    if failures != [('gprofng/gprofng.sum', 'FAIL: tmpdir/gp-gmon')] or 'No calltree for ' not in log:
        raise ValueError('Unexpected Binutils test failure: ' + repr(failures))
    print('KNOWN LFS FAILURE (not PASS): gprofng tmpdir/gp-gmon, missing calltree')
    print('Reference: https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/binutils.html')


if __name__ == '__main__':
    verify(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
