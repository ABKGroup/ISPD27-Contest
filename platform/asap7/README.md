# Shared ASAP7 7.5T platform

This package includes four LEFs and 45 Liberty files for RVT, LVT
and SLVT at BC/FF, TC/TT and WC/SS. 

- `libraries.tcl`: per-corner Liberty file lists, relative to `PLATFORM_DIR`.
- `setRC.tcl`: the common interconnect RC model.
- `constraints.sdc`: helper sourced by the JPEG scenario SDCs.
- `liberty_suppressions.tcl`: the existing parser-warning suppression settings.
- `manifest.json`: original library/cell inventory and checksums.

