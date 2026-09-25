# ISPD 2027 contest, post-CTS MCMM benchmarks

Each benchmark is addressed by design and by measured cell utilization:

    benchmarks/<design>/u<utilization>/

A design with more than one entry is the same netlist placed into
different die sizes.

## Benchmarks

Utilization is (standard cell area + macro area) / core area. The next
column repeats it with the buffers clock tree synthesis inserted taken
out, which is what says whether the density is logic rather than clock
repeaters. Clock periods are per mode. Slacks are the worst in each
corner, measured after global routing with an extracted SPEF.

<table>
  <thead>
    <tr>
      <th>design</th><th>utilization</th><th>without the clock tree</th><th>clock period BC / TC / WC</th><th>setup WNS BC / TC / WC</th><th>hold WNS BC / TC / WC</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="2"><code>ariane</code></td>
      <td><code>u43</code> &nbsp; 42.63%</td>
      <td>42.07%</td>
      <td>- / - / - ps</td>
      <td>- / - / - ns</td>
      <td>- / - / - ns</td>
    </tr>
    <tr>
      <td><code>u76</code> &nbsp; 75.99%</td>
      <td>75.06%</td>
      <td>1638 / 2014 / 2716 ps</td>
      <td>-1.253 / -1.841 / -2.997 ns</td>
      <td>-0.160 / -0.103 / -0.022 ns</td>
    </tr>
    <tr>
      <td rowspan="1"><code>blackparrot_2</code></td>
      <td><code>u66</code> &nbsp; 66.06%</td>
      <td>64.96%</td>
      <td>925 / 1055 / 1305 ps</td>
      <td>-0.615 / -0.906 / -1.601 ns</td>
      <td>-0.116 / -0.114 / -0.110 ns</td>
    </tr>
    <tr>
      <td rowspan="2"><code>mempool_tile</code></td>
      <td><code>u43</code> &nbsp; 43.03%</td>
      <td>42.20%</td>
      <td>- / - / - ps</td>
      <td>- / - / - ns</td>
      <td>- / - / - ns</td>
    </tr>
    <tr>
      <td><code>u88</code> &nbsp; 87.80%</td>
      <td>86.14%</td>
      <td>2863 / 2890 / 3843 ps</td>
      <td>-1.008 / -1.882 / -3.050 ns</td>
      <td>-0.390 / -0.452 / -0.567 ns</td>
    </tr>
    <tr>
      <td rowspan="2"><code>picorv32</code></td>
      <td><code>u46</code> &nbsp; 45.60%</td>
      <td>44.75%</td>
      <td>- / - / - ps</td>
      <td>- / - / - ns</td>
      <td>- / - / - ns</td>
    </tr>
    <tr>
      <td><code>u90</code> &nbsp; 90.25%</td>
      <td>88.55%</td>
      <td>514 / 619 / 916 ps</td>
      <td>-0.468 / -0.726 / -1.088 ns</td>
      <td>-0.023 / -0.017 / -0.002 ns</td>
    </tr>
    <tr>
      <td rowspan="2"><code>tpu</code></td>
      <td><code>u47</code> &nbsp; 46.71%</td>
      <td>45.94%</td>
      <td>- / - / - ps</td>
      <td>- / - / - ns</td>
      <td>- / - / - ns</td>
    </tr>
    <tr>
      <td><code>u94</code> &nbsp; 93.87%</td>
      <td>92.31%</td>
      <td>623 / 759 / 1022 ps</td>
      <td>-0.474 / -0.661 / -1.041 ns</td>
      <td>-0.023 / -0.018 / -0.004 ns</td>
    </tr>
    <tr>
      <td rowspan="2"><code>xiangshan_coupledl2</code></td>
      <td><code>u41</code> &nbsp; 41.12%</td>
      <td>40.37%</td>
      <td>- / - / - ps</td>
      <td>- / - / - ns</td>
      <td>- / - / - ns</td>
    </tr>
    <tr>
      <td><code>u86</code> &nbsp; 86.00%</td>
      <td>84.60%</td>
      <td>973 / 1253 / 2276 ps</td>
      <td>-1.482 / -1.986 / -2.571 ns</td>
      <td>-0.380 / -0.379 / -0.581 ns</td>
    </tr>
  </tbody>
