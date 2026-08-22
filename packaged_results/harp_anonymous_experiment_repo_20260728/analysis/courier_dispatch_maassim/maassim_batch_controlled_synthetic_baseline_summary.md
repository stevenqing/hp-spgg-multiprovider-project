# MaaSSim Controlled Synthetic Baseline Comparison

Controlled MaaSSim matching with synthetic hidden driver rules, seed set `{0,1,2,3,4}`.

| Policy | Seeds | Driver P(true) | Driver rule acc | Mean wait | Rides | Rejects | Synthetic decline |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 5 | 0.214 +/- 0.023 | 0.742 +/- 0.007 | 167.5 +/- 6.9 | 39.0 +/- 0.4 | 24.2 +/- 3.2 | 0.433 |
| Random | 5 | 0.224 +/- 0.022 | 0.751 +/- 0.016 | 216.8 +/- 9.1 | 39.0 +/- 0.4 | 34.4 +/- 5.5 | 0.520 |
| PACT | 5 | 0.208 +/- 0.022 | 0.730 +/- 0.013 | 170.7 +/- 7.2 | 39.0 +/- 0.4 | 22.2 +/- 3.5 | 0.409 |
| PACT+ | 5 | 0.208 +/- 0.022 | 0.728 +/- 0.013 | 170.7 +/- 7.2 | 39.0 +/- 0.4 | 22.0 +/- 3.6 | 0.406 |
| Oracle | 5 | 0.198 +/- 0.020 | 0.705 +/- 0.018 | 170.2 +/- 7.4 | 39.2 +/- 0.5 | 16.8 +/- 4.0 | 0.336 |

Readout: this is still a smoke-scale integration table, not a tuned MaaSSim result. PACT and PACT+ can be identical when the small candidate sets do not make the exploration bonus change the selected assignment.

![MaaSSim baseline comparison](../../figs/fig_maassim_batch_controlled_baselines.png)
