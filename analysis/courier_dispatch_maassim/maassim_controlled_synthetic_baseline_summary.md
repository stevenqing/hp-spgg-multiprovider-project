# MaaSSim Controlled Synthetic Baseline Comparison

Controlled MaaSSim matching with synthetic hidden driver rules, seed set `{0,1,2,3,4}`.

| Policy | Seeds | P(true) | Rule acc | Mean wait | Rides | Rejects | Synthetic decline |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 5 | 0.199 +/- 0.030 | 0.695 +/- 0.023 | 102.8 +/- 15.4 | 19.6 +/- 0.4 | 12.0 +/- 3.8 | 0.347 |
| Random | 5 | 0.233 +/- 0.037 | 0.731 +/- 0.021 | 136.6 +/- 5.9 | 19.8 +/- 0.2 | 13.2 +/- 3.8 | 0.370 |
| PACT-proxy | 5 | 0.204 +/- 0.034 | 0.707 +/- 0.029 | 132.3 +/- 10.3 | 19.6 +/- 0.2 | 10.0 +/- 2.6 | 0.318 |
| PACT+-proxy | 5 | 0.216 +/- 0.030 | 0.720 +/- 0.020 | 133.2 +/- 10.0 | 19.6 +/- 0.2 | 11.8 +/- 2.0 | 0.369 |
| PACT | 5 | 0.198 +/- 0.029 | 0.702 +/- 0.029 | 99.8 +/- 12.7 | 19.6 +/- 0.4 | 13.0 +/- 5.0 | 0.353 |
| PACT+ | 5 | 0.198 +/- 0.029 | 0.702 +/- 0.029 | 99.8 +/- 12.7 | 19.6 +/- 0.4 | 13.0 +/- 5.0 | 0.353 |
| Oracle | 5 | 0.200 +/- 0.029 | 0.688 +/- 0.023 | 102.8 +/- 15.4 | 19.6 +/- 0.4 | 10.2 +/- 3.9 | 0.304 |

Readout: this is still a smoke-scale integration table, not a tuned MaaSSim result. PACT and PACT+ can be identical when the small candidate sets do not make the exploration bonus change the selected assignment.

![MaaSSim baseline comparison](../../figs/fig_maassim_controlled_baselines.png)
