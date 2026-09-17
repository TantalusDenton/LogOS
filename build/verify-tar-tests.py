#!/usr/bin/env python3
"""Accept only the observed getcap display change, not lost capabilities."""
from pathlib import Path
import re
import sys


def verify(directory, started):
    summary = Path(directory) / 'tests/testsuite.log'
    if summary.stat().st_mtime < started:
        raise ValueError('Stale Tar test summary')
    text = summary.read_text()
    if 'ERROR: 224 tests were run,\n1 failed unexpectedly.\n20 tests were skipped.' not in text:
        raise ValueError('Unexpected Tar test totals')
    failed = re.findall(r'^\d+\. .*: FAILED .*$', text, re.M)
    if failed != ['233. capabs_raw01.at:25: 233. capabilities: binary store/restore (capabs_raw01.at:25): FAILED (capabs_raw01.at:28)']:
        raise ValueError('Unexpected failed Tar test')
    section = text.split('## Detailed failed tests. ##', 1)[1].split('## ------------- ##', 1)[0]
    changes = [line for line in section.splitlines() if line.startswith(('-', '+')) and not line.startswith(('---', '+++'))]
    if changes != ['-dir/file = cap_chown=ei', '+dir/file cap_chown=ei']:
        raise ValueError('Tar capability diagnostic differs from getcap formatting change')
    print('KNOWN TEST COMPATIBILITY FAILURE (not PASS): Tar restored cap_chown=ei; getcap omits the legacy equals separator')
    print('Reference: https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/tar.html')

if __name__ == '__main__':
    verify(sys.argv[1], int(sys.argv[2]))
