# ISPD 2027 contest, post-CTS MCMM benchmarks

Each benchmark is addressed by design and by the utilization it was asked for:

    benchmarks/<design>/u<target utilization>/

A design with more than one entry is the same netlist placed into different die
sizes. The utilization actually achieved is in the table, and it is a little
above the request because the placement has to fit whole rows.

## Benchmarks

Utilization is (standard cell area + macro area) / core area. Clock periods are
per mode and slacks are the worst in each corner, measured after global routing
with an extracted SPEF. Both are in nanoseconds. Every benchmark violates setup
and hold in all three corners, so closing one costs the other.

<table>
  <thead>
    <tr>
      <th>design</th><th>target util</th><th>measured util</th><th>clock period BC / TC / WC (ns)</th><th>setup WNS BC / TC / WC (ns)</th><th>hold WNS BC / TC / WC (ns)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="6"><code>ariane</code></td>
      <td>40%</td>
      <td>42.60%</td>
      <td>2.611 / 3.531 / 5.341</td>
      <td>-0.312 / -0.420 / -0.630</td>
      <td>-0.066 / -0.032 / -0.004</td>
    </tr>
    <tr>
      <td>65%</td>
      <td>66.74%</td>
      <td>2.905 / 3.898 / 5.780</td>
      <td>-0.430 / -0.579 / -0.891</td>
      <td>-0.117 / -0.086 / -0.029</td>
    </tr>
    <tr>
      <td>70%</td>
      <td>71.88%</td>
      <td>3.098 / 4.137 / 6.172</td>
      <td>-0.446 / -0.627 / -0.932</td>
      <td>-0.124 / -0.073 / -0.011</td>
    </tr>
    <tr>
      <td>72%</td>
      <td>74.03%</td>
      <td>2.773 / 3.736 / 5.578</td>
      <td>-0.419 / -0.565 / -0.842</td>
      <td>-0.133 / -0.099 / -0.039</td>
    </tr>
    <tr>
      <td>73%</td>
      <td>74.83%</td>
      <td>2.258 / 3.047 / 4.580</td>
      <td>-0.343 / -0.461 / -0.691</td>
      <td>-0.148 / -0.120 / -0.070</td>
    </tr>
    <tr>
      <td>74%</td>
      <td>75.99%</td>
      <td>2.705 / 3.636 / 5.453</td>
      <td>-0.399 / -0.544 / -0.808</td>
      <td>-0.210 / -0.153 / -0.072</td>
    </tr>
    <tr>
      <td rowspan="1"><code>blackparrot_2</code></td>
      <td>65%</td>
      <td>66.06%</td>
      <td>1.404 / 1.765 / 2.615</td>
      <td>-0.232 / -0.263 / -0.317</td>
      <td>-0.108 / -0.080 / -0.068</td>
    </tr>
    <tr>
      <td rowspan="6"><code>mempool_tile</code></td>
      <td>40%</td>
      <td>43.04%</td>
      <td>3.236 / 4.344 / 6.447</td>
      <td>-0.487 / -0.643 / -0.956</td>
      <td>-0.558 / -0.611 / -0.740</td>
    </tr>
    <tr>
      <td>65%</td>
      <td>67.24%</td>
      <td>3.832 / 5.225 / 7.845</td>
      <td>-0.576 / -0.785 / -1.178</td>
      <td>-0.425 / -0.486 / -0.613</td>
    </tr>
    <tr>
      <td>70%</td>
      <td>72.52%</td>
      <td>4.049 / 5.280 / 7.845</td>
      <td>-0.608 / -0.793 / -1.178</td>
      <td>-0.596 / -0.636 / -0.750</td>
    </tr>
    <tr>
      <td>75%</td>
      <td>77.63%</td>
      <td>3.796 / 5.176 / 7.745</td>
      <td>-0.570 / -0.777 / -1.163</td>
      <td>-0.415 / -0.477 / -0.609</td>
    </tr>
    <tr>
      <td>80%</td>
      <td>82.75%</td>
      <td>3.988 / 5.389 / 8.003</td>
      <td>-0.561 / -0.749 / -1.106</td>
      <td>-0.587 / -0.631 / -0.748</td>
    </tr>
    <tr>
      <td>85%</td>
      <td>87.80%</td>
      <td>3.868 / 5.122 / 7.304</td>
      <td>-0.505 / -0.766 / -1.320</td>
      <td>-0.440 / -0.502 / -0.617</td>
    </tr>
    <tr>
      <td rowspan="9"><code>picorv32</code></td>
      <td>40%</td>
      <td>45.60%</td>
      <td>0.605 / 0.782 / 1.158</td>
      <td>-0.091 / -0.118 / -0.174</td>
      <td>-0.073 / -0.067 / -0.052</td>
    </tr>
    <tr>
      <td>65%</td>
      <td>66.00%</td>
      <td>0.802 / 1.094 / 1.639</td>
      <td>-0.120 / -0.166 / -0.245</td>
      <td>-0.075 / -0.069 / -0.055</td>
    </tr>
    <tr>
      <td>70%</td>
      <td>71.01%</td>
      <td>0.808 / 1.113 / 1.664</td>
      <td>-0.122 / -0.167 / -0.250</td>
      <td>-0.076 / -0.070 / -0.055</td>
    </tr>
    <tr>
      <td>75%</td>
      <td>76.53%</td>
      <td>0.812 / 1.113 / 1.664</td>
      <td>-0.124 / -0.169 / -0.254</td>
      <td>-0.074 / -0.069 / -0.056</td>
    </tr>
    <tr>
      <td>80%</td>
      <td>81.25%</td>
      <td>0.813 / 1.113 / 1.669</td>
      <td>-0.120 / -0.170 / -0.248</td>
      <td>-0.075 / -0.069 / -0.056</td>
    </tr>
    <tr>
      <td>85%</td>
      <td>86.34%</td>
      <td>0.821 / 1.133 / 1.686</td>
      <td>-0.125 / -0.169 / -0.252</td>
      <td>-0.073 / -0.067 / -0.051</td>
    </tr>
    <tr>
      <td>87%</td>
      <td>88.34%</td>
      <td>0.831 / 1.146 / 1.708</td>
      <td>-0.124 / -0.174 / -0.256</td>
      <td>-0.073 / -0.067 / -0.051</td>
    </tr>
    <tr>
      <td>88%</td>
      <td>89.16%</td>
      <td>0.814 / 1.121 / 1.670</td>
      <td>-0.122 / -0.167 / -0.250</td>
      <td>-0.079 / -0.074 / -0.062</td>
    </tr>
    <tr>
      <td>89%</td>
      <td>90.25%</td>
      <td>0.884 / 1.210 / 1.804</td>
      <td>-0.098 / -0.135 / -0.200</td>
      <td>-0.073 / -0.067 / -0.052</td>
    </tr>
    <tr>
      <td rowspan="9"><code>tpu</code></td>
      <td>40%</td>
      <td>46.71%</td>
      <td>0.950 / 1.272 / 1.909</td>
      <td>-0.117 / -0.155 / -0.231</td>
      <td>-0.073 / -0.067 / -0.053</td>
    </tr>
    <tr>
      <td>65%</td>
      <td>65.89%</td>
      <td>1.034 / 1.380 / 2.033</td>
      <td>-0.158 / -0.206 / -0.314</td>
      <td>-0.072 / -0.067 / -0.052</td>
    </tr>
    <tr>
      <td>70%</td>
      <td>70.88%</td>
      <td>1.098 / 1.447 / 2.107</td>
      <td>-0.167 / -0.217 / -0.326</td>
      <td>-0.073 / -0.067 / -0.053</td>
    </tr>
    <tr>
      <td>75%</td>
      <td>76.00%</td>
      <td>1.204 / 1.578 / 2.246</td>
      <td>-0.183 / -0.235 / -0.348</td>
      <td>-0.073 / -0.068 / -0.054</td>
    </tr>
    <tr>
      <td>80%</td>
      <td>80.76%</td>
      <td>1.052 / 1.373 / 2.007</td>
      <td>-0.160 / -0.215 / -0.302</td>
      <td>-0.072 / -0.067 / -0.052</td>
    </tr>
    <tr>
      <td>85%</td>
      <td>85.88%</td>
      <td>0.990 / 1.300 / 1.918</td>
      <td>-0.155 / -0.203 / -0.296</td>
      <td>-0.073 / -0.068 / -0.054</td>
    </tr>
    <tr>
      <td>90%</td>
      <td>90.76%</td>
      <td>1.066 / 1.414 / 2.102</td>
      <td>-0.163 / -0.220 / -0.325</td>
      <td>-0.073 / -0.067 / -0.053</td>
    </tr>
    <tr>
      <td>92%</td>
      <td>93.08%</td>
      <td>1.010 / 1.357 / 2.032</td>
      <td>-0.154 / -0.203 / -0.304</td>
      <td>-0.073 / -0.067 / -0.053</td>
    </tr>
    <tr>
      <td>93%</td>
      <td>93.87%</td>
      <td>1.030 / 1.365 / 1.973</td>
      <td>-0.148 / -0.176 / -0.280</td>
      <td>-0.073 / -0.068 / -0.054</td>
    </tr>
    <tr>
      <td rowspan="8"><code>xiangshan_coupledl2</code></td>
      <td>40%</td>
      <td>41.28%</td>
      <td>2.838 / 3.899 / 5.946</td>
      <td>-0.426 / -0.585 / -0.892</td>
      <td>-1.131 / -1.450 / -2.080</td>
    </tr>
    <tr>
      <td>65%</td>
      <td>65.89%</td>
      <td>2.101 / 2.894 / 4.457</td>
      <td>-0.314 / -0.434 / -0.667</td>
      <td>-0.728 / -0.916 / -1.330</td>
    </tr>
    <tr>
      <td>70%</td>
      <td>70.97%</td>
      <td>2.572 / 3.502 / 5.307</td>
      <td>-0.391 / -0.531 / -0.803</td>
      <td>-0.960 / -1.238 / -1.802</td>
    </tr>
    <tr>
      <td>75%</td>
      <td>75.97%</td>
      <td>3.177 / 4.337 / 6.729</td>
      <td>-0.480 / -0.634 / -0.818</td>
      <td>-1.026 / -1.328 / -2.005</td>
    </tr>
    <tr>
      <td>80%</td>
      <td>81.10%</td>
      <td>2.877 / 3.866 / 5.837</td>
      <td>-0.409 / -0.581 / -0.878</td>
      <td>-1.012 / -1.304 / -1.904</td>
    </tr>
    <tr>
      <td>85%</td>
      <td>86.00%</td>
      <td>2.295 / 3.031 / 4.493</td>
      <td>-0.375 / -0.507 / -0.731</td>
      <td>-0.764 / -0.963 / -1.390</td>
    </tr>
    <tr>
      <td>86%</td>
      <td>86.93%</td>
      <td>2.165 / 2.992 / 4.560</td>
      <td>-0.329 / -0.446 / -0.686</td>
      <td>-0.831 / -1.063 / -1.520</td>
    </tr>
    <tr>
      <td>87%</td>
      <td>88.05%</td>
      <td>2.298 / 3.171 / 4.781</td>
      <td>-0.365 / -0.468 / -0.742</td>
      <td>-0.791 / -1.016 / -1.455</td>
    </tr>
  </tbody>
