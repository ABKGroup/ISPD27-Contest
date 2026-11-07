# ISPD 2027 Contest Benchmarks

This directory contains the six public benchmarks for the ISPD 2027 Contest on **MCMM Post-CTS Buffering and Sizing**.

As of **October 5, 2026**, two public benchmarks were released:

- `aes` and `jpeg`

As of **November 7, 2026**, the remaining four public benchmarks were released:

- `aes/scan`, `jpeg/scan`, `coralnpu` (Coral NPU) and `nyuzi` (NyuziProcessor).

The public benchmarks are used only for tool development, debugging, and testing. **Final contest scores and rankings will be determined solely by performance on the hidden benchmarks.**

## Directory layout

A benchmark is `benchmarks/<design>/`, for example `benchmarks/nyuzi/`. A scan testcase is `scan/` of its benchmark
directory, for example `benchmarks/jpeg/scan/`. Reference results of a testcase are in `postgrt_results.csv` and in `evaluator/reference_results/`. 

Unpack the inputs, then run a benchmark by its path:

    gunzip -k benchmarks/nyuzi/input.def.gz benchmarks/nyuzi/input.v.gz
    bash evaluator/eval.sh nyuzi /tmp/nyuzi-run

The path of a scan testcase ends with `/scan`:

    gunzip -k benchmarks/jpeg/scan/input.def.gz benchmarks/jpeg/scan/input.v.gz
    bash evaluator/eval.sh jpeg/scan /tmp/jpeg-scan-run

AES and JPEG without scan include `input.def` and `input.v` unpacked.

## Testcases

| Design | Testcase | Mode | Utilization (%) | Hold (ps) | Period scale | Cap scale BC / TC / WC | Periods BC / TC / WC (ps) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AES | `aes` | functional | 50 | 55 | 1.00x | 1 / 1 / 1 | 248 / 308 / 429 |
| AES | `aes/scan` | functional / scan | 50 | 55 | 1.00x | 1 / 1 / 1 | 248 / 308 / 429 |
| JPEG | `jpeg` | functional | 65 | 35 | 1.00x | 1 / 1 / 1 | 407 / 550 / 770 |
| JPEG | `jpeg/scan` | functional / scan | 65 | 35 | 1.00x | 1 / 1 / 1 | 407 / 550 / 770 |
| Coral NPU | `coralnpu` | functional | 70 | 50 | 0.60x | 1 / 1 / 1 | 1358 / 1850 / 2779 |
| NyuziProcessor | `nyuzi` | functional | 55 | 50 | 0.60x | 0.9 / 1 / 1.1 | 787 / 1012 / 1444 |

- Mode `functional`: three scenes, BC, TC and WC.
- Mode `functional / scan`: a scan testcase with six scenes (see Scan mode below).
- Cap scale: wire capacitance of the corner as a multiple of the platform RC, set in `rc.tcl` of the benchmark directory.
- Hold check: in Coral NPU and NyuziProcessor, hold is not checked on paths that start at an input port or end at a hard-macro input.
  In the scan test mode of AES scan, hold is not checked on paths that start at an input port. These exclusions are written
  in the SDC files (`set_false_path -hold`). Setup is checked on all paths.


## Files of a testcase

| File | Contents |
| --- | --- |
| `input.def`, `input.v` | Legalized post-CTS placement and the matching netlist |
| `sdc/BC.sdc`, `sdc/TC.sdc`, `sdc/WC.sdc` | Functional mode constraints of each corner |
| `sdc/BC_test.sdc`, `sdc/TC_test.sdc`, `sdc/WC_test.sdc` | Scan test mode constraints of each corner. Scan testcases only. |
| `mcmm.tcl` | Scenes, the SDC file of each scene, and the RC file |
| `rc.tcl` | Wire RC of each corner. Only for a testcase with a cap scale other than 1 / 1 / 1 (NyuziProcessor). |
| `macros/lef`, `macros/lib` | LEF and Liberty files of the hard macros. Only for a testcase with hard macros. |
| `benchmark.json`, `geometry.json`, `sdc/config.json` | Metadata: top module, clock periods, uncertainties, file lists, areas |
| `input.scandef.gz` | Scan chains. Scan testcases only. The evaluator does not read it. |
| `scan_enable_pins.txt.gz` | The scan enable port and the scan enable pin of every scan flop. Scan testcases only. The evaluator does not read it. |

