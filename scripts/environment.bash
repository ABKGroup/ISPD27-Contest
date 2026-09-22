# Shared environment setup for the two public entry points.
flow_environment() {
    local script="$1"
    shift
    if [[ ! -d /.singularity.d && -z "${SINGULARITY_CONTAINER:-}${APPTAINER_CONTAINER:-}" ]]; then
        local key
        local -a forwarded=()
        for key in SOURCE_NETLIST GEN_SDC DESIGN_CONFIG DESIGN_NAME UTIL CLOCK_PERIOD_PS \
            PLACE_DENSITY NUM_CORES RESIZER INPUT_DEF INPUT_VERILOG SCENARIO_DIR \
            ORFS ENV_SCRIPT PLATFORM_DIR RSZ_MAX_ITERATIONS RSZ_TNS_PERCENT \
            RSZ_SETUP_SEQUENCE SIGNAL_LAYERS CLOCK_LAYERS ROUTE_ADJUSTMENT \
            ROUTE_ITERATIONS ROUTE_SEED; do
            if [[ -v "$key" ]]; then forwarded+=("$key=${!key}"); fi
        done
        exec singularity exec -B /home -B /tmp -e \
            "${CONTAINER_IMAGE:-/home/tool/singularity/images/ispd26.sif}" \
            env "${forwarded[@]}" bash "$script" "$@"
    fi
    source "${ENV_SCRIPT:-$FLOW_ROOT/../openroad_env_singularity.sh}"
    export LD_LIBRARY_PATH="$(dirname "$KEPLER_FORMAL_EXE")/../lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    export PYTHONDONTWRITEBYTECODE=1
}
