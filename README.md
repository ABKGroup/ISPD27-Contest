# MCMM benchmark flow

Two entry points cover the complete flow. They enter Singularity automatically:

```bash
bash 01_generate_post_cts.sh aes "$HOME/ispd27_aes_run1"
bash 02_evaluate_post_grt.sh aes "$HOME/ispd27_aes_run1"
```

Use `jpeg` for JPEG and choose a fresh workspace. See the [short user guide](user_guide.md) for configuration changes, multiple SDC scenarios, and other designs.

| Directory | Contents |
| --- | --- |
| [generation/](generation/README.md) | Synthesized netlists, published post-CTS benchmarks, and complete ORFS results/logs/reports/objects for AES 50% / 620 ps and JPEG 65% / 1100 ps |
| [evaluation/difficulty_v2/](evaluation/difficulty_v2/README.md) | Validated evaluator, all scenarios, 10 screening configurations, and 6 configurations with Resizer off/on post-GRT results |
| `evaluation/screening_baselines/` | Retained routed baselines/SPEFs used by difficulty_v2 screening |
| `platform/` | Shared ASAP7 libraries, LEFs and RC settings |
| `scripts/` | Helpers for the two entry points |
| `validation/` | End-to-end checks of the new entry points in isolated workspaces |
| `backup/` | Superseded experiments and documentation snapshots |

- [Published results](evaluation/difficulty_v2/RESULTS.md) · [CSV](evaluation/difficulty_v2/results_summary.csv)
- [Directory changes and verification](WORKSPACE_REORGANIZATION.md)

Generation uses ORFS. Evaluation uses OpenROAD directly: optional Resizer, legalization, global routing, and fresh MCMM timing using OpenSTA and saved SPEFs. The published difficulty_v2 results are preserved.

`calibration -> evaluation` and `sweeps -> generation/provenance/sweeps` retain historical paths used by saved configurations. `patches/`, `rebuild_openroad.sh`, and `provenance.json` preserve shared tool support.
