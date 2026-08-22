# E-H MaaSSim Grouped Coupling Prior — Minimal Unit

The preregistered minimal unit is rho in {0,1}, g=4, n=8, m=2, K=20, seeds 20--59 (n=40).
Driver decisions are deterministic hidden rules; provider/LLM calls are zero.
Likelihood mode: deterministic-rule.

| rho | arm - Joint | mean | SEM | 95% CI | covers zero |
|---:|---|---:|---:|---:|:---:|
| 0 | harp | +0.000 | 0.000 | [+0.000, +0.000] | True |
| 0 | harp_s | +0.000 | 0.000 | [+0.000, +0.000] | True |
| 1 | harp | +0.786 | 0.364 | [+0.050, +1.523] | False |
| 1 | harp_s | +0.000 | 0.000 | [+0.000, +0.000] | True |

Mean corr TV: rho=0 0.000e+00; rho=1 1.000.
Mean unelicited fraction: rho=0 0.580; rho=1 0.580.
Belief movement gate: {'definition': "rho=1 final-round pre-decision mean marginal probability assigned to each driver's true full persona, averaged over n=8 drivers and 40 seeds", 'uniform_prior': 0.0625, 'threshold': 0.125, 'threshold_multiple': 2.0, 'arms': {'joint': {'mean': 0.1890625, 'sem': 0.013471372037893291, 'ratio_to_uniform_prior': 3.025}, 'harp': {'mean': 0.119140625, 'sem': 0.0047943713189688006, 'ratio_to_uniform_prior': 1.90625}, 'harp_s': {'mean': 0.119140625, 'sem': 0.0047943713189688006, 'ratio_to_uniform_prior': 1.90625}}, 'passed': True}.
Prediction status: {'P1': True, 'P2': 'not supported by rho={0,1} endpoints; rho=0.5 not run after minimal stop', 'P3': 'not tested after minimal stop', 'P4': True}.
Direct HARP-S minus HARP at rho=1: -0.786 +/- 0.364, 95% CI [-1.523, -0.050].
Decision: None
