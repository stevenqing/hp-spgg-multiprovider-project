# E-D: True Reward-Locality Violation

This is a controlled HP-SPGG-derived DGP. Only agent 0 has the cross-agent reward $r_0=r_0^{\theta_0}-\alpha r_1^{\theta_1}$; the other rewards remain local. The asymmetric edge prevents the social-comparison term from cancelling in total welfare.

Episodes: 100; seeds: 10; Gaussian sigma: 0.08.

| calibration | alpha | method | cumulative regret | gap vs joint | true-type mass |
|---|---:|---|---:|---:|---:|
| analytic-mixed | 0.00 | Joint-PSRL-Coupled | 0.005 $\pm$ 0.004 | +0.000 | 1.000 |
| analytic-mixed | 0.00 | PACT (factored) | 0.007 $\pm$ 0.006 | +0.002 | 1.000 |
| analytic-mixed | 0.00 | PSRL-NoType | 1.075 $\pm$ 0.161 | +1.070 | 0.016 |
| analytic-mixed | 0.25 | Joint-PSRL-Coupled | 0.002 $\pm$ 0.002 | +0.000 | 1.000 |
| analytic-mixed | 0.25 | PACT (factored) | 0.028 $\pm$ 0.014 | +0.026 | 1.000 |
| analytic-mixed | 0.25 | PSRL-NoType | 1.257 $\pm$ 0.195 | +1.255 | 0.016 |
| analytic-mixed | 0.50 | Joint-PSRL-Coupled | 0.021 $\pm$ 0.011 | +0.000 | 0.999 |
| analytic-mixed | 0.50 | PACT (factored) | 0.034 $\pm$ 0.015 | +0.014 | 1.000 |
| analytic-mixed | 0.50 | PSRL-NoType | 3.735 $\pm$ 0.540 | +3.714 | 0.016 |
| analytic-mixed | 1.00 | Joint-PSRL-Coupled | 0.145 $\pm$ 0.056 | +0.000 | 1.000 |
| analytic-mixed | 1.00 | PACT (factored) | 0.222 $\pm$ 0.076 | +0.077 | 1.000 |
| analytic-mixed | 1.00 | PSRL-NoType | 17.090 $\pm$ 1.883 | +16.944 | 0.016 |
| analytic-mixed | 2.00 | Joint-PSRL-Coupled | 0.665 $\pm$ 0.125 | +0.000 | 1.000 |
| analytic-mixed | 2.00 | PACT (factored) | 0.784 $\pm$ 0.142 | +0.118 | 1.000 |
| analytic-mixed | 2.00 | PSRL-NoType | 27.890 $\pm$ 1.791 | +27.225 | 0.016 |
| analytic-mixed | 4.00 | Joint-PSRL-Coupled | 0.584 $\pm$ 0.146 | +0.000 | 0.999 |
| analytic-mixed | 4.00 | PACT (factored) | 1.266 $\pm$ 0.335 | +0.683 | 0.999 |
| analytic-mixed | 4.00 | PSRL-NoType | 44.172 $\pm$ 4.334 | +43.589 | 0.016 |

PACT uses the correct coupled reward for planning but projects the likelihood to independent marginals; Joint-PSRL-Coupled uses the full joint likelihood. No CCE program is solved: all finite actions are enumerated exactly.
