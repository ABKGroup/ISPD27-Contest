#!/usr/bin/env bash
# Internal stage runner. Official run/design settings are supplied by run.py.
set -euo pipefail
EVAL_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$EVAL_ROOT/../.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1
: "${SCENARIO_DIR:?Select a new experiment scenario directory}"
: "${OUTPUT_DIR:?Select a fresh experiment output directory}"
export SCENARIO_DIR
: "${BENCHMARK:?run.py supplies the benchmark name}"
: "${DESIGN_NAME:?run.py supplies the top module}"
: "${INPUT_DEF:?run.py supplies the DEF}"
: "${INPUT_VERILOG:?run.py supplies the Verilog}"
: "${SDC_FILE:?run.py supplies the SDC}"
export BENCHMARK DESIGN_NAME INPUT_DEF INPUT_VERILOG SDC_FILE OUTPUT_DIR
export REPAIR_KIND="${REPAIR_KIND:-both}"
export RUN_RESIZER="${RUN_RESIZER:-0}"
export PLATFORM_DIR="${PLATFORM_DIR:-$REPO_ROOT/platform/asap7}"
export CORNERS="${CORNERS:-TC BC WC}"
export LIBRARY_CORNERS="${LIBRARY_CORNERS:-TC BC WC}"
export SCENES="${SCENES:-$CORNERS}"
export NUM_CORES="${NUM_CORES:-8}"
export SIGNAL_LAYERS="${SIGNAL_LAYERS:-M2-M7}"
export CLOCK_LAYERS="${CLOCK_LAYERS:-M4-M7}"
export ROUTE_ADJUSTMENT="${ROUTE_ADJUSTMENT:-0.25}"
export ROUTE_ITERATIONS="${ROUTE_ITERATIONS:-30}"
export ROUTE_SEED="${ROUTE_SEED:-42}"
export RSZ_MAX_ITERATIONS="${RSZ_MAX_ITERATIONS:-500}"
export RSZ_TNS_PERCENT="${RSZ_TNS_PERCENT:-100}"
export RSZ_SETUP_SEQUENCE="${RSZ_SETUP_SEQUENCE:-vt_swap sizeup swap buffer}"
export PHASE="${PHASE:-full}"
export VERIFY_FORMAL="${VERIFY_FORMAL:-1}"
export OPENROAD_EXE="${OPENROAD_EXE:-$(command -v openroad)}"
export KEPLER_FORMAL_EXE="${KEPLER_FORMAL_EXE:-$(command -v kepler-formal)}"
[[ "$RUN_RESIZER" == 0 || "$RUN_RESIZER" == 1 ]]
# Never overwrite an existing run directory.
if [[ -e "$OUTPUT_DIR" ]]; then
    echo "Refusing to overwrite existing OUTPUT_DIR: $OUTPUT_DIR" >&2
    exit 2
fi
mkdir -p "$OUTPUT_DIR"
python3 "$EVAL_ROOT/audit.py" config
if [[ "$PHASE" == full ]]; then
    PHASE=baseline_snapshot "$OPENROAD_EXE" -no_init -no_splash -exit "$EVAL_ROOT/evaluation.tcl" > "$OUTPUT_DIR/baseline_snapshot.log" 2>&1
fi
PHASE=verilog_check "$OPENROAD_EXE" -no_init -no_splash -exit "$EVAL_ROOT/evaluation.tcl" > "$OUTPUT_DIR/verilog_check.log" 2>&1
"$OPENROAD_EXE" -no_init -no_splash -exit "$EVAL_ROOT/evaluation.tcl" 2>&1 | tee "$OUTPUT_DIR/evaluation.log"
python3 "$EVAL_ROOT/audit.py" finish
# Evaluate final MCMM on a clean timing state after physical optimization/routing.
if [[ "$PHASE" == full ]]; then
    python3 "$EVAL_ROOT/refresh_timing.py" "$OUTPUT_DIR"
fi
