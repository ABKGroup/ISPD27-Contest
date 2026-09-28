# Evaluation Scripts

Evaluate a legalized DEF/Verilog pair using global routing and setup/hold timing
analysis at BC, TC and WC. The evaluator does not run Resizer.

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

## 3. Check the results

The output directory contains:

- `summary.csv`: per-corner timing, power, ERC, routing overflow and displacement.
  Timing values are in **ns**; raw `timing.csv` uses **ps**.
- `evaluation.log`: the main evaluation log.
- `final_timing/`: final MCMM timing reports.
- `EVALUATION_COMPLETE`: the evaluation finished successfully.

**Current status:** metrics are available; numeric scoring and complete contest
legality checks are pending. `EVALUATION_COMPLETE` does not certify final eligibility.

## File guide

Use `eval.sh` to run the flow. The other scripts are internal helpers.

| File | Purpose |
| --- | --- |
| [README.md](README.md) | Usage instructions and this file guide. |
| [eval.sh](eval.sh) | User entry point; forwards arguments to `run.py`. |
| [run.py](run.py) | Selects the benchmark, applies official settings, and coordinates evaluation. Writes `EVALUATION_COMPLETE` on success. |
| [core_run.sh](core_run.sh) | Runs the OpenROAD stages, audits, and final timing refresh. |
| [evaluation.tcl](evaluation.tcl) | Loads the design and MCMM constraints, checks placement, runs global routing, and exports parasitics and analysis results. |
| [audit.py](audit.py) | Checks DEF/Verilog consistency and protected clock-tree data, runs Kepler Formal equivalence checks, and records audit results. |
| [refresh_timing.py](refresh_timing.py) | Recomputes final MCMM timing in a fresh OpenROAD process using the exported design and SPEFs. |
| [metrics.py](metrics.py) | Collects timing, power, ERC, routing, displacement, and runtime into `summary.csv`; writes a placeholder `score.json`. |
| [inspect_geometry.tcl](inspect_geometry.tcl) | Extracts design dimensions, cell counts, area, and utilization. |
| [check_spef.py](check_spef.py) | Checks that exported wire capacitances sum to each net's declared total. |
| [verify_package.py](verify_package.py) | Verifies released files against the package manifest. |
| [package_manifest.json](package_manifest.json) | Lists expected SHA-256 hashes of released files. |
| [tool_versions.json](tool_versions.json) | Records tool revisions, Python requirements, and the OpenROAD patch. |
| [patches/openroad-spef-pin-wire-cap.patch](patches/openroad-spef-pin-wire-cap.patch) | OpenROAD source patch for SPEF export, including wire capacitance at pin nodes. Apply before building OpenROAD. |
| [displacement/netlist_equiv_check.py](displacement/netlist_equiv_check.py) | Original ISPD26 helper; this evaluator uses only its cell-table loader and displacement calculation. Formal equivalence is checked separately by Kepler Formal. |
| [displacement/asap7_equivalent_cell_list.csv](displacement/asap7_equivalent_cell_list.csv) | Cell groups used by the displacement calculation to identify logic cells. |
| [displacement/LICENSE](displacement/LICENSE) | Original license for the reused ISPD26 files; retain it with these files. |

The `displacement/` folder was previously named `ispd26/`. Its source and license
are preserved. All listed scripts support the current flow; removing one requires
updating its callers. The patch and tool-version record may move to `environment/`
when the Docker environment is packaged, with their references updated.
