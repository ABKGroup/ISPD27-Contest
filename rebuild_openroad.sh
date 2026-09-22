#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
contest="$(cd -- "$root/.." && pwd)"
if [[ ! -d /.singularity.d && -z "${SINGULARITY_CONTAINER:-}${APPTAINER_CONTAINER:-}" ]]; then
    exec singularity exec -B /home -B /tmp -e /home/tool/singularity/images/ispd26.sif bash "$0" "$@"
fi
source "$contest/openroad_env_singularity.sh"
engine="$contest/OpenROAD-flow-scripts/tools/OpenROAD"
patch="$root/patches/openroad-spef-pin-wire-cap.patch"
if git -C "$engine" apply --reverse --check "$patch" 2>/dev/null; then
    echo 'SPEF pin-node wire-capacitance patch is already applied.'
else
    git -C "$engine" apply --check "$patch"
    git -C "$engine" apply "$patch"
fi
cmake --build "$engine/build" --target openroad --parallel "${1:-16}"
cmake --install "$engine/build"
