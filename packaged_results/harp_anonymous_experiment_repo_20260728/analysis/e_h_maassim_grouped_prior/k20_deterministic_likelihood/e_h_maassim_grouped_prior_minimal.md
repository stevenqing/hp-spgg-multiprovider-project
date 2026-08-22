# E-H MaaSSim Grouped Coupling Prior — Minimal Unit

The preregistered minimal unit is rho in {0,1}, g=4, n=8, m=2, K=20, 20 common environment seeds.
Driver decisions are deterministic hidden rules; provider/LLM calls are zero.
Likelihood mode: deterministic-rule.

| rho | arm - Joint | mean | SEM | 95% CI | covers zero |
|---:|---|---:|---:|---:|:---:|
| 0 | harp | -0.833 | 0.901 | [-2.719, +1.054] | True |
| 0 | harp_s | -0.833 | 0.901 | [-2.719, +1.054] | True |
| 1 | harp | +0.302 | 0.356 | [-0.444, +1.047] | True |
| 1 | harp_s | -1.607 | 0.522 | [-2.698, -0.515] | False |

Mean corr TV: rho=0 0.000e+00; rho=1 1.000.
Mean unelicited fraction: rho=0 0.541; rho=1 0.541.
Belief movement gate: {'definition': "rho=1 final-round pre-decision mean marginal probability assigned to each driver's true full persona, averaged over n=8 drivers and 20 seeds", 'uniform_prior': 0.0625, 'threshold': 0.125, 'threshold_multiple': 2.0, 'arms': {'joint': {'mean': 0.203125, 'sem': 0.011670679917504466, 'ratio_to_uniform_prior': 3.25}, 'harp': {'mean': 0.13203125, 'sem': 0.004905170850141608, 'ratio_to_uniform_prior': 2.1125}, 'harp_s': {'mean': 0.13203125, 'sem': 0.004905170850141608, 'ratio_to_uniform_prior': 2.1125}}, 'passed': True}.
Prediction status: {'P1': True, 'P2': 'not supported by rho={0,1} endpoints; rho=0.5 not run after minimal stop', 'P3': 'not tested after minimal stop', 'P4': False}.
Direct HARP-S minus HARP at rho=1: -1.908 +/- 0.578, 95% CI [-3.117, -0.699].
Decision: The full-persona decision-relevance gate passed and posterior correlation reached its maximum, but Joint showed no measurable oracle-regret advantage over HARP. This is the preregistered positive null result; the wider parameter grid was halted without tuning.
