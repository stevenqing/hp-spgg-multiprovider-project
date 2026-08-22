# E-D: True Reward-Locality Violation

This is a controlled HP-SPGG-derived DGP. Only agent 0 has the cross-agent reward $r_0=(r_0^{\theta_0}-\alpha r_1^{\theta_1}+\alpha)/(1+\alpha)$; the other rewards remain local. The affine normalization keeps rewards in $[0,1]$, and the asymmetric edge prevents cancellation in total welfare.

Episodes: 100; seeds: 10; Gaussian sigma: 0.08.

| calibration | alpha | method | cumulative regret | gap vs joint | true-type mass | marginal TV |
|---|---:|---|---:|---:|---:|---:|
| DeepSeek-V3.2-live | 0.00 | Joint-PSRL-Coupled | 1.130 $\pm$ 0.154 | +0.000 $\pm$ 0.000 | 0.894 | 0.000 |
| DeepSeek-V3.2-live | 0.00 | PACT (factored) | 1.130 $\pm$ 0.154 | +0.000 $\pm$ 0.000 | 0.964 | 0.000 |
| DeepSeek-V3.2-live | 0.00 | PSRL-NoType | 31.465 $\pm$ 5.175 | +30.335 $\pm$ 5.142 | 0.016 | nan |
| DeepSeek-V3.2-live | 0.25 | Joint-PSRL-Coupled | 0.741 $\pm$ 0.129 | +0.000 $\pm$ 0.000 | 0.863 | 0.000 |
| DeepSeek-V3.2-live | 0.25 | PACT (factored) | 0.724 $\pm$ 0.134 | -0.017 $\pm$ 0.018 | 0.948 | 0.007 |
| DeepSeek-V3.2-live | 0.25 | PSRL-NoType | 29.134 $\pm$ 4.904 | +28.393 $\pm$ 4.806 | 0.016 | nan |
| DeepSeek-V3.2-live | 0.50 | Joint-PSRL-Coupled | 0.687 $\pm$ 0.119 | +0.000 $\pm$ 0.000 | 0.850 | 0.000 |
| DeepSeek-V3.2-live | 0.50 | PACT (factored) | 0.633 $\pm$ 0.122 | -0.053 $\pm$ 0.039 | 0.935 | 0.005 |
| DeepSeek-V3.2-live | 0.50 | PSRL-NoType | 26.523 $\pm$ 4.637 | +25.837 $\pm$ 4.552 | 0.016 | nan |
| DeepSeek-V3.2-live | 1.00 | Joint-PSRL-Coupled | 0.575 $\pm$ 0.116 | +0.000 $\pm$ 0.000 | 0.778 | 0.000 |
| DeepSeek-V3.2-live | 1.00 | PACT (factored) | 0.583 $\pm$ 0.115 | +0.008 $\pm$ 0.008 | 0.930 | 0.008 |
| DeepSeek-V3.2-live | 1.00 | PSRL-NoType | 24.788 $\pm$ 5.147 | +24.212 $\pm$ 5.056 | 0.016 | nan |
| DeepSeek-V3.2-live | 2.00 | Joint-PSRL-Coupled | 0.545 $\pm$ 0.108 | +0.000 $\pm$ 0.000 | 0.730 | 0.000 |
| DeepSeek-V3.2-live | 2.00 | PACT (factored) | 0.587 $\pm$ 0.132 | +0.042 $\pm$ 0.047 | 0.897 | 0.013 |
| DeepSeek-V3.2-live | 2.00 | PSRL-NoType | 22.067 $\pm$ 4.902 | +21.522 $\pm$ 4.812 | 0.016 | nan |
| DeepSeek-V3.2-live | 4.00 | Joint-PSRL-Coupled | 0.466 $\pm$ 0.108 | +0.000 $\pm$ 0.000 | 0.693 | 0.000 |
| DeepSeek-V3.2-live | 4.00 | PACT (factored) | 0.517 $\pm$ 0.131 | +0.051 $\pm$ 0.107 | 0.886 | 0.017 |
| DeepSeek-V3.2-live | 4.00 | PSRL-NoType | 19.930 $\pm$ 4.766 | +19.464 $\pm$ 4.702 | 0.016 | nan |
| analytic-mixed | 0.00 | Joint-PSRL-Coupled | 0.001 $\pm$ 0.001 | +0.000 $\pm$ 0.000 | 1.000 | 0.000 |
| analytic-mixed | 0.00 | PACT (factored) | 0.001 $\pm$ 0.001 | +0.000 $\pm$ 0.000 | 1.000 | 0.000 |
| analytic-mixed | 0.00 | PSRL-NoType | 0.177 $\pm$ 0.048 | +0.176 $\pm$ 0.047 | 0.016 | nan |
| analytic-mixed | 0.25 | Joint-PSRL-Coupled | 0.047 $\pm$ 0.030 | +0.000 $\pm$ 0.000 | 1.000 | 0.000 |
| analytic-mixed | 0.25 | PACT (factored) | 0.045 $\pm$ 0.031 | -0.002 $\pm$ 0.002 | 1.000 | 0.000 |
| analytic-mixed | 0.25 | PSRL-NoType | 0.505 $\pm$ 0.135 | +0.458 $\pm$ 0.118 | 0.016 | nan |
| analytic-mixed | 0.50 | Joint-PSRL-Coupled | 0.049 $\pm$ 0.028 | +0.000 $\pm$ 0.000 | 1.000 | 0.000 |
| analytic-mixed | 0.50 | PACT (factored) | 0.049 $\pm$ 0.028 | -0.000 $\pm$ 0.000 | 1.000 | 0.000 |
| analytic-mixed | 0.50 | PSRL-NoType | 2.447 $\pm$ 0.493 | +2.398 $\pm$ 0.482 | 0.016 | nan |
| analytic-mixed | 1.00 | Joint-PSRL-Coupled | 0.206 $\pm$ 0.087 | +0.000 $\pm$ 0.000 | 1.000 | 0.000 |
| analytic-mixed | 1.00 | PACT (factored) | 0.155 $\pm$ 0.065 | -0.051 $\pm$ 0.051 | 1.000 | 0.000 |
| analytic-mixed | 1.00 | PSRL-NoType | 7.039 $\pm$ 0.951 | +6.832 $\pm$ 0.887 | 0.016 | nan |
| analytic-mixed | 2.00 | Joint-PSRL-Coupled | 0.203 $\pm$ 0.065 | +0.000 $\pm$ 0.000 | 0.981 | 0.000 |
| analytic-mixed | 2.00 | PACT (factored) | 0.212 $\pm$ 0.064 | +0.009 $\pm$ 0.009 | 0.994 | 0.001 |
| analytic-mixed | 2.00 | PSRL-NoType | 8.083 $\pm$ 0.631 | +7.879 $\pm$ 0.582 | 0.016 | nan |
| analytic-mixed | 4.00 | Joint-PSRL-Coupled | 0.213 $\pm$ 0.057 | +0.000 $\pm$ 0.000 | 0.850 | 0.000 |
| analytic-mixed | 4.00 | PACT (factored) | 0.199 $\pm$ 0.057 | -0.013 $\pm$ 0.013 | 0.955 | 0.007 |
| analytic-mixed | 4.00 | PSRL-NoType | 8.391 $\pm$ 0.790 | +8.179 $\pm$ 0.765 | 0.016 | nan |

PACT uses the correct coupled reward for planning but projects the likelihood to independent marginals; Joint-PSRL-Coupled uses the full joint likelihood. No CCE program is solved: all 27 actions in the Cartesian subgrid $\{0,0.5,1\}^3$ are enumerated exactly.
