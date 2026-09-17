#!/usr/bin/env python3
"""Accept only the LFS 13.1 documented Greek-locale regex fastmap failure."""
from pathlib import Path
import re
import sys


def verify(directory, started):
    directory = Path(directory)
    for name in ('lib/test-suite.log', 'gnulib-tests/test-suite.log', 'tests/test-suite.log',
                 'find/testsuite/find.sum', 'locate/testsuite/locate.sum', 'xargs/testsuite/xargs.sum'):
        path = directory / name
        if path.stat().st_mtime < started:
            raise ValueError('Stale Findutils test results: ' + name)
        text = path.read_text()
        failures = re.findall(r'^(?:FAIL|XPASS|ERROR): (.+)$', text, re.M)
        expected = ['test-regex-el'] if name.startswith('gnulib-tests/') else []
        if failures != expected:
            raise ValueError('Unexpected Findutils failures: ' + name + repr(failures))
        if name.endswith('.sum'):
            if not re.search(r'# of expected passes\s+[1-9]\d*', text):
                raise ValueError('Incomplete DejaGNU summary: ' + name)
        else:
            stats = dict((k, int(v)) for k, v in re.findall(r'^# (\w+):\s+(\d+)$', text, re.M))
            if (stats.get('FAIL') != len(expected) or stats.get('XPASS') != 0
                    or stats.get('ERROR') != 0 or stats.get('PASS', 0) < 1
                    or stats.get('TOTAL') != sum(stats.get(k, 0) for k in ('PASS','SKIP','XFAIL','FAIL','XPASS','ERROR'))):
                raise ValueError('Incomplete/unexpected Automake summary: ' + name)
    diagnostic = (directory / 'gnulib-tests/test-regex-el.log').read_text().splitlines()
    expected = ['test-regex: fastmap mismatch: pattern = ' + chr(92) + value + r', string = \xf2, with = -1, without = 0'
                for value in ('xd3', 'xf2', 'xf3')]
    if diagnostic != expected + ['FAIL test-regex-el (exit status: 1)']:
        raise ValueError('Different regex failure diagnostic')
    print('KNOWN LFS FAILURE (not PASS): test-regex-el; Greek locale fastmap mismatch')
    print('Reference: https://www.linuxfromscratch.org/lfs/view/13.1-systemd/chapter08/findutils.html')

if __name__ == '__main__':
    verify(sys.argv[1], int(sys.argv[2]))
