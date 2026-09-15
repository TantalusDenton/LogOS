# Locked source inputs

Archives live in `$LOGOS_BUILD/sources`, not Git. `lfs.json` and `blfs.json` retain the stable projects' source URLs and published checksums. The official LFS wget-list and md5sums are also stored verbatim. `ai.json` pins NVIDIA component SHA256 values, upstream GCC SHA512, and a llama.cpp Git commit. `model.json` pins one model and the upstream repository's SHA256.

`download-sources.sh` verifies cached inputs and fails on mismatch. Source/model updates require an explicit lock change and new build workspace. The model installer uses only this locked file; there is no search or selection of arbitrary model repositories at runtime.
