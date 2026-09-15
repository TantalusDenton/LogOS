#!/bin/bash
source "$(dirname "$0")/../lib/common.sh"
source "$REPO/build/lib/package.sh"
# Check the host before downloading/installing CUDA userspace components.
nvidia-smi || fail 'Host NVIDIA driver/library mismatch or GPU failure; no driver changes were made.'
python3 "$REPO/build/fetch.py" --group ai
python3 "$REPO/build/install-cuda.py"
in_root /bin/bash -e <<'INNER'
cd /sources/gcc-14.3.0
case $(uname -m) in x86_64) sed -i.orig '/m64=/s/lib64/lib/' gcc/config/i386/t-linux64;; esac
mkdir -p build
cd build
../configure --prefix=/opt/gcc-14 --disable-multilib --with-system-zlib --enable-default-pie --enable-default-ssp --enable-host-pie --disable-fixincludes --enable-languages=c,c++
make
make -k check
../contrib/test_summary
make install
# NVCC uses the source-built compatibility compiler; final OS remains GCC 16.
install -d /usr/libexec/logos
/opt/cuda-12.9/bin/nvcc -ccbin /opt/gcc-14/bin/g++ -arch=sm_52 /logos-build/build/cuda-test.cu -o /usr/libexec/logos/cuda-test
printf '/opt/cuda-12.9/lib\n' > /etc/ld.so.conf.d/cuda.conf
ldconfig
INNER
"$REPO/host/verify-build-cuda.sh"
printf 'CUDA toolkit\t12.9.1\tNVIDIA redistributable components only\nGCC CUDA host compiler\t14.3.0\t/opt/gcc-14\n' >> "$LOGOS_BUILD/artifacts/package-manifest.txt"
