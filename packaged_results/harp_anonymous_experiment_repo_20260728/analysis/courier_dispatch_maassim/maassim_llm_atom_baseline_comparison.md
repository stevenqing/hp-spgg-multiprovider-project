# MaaSSim LLM / A-ToM Baseline Comparison

Common-state replay over `5` seeds and the first `20` active snapshots per seed using `gpt-5.4-mini-20260317`.

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Oracle-match | Parse | Repair | Fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 28.90 +/- 8.34 | 19.6 | 5.4 | 0.822 | 1.66 | 0.920 | n/a | n/a | n/a |
| Random | -0.72 +/- 4.17 | 13.6 | 8.8 | 0.716 | 120.77 | 0.180 | n/a | n/a | n/a |
| PACT | 31.29 +/- 7.76 | 20.2 | 4.2 | 0.862 | 2.19 | 0.900 | n/a | n/a | n/a |
| LLM+PACT-score | 31.29 +/- 7.76 | 20.2 | 4.2 | 0.862 | 2.19 | 0.920 | 1.000 | 0.000 | 0.000 |
| A-ToM-0 | 29.02 +/- 7.99 | 19.6 | 5.4 | 0.822 | 0.26 | 0.970 | 1.000 | 0.000 | 0.000 |
| A-ToM-1 | 28.96 +/- 8.00 | 19.6 | 5.4 | 0.822 | 1.31 | 0.930 | 1.000 | 0.000 | 0.000 |
| ECON-BNE | 28.88 +/- 8.03 | 19.6 | 5.4 | 0.822 | 1.05 | 0.950 | 1.000 | 0.000 | 0.000 |
| Oracle | 37.64 +/- 6.01 | 20.6 | 0.4 | 0.989 | 18.48 | 0.740 | n/a | n/a | n/a |

Readout: the A-ToM and ECON-BNE baselines are now connected to the same MaaSSim legal-assignment replay interface and all parse cleanly. On the scaled 5-seed core run, PACT and LLM+PACT-score tie at `31.29` utility, while A-ToM-0, A-ToM-1, and ECON-BNE sit around `28.9-29.0`. LLM+PACT-score is not a pure baseline; it exposes PACT-style assignment scores to the model. The PACT-vs-A-ToM gap is directionally consistent but still not a strong significance claim because seed-level SEM remains large.