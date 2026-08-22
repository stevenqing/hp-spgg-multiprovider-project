# E-D: True Reward-Locality Violation

This is a controlled HP-SPGG-derived DGP. Only agent 0 has the cross-agent reward $r_0=r_0^{\theta_0}-\alpha r_1^{\theta_1}$; the other rewards remain local. The asymmetric edge prevents the social-comparison term from cancelling in total welfare.

Episodes: 10; seeds: 2; Gaussian sigma: 0.08.

| calibration | alpha | method | cumulative regret | gap vs joint | true-type mass |
|---|---:|---|---:|---:|---:|
| analytic-mixed | 0.00 | Joint-PSRL-Coupled | 0.000 $\pm$ 0.000 | +0.000 | 0.871 |
| analytic-mixed | 0.00 | PACT (factored) | 0.000 $\pm$ 0.000 | +0.000 | 0.956 |
| analytic-mixed | 0.00 | PSRL-NoType | 0.016 $\pm$ 0.016 | +0.016 | 0.016 |
| analytic-mixed | 1.00 | Joint-PSRL-Coupled | 0.193 $\pm$ 0.193 | +0.000 | 0.924 |
| analytic-mixed | 1.00 | PACT (factored) | 0.254 $\pm$ 0.254 | +0.061 | 0.974 |
| analytic-mixed | 1.00 | PSRL-NoType | 1.241 $\pm$ 0.241 | +1.048 | 0.016 |

PACT uses the correct coupled reward for planning but projects the likelihood to independent marginals; Joint-PSRL-Coupled uses the full joint likelihood. No CCE program is solved: all finite actions are enumerated exactly.
