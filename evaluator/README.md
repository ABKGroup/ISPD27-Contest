# Evaluation and scoring

The evaluator checks a legalized DEF/Verilog pair and measures design quality
using global routing and setup/hold timing analysis at BC, TC, and WC. It does
not run OpenROAD Resizer.

**Current scores use dummy weights. Final weights will be announced after the
Alpha submission. Setup TNS and WNS have equal weights.**

## Choose a workflow

| Command | Purpose |
| --- | --- |
| `evaluator/run_submission.py` | Run a submission, measure runtime, and evaluate the outputs. |
| `evaluator/score.py` | Compute the score from evaluation results and runtime. |
| `evaluator/eval.sh` | Evaluate existing DEF/Verilog outputs without running or timing the submission. |

For normal scoring, run `run_submission.py` first and then `score.py`.

Use `eval.sh` to evaluate existing DEF/Verilog files without running the
submission tool.


<!-- 
## Requirements

- Python 3.9+ and compatible OpenROAD and Kepler Formal executables on `PATH`.
  See [tool versions](../public/ISPD27-Contest/evaluator/config/tool_versions.json).
- A legalized `.def` and matching `.v` produced by your tool.
- The supplied clock tree, official timing constraints, libraries, and RC
  settings must remain unchanged.

Run all commands below from the contest repository root: the directory containing
`evaluator/`, `benchmarks/`, and `platform/`. -->

## Run your tool and score

### 1. Run the submitted tool

```bash
python3 evaluator/run_submission.py aes /tmp/aes-run -- bash /path/to/run.sh
```

Everything after `--` is
the command used to launch the submitted tool.

The launcher creates `/tmp/aes-run` to store the results. The directory must not already exist.

The launcher calls `run.sh` with four positional arguments:

```bash
bash /path/to/run.sh <input_dir> <platform_dir> <output_dir> <top_module>
```

| Argument | Meaning | Value for this AES run |
| --- | --- | --- |
| `$1` | Benchmark input directory | `<repository>/benchmarks/aes` |
| `$2` | Technology platform directory | `<repository>/platform/asap7` |
| `$3` | Tool output directory | `/tmp/aes-run/tool` |
| `$4` | Top-level Verilog module | `aes_cipher_top` |

Directory arguments are absolute paths. The top module is read from
`benchmarks/<design_name>/benchmark.json`.

The submitted tool must produce:
```text
/tmp/aes-run/tool/aes.def
/tmp/aes-run/tool/aes.v
```

Use the design name (`aes` or `jpeg`) for output filenames, **not** the top-module
name. The launcher also sets the following environment variables:

| Variable | Meaning |
| --- | --- |
| `INPUT_DEF`, `INPUT_VERILOG` | Paths to the supplied input files |
| `OUTPUT_DEF`, `OUTPUT_VERILOG` | Required output file paths |
| `BENCHMARK_DIR` | Benchmark input directory |
| `MCMM_CONFIG` | Benchmark timing configuration  |
| `PLATFORM_DIR` | Technology platform directory |

After the submitted tool finishes running, the launcher automatically validates and evaluates its
outputs. Results are saved in `/tmp/aes-run/evaluation/`.

- **Tool runtime:** time spent running the submitted tool.
- **Total-flow runtime:** time spent running the tool, validation, and evaluation.

The limit for both is five hours. Unchanged baseline submissions are rejected.

### 2. Calculate the score

After the run completes successfully:

```bash
python3 evaluator/score.py \
  --baseline evaluator/reference_results/aes/baseline.csv \
  --candidate /tmp/aes-run/evaluation/summary.csv \
  --reference evaluator/reference_results/aes/resizer.csv \
  --runtimes /tmp/aes-run/evaluation/runtimes.json \
  --output /tmp/aes-run/evaluation/score.json
```

The command prints the score and writes the score breakdown to `score.json`. **Higher scores
are better.** 

Normal scoring requires passed legality checks, runtime measurements from `run_submission.py`, and validated output files that have not changed after evaluation. See
[scoring configuration](../public/ISPD27-Contest/evaluator/config/scoring_config.json)
for the current weights and tolerances.

