# E-D: True Reward-Locality Violation

This is a controlled HP-SPGG-derived DGP. Only agent 0 has the cross-agent reward $r_0=r_0^{\theta_0}-\alpha r_1^{\theta_1}$; the other rewards remain local. The asymmetric edge prevents the social-comparison term from cancelling in total welfare.

Episodes: 100; seeds: 10; Gaussian sigma: 0.08.

| calibration | alpha | method | cumulative regret | gap vs joint | true-type mass |
|---|---:|---|---:|---:|---:|
| DeepSeek-V3.2-live | 0.00 | Joint-PSRL-Coupled | 0.980 $\pm$ 0.173 | +0.000 | 0.796 |
| DeepSeek-V3.2-live | 0.00 | PACT (factored) | 0.795 $\pm$ 0.130 | -0.185 | 0.934 |
| DeepSeek-V3.2-live | 0.00 | PSRL-NoType | 31.200 $\pm$ 6.009 | +30.220 | 0.016 |
| DeepSeek-V3.2-live | 0.25 | Joint-PSRL-Coupled | 0.877 $\pm$ 0.152 | +0.000 | 0.871 |
| DeepSeek-V3.2-live | 0.25 | PACT (factored) | 0.746 $\pm$ 0.141 | -0.131 | 0.938 |
| DeepSeek-V3.2-live | 0.25 | PSRL-NoType | 32.964 $\pm$ 6.776 | +32.086 | 0.016 |
| DeepSeek-V3.2-live | 0.50 | Joint-PSRL-Coupled | 0.825 $\pm$ 0.146 | +0.000 | 0.871 |
| DeepSeek-V3.2-live | 0.50 | PACT (factored) | 0.818 $\pm$ 0.131 | -0.007 | 0.937 |
| DeepSeek-V3.2-live | 0.50 | PSRL-NoType | 31.360 $\pm$ 6.727 | +30.535 | 0.016 |
| DeepSeek-V3.2-live | 1.00 | Joint-PSRL-Coupled | 0.755 $\pm$ 0.156 | +0.000 | 0.705 |
| DeepSeek-V3.2-live | 1.00 | PACT (factored) | 0.795 $\pm$ 0.172 | +0.040 | 0.897 |
| DeepSeek-V3.2-live | 1.00 | PSRL-NoType | 43.845 $\pm$ 9.609 | +43.090 | 0.016 |
| DeepSeek-V3.2-live | 2.00 | Joint-PSRL-Coupled | 0.810 $\pm$ 0.226 | +0.000 | 0.908 |
| DeepSeek-V3.2-live | 2.00 | PACT (factored) | 1.280 $\pm$ 0.328 | +0.470 | 0.971 |
| DeepSeek-V3.2-live | 2.00 | PSRL-NoType | 65.755 $\pm$ 13.851 | +64.945 | 0.016 |
| DeepSeek-V3.2-live | 4.00 | Joint-PSRL-Coupled | 1.335 $\pm$ 0.354 | +0.000 | 0.883 |
| DeepSeek-V3.2-live | 4.00 | PACT (factored) | 2.095 $\pm$ 0.483 | +0.760 | 0.914 |
| DeepSeek-V3.2-live | 4.00 | PSRL-NoType | 132.455 $\pm$ 25.798 | +131.120 | 0.016 |

PACT uses the correct coupled reward for planning but projects the likelihood to independent marginals; Joint-PSRL-Coupled uses the full joint likelihood. No CCE program is solved: all finite actions are enumerated exactly.
