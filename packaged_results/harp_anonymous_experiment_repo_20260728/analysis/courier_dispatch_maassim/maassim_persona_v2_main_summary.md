# MaaSSim Controlled Synthetic Baseline Comparison

Controlled MaaSSim matching with synthetic hidden driver rules, seed set `{0,1,2,3,4,5,6,7,8,9}`.

| Policy | Seeds | Driver P(true) | Driver rule acc | Mean wait | Rides | Rejects | Synthetic decline | Passenger rule acc | Passenger reject |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 10 | 0.257 +/- 0.046 | 0.732 +/- 0.025 | 121.4 +/- 4.6 | 30.3 +/- 1.2 | 18.9 +/- 3.4 | 0.368 | 0.532 +/- 0.003 | 0.233 |
| Random | 10 | 0.321 +/- 0.054 | 0.778 +/- 0.020 | 145.9 +/- 6.0 | 25.3 +/- 0.9 | 26.3 +/- 3.2 | 0.449 | 0.551 +/- 0.002 | 0.354 |
| PACT | 10 | 0.268 +/- 0.040 | 0.739 +/- 0.022 | 127.6 +/- 7.0 | 29.8 +/- 1.1 | 18.5 +/- 2.8 | 0.382 | 0.531 +/- 0.002 | 0.230 |
| PACT+ | 10 | 0.268 +/- 0.040 | 0.739 +/- 0.022 | 127.6 +/- 7.0 | 29.8 +/- 1.1 | 18.5 +/- 2.8 | 0.382 | 0.531 +/- 0.002 | 0.230 |
| Oracle | 10 | 0.268 +/- 0.040 | 0.739 +/- 0.022 | 127.6 +/- 7.0 | 29.8 +/- 1.1 | 18.5 +/- 2.8 | 0.382 | 0.531 +/- 0.002 | 0.230 |

Readout: this is still a smoke-scale integration table, not a tuned MaaSSim result. PACT and PACT+ can be identical when the small candidate sets do not make the exploration bonus change the selected assignment.

![MaaSSim baseline comparison](../../figs/fig_maassim_persona_v2_main.png)
