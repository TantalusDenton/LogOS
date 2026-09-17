import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'build' / filename)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(os.environ, {'LOGOS_BUILD': str(ROOT / '.work/test-temp')}):
        spec.loader.exec_module(module)
    return module

resume = load('resume', 'check-resume.py')
glibc = load('glibc', 'verify-glibc-tests.py')
binutils = load('binutils', 'verify-binutils-tests.py')
acl = load('acl', 'verify-acl-tests.py')

class Recovery(unittest.TestCase):
    def setUp(self):
        (ROOT / '.work/test-temp').mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / '.work/test-temp')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'state/packages').mkdir(parents=True)
        (self.root / 'sources').mkdir()
        (self.root / 'build').mkdir()
        for group in ('lfs', 'blfs', 'ai'):
            (self.root / 'sources' / (group + '.json')).write_text('[]')
        for group in ('lfs', 'blfs'):
            (self.root / 'build' / (group + '-plan.json')).write_text('[]')
        self.patch = patch.multiple(resume, ROOT=self.root, STATE=self.root / 'state')
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_runner_repair_allowed_but_completed_inputs_protected(self):
        (self.root / 'state/01-toolchain.done').touch()
        self.assertEqual(resume.audit({'build/run-packages.py':'a'}, {'build/run-packages.py':'b'}), ['build/run-packages.py'])
        for name in ('sources/lfs.json', 'build/lfs-plan.json', 'build/stages/01-toolchain.sh'):
            with self.assertRaises(RuntimeError):
                resume.audit({name:'a'}, {name:'b'})

    def test_completed_recipe_cannot_be_waived(self):
        recipe = self.root / 'build/example.sh'
        recipe.write_text('original')
        package = {'id':'example', 'source':None, 'recipe':'build/example.sh'}
        (self.root / 'build/lfs-plan.json').write_text(json.dumps([package]))
        (self.root / 'state/packages/example.done').write_text(hashlib.sha256(b'originalnull').hexdigest())
        recipe.write_text('changed')
        with self.assertRaisesRegex(RuntimeError, 'Completed package'):
            resume.audit({}, {})

    def test_installed_overlay_cannot_be_waived(self):
        (self.root / 'state/04-systemd.done').touch()
        with self.assertRaises(RuntimeError):
            resume.audit({}, {'rootfs-overlay/etc/os-release':'new'})

    def summary(self, extra=''):
        path = self.root / 'tests.sum'
        path.write_text(''.join(f'PASS: test-{i}\n' for i in range(6001)) + 'FAIL: io/tst-lchmod\n' + extra)
        (self.root / 'io').mkdir(exist_ok=True)
        (self.root / 'io/tst-lchmod.out').write_text('error: descriptor 1 changed from "/sources/x" to "/host/x"\nerror: 1 test failures\n')
        return path

    def test_only_diagnosed_glibc_failure_allowed(self):
        glibc.verify(self.summary(), 0)
        with self.assertRaises(ValueError):
            glibc.verify(self.summary('FAIL: elf/surprise\n'), 0)
        with self.assertRaises(ValueError):
            glibc.verify(self.summary(), 99999999999)
        p = self.summary()
        (self.root / 'io/tst-lchmod.out').write_text('segmentation fault')
        with self.assertRaises(ValueError):
            glibc.verify(p, 0)

    def test_binutils_rejects_additional_failures_and_stale_suites(self):
        suites = ('binutils/binutils.sum', 'libsframe/libsframe.sum',
                  'gas/testsuite/gas.sum', 'gprofng/gprofng.sum',
                  'libctf/libctf.sum', 'ld/ld.sum')
        for name in suites:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('PASS: example\n=== test Summary ===\n# of expected passes 1\n')
        (self.root / 'gprofng/gprofng.sum').write_text('FAIL: tmpdir/gp-gmon\n=== gprofng Summary ===\n# of expected passes 5\n')
        (self.root / 'gprofng/gprofng.log').write_text('No calltree for test\n')
        binutils.verify(self.root, 0, 2)
        with self.assertRaises(ValueError):
            binutils.verify(self.root, 99999999999, 2)
        with (self.root / 'ld/ld.sum').open('a') as f:
            f.write('FAIL: unexpected linker defect\n')
        with self.assertRaises(ValueError):
            binutils.verify(self.root, 0, 2)

    def test_acl_accepts_only_cp_preservation_failure(self):
        (self.root / 'test').mkdir()
        summary = self.root / 'test-suite.log'
        original = '# TOTAL: 16\n# PASS: 13\n# SKIP: 0\n# XFAIL: 2\n# FAIL: 1\n# XPASS: 0\n# ERROR: 0\nFAIL: test/cp\n'
        summary.write_text(original)
        (self.root / 'test/cp.log').write_text('cp -p f g -- ok\n22 commands (20 passed, 2 failed)\n')
        acl.verify(self.root, 0)
        with self.assertRaises(ValueError):
            acl.verify(self.root, 99999999999)
        summary.write_text(original.replace('FAIL: test/cp', 'FAIL: test/root/permissions'))
        with self.assertRaises(ValueError):
            acl.verify(self.root, 0)

if __name__ == '__main__':
    unittest.main()
