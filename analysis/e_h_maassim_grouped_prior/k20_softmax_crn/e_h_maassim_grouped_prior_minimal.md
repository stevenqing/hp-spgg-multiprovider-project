# E-H MaaSSim Grouped Coupling Prior — Minimal Unit

The preregistered minimal unit is rho in {0,1}, g=4, n=8, m=2, K=20, 20 common environment seeds.
Driver decisions are deterministic hidden rules; provider/LLM calls are zero.
Likelihood mode: softmax.

| rho | arm - Joint | mean | SEM | 95% CI | covers zero |
|---:|---|---:|---:|---:|:---:|
| 0 | harp | +0.000 | 0.000 | [+0.000, +0.000] | True |
| 0 | harp_s | +0.000 | 0.000 | [+0.000, +0.000] | True |
| 1 | harp | +0.786 | 0.317 | [+0.123, +1.448] | False |
| 1 | harp_s | +0.000 | 0.000 | [+0.000, +0.000] | True |

Mean corr TV: rho=0 0.000e+00; rho=1 1.000.
Mean unelicited fraction: rho=0 0.541; rho=1 0.541.
Belief movement gate: {'definition': "rho=1 final-round pre-decision mean marginal probability assigned to each driver's true full persona, averaged over n=8 drivers and 20 seeds", 'uniform_prior': 0.0625, 'threshold': 0.125, 'threshold_multiple': 2.0, 'arms': {'joint': {'mean': 0.15236638242484496, 'sem': 0.026781788863827403, 'ratio_to_uniform_prior': 2.4378621187975194}, 'harp': {'mean': 0.10247222397202707, 'sem': 0.007142265785256714, 'ratio_to_uniform_prior': 1.6395555835524331}, 'harp_s': {'mean': 0.10247222397202707, 'sem': 0.007142265785256714, 'ratio_to_uniform_prior': 1.6395555835524331}}, 'passed': True}.
Prediction status: {'P1': True, 'P2': 'not supported by rho={0,1} endpoints; rho=0.5 not run after minimal stop', 'P3': 'not tested after minimal stop', 'P4': True}.
Direct HARP-S minus HARP at rho=1: -0.786 +/- 0.317, 95% CI [-1.448, -0.123].
Decision: None
