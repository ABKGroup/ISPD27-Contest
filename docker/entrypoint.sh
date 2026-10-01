#!/bin/bash

source /opt/miniconda3/etc/profile.d/conda.sh

export PATH="/opt/oss-cad-suite/bin:/install/OpenROAD/bin":$PATH
export YOSYS_EXE=/opt/oss-cad-suite/bin/yosys
export OPENROAD_EXE=/OpenROAD/build/bin/openroad

cat /etc/motd

export PS1="\[\e]0;\u@\h: \w\a\]${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$"

bash -i <<< "source /opt/miniconda3/etc/profile.d/conda.sh && conda activate base && echo 'Ready.'; exec </dev/tty"