</table>

A dash means the benchmark does not carry that file.

| benchmark | standard cell area | inserted by the clock tree | macro area | core area |
| --- | --- | --- | --- | --- |
| `ariane/u40` | 24,902 um2 | 1,333 cells | 19,758 um2 | 104,836 um2 |
| `ariane/u65` | 23,271 um2 | 1,258 cells | 19,758 um2 | 64,469 um2 |
| `ariane/u70` | 23,282 um2 | 1,212 cells | 19,758 um2 | 59,879 um2 |
| `ariane/u72` | 23,326 um2 | 1,218 cells | 19,758 um2 | 58,199 um2 |
| `ariane/u73` | 23,200 um2 | 1,208 cells | 19,758 um2 | 57,407 um2 |
| `ariane/u74` | 23,276 um2 | 1,197 cells | 19,758 um2 | 56,634 um2 |
| `blackparrot_2/u65` | 16,117 um2 | 1,200 cells | 15,341 um2 | 47,617 um2 |
| `mempool_tile/u40` | 30,533 um2 | 1,524 cells | 3,757 um2 | 79,670 um2 |
| `mempool_tile/u65` | 29,219 um2 | 1,503 cells | 3,757 um2 | 49,042 um2 |
| `mempool_tile/u70` | 29,263 um2 | 1,521 cells | 3,757 um2 | 45,531 um2 |
| `mempool_tile/u75` | 29,224 um2 | 1,421 cells | 3,757 um2 | 42,485 um2 |
| `mempool_tile/u80` | 29,206 um2 | 1,445 cells | 3,757 um2 | 39,834 um2 |
| `mempool_tile/u85` | 29,166 um2 | 1,418 cells | 3,757 um2 | 37,498 um2 |
| `picorv32/u40` | 2,573 um2 | 112 cells | 0 um2 | 5,642 um2 |
| `picorv32/u65` | 2,291 um2 | 108 cells | 0 um2 | 3,471 um2 |
| `picorv32/u70` | 2,287 um2 | 106 cells | 0 um2 | 3,221 um2 |
| `picorv32/u75` | 2,290 um2 | 106 cells | 0 um2 | 2,992 um2 |
| `picorv32/u80` | 2,285 um2 | 108 cells | 0 um2 | 2,812 um2 |
| `picorv32/u85` | 2,282 um2 | 99 cells | 0 um2 | 2,643 um2 |
| `picorv32/u87` | 2,284 um2 | 101 cells | 0 um2 | 2,585 um2 |
| `picorv32/u88` | 2,280 um2 | 100 cells | 0 um2 | 2,557 um2 |
| `picorv32/u89` | 2,284 um2 | 101 cells | 0 um2 | 2,530 um2 |
| `tpu/u40` | 6,101 um2 | 229 cells | 0 um2 | 13,062 um2 |
| `tpu/u65` | 5,282 um2 | 219 cells | 0 um2 | 8,016 um2 |
| `tpu/u70` | 5,278 um2 | 216 cells | 0 um2 | 7,446 um2 |
| `tpu/u75` | 5,277 um2 | 215 cells | 0 um2 | 6,942 um2 |
| `tpu/u80` | 5,270 um2 | 209 cells | 0 um2 | 6,526 um2 |
| `tpu/u85` | 5,272 um2 | 208 cells | 0 um2 | 6,139 um2 |
| `tpu/u90` | 5,269 um2 | 206 cells | 0 um2 | 5,806 um2 |
| `tpu/u92` | 5,267 um2 | 204 cells | 0 um2 | 5,658 um2 |
| `tpu/u93` | 5,266 um2 | 204 cells | 0 um2 | 5,610 um2 |
| `xiangshan_coupledl2/u40` | 60,712 um2 | 4,950 cells | 33,686 um2 | 228,698 um2 |
| `xiangshan_coupledl2/u65` | 59,032 um2 | 3,702 cells | 33,686 um2 | 140,708 um2 |
| `xiangshan_coupledl2/u70` | 59,008 um2 | 3,544 cells | 33,686 um2 | 130,606 um2 |
| `xiangshan_coupledl2/u75` | 58,948 um2 | 3,565 cells | 33,686 um2 | 121,934 um2 |
| `xiangshan_coupledl2/u80` | 59,028 um2 | 3,530 cells | 33,686 um2 | 114,326 um2 |
| `xiangshan_coupledl2/u85` | 58,808 um2 | 3,449 cells | 33,686 um2 | 107,546 um2 |
| `xiangshan_coupledl2/u86` | 58,714 um2 | 3,481 cells | 33,686 um2 | 106,292 um2 |
| `xiangshan_coupledl2/u87` | 58,824 um2 | 3,464 cells | 33,686 um2 | 105,064 um2 |

