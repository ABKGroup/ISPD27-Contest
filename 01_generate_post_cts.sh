#!/usr/bin/env bash
# Usage: bash 01_generate_post_cts.sh [aes|jpeg|DESIGN] [RUN_DIR]
# Overrides: SOURCE_NETLIST, GEN_SDC, DESIGN_CONFIG, DESIGN_NAME,
#            UTIL, CLOCK_PERIOD_PS, PLACE_DENSITY, NUM_CORES.
set -euo pipefail
FLOW_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$FLOW_ROOT/scripts/environment.bash"
flow_environment "$FLOW_ROOT/01_generate_post_cts.sh" "$@"
exec "$PYTHON_EXE" "$FLOW_ROOT/scripts/run_flow.py" generate "$@"
