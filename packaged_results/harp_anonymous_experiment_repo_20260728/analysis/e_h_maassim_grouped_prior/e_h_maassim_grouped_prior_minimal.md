# E-H MaaSSim Grouped Coupling Prior — Minimal Unit

The preregistered minimal unit is rho in {0,1}, g=4, n=8, m=2, K=5, 20 common environment seeds.
Driver decisions are deterministic hidden rules; provider/LLM calls are zero.

| rho | arm - Joint | mean | SEM | 95% CI | covers zero |
|---:|---|---:|---:|---:|:---:|
| 0 | harp | -0.234 | 0.365 | [-0.997, +0.530] | True |
| 0 | harp_s | -0.234 | 0.365 | [-0.997, +0.530] | True |
| 1 | harp | -0.336 | 0.256 | [-0.872, +0.200] | True |
| 1 | harp_s | -0.399 | 0.241 | [-0.903, +0.106] | True |

Mean corr TV: rho=0 0.000e+00; rho=1 1.000.
Mean unelicited fraction: rho=0 0.724; rho=1 0.724.
Prediction status: {'P1': True, 'P2': 'not supported by rho={0,1} endpoints; rho=0.5 not run after minimal stop', 'P3': 'not tested after minimal stop', 'P4': True}.
Direct HARP-S minus HARP at rho=1: -0.063 +/- 0.172, 95% CI [-0.423, +0.298].
Decision: The full-persona decision-relevance gate passed and posterior correlation reached its maximum, but Joint showed no measurable oracle-regret advantage over HARP. This is the preregistered positive null result; the wider parameter grid was halted without tuning.
