#!/usr/bin/env python3
"""Audit explicit repairs without accepting stale completed package recipes."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(os.environ['LOGOS_BUILD'])
STATE = BUILD / 'state'


def snapshot():
    return {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for directory in ('build', 'sources', 'rootfs-overlay', 'logos-ai/logos_ai')
        for p in (ROOT / directory).rglob('*')
        if p.is_file() and p.suffix != '.pyc'
    }


def audit(old, new):
    changed = sorted(k for k in old.keys() | new.keys() if old.get(k) != new.get(k))
    completed = {p.stem for p in STATE.glob('*.done')}
    items = {p['name']: p for group in ('lfs', 'blfs', 'ai')
             for p in json.loads((ROOT / 'sources' / (group + '.json')).read_text())}
    plans = sum([json.loads((ROOT / 'build' / (group + '-plan.json')).read_text())
                 for group in ('lfs', 'blfs')], [])
    for p in plans:
        marker = STATE / 'packages' / (p['id'] + '.done')
        if marker.exists():
            fingerprint_inputs = (ROOT / p['recipe']).read_bytes()
            if p['id'] == 'chapter08-systemd':
                fingerprint_inputs += (ROOT / 'build/patches/systemd-userns-map-skip.patch').read_bytes()
            digest = hashlib.sha256(
                fingerprint_inputs
                + json.dumps(items.get(p['source']), sort_keys=True).encode()
            ).hexdigest()
            if marker.read_text().strip() != digest:
                raise RuntimeError('Completed package input changed: ' + p['id'])
    for name in changed:
        # Plans, source locks and completed stage scripts cannot be waived.
        if (name.startswith('sources/') or name.endswith('-plan.json')) and completed:
            raise RuntimeError('Completed build provenance changed: ' + name)
        if name.startswith('build/stages/') and Path(name).stem in completed:
            raise RuntimeError('Completed stage changed: ' + name)
        if name.startswith('rootfs-overlay/') and completed & {'04-systemd', '10-logos'}:
            raise RuntimeError('Installed overlay changed: ' + name)
        if name.startswith('logos-ai/') and '10-logos' in completed:
            raise RuntimeError('Installed AI client changed: ' + name)
        if name in ('build/install-cuda.py', 'build/cuda-test.cu') and '08-cuda' in completed:
            raise RuntimeError('Installed CUDA inputs changed: ' + name)
    return changed


if __name__ == '__main__':
    path = STATE / 'build-inputs.json'
    current = snapshot()
    if sys.argv[1:] == ['--accept']:
        if not path.is_file():
            raise SystemExit('No previous input snapshot; cannot safely accept changes')
        changed = audit(json.loads(path.read_text()), current)
        with (STATE / 'history.tsv').open('a') as f:
            f.write(f'{time.time()}\tINPUT-REPAIR\tREVIEWED\t' + ', '.join(changed) + '\n')
        print('Reviewed repair:', ', '.join(changed))
    elif sys.argv[1:] == ['--snapshot']:
        path.write_text(json.dumps(current, sort_keys=True, indent=2) + '\n')
    else:
        raise SystemExit('Usage: check-resume.py --accept|--snapshot')
