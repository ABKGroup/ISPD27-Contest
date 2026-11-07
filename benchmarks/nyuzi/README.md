# NyuziProcessor

- Top module: `NyuziProcessor`.
- Inputs: `input.def` (legalized post-CTS placement), `input.v` (matching netlist), shipped as `input.def.gz` and `input.v.gz`.
- Existing data buffers and functional inverters are retained; no debuffering is applied.
- Physical provenance: 55% target utilization.
- Post-CTS functional/clock cell count: 337,874; 55 macros (`ht_asap7_nyuzi_128x32_2r1w`, `ht_asap7_nyuzi_16x52`, `ht_asap7_nyuzi_2048x512`, `ht_asap7_nyuzi_256x1`, `ht_asap7_nyuzi_256x18`, `ht_asap7_nyuzi_256x512`, `ht_asap7_nyuzi_256x7`, `ht_asap7_nyuzi_64x20`, `ht_asap7_nyuzi_64x20_2r1w`, `ht_asap7_nyuzi_64x3`).
- Evaluation periods BC/TC/WC: 787 / 1012 / 1444 ps.
- Setup / hold uncertainty: 0.0 / 50.0 ps, all corners.
- Wire capacitance scaling BC/TC/WC: x0.9 / x1 / x1.1 of the platform RC (`rc.tcl`, read through `mcmm_rc_file` in `mcmm.tcl`).
- Hold is not checked on paths that start at an input port or end at a hard-macro input (`set_false_path -hold` at the end of the SDCs).

Unpack the inputs first: `gunzip -k input.def.gz input.v.gz`.
Use `sdc/BC.sdc`, `sdc/TC.sdc` and `sdc/WC.sdc` for evaluation.
`mcmm.tcl` maps scenarios to independent SDC contexts and documents common settings.
Shared Liberty sets are mapped in `../../../platform/asap7/util/libraries.tcl`.
The technology LEF is `../../../platform/asap7/lef/asap7_tech_1x_201209.lef`.
Macro LEF and Liberty files are in `macros/`. The macro Liberty is characterized at one corner and is used in every scene.
`benchmark.json` records portable paths and configuration metadata.

Keep the official SDCs, libraries, RC settings and clock tree unchanged.
Timing is measured after global routing.
