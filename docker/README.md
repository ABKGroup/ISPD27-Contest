# ISPD27 Contest: Containers and Submission Information

## Container

The intention of this container is to provide a consistent interactive environment for development and evaluation. It is based on Ubuntu 24.04 and contains:
- OpenROAD - Binary installation with sources at `/OpenROAD` (Commit `8443f6f`).
- OpenROAD-Flow-Scripts (commit `a12d469`)
- Conda (Miniconda)
- Miscellaneous tools including Yosys and Kepler-formal.

See the [Dockerfile here](./dockerfile). A precompiled image can be retrieved from the Docker Hub [`udxs/ispd27:v2`](https://hub.docker.com/repository/docker/udxs/ispd27/tags/v2/sha256:44e13208c5fd225b5809b01d706e24a001f503387c142299c5426d8e124d6c2b). This image is also compatbile with Apptainer (formerly Singularity) - see below.

### Using Apptainer (Singularity)

For users with supercomputing environments, including contestants granted access to the Purdue Anvil system, it is possible to use Apptainer/Singularity instead of Docker. Unlike Docker, Apptainer (in `fakeroot` mode) will make your container directories read-only.

Thus, to support package installation, you need to create a writable "overlay" layer first, where Apptainer will store all changes. The process to do this and run the container is as follows:
```sh
# You only need to do this once but may create multiple overlays to represent multiple isolated instances.
# This example creates a 20 GB overlay but you may change this amount.
singularity overlay create --fakeroot -S -s 20480 my_overlay.img 

# For CPU only operation
singularity run -o my_overlay.img --fakeroot docker://udxs/ispd27:v2
# For CUDA-capable NVIDIA GPUs:
singularity run -o my_overlay.img --fakeroot --nv docker://udxs/ispd27:v2
```
