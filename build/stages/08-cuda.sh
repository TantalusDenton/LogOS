#!/bin/bash
source "$(dirname "$0")/../lib/common.sh"
source "$REPO/build/lib/package.sh"
# Inspect first, but source-built userspace preparation does not need the GPU.
# Actual computation below remains mandatory before this stage can complete.
nvidia-smi || echo 'Host NVIDIA is unavailable; preparing toolkit only, then requiring GPU verification.'
inputs=$(sha256sum "$0" "$REPO/build/install-cuda.py" "$REPO/build/cuda-test.cu" "$REPO/sources/ai.json" | sha256sum | cut -d' ' -f1)
prepared="$LOGOS_BUILD/state/cuda-userspace.prepared"
if [[ ! -f $prepared || $(cat "$prepared") != "$inputs" ]]; then
python3 "$REPO/build/fetch.py" --group ai
python3 "$REPO/build/install-cuda.py"
in_root /bin/bash -e <<'INNER'
python3 - <<'PY'
from pathlib import Path
import re

p = Path('/opt/cuda-12.9/include/crt/math_functions.h')
s = p.read_text()
for name, typ in (
    ('cospi', 'double'), ('sinpi', 'double'),
    ('cospif', 'float'), ('sinpif', 'float'),
    ('rsqrt', 'double'), ('rsqrtf', 'float'),
):
    pat = rf'(\b{name}\s*\({typ}\s+x\))\s*;'
    s, n = re.subn(pat, r'\1 noexcept(true);', s, count=1)
    if n != 1:
        raise SystemExit(f'CUDA math declaration not patched exactly once: {name} ({n})')
p.write_text(s)
PY
cd /sources/gcc-14.3.0
if [[ ! -x /opt/gcc-14/bin/g++ ]]; then
  case $(uname -m) in x86_64) sed -i.orig '/m64=/s/lib64/lib/' gcc/config/i386/t-linux64;; esac
  mkdir -p build
  cd build
  ../configure --prefix=/opt/gcc-14 --disable-multilib --with-system-zlib --enable-default-pie --enable-default-ssp --enable-host-pie --disable-fixincludes --disable-libsanitizer --enable-languages=c,c++
  make
  ulimit -s -H unlimited
  chown -R tester .
  if [[ ${LOGOS_FULL_GCC_CHECK:-0} == 1 ]]; then
    su tester -c "PATH=$PATH make -k check"
  else
    echo 'GCC compatibility suite already completed; skipping repeated sanitizer/plugin matrix (set LOGOS_FULL_GCC_CHECK=1 to rerun).'
  fi
  ../contrib/test_summary
  make install
else
  echo 'Reusing previously installed GCC 14.3.0 compatibility compiler.'
fi
# NVCC uses the source-built compatibility compiler; final OS remains GCC 16.
install -d /usr/libexec/logos
/opt/cuda-12.9/bin/nvcc -ccbin /opt/gcc-14/bin/g++ -arch=sm_52 -L/opt/cuda-12.9/lib /logos-build/build/cuda-test.cu -o /usr/libexec/logos/cuda-test
printf '/opt/cuda-12.9/lib\n' > /etc/ld.so.conf.d/cuda.conf
ldconfig
INNER
printf 'CUDA toolkit\t12.9.1\tNVIDIA redistributable components only\nGCC CUDA host compiler\t14.3.0\t/opt/gcc-14\n' >> "$LOGOS_BUILD/artifacts/package-manifest.txt"
printf '%s\n' "$inputs" > "$prepared"
fi
nvidia-smi || fail 'CUDA userspace prepared, but host NVIDIA driver/library mismatch blocks actual GPU computation. No driver changes were made.'
"$REPO/host/verify-build-cuda.sh"
