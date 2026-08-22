# MaaSSim Controlled Synthetic Baseline Comparison

Controlled MaaSSim matching with synthetic hidden driver rules, seed set `{0,1,2,3,4}`.

| Policy | Seeds | Driver P(true) | Driver rule acc | Mean wait | Rides | Rejects | Synthetic decline | Passenger rule acc | Passenger reject |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 5 | 0.205 +/- 0.023 | 0.730 +/- 0.014 | 138.6 +/- 9.5 | 31.0 +/- 1.1 | 24.8 +/- 2.5 | 0.426 | 0.536 +/- 0.001 | 0.208 |
| Random | 5 | 0.220 +/- 0.019 | 0.757 +/- 0.014 | 158.4 +/- 12.9 | 26.2 +/- 1.8 | 29.6 +/- 3.2 | 0.473 | 0.551 +/- 0.003 | 0.334 |
| PACT | 5 | 0.203 +/- 0.031 | 0.728 +/- 0.007 | 143.8 +/- 9.4 | 31.2 +/- 1.1 | 27.4 +/- 2.7 | 0.463 | 0.532 +/- 0.002 | 0.203 |
| PACT+ | 5 | 0.203 +/- 0.031 | 0.727 +/- 0.007 | 143.8 +/- 9.4 | 31.2 +/- 1.1 | 27.4 +/- 2.7 | 0.463 | 0.532 +/- 0.002 | 0.203 |
| Oracle | 5 | 0.203 +/- 0.031 | 0.728 +/- 0.007 | 143.8 +/- 9.4 | 31.2 +/- 1.1 | 27.4 +/- 2.7 | 0.463 | 0.532 +/- 0.002 | 0.203 |

Readout: this is still a smoke-scale integration table, not a tuned MaaSSim result. PACT and PACT+ can be identical when the small candidate sets do not make the exploration bonus change the selected assignment.

![MaaSSim baseline comparison](../../figs/fig_maassim_persona_v2_baselines.png)