## Contents of a benchmark

| file | what it is |
| --- | --- |
| `input.v.gz`, `input.def.gz`, `input.odb.gz` | post-CTS netlist with the clock tree, legalized placement, database |
| `constraint.sdc` | the constraint the layout was generated under |
| `scenario/BC.sdc`, `TC.sdc`, `WC.sdc` | one constraint per corner |
| `scenario/config.json` | periods, uncertainties and boundary values |
| `mcmm.tcl` | modes, corners and scenes, in the commands the evaluation uses |
| `benchmark.json` | target and measured utilization, areas, and the timing this benchmark was published with |
| `sha256.json` | digests of the uncompressed files |
| `evaluation_timing_summary.csv` | post-route timing from the evaluation |
| `orfs_generated.sdc` | what ORFS wrote back, for reference |

`benchmarks/<design>/source_synth.v.gz` sits one level up, beside the
utilization directories. It is the pre-CTS synthesis reference the equivalence
proof compares against, and it is the same file for every sweep point of a
design, so it is published once. Each benchmark's `sha256.json` still carries
its digest.

## Platform

`platform/asap7` holds the technology LEF `asap7_tech_1x_260907.lef`, the three
standard cell LEFs and the 45 NLDM libraries, 15 per corner.

The SRAM abstracts live with the design that uses them, at
`platform/<design>/lef` and `platform/<design>/lib`. A design with macros
cannot be read without them. The macro Liberty is characterised at a single
corner and that one file is used in all three scenes.

- `platform/ariane`: 1 LEF, 1 Liberty
- `platform/blackparrot_2`: 5 LEF, 5 Liberty
- `platform/mempool_tile`: 2 LEF, 2 Liberty
- `platform/xiangshan_coupledl2`: 6 LEF, 6 Liberty

Corners are BC at FF 0.77V 0C, TC at TT 0.70V 25C and WC at SS 0.63V 100C.
Units inside the files are ps, fF and um.

## Unpacking

    gunzip -k benchmarks/<design>/u<target>/*.gz
    gunzip -k platform/<design>/lib/*.gz

`sha256.json` lists digests of the uncompressed files.

## Timing a benchmark

    source benchmarks/<design>/u<target>/mcmm.tcl
    ispd27_read_libraries
    read_def benchmarks/<design>/u<target>/input.def
    ispd27_define_scenes

The paths inside `mcmm.tcl` resolve from the repository root. The numbers this
reports are more optimistic than the ones above, because those include a SPEF
extracted after global routing and this setup has no parasitics.