For manual experiments, `--allow-unverified` can be used to compute an **unverified dummy score**
without legality/runtime certification. A runtime JSON file is still required.

For JPEG, replace `aes` with `jpeg` in the commands and paths above. The launcher
reads the JPEG top-module name automatically.

## Evaluate existing output files

To evaluate an existing DEF/Verilog pair:

```bash
bash evaluator/eval.sh aes /tmp/aes-evaluation \
  --def /path/to/submission.def \
  --verilog /path/to/submission.v
```

The output directory must not already exist. Replace `aes` with
`jpeg` for JPEG.

`eval.sh` runs legality checks and reports design-quality metrics. It does not run
the submission tool, measure tool runtime, or calculate a score. 

To evaluate the supplied unoptimized baseline:

```bash
bash evaluator/eval.sh aes /tmp/aes-baseline-evaluation
```

## Evaluation Results


| Output | Contents |
| --- | --- |
| `summary.csv` | Timing, power, electrical rule violations (ERC), routing overflow, and displacement. WNS/TNS use ns; raw timing and slew-violation sums use ps. |
| `final_timing/` | Final timing reports from a fresh SPEF reload. |
| `evaluation.log` | Evaluator log. |
| `evaluation_runtime.json` | Evaluator wall time. |
| `legality.json` | Final legality result. `complete_contest_legality` is true after all evaluator legality checks pass. |
| `structural_validation.json`, `final_structural_validation.json`, `submission_validation.json` | Detailed validation reports. |
| `EVALUATION_COMPLETE` | Marker for successful evaluation. |
| `runtimes.json` | Candidate and reference runtimes used by scoring. |
| `score.json` | Score and score breakdown. |


## Legality checks

<!-- Checks cover the fixed floorplan, I/O, PDN, blockages, protected cells, clock tree
and clock sinks, permitted transformations, formal
equivalence, and package integrity.

Data repeater changes must preserve polarity. Other gate changes are limited to
approved sizing/VT variants and equivalent-pin swaps. Failed checks prevent
normal scoring. -->
The evaluator checks that the submitted design follows the contest rules,
including:

- The die/core area, I/O locations, PDN,
and placement blockages must not be changed.

- Protected cells, the clock tree, and
clock sinks must remain unchanged.

- All movable cells must be legally placed inside the placement
region, aligned to valid sites/rows, and must not overlap other cells or
blocked regions.

- The physical design in the DEF and the netlist in
the Verilog must describe the same cells and connectivity.

- The submitted netlist must preserve the logic
function of the original design.

- Data-path buffers/inverters may be added, removed,
or replaced only if the signal polarity is preserved. Other cells may only be
changed to approved sizing/VT variants or through equivalent-pin swaps.

- All required output files must be present, and files
provided by the contest must not be modified.

A submission that fails any required legality check cannot receive a normal
score.

## Supplied reference results

The scoring script compares each submitted result against a set of reference
results provided with the contest. These reference results are used to normalize
the scoring metrics and runtime.

Reference files for each design are stored under: `evaluator/reference_results/<design_name>/`

| File | Purpose |
| --- | --- |
| `baseline.csv` | Results from the released unoptimized design. Used to normalize setup timing, power, and ERC. |
| `resizer.csv` | Results from the OpenROAD Resizer reference run. Used to normalize displacement. |
| `runtimes.json` | Recorded runtimes of the reference runs. Used for runtime normalization. |


## Evaluator directory guide

| Location | Purpose |
| --- | --- |
| `eval.sh`, `run_submission.py`, `score.py` | Main scripts for evaluation, runtime measurement, and scoring. |
| `config/` | Scoring parameters, tool versions, and evaluator configuration files. |
| `internal/` | Internal scripts for legality checks, timing analysis, and metric calculation. |
| `reference_results/` | Contest-provided baseline and OpenROAD Resizer reference results used for scoring. |
| `third_party/displacement/` | Reused ISPD26 displacement helper and related files. |
| `tests/` | Evaluator regression tests. |


