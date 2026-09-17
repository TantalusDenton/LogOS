#!/bin/bash
source "$(dirname "$0")/../lib/common.sh"
source "$REPO/build/lib/package.sh"
[[ -f $LOGOS_BUILD/state/cuda-compute.pass ]] || fail 'Actual CUDA computation must pass before building llama.cpp'
commit=$(python3 -c 'import json,sys; print(next(x["checksum"].split(":")[1] for x in json.load(open(sys.argv[1])) if x["name"]=="llama.cpp.git"))' "$REPO/sources/ai.json")
mkdir -p "$LOGOS_BUILD/work/llama.cpp"
git --git-dir="$LOGOS_BUILD/sources/llama.cpp.git" archive "$commit" | tar -x -C "$LOGOS_BUILD/work/llama.cpp"
in_root /bin/bash -e <<'INNER'
export PATH=/opt/cuda-12.9/bin:/usr/bin:/usr/sbin
cd /sources/llama.cpp
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr \
 -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=52 \
 -DCMAKE_CUDA_HOST_COMPILER=/opt/gcc-14/bin/g++ \
 -DCMAKE_C_COMPILER=/opt/gcc-14/bin/gcc -DCMAKE_CXX_COMPILER=/opt/gcc-14/bin/g++ \
 -DGGML_NATIVE=OFF -DGGML_CUDA_GRAPHS=OFF -DLLAMA_OPENSSL=OFF \
 -DLLAMA_SUBPROCESS=OFF -DLLAMA_BUILD_APP=OFF -DLLAMA_BUILD_EXAMPLES=OFF \
 -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF \
 -DLLAMA_BUILD_TESTS=ON -DLLAMA_BUILD_SERVER=ON
cmake --build build --parallel "$CMAKE_BUILD_PARALLEL_LEVEL"
ctest --test-dir build --output-on-failure
cmake --install build
ldconfig
/usr/bin/llama-server --version
INNER
printf 'llama.cpp\t%s\tCUDA=ON architectures=52\n' "$commit" >> "$LOGOS_BUILD/artifacts/package-manifest.txt"
