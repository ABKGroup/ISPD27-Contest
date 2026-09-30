# Evaluation and scoring

The evaluator checks a legalized DEF/Verilog pair and measures design quality
using global routing and setup/hold timing analysis at BC, TC, and WC. It does
not run OpenROAD Resizer.

**Current scores use dummy weights. Final weights will be announced after the
Alpha submission. Setup TNS and WNS have equal weights.**

## Choose a workflow

| Command | Purpose |
| --- | --- |
| `evaluator/eval.sh` | Evaluate existing DEF/Verilog files. Does not run or time your tool. |
| `evaluator/run_submission.py` | Run and time your tool, then automatically evaluate its outputs. |
| `evaluator/score.py` | Calculate a numerical score from evaluation results and runtimes. |

For a score with validated runtime measurements, run `run_submission.py` first,
then `score.py`. For design-quality checks on existing files, use `eval.sh`.

## Requirements

- Python 3.9+ and compatible OpenROAD and Kepler Formal executables on `PATH`.
  See [tool versions](../public/ISPD27-Contest/evaluator/config/tool_versions.json).
- A legalized `.def` and matching `.v` produced by your tool.
- The supplied clock tree, official timing constraints, libraries, and RC
  settings must remain unchanged.

Run all commands below from the contest repository root: the directory containing
`evaluator/`, `benchmarks/`, and `platform/`.

## Run your tool and score

### 1. Run your tool and evaluate its outputs

```bash
python3 evaluator/run_submission.py aes /tmp/aes-run -- bash /path/to/run.sh
```

Replace `/path/to/run.sh` with your own tool launcher. Everything after `--` is
the command used to start your tool.

The launcher creates `/tmp/aes-run` to store the results. **Do not create this
directory beforehand.** If it already exists, even if empty, use a different
name such as `/tmp/aes-run-2`.

Your script receives four positional arguments:

```bash
bash /path/to/run.sh <input_dir> <platform_dir> <output_dir> <top_module>
```

| Argument | Meaning | Value for this AES run |
| --- | --- | --- |
| `$1` | Benchmark input directory | `<repository>/benchmarks/aes` |
| `$2` | Technology platform directory | `<repository>/platform/asap7` |
| `$3` | Directory for your tool's output files | `/tmp/aes-run/tool` |
| `$4` | Top-level Verilog module | `aes_cipher_top` |

Directory arguments are absolute paths. The top module is read from
`benchmarks/<design_name>/benchmark.json`.

Your tool must write these two files before exiting successfully:

```text
/tmp/aes-run/tool/aes.def
/tmp/aes-run/tool/aes.v
```

Use the design name (`aes` or `jpeg`) for output filenames, **not** the top-module
name. The launcher also provides these environment variables:

| Variable | Meaning |
| --- | --- |
| `INPUT_DEF`, `INPUT_VERILOG` | Paths to the supplied input files |
| `OUTPUT_DEF`, `OUTPUT_VERILOG` | Required output file paths |
| `BENCHMARK_DIR` | Benchmark input directory |
| `MCMM_CONFIG` | Benchmark timing configuration file |
| `PLATFORM_DIR` | Technology platform directory |

After your tool finishes, the launcher automatically validates and evaluates its
outputs. Results are saved in `/tmp/aes-run/evaluation/`.

- **Tool runtime:** time spent running your command.
- **Total-flow runtime:** time spent running the tool, validation, and evaluation.

Both limits are five hours. Evaluation must finish within the remaining
total-flow time. Unchanged baseline submissions are rejected.

### 2. Calculate the score

After step 1 succeeds, run:

```bash
python3 evaluator/score.py \
  --baseline evaluator/reference_results/aes/baseline.csv \
  --candidate /tmp/aes-run/evaluation/summary.csv \
  --reference evaluator/reference_results/aes/resizer.csv \
  --runtimes /tmp/aes-run/evaluation/runtimes.json \
  --output /tmp/aes-run/evaluation/score.json
```

