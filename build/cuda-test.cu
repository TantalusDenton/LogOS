#include <cuda_runtime.h>
#include <cstdio>
#include <cstring>
#define CUDA(x) do { cudaError_t e=(x); if(e!=cudaSuccess){std::fprintf(stderr,"%s: %s\n",#x,cudaGetErrorString(e));return 1;} } while(0)
__global__ void compute(int *out) { const int i=threadIdx.x; out[i]=i*i+17; }
int main() {
 int count=0;CUDA(cudaGetDeviceCount(&count));if(count<1)return 2;
 CUDA(cudaSetDevice(0));cudaDeviceProp p{};CUDA(cudaGetDeviceProperties(&p,0));
 if(!std::strstr(p.name,"Quadro M2000")||p.major!=5||p.minor!=2){std::fprintf(stderr,"Unexpected GPU: %s cc %d.%d\n",p.name,p.major,p.minor);return 3;}
 int *dev=nullptr;int result[128];CUDA(cudaMalloc(&dev,sizeof(result)));
 compute<<<1,128>>>(dev);CUDA(cudaGetLastError());CUDA(cudaDeviceSynchronize());
 CUDA(cudaMemcpy(result,dev,sizeof(result),cudaMemcpyDeviceToHost));CUDA(cudaFree(dev));
 for(int i=0;i<128;i++)if(result[i]!=i*i+17)return 4;
 std::printf("CUDA compute PASS: %s, cc %d.%d, VRAM %zu MiB, runtime %d\n",p.name,p.major,p.minor,p.totalGlobalMem/1048576,CUDART_VERSION);
 return 0;
}
