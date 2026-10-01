# Packages

apt-get -y update
apt-get -y install git build-essential gcc g++ wget make time x11-apps vim nano sxiv python3-pip
pip install pyaml

mkdir -p /opt/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /opt/miniconda3/miniconda.sh
bash /opt/miniconda3/miniconda.sh -b -u -p /opt/miniconda3

cd opt
    wget  "https://www.klayout.org/downloads/Ubuntu-24/klayout_0.30.12-1_amd64.deb" -O klayout.deb

apt-get -y install ./klayout.deb

wget https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-09-29/oss-cad-suite-linux-x64-20260929.tgz -O oss-cad-suite.tgz
tar -xvzf oss-cad-suite.tgz
rm oss-cad-suite.tgz

apt update
apt install g++ libboost-dev python3.9-dev capnproto libcapnp-dev libtbb-dev pkg-config bison flex doxygen libspdlog-dev libfmt-dev libboost-iostreams-dev zlib1g-dev

git clone --recurse-submodules https://github.com/keplertech/kepler-formal.git
cd kepler-formal
mkdir build
cd build
cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_STANDARD=20 \
  -DCMAKE_CXX_FLAGS="-O3 -flto -DNDEBUG" \
  -DCMAKE_CXX_FLAGS_RELEASE="-O3  -flto -DNDEBUG" \
  -DCMAKE_EXE_LINKER_FLAGS="-flto"
make -j
make -j install




# GitHub CLI

(type -p wget >/dev/null || ( apt update &&  apt-get install wget -y)) \
	&&  mkdir -p -m 755 /etc/apt/keyrings \
        && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        && cat $out |  tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
	&&  chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
	&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" |  tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
	&&  apt update \
	&&  apt install gh -y

# OpenROAD

cd /
git clone https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git
cd OpenROAD-flow-scripts
git reset --hard a12d46907510891a2e3d3310abdd19975d28db0e

cd /
git clone https://github.com/The-OpenROAD-Project/OpenROAD.git
cd OpenROAD
git reset --hard  8443f6ff398e3c4e06cb65a05a0abf22734ad345
git submodule update --init --recursive
