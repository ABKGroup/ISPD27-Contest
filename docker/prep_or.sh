source /opt/miniconda3/etc/profile.d/conda.sh && conda activate base
cd /OpenROAD
./etc/DependencyInstaller.sh -bazel
./etc/DependencyInstaller.sh -all
./etc/Build.sh
bazelisk build //python/openroad:openroad_wheel
pip install $(bazelisk info bazel-bin)/python/openroad/openroad-0.0.1-cp310-abi3-linux_x86_64.whl

