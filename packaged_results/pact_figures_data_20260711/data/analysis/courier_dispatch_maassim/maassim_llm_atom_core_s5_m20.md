# MaaSSim LLM Common-State Smoke

Model: `gpt-5.4-mini-20260317`. Prompt variant: `scored`. Seeds: `5`. Max active snapshots per seed: `20`.

LLM-family policies see a legal one-to-one assignment menu plus method-specific public, belief, history, or score context, then return JSON with `assignment_id` and copied `candidate_ids`.

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Oracle-match | LLM parse | LLM repair | LLM fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 28.90 +/- 8.34 | 19.6 | 5.4 | 0.822 | 1.66 | 0.920 | n/a | n/a | n/a |
| Random | -0.72 +/- 4.17 | 13.6 | 8.8 | 0.716 | 120.77 | 0.180 | n/a | n/a | n/a |
| PACT | 31.29 +/- 7.76 | 20.2 | 4.2 | 0.862 | 2.19 | 0.900 | n/a | n/a | n/a |
| LLM+PACT-score | 31.29 +/- 7.76 | 20.2 | 4.2 | 0.862 | 2.19 | 0.920 | 1.000 | 0.000 | 0.000 |
| A-ToM-0 | 29.02 +/- 7.99 | 19.6 | 5.4 | 0.822 | 0.26 | 0.970 | 1.000 | 0.000 | 0.000 |
| A-ToM-1 | 28.96 +/- 8.00 | 19.6 | 5.4 | 0.822 | 1.31 | 0.930 | 1.000 | 0.000 | 0.000 |
| ECON-BNE | 28.88 +/- 8.03 | 19.6 | 5.4 | 0.822 | 1.05 | 0.950 | 1.000 | 0.000 | 0.000 |
| Oracle | 37.64 +/- 6.01 | 20.6 | 0.4 | 0.989 | 18.48 | 0.740 | n/a | n/a | n/a |
