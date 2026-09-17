#!/bin/bash
source "$(dirname "$0")/lib/common.sh"
space_check "$RESERVE_GIB"
workspace
exec 9>"$LOGOS_BUILD/state/model.lock"
flock -n 9 || fail 'Another model download is running'
python3 - "$REPO" "$LOGOS_BUILD" <<'PY'
import json, pathlib, sys
repo, build = map(pathlib.Path, sys.argv[1:])
sys.path.insert(0, str(repo / 'build'))
from fetch import fetch
item = json.loads((repo / 'sources/model.json').read_text())
cache = build / 'models'
cache.mkdir(exist_ok=True)
path = fetch(item, cache)
(build / 'artifacts/model-manifest.txt').write_text(
    '\t'.join([item['name'], item['url'], item['checksum'], item['license']]) + '\n')
print('Verified default model:', path)
PY
