# Evaluation

Evaluate a legalized DEF/Verilog pair using global routing and setup/hold timing analysis at BC, TC and WC. The evaluator does not run Resizer.

**The current score is a dummy score for testing. The weights of individual score components will be announced after the Alpha submission, as stated in the contest description.** Setup TNS and WNS have equal weights.

## 1. Prepare your files and tools

- Provide the legalized `.def` and matching `.v` produced by your tool.
- Keep the supplied clock tree and official timing constraints unchanged.
- Use Python 3.9+ and compatible OpenROAD/Kepler Formal executables on PATH.
  See [tool_versions.json](tool_versions.json) for versions and the required patch.

## 2. Run the evaluation

From the repository root:

```bash
bash evaluator/eval.sh aes /tmp/aes-evaluation \
  --def /path/to/submission.def --verilog /path/to/submission.v
```

Replace `aes` with `jpeg` for JPEG. Choose a new output directory for every run.

To evaluate the supplied unoptimized baseline, omit the input-file arguments:

```bash
bash evaluator/eval.sh aes /tmp/aes-baseline
```

## 3. Calculate the dummy score

Reference metrics for the released benchmarks are provided below:

| Design | Unoptimized baseline | Resizer reference | Runtime template |
| --- | --- | --- | --- |
| AES | [baseline.csv](results/aes/baseline.csv) | [resizer.csv](results/aes/resizer.csv) | [runtimes.json](results/aes/runtimes.json) |
| JPEG | [baseline.csv](results/jpeg/baseline.csv) | [resizer.csv](results/jpeg/resizer.csv) | [runtimes.json](results/jpeg/runtimes.json) |

The **unoptimized baseline** is used to normalize setup timing, power, and ERC metrics.
Hold and routing-overflow penalties use the tolerances and thresholds in the scoring configuration.

The **OpenROAD Resizer reference** is used to normalize displacement and runtime.
These files contain recorded reference results for the released benchmarks; they are
not regenerated during evaluation. Reference runtimes therefore depend on the machine
on which they were originally measured.
Use the baseline and reference matching your design and timing configuration.

First, copy the runtime template into your output directory:

```bash
cp evaluator/results/aes/runtimes.json /tmp/aes-evaluation/runtimes.json
```

Fill in `tool_s` with your tool runtime and `flow_s` with your tool runtime plus
`evaluation_wall_seconds` from `evaluation_runtime.json`. All times are in seconds.
Use this wall time rather than `runtime_s` in `summary.csv`, which covers only the
recorded OpenROAD stages. Keep the supplied `reference_*` values unchanged. Then run:

```bash
python3 evaluator/score.py \
  --baseline evaluator/results/aes/baseline.csv \
  --candidate /tmp/aes-evaluation/summary.csv \
  --reference evaluator/results/aes/resizer.csv \
  --runtimes /tmp/aes-evaluation/runtimes.json \
  --output /tmp/aes-evaluation/score.json
```

The command prints one number; **higher is better**. `score.json` contains the
component breakdown. The output file must not already exist.
The provisional weights are in [scoring_config.json](scoring_config.json).
Use `--config /path/to/config.json` to try other weights; keep TNS and WNS weights
equal within both the setup and hold pairs.

## 4. Check the results

The output directory contains:

- `summary.csv`: per-corner timing, power, ERC, routing overflow and displacement.
  WNS/TNS values are in **ns**; raw `timing.csv` uses **ps**. Slew violations remain in **ps**.
- `evaluation_runtime.json`: evaluator wall time used for scoring.
- `evaluation.log`: the main evaluation log.
- `final_timing/`: final MCMM timing reports.
- `EVALUATION_COMPLETE`: evaluation and metric extraction finished; scoring is a separate step.

**Note:** Complete contest
legality checks are pending. `EVALUATION_COMPLETE` does not certify final eligibility.

## File guide

Use `eval.sh` for evaluation and `score.py` for scoring. The other scripts support these steps.

| File | Purpose |
| --- | --- |
| [README.md](README.md) | Quick-start instructions. |
| [eval.sh](eval.sh) | User entry point; forwards arguments to `run.py`. |
| [run.py](run.py) | Selects the benchmark, applies official settings, and coordinates evaluation. Writes `EVALUATION_COMPLETE` on success. |
| [core_run.sh](core_run.sh) | Runs the OpenROAD stages, audits, and final timing refresh. |
| [evaluation.tcl](evaluation.tcl) | Loads the design and MCMM constraints, checks placement, runs global routing, and exports parasitics and analysis results. |
| [audit.py](audit.py) | Checks DEF/Verilog consistency and protected clock-tree data, runs Kepler Formal equivalence checks, and records audit results. |
| [refresh_timing.py](refresh_timing.py) | Recomputes final MCMM timing in a fresh OpenROAD process using the exported design and SPEFs. |
| [metrics.py](metrics.py) | Collects timing, power, ERC, routing, displacement, and runtime into `summary.csv`. |
| [score.py](score.py) | Computes one design's Section 3.3.1 score from R0, candidate, Resizer-reference metrics, and measured runtimes. |
| [scoring_config.json](scoring_config.json) | Provisional scoring weights, scenario tolerances, thresholds, and numerical epsilons. |
| [tests/test_score.py](tests/test_score.py) | Checks scoring arithmetic, input validation, and the command-line interface. |
| [inspect_geometry.tcl](inspect_geometry.tcl) | Extracts design dimensions, cell counts, area, and utilization. |
| [check_spef.py](check_spef.py) | Checks that exported wire capacitances sum to each net's declared total. |
| [verify_package.py](verify_package.py) | Verifies released files against the package manifest. |
| [package_manifest.json](package_manifest.json) | Lists expected SHA-256 hashes of released files. |
| [tool_versions.json](tool_versions.json) | Records tool revisions, Python requirements, and the OpenROAD patch. |
| [patches/openroad-spef-pin-wire-cap.patch](patches/openroad-spef-pin-wire-cap.patch) | OpenROAD source patch for SPEF export, including wire capacitance at pin nodes. Apply before building OpenROAD. |
| [displacement/netlist_equiv_check.py](displacement/netlist_equiv_check.py) | Original ISPD26 helper; this evaluator uses only its cell-table loader and displacement calculation. Formal equivalence is checked separately by Kepler Formal. |
| [displacement/asap7_equivalent_cell_list.csv](displacement/asap7_equivalent_cell_list.csv) | Cell groups used by the displacement calculation to identify logic cells. |
| [displacement/LICENSE](displacement/LICENSE) | Original license for the reused ISPD26 files; retain it with these files. |
<!--

## Scoring conventions

Timing inputs are signed WNS/TNS in **ns**; hold penalties use their nonnegative
violation magnitudes. The scorer follows the PDF's printed setup denominator
`abs(baseline + epsilon)`. It interprets the total-overflow formula's incomplete
`max(...)` as `max(0, overflow - threshold)`, matching the maximum-overflow formula.
ERC, runtime, and displacement penalties may be negative (a reward), as in the PDF.
Physical displacement, routing overflow, and runtime are counted once per design.

Missing/nonfinite data, mismatched scenarios, invalid denominators, and candidate
tool or flow runtime above five hours cause an error instead of a score. A numerical
score does not certify legality; the across-team illegal-submission ranking rule
in Section 3.3.2 is outside this per-design scorer.

The default weights, tolerances, and epsilons are provisional. Zero overflow thresholds and small epsilons can produce large penalties. The dummy score is for testing; weights and calibration will be adjusted before final scoring. -->
