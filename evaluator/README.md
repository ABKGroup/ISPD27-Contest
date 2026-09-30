# Evaluation

Evaluate a legalized DEF/Verilog pair using global routing and setup/hold timing analysis at BC, TC and WC. The evaluator does not run OpenROAD Resizer.

**Scoring currently uses dummy weights. Final weights will be announced after the
Alpha submission. Setup TNS and WNS have equal weights.**

## Requirements

- Provide the legalized `.def` and matching `.v` produced by your tool.
- Keep the supplied clock tree and official timing constraints unchanged.
- Use Python 3.9+ and compatible OpenROAD/Kepler Formal executables on PATH.
  See [tool_versions.json](config/tool_versions.json) for tool versions.

## Evaluate

From the repository root:

```bash
bash evaluator/eval.sh aes /tmp/aes-evaluation \
  --def /path/to/submission.def --verilog /path/to/submission.v
```

Replace `aes` with `jpeg` for JPEG. Always choose a new output directory.
Omit `--def` and `--verilog` to evaluate the supplied unoptimized baseline.
The released inputs retain their existing data buffers and functional inverters.

## Run your tool and score

To measure tool and total-flow runtime:

```bash
python3 evaluator/run_submission.py aes /tmp/aes-run -- bash /path/to/run.sh
```

The launcher appends four arguments to your command:

```bash
run.sh <input_dir> <platform_dir> <output_dir> <top_module>
```

Write `<output_dir>/<design_name>.def` and `<output_dir>/<design_name>.v`,
where `design_name` is `aes` or `jpeg` (not the top-module name).
For the AES command above, outputs are `/tmp/aes-run/tool/aes.def` and `aes.v`;
the top module is read from `benchmarks/aes/benchmark.json`.
The launcher also supplies `INPUT_DEF`, `INPUT_VERILOG`, `OUTPUT_DEF`,
`OUTPUT_VERILOG`, `BENCHMARK_DIR`, `MCMM_CONFIG`, and `PLATFORM_DIR`.
Each tool/total-flow time limit is five hours; unchanged baseline submissions
are rejected. Evaluation outputs are saved in `/tmp/aes-run/evaluation/`.

```bash
python3 evaluator/score.py \
  --baseline evaluator/reference_results/aes/baseline.csv \
  --candidate /tmp/aes-run/evaluation/summary.csv \
  --reference evaluator/reference_results/aes/resizer.csv \
  --runtimes /tmp/aes-run/evaluation/runtimes.json \
  --output /tmp/aes-run/evaluation/score.json
```

Higher scores are better. The output file must be new. Scoring requires passed
legality checks, measured runtimes, and unchanged validated artifacts. For manual
experiments, `--allow-unverified` permits an **unverified dummy score** with a supplied
runtime JSON. Weights and tolerances are in [config/scoring_config.json](config/scoring_config.json).

## Supplied reference results

| Design | Baseline | Resizer reference | Runtime |
| --- | --- | --- | --- |
| AES | [baseline.csv](reference_results/aes/baseline.csv) | [resizer.csv](reference_results/aes/resizer.csv) | [runtimes.json](reference_results/aes/runtimes.json) |
| JPEG | [baseline.csv](reference_results/jpeg/baseline.csv) | [resizer.csv](reference_results/jpeg/resizer.csv) | [runtimes.json](reference_results/jpeg/runtimes.json)|

These are recorded results for the released inputs, not outputs of your
current run. The baseline normalizes setup timing, power, and ERC; the Resizer
reference normalizes displacement and runtime.Reference runtimes depend on the host.
<!--
Displacement is the average Manhattan movement of **surviving original movable
cells**. Clock cells/sinks, fixed cells, macros, and physical-only cells are excluded.
Inserted and removed cells are excluded; `matched_logic_cells` reports the number
of eligible surviving cells. Eligibility comes from the original benchmark.
Reference displacement values use the same definition, re-extracted from saved
snapshots; the recorded physical runs and runtimes are unchanged.
-->


## Outputs and legality

- `summary.csv`: per-corner timing, power, ERC, routing overflow, and displacement.
  WNS/TNS are in **ns**; raw timing and slew-violation sums use **ps**.
- `final_timing/`: final timing reports from a fresh SPEF reload.
- `evaluation.log`, `evaluation_runtime.json`: logs and evaluator wall time.
- `legality.json`: final validation record; `complete_contest_legality` is true
  after all evaluator legality checks pass. Detailed reports are in
  `structural_validation.json`, `final_structural_validation.json`, and `submission_validation.json`.
- `EVALUATION_COMPLETE`: successful evaluation. Measured tool runtime and scoring
  are separate; the launcher also writes `runtimes.json` and `SUBMISSION_COMPLETE`.

Checks cover fixed floorplan/I/O/PDN/blockages, protected cells, clock-tree and sink
integrity, permitted transformations, placement, DEF/Verilog consistency, formal
equivalence, and package integrity. Data repeater changes must preserve polarity;
other gate changes are limited to approved sizing/VT variants and equivalent-pin
swaps. Official timing constraints, libraries, and RC settings remain fixed.
Failed checks prevent normal scoring.

## Directory guide

| Location | Purpose |
| --- | --- |
| `eval.sh`, `run_submission.py`, `score.py` | The three public commands. |
| `config/` | Scoring policy, tool versions, and package integrity manifest. |
| `internal/` | Evaluation, timing, legality, and metric implementation. |
| `reference_results/` | Supplied baseline and Resizer measurements. |
| `third_party/displacement/` | Reused ISPD26 displacement helper, cell groups, and license. |
| `tests/` | Evaluator regression tests. |

New evaluation outputs go to the directory you specify, outside these supplied files.
