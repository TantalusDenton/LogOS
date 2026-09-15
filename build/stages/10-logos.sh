#!/bin/bash
source "$(dirname "$0")/../lib/common.sh"
source "$REPO/build/lib/package.sh"
cp -a "$REPO/rootfs-overlay/." "$LFS/"
in_root /bin/bash -e <<'INNER'
getent group logos >/dev/null || groupadd -g 1000 logos
id logos >/dev/null 2>&1 || useradd -m -u 1000 -g logos -G video -s /bin/bash logos
getent group logos-ai >/dev/null || groupadd -r logos-ai
id logos-ai >/dev/null 2>&1 || useradd -r -g logos-ai -G video -d /var/lib/logos -s /usr/bin/false logos-ai
passwd -l logos
install -d -m 755 /var/lib/logos/models /usr/libexec/logos
python3 - <<'PYTHON'
import shutil,sysconfig
shutil.copytree('/logos-build/logos-ai/logos_ai',sysconfig.get_path('purelib')+'/logos_ai',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
PYTHON
chmod 755 /usr/bin/logos-* /usr/libexec/logos/*
systemctl enable logos-ai.service
userdel -r tester
INNER
cp "$REPO/sources/model.json" "$LFS/etc/logos/model.json"
python3 "$REPO/build/validate-rootfs.py"

printf 'LogOS software\t0.1\tLogOS repository\n' >> "$LOGOS_BUILD/artifacts/package-manifest.txt"
