# JPEG

- Top module: `jpeg_encoder`.
- Inputs: `input.def` (legalized post-CTS placement), `input.v` (matching netlist).
- Physical provenance: 65% target utilization.
- Post-CTS functional/clock cell count: 56,061; no macros.
- Evaluation periods BC/TC/WC: 407 / 550 / 770 ps.
- Setup / hold uncertainty: 0 / 35 ps, all corners.

Use `sdc/BC.sdc`, `sdc/TC.sdc` and `sdc/WC.sdc` for evaluation.
`mcmm.tcl` maps scenarios to independent SDC contexts and documents common settings.
Shared Liberty sets are mapped in `../../platform/asap7/libraries.tcl`.
`benchmark.json` records portable paths and configuration metadata.

Keep the official SDCs, libraries, RC settings and clock tree unchanged.
Timing is measured after global routing.