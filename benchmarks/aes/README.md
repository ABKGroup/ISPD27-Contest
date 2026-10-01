# AES 

- Top module: `aes_cipher_top`.
- Inputs: `input.def` (legalized post-CTS placement), `input.v` (matching netlist).
- Existing data buffers and functional inverters are retained; no debuffering is applied.
- Physical provenance: 50% target utilization.
- Post-CTS functional/clock cell count: 15,343; no macros.
- Evaluation periods BC/TC/WC: 248 / 308 / 429 ps.
- Setup / hold uncertainty: 0 / 55 ps, all corners.

Use `sdc/BC.sdc`, `sdc/TC.sdc` and `sdc/WC.sdc` for evaluation.
`mcmm.tcl` maps scenarios to independent SDC contexts and documents common settings.
Shared Liberty sets are mapped in `../../platform/asap7/util/libraries.tcl`.
`benchmark.json` records portable paths and configuration metadata.

Keep the official SDCs, libraries, RC settings and clock tree unchanged.
Timing is measured after global routing.