</table>

A dash means the benchmark does not carry that file. The entries with no
scenario are the set published earlier, which has the netlist, the DEF,
the database and the constraint and no MCMM scenario.

| benchmark | standard cells | inserted by the clock tree | macros | core area |
| --- | --- | --- | --- | --- |
| `ariane/u43` | 210,947 | 1,332 | 136 | 104,836 um2 |
| `ariane/u76` | 191,526 | 1,197 | 136 | 56,634 um2 |
| `blackparrot_2/u66` | 133,840 | 1,200 | 24 | 47,617 um2 |
| `mempool_tile/u43` | 274,756 | 1,512 | 20 | 79,670 um2 |
| `mempool_tile/u88` | 258,875 | 1,418 | 20 | 37,498 um2 |
| `picorv32/u46` | 23,228 | 112 | 0 | 5,642 um2 |
| `picorv32/u90` | 19,695 | 101 | 0 | 2,530 um2 |
| `tpu/u47` | 56,814 | 229 | 0 | 13,062 um2 |
| `tpu/u94` | 45,999 | 204 | 0 | 5,610 um2 |
| `xiangshan_coupledl2/u41` | 474,466 | 3,918 | 39 | 228,698 um2 |
| `xiangshan_coupledl2/u86` | 454,934 | 3,449 | 39 | 107,546 um2 |

## Contents of a benchmark

| file | what it is |
| --- | --- |
| `input.v.gz`, `input.def.gz`, `input.odb.gz` | post-CTS netlist with the clock tree, legalized placement, database |
| `constraint.sdc` | the constraint the layout was generated under |
| `scenario/BC.sdc`, `TC.sdc`, `WC.sdc` | one constraint per corner |
| `scenario/config.json` | periods, uncertainties and boundary values |
| `mcmm.tcl` | modes, corners and scenes, in the commands the evaluation uses |
| `sha256.json` | digests of the uncompressed files |
| `source_synth.v.gz` | the reference the equivalence proof compares against |
| `calibration.json` | how the scenario period was chosen, round by round |
| `evaluation_timing_summary.csv` | post-route timing from the evaluation |
| `orfs_generated.sdc` | what ORFS wrote back, for reference |

## Platform

`platform/asap7` holds the technology LEF `asap7_tech_1x_260907.lef`, the three
standard cell LEFs and the 45 NLDM libraries, 15 per corner.

The SRAM abstracts live with the design that uses them, at
`platform/<design>/lef` and `platform/<design>/lib`. A design with
macros cannot be read without them. The macro Liberty is
characterised at a single corner and that one file is used in all
three scenes.

- `platform/ariane`: 1 LEF, 1 Liberty
- `platform/blackparrot_2`: 5 LEF, 5 Liberty
- `platform/mempool_tile`: 2 LEF, 2 Liberty
- `platform/xiangshan_coupledl2`: 6 LEF, 6 Liberty

Corners are BC at FF 0.77V 0C, TC at TT 0.70V 25C and WC at SS 0.63V
100C. Units are ps, fF and um.

## Unpacking

    gunzip -k benchmarks/<design>/u<pct>/*.gz
    gunzip -k platform/<design>/lib/*.gz

`sha256.json` lists digests of the uncompressed files.

## Timing a benchmark

    source benchmarks/<design>/u<pct>/mcmm.tcl
    ispd27_read_libraries
    read_def benchmarks/<design>/u<pct>/input.def
    ispd27_define_scenes

The paths inside `mcmm.tcl` resolve from the repository root. The
numbers this reports are higher than the ones above, because those
include a SPEF extracted after global routing and this setup has no
parasitics.
