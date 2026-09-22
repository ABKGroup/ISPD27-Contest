# Two-step workspace reorganization — 2026-09-21

The active workspace now contains both the ORFS generation history and the MCMM evaluation flow. The two public entry points are:

- `01_generate_post_cts.sh`: mapped netlist → ORFS floorplan, placement, CTS, legalization and export; includes generation equivalence checking.
- `02_evaluate_post_grt.sh`: post-CTS DEF/Verilog → Resizer off/on → global routing → fresh MCMM timing through OpenSTA in OpenROAD; includes input consistency, placement/clock protection, equivalence and SPEF checks.

Both scripts enter the existing Singularity image automatically and accept a design and private workspace. Step 2 accepts multiple scenario IDs/directories. The shared evaluator code and its optimization policy are unchanged. See [user_guide.md](user_guide.md); `user_guild.md` links to the same guide.

## Restored and moved data

The following ORFS directories were restored from `backup/cleanup_2026-09-21/sweeps/util_period_v1/work/` into `generation/`:

```text
results/asap7/aes/u50_p620/       logs/asap7/aes/u50_p620/
reports/asap7/aes/u50_p620/       objects/asap7/aes/u50_p620/
results/asap7/jpeg/u65_p1100/     logs/asap7/jpeg/u65_p1100/
reports/asap7/jpeg/u65_p1100/     objects/asap7/jpeg/u65_p1100/
```

The source configurations are AES 50% / 620 ps and JPEG 65% / 1100 ps. Other obsolete physical configurations remain in the archive.

| Previous path | Canonical active path |
| --- | --- |
| `calibration/difficulty_v2/` | `evaluation/difficulty_v2/` |
| `sweeps/util_period_v1/cases/aes/u50_p620/benchmark/` | `generation/benchmarks/aes/` |
| `sweeps/util_period_v1/cases/jpeg/u65_p1100/benchmark/` | `generation/benchmarks/jpeg/` |
| Those cases' `rsz0/` directories | `evaluation/screening_baselines/{aes,jpeg}/` |
| Other retained sweep generation records | `generation/provenance/sweeps/` |

Compatibility symlinks preserve the old input/configuration paths. The two root result links now point directly to `evaluation/difficulty_v2/`. Historical logs and archive manifests retain the paths that were valid when written; this document and `generation/provenance/workspace_reorganization.json` record the subsequent moves.

## New and updated files

Added the two public shell scripts, `scripts/environment.bash`, and `scripts/run_flow.py`. The Python helper handles private input/SDC copies, native ORFS invocation, scenario selection, and a new timing-only summary in ns. Per-run detailed metrics still come from the validated evaluator. Added `generation/README.md` and this record; updated the root README, user guide, and difficulty_v2 README navigation.

Original documentation was copied to `backup/before_two_step_layout_20260921T205531Z/`. No default ORFS/OpenROAD source, published SDC, evaluator source, or published result was edited. New experiment outputs refuse existing step directories; original results are preserved.

## Verification

The move checked 898 protected input/configuration/script/result SHA-256 hashes and size/mtime/inode metadata for 3,361 moved file entries. The machine-readable record is `generation/provenance/workspace_reorganization.json`.

End-to-end validation **passed**. The [verification record](validation/two_step_20260921/validation.json) and `verify_results.py` are under `validation/two_step_20260921/`.

- Ran both new shell entry points from the host; their automatic Singularity/environment setup worked.
- Regenerated AES and JPEG through ORFS floorplan, placement and CTS. Both passed generation equivalence; DEF, Verilog and ODB files exactly matched the published benchmark inputs.
- Ran AES `aes_p55_h55` and `aes_p55_h50`, and JPEG `jpeg_p70_h35`, each with Resizer off/on: six complete physical evaluations and 18 corner rows.
- All runs passed formal checks, placement/clock checks, fresh MCMM timing, and SPEF capacitance checks. Final endpoint profiles independently reproduced reported TNS, worst slack and violating endpoint counts.
- All per-corner setup/hold worst slack and TNS values, and violating endpoint counts, matched the corresponding published runs. The generated timing summaries' ns conversions were checked against the raw ps values.
- Existing-output guards, mismatched design/scenario rejection, and forwarding/validation of environment overrides passed.
- All 898 protected hashes and the five published report hashes still match. The evaluator source and default ORFS/OpenROAD sources were not edited.

The validation workspaces retain their complete generated stage files and post-GRT outputs, separately from the published experiment.
