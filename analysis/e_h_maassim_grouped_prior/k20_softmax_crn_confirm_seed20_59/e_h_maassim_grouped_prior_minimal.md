# E-H MaaSSim Grouped Coupling Prior — Minimal Unit

The preregistered minimal unit is rho in {0,1}, g=4, n=8, m=2, K=20, seeds 20--59 (n=40).
Driver decisions are deterministic hidden rules; provider/LLM calls are zero.
Likelihood mode: softmax.

| rho | arm - Joint | mean | SEM | 95% CI | covers zero |
|---:|---|---:|---:|---:|:---:|
| 0 | harp | +0.000 | 0.000 | [+0.000, +0.000] | True |
| 0 | harp_s | +0.000 | 0.000 | [+0.000, +0.000] | True |
| 1 | harp | +0.423 | 0.313 | [-0.210, +1.056] | True |
| 1 | harp_s | +0.000 | 0.000 | [+0.000, +0.000] | True |

Mean corr TV: rho=0 0.000e+00; rho=1 1.000.
Mean unelicited fraction: rho=0 0.580; rho=1 0.580.
Belief movement gate: {'definition': "rho=1 final-round pre-decision mean marginal probability assigned to each driver's true full persona, averaged over n=8 drivers and 40 seeds", 'uniform_prior': 0.0625, 'threshold': 0.125, 'threshold_multiple': 2.0, 'arms': {'joint': {'mean': 0.14703843615495604, 'sem': 0.0177319919541938, 'ratio_to_uniform_prior': 2.3526149784792967}, 'harp': {'mean': 0.09705837847783652, 'sem': 0.005087486738738183, 'ratio_to_uniform_prior': 1.5529340556453843}, 'harp_s': {'mean': 0.09705837847783652, 'sem': 0.005087486738738183, 'ratio_to_uniform_prior': 1.5529340556453843}}, 'passed': True}.
Prediction status: {'P1': True, 'P2': 'not supported by rho={0,1} endpoints; rho=0.5 not run after minimal stop', 'P3': 'not tested after minimal stop', 'P4': True}.
Direct HARP-S minus HARP at rho=1: -0.423 +/- 0.313, 95% CI [-1.056, +0.210].
Decision: The full-persona decision-relevance gate passed and posterior correlation reached its maximum, but Joint showed no measurable oracle-regret advantage over HARP. This is the preregistered positive null result; the wider parameter grid was halted without tuning.
