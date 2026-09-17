#!/usr/bin/env python3
"""Record only Groff's documented pre-install neqn smoke-test failure."""
from pathlib import Path
import re
import sys


def verify(directory, started):
    directory = Path(directory)
    summary = directory / 'test-suite.log'
    if summary.stat().st_mtime < started:
        raise ValueError('Stale Groff test summary')
    text = summary.read_text()
    stats = {k: int(v) for k, v in re.findall(r'^# (\w+):\s+(\d+)$', text, re.M)}
    if stats != {'TOTAL':316, 'PASS':298, 'SKIP':13, 'XFAIL':4, 'FAIL':1, 'XPASS':0, 'ERROR':0}:
        raise ValueError('Unexpected Groff test results: ' + repr(stats))
    test = 'src/preproc/eqn/tests/neqn-smoke-test.sh'
    if re.findall(r'^(?:FAIL|ERROR|XPASS): (.+)$', text, re.M) != [test]:
        raise ValueError('Unexpected failing Groff test')
    diagnostic = (directory / (test + '.log')).read_text().strip()
    expected = '/sources/groff-1.24.1/neqn: line 59: exec: eqn: not found\n\nFAIL ' + test + ' (exit status: 1)'
    if diagnostic != expected:
        raise ValueError('Different Groff smoke-test failure')
    print('KNOWN LFS FAILURE (not PASS): neqn-smoke-test.sh; eqn not installed yet')
    print('Reference: https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/groff.html')

if __name__ == '__main__':
    verify(sys.argv[1], int(sys.argv[2]))
