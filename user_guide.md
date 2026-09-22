# Run the flow in two steps

Use this shared installation on the same server. Both scripts enter Singularity and set up the tools automatically. Give each new experiment a **fresh private workspace**.

```bash
FLOW=/home/memzfs_projects/ispd26_contest/ISPD27_CONTEST/yiting/mcmm_prototype
RUN="$HOME/ispd27_aes_run1"

# 1. Synthesized netlist → ORFS floorplan → placement → legalized CTS.
bash "$FLOW/01_generate_post_cts.sh" aes "$RUN"

# 2. Post-CTS → Resizer off/on → global routing → MCMM timing.
bash "$FLOW/02_evaluate_post_grt.sh" aes "$RUN"
```

For JPEG, use `jpeg` in both commands and a different workspace, e.g. `$HOME/ispd27_jpeg_run1`.

| Default | AES | JPEG |
| --- | --- | --- |
| Generation utilization | 50% | 65% |
| Generation clock period | 620 ps | 1100 ps |
| Placement density | 0.65 | 0.75 |
| Evaluation scenario | `aes_p55_h55` | `jpeg_p70_h35` |
| Evaluation periods BC / TC / WC | 248 / 308 / 429 ps | 518 / 700 / 980 ps |
| Hold uncertainty | 55 ps | 35 ps |

Setup uncertainty is 0 ps. Generation uses the TC libraries. Evaluation uses all three corners simultaneously and OpenSTA inside OpenROAD; it does not invoke ORFS.

## Where your outputs go

```text
$RUN/
├── generation/
│   ├── results/asap7/<design>/post_cts/  # All ORFS stage ODBs and SDCs
│   ├── logs/asap7/<design>/post_cts/
│   ├── reports/asap7/<design>/post_cts/
│   ├── objects/asap7/<design>/post_cts/
│   ├── benchmark/                       # input.def, input.v, input.odb
│   └── generation.log
└── evaluation/
    ├── <scenario>/
    │   ├── scenario/                    # Private copy of BC/TC/WC SDCs
    │   ├── off/                         # No Resizer; then GRT and timing
    │   └── both/                        # repair_design + setup/hold repair; then GRT and timing
    └── timing_summary.csv               # Setup/hold WNS and TNS in ns
```

Each evaluation branch has `routed.odb`, `route.guide`, three `parasitics_*.spef` files, `timing.csv` (**ps**), `metrics.json`, and `final_timing/`. `evaluated.def` and `evaluated.v` are the legalized outputs exported before GRT. Detailed routing is not run. Each step writes `SUCCESS` only after its checks pass. Existing step output directories are never overwritten.

## Change generation settings

```bash
UTIL=40 CLOCK_PERIOD_PS=700 PLACE_DENSITY=0.65 \
  bash "$FLOW/01_generate_post_cts.sh" aes "$HOME/aes_u40_p700"
bash "$FLOW/02_evaluate_post_grt.sh" aes "$HOME/aes_u40_p700"
```

Step 1 reuses the mapped netlist, runs ORFS through CTS with post-CTS timing repair disabled, exports legalized inputs, and checks formal equivalence. It edits only its private SDC copy. Changing the generation period does **not** change step 2's selected evaluation periods.

## Evaluate existing inputs or several SDC settings

You may skip step 1. If the workspace has no `generation/` directory, step 2 uses the shared AES/JPEG post-CTS benchmark. An incomplete generation run causes an error instead of falling back.

```bash
# Three SDC configurations, each evaluated with Resizer off and on.
bash "$FLOW/02_evaluate_post_grt.sh" aes "$HOME/aes_sdc_comparison1" \
  aes_p55_h50 aes_p55_h55 aes_p55_h60

# All saved JPEG configurations.
bash "$FLOW/02_evaluate_post_grt.sh" jpeg "$HOME/jpeg_sdc_comparison1" all
```

To run one branch only, prefix the command with `RESIZER=off` or `RESIZER=on`. Default `RESIZER=both` runs both branches. Use `NUM_CORES=8` to choose threads per process.

To change evaluation periods/uncertainty, copy a directory from `$FLOW/evaluation/difficulty_v2/scenarios/`, edit its `BC.sdc`, `TC.sdc`, and `WC.sdc`, and pass the copied directory as the scenario argument. Keep any SDC dependencies with it. The SDCs control timing; `config.json` is descriptive metadata. Supply several directories to compare several settings.

## Use another ASAP7 design

Provide its mapped netlist, ORFS design configuration, generation SDC, top module, and a directory containing complete `BC.sdc`, `TC.sdc`, and `WC.sdc` constraints:

```bash
SOURCE_NETLIST=/absolute/path/1_synth.v \
GEN_SDC=/absolute/path/generation.sdc \
DESIGN_CONFIG=/absolute/path/config.mk DESIGN_NAME=my_top \
UTIL=50 PLACE_DENSITY=0.65 \
  bash "$FLOW/01_generate_post_cts.sh" my_design "$HOME/my_design_run1"

DESIGN_NAME=my_top \
  bash "$FLOW/02_evaluate_post_grt.sh" my_design "$HOME/my_design_run1" \
  /absolute/path/my_scenarios
```

`CLOCK_PERIOD_PS` overrides a single `set clk_period VALUE` line; otherwise a custom design's generation SDC is used as supplied. Input paths for ORFS must not contain whitespace. This package supports the included ASAP7 standard cells; additional macros need corresponding physical, timing, and formal-model support.

For externally generated post-CTS inputs, set **both** `INPUT_DEF` and `INPUT_VERILOG` when invoking step 2.

## Where the shared difficulty_v2 data live

- **ORFS stages:** `$FLOW/generation/{results,logs,reports,objects}/asap7/aes/u50_p620/` and `.../jpeg/u65_p1100/`.
- **Published post-CTS inputs:** `$FLOW/generation/benchmarks/{aes,jpeg}/`.
- **Evaluation scenarios and results:** `$FLOW/evaluation/difficulty_v2/{scenarios,runs,logs}/`.
- **Results table:** [RESULTS.md](RESULTS.md) and [results_summary.csv](results_summary.csv).

The historical `calibration/` and `sweeps/` paths remain as compatibility links for saved configurations. Use `generation/` and `evaluation/` for navigation.
