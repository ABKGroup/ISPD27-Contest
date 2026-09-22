#!/usr/bin/env bash
# Usage: bash 02_evaluate_post_grt.sh [aes|jpeg|DESIGN] [RUN_DIR] [SCENARIO ...]
# Default: recommended scenario, Resizer off AND on, BC/TC/WC.
# Overrides: RESIZER=off|on|both, INPUT_DEF, INPUT_VERILOG, DESIGN_NAME,
#            SCENARIO_DIR, NUM_CORES. Use 'all' for all saved design scenarios.
set -euo pipefail
FLOW_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$FLOW_ROOT/scripts/environment.bash"
flow_environment "$FLOW_ROOT/02_evaluate_post_grt.sh" "$@"
exec "$PYTHON_EXE" "$FLOW_ROOT/scripts/run_flow.py" evaluate "$@"
