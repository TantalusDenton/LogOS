import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('host_control', ROOT / 'host/control.py')
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)

class ModelCache(unittest.TestCase):
    def setUp(self):
        (ROOT / '.work/test-temp').mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.work/test-temp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'sources').mkdir()
        (self.root / 'models').mkdir()
        (self.root / 'sources/model.json').write_text(json.dumps({
            'name':'model.gguf', 'checksum':'sha256:' + hashlib.sha256(b'model').hexdigest()}))
        self.cached = self.root / 'models/model.gguf'
        self.cached.write_bytes(b'model')
        p = patch.multiple(host, ROOT=self.root, BUILD=self.root)
        p.start()
        self.addCleanup(p.stop)

    def test_bad_cache_never_reaches_container(self):
        self.cached.write_bytes(b'corrupt')
        with patch.object(host, 'lxc') as lxc, patch.object(host, 'guest') as guest:
            with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
                host.seed_cached_model()
            lxc.assert_not_called()
            guest.assert_not_called()

    def test_existing_model_is_not_overwritten(self):
        with patch.object(host.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)), patch.object(host, 'lxc') as lxc:
            host.seed_cached_model()
            lxc.assert_not_called()

    def test_push_failure_cleans_partial_file(self):
        with patch.object(host.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)), patch.object(host, 'lxc', side_effect=RuntimeError('push failed')), patch.object(host, 'guest') as guest:
            with self.assertRaisesRegex(RuntimeError, 'push failed'):
                host.seed_cached_model()
            self.assertEqual(guest.call_args.args[:2], ('rm', '-f'))
            self.assertIn('.preseed-', guest.call_args.args[2])

if __name__ == '__main__':
    unittest.main()