This prints the score and saves its breakdown to `score.json`. **Higher scores
are better.** The output file must not already exist.

Normal scoring requires passed legality checks, runtime measurements recorded by
the launcher, and validated artifacts that have not subsequently changed. See
[scoring configuration](../public/ISPD27-Contest/evaluator/config/scoring_config.json)
for weights and tolerances.

For manual experiments, `--allow-unverified` permits an **unverified dummy score**
without legality/runtime certification. A runtime JSON file is still required.

For JPEG, replace `aes` with `jpeg` in the commands and paths above. The launcher
reads the JPEG top-module name automatically.

## Evaluate existing output files

Use this command when your tool has already produced a DEF/Verilog pair:

```bash
bash evaluator/eval.sh aes /tmp/aes-evaluation \
  --def /path/to/submission.def \
  --verilog /path/to/submission.v
```

Choose an output directory that does not already exist. Replace `aes` with
`jpeg` for JPEG.

This runs legality checks and produces design-quality metrics. It does not run
your tool, record its runtime, or calculate a numerical score. For normal
scoring, use the two-step workflow above.

To evaluate the supplied unoptimized baseline, omit both file arguments:

```bash
bash evaluator/eval.sh aes /tmp/aes-baseline-evaluation
```

The released inputs retain their existing data buffers and functional inverters.

## Results

The following paths are relative to the evaluation directory: either the
directory passed to `eval.sh` or `<run_dir>/evaluation/` for the launcher.

| Output | Contents |
| --- | --- |
| `summary.csv` | Timing, power, electrical rule violations (ERC), routing overflow, and displacement. WNS/TNS use ns; raw timing and slew-violation sums use ps. |
| `final_timing/` | Final timing reports from a fresh SPEF reload. |
| `evaluation.log` | Evaluator log. |
| `evaluation_runtime.json` | Evaluator wall time. |
| `legality.json` | Final validation record; `complete_contest_legality` is true after all evaluator legality checks pass. |
| `structural_validation.json`, `final_structural_validation.json`, `submission_validation.json` | Detailed validation reports. |
| `EVALUATION_COMPLETE` | Marker indicating successful evaluation. |
| `runtimes.json` | Candidate and reference runtimes, written by the launcher for scoring. |
| `score.json` | Score and breakdown, written by the scoring command above. |

The launcher also writes `<run_dir>/tool.log` and, on success,
`<run_dir>/SUBMISSION_COMPLETE`. Successful evaluation alone does not mean a
score has been calculated.

## Legality checks

Checks cover the fixed floorplan, I/O, PDN, blockages, protected cells, clock tree
and sinks, permitted transformations, placement, DEF/Verilog consistency, formal
equivalence, and package integrity.

Data repeater changes must preserve polarity. Other gate changes are limited to
approved sizing/VT variants and equivalent-pin swaps. Failed checks prevent
normal scoring.

## Supplied reference results

Each design has recorded results under `evaluator/reference_results/<design_name>/`:

| File | Purpose |
| --- | --- |
| `baseline.csv` | Normalize setup timing, power, and ERC. |
| `resizer.csv` | Normalize displacement. |
| `runtimes.json` | Supply reference tool and total-flow runtimes. |

These files describe the released reference runs, not your current run. Reference
runtimes depend on the host. Use your run's `evaluation/runtimes.json` as the
`--runtimes` input when scoring your tool.

## Evaluator directory guide

| Location | Purpose |
| --- | --- |
| `eval.sh`, `run_submission.py`, `score.py` | Public commands. |
| `config/` | Scoring policy, tool versions, and package integrity manifest. |
| `internal/` | Evaluation, timing, legality, and metric implementation. |
| `reference_results/` | Supplied baseline and Resizer measurements. |
| `third_party/displacement/` | Reused ISPD26 displacement helper, cell groups, and license. |
| `tests/` | Evaluator regression tests. |

Store new run results in the output directory you choose, outside the supplied
evaluator files.