<!-- 

## Post-GRT results


All metrics are in `postgrt_results.csv` and in `evaluator/reference_results/<testcase>/`. 

| Design | Testcase | Mode | OR Resizer | Setup WNS BC / TC / WC (ps) | Setup TNS BC / TC / WC (ns) | Hold WNS BC / TC / WC (ps) | Hold TNS BC / TC / WC (ns) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AES | `aes` | functional | No | -199 / -283 / -444 | -32 / -45 / -65 | -19 / -8 / -4 | -1 / 0 / 0 |
| AES | `aes` | functional | Yes | -158 / -191 / -261 | -25 / -31 / -42 | -1 / -5 / -4 | 0 / 0 / 0 |
| AES | `aes/scan` | functional | No | -210 / -313 / -494 | -36 / -50 / -73 | -10 / 0 / 0 | 0 / 0 / 0 |
| AES | `aes/scan` | scan test | No | 0 / 0 / 0 | 0 / 0 / 0 | -42 / -37 / -28 | -14 / -9 / -3 |
| AES | `aes/scan` | functional | Yes | -166 / -204 / -272 | -28 / -35 / -48 | -3 / 0 / 0 | 0 / 0 / 0 |
| AES | `aes/scan` | scan test | Yes | 0 / 0 / 0 | 0 / 0 / 0 | -28 / -17 / 0 | -4 / -1 / 0 |
| JPEG | `jpeg` | functional | No | -345 / -484 / -746 | -192 / -268 / -443 | -10 / -5 / 0 | -5 / 0 / 0 |
| JPEG | `jpeg` | functional | Yes | -210 / -274 / -445 | -129 / -172 / -289 | -4 / 0 / 0 | 0 / 0 / 0 |
| JPEG | `jpeg/scan` | functional | No | -351 / -489 / -757 | -198 / -277 / -456 | -2 / 0 / 0 | 0 / 0 / 0 |
| JPEG | `jpeg/scan` | scan test | No | 0 / 0 / 0 | 0 / 0 / 0 | -28 / -23 / -13 | -52 / -24 / -1 |
| JPEG | `jpeg/scan` | functional | Yes | -214 / -285 / -451 | -133 / -177 / -294 | 0 / 0 / 0 | 0 / 0 / 0 |
| JPEG | `jpeg/scan` | scan test | Yes | 0 / 0 / 0 | 0 / 0 / 0 | -13 / -1 / 0 | -2 / 0 / 0 |
| Coral NPU | `coralnpu` | functional | No | -1244 / -1691 / -2563 | -11161 / -12629 / -15133 | -34 / -25 / -12 | -814 / -304 / 0 |
| Coral NPU | `coralnpu` | functional | Yes | -825 / -917 / -1131 | -9574 / -10499 / -12190 | -15 / -3 / 0 | -6 / 0 / 0 |
| NyuziProcessor | `nyuzi` | functional | No | -546 / -819 / -1291 | -1799 / -2596 / -4228 | -49 / -45 / -34 | -444 / -245 / -47 |
| NyuziProcessor | `nyuzi` | functional | Yes | -389 / -518 / -747 | -1498 / -1942 / -2993 | -26 / -13 / 0 | -19 / 0 / 0 | -->

## Scan mode

The `scan/` directory contains the scan-enabled layout with four scan chains, with all scan flops stitched into the chains. 

Each scan testcase is evaluated in six scenes: functional
mode (scan_enable=0) and scan test mode (scan_enable=1) on BC, TC and WC. The corresponding SDC files are `scan/sdc/<corner>.sdc` and
`scan/sdc/<corner>_test.sdc`.

- Functional mode: Scan-shift paths ending at the scan input (SI) of a scan flop are set as false paths.
- Scan test mode: the scan test clock `test_clk` is applied to every clock port and uses the `clk_period` defined for the corresponding corner.
The functional data input (D) of every register and all hard-macro inputs are set as false paths. Scan shift paths ending at `SI` and IO paths are timed.

| Design | Testcase | Scan flops |
| --- | --- | --- |
| AES | `aes/scan` | 562 |
| JPEG | `jpeg/scan` | 4325 |

<!-- ## Notes

- The evaluator allows `inout` on top-level ports. -->
