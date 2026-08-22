# MaaSSim LLM Common-State Smoke

Model: `gpt-5.4-mini-20260317`. Prompt variant: `scored`. Seeds: `5`. Max active snapshots per seed: `20`.
Utility penalties: driver_reject_penalty=`5.0`, passenger_reject_penalty=`0.5`.

LLM-family policies see a legal one-to-one assignment menu plus method-specific public, belief, history, or score context, then return JSON with `assignment_id` and copied `candidate_ids`.

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Oracle-match | LLM parse | LLM repair | LLM fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 12.70 +/- 11.83 | 19.6 | 5.4 | 0.822 | 1.66 | 0.920 | n/a | n/a | n/a |
| Random | -27.12 +/- 7.54 | 13.6 | 8.8 | 0.716 | 120.77 | 0.180 | n/a | n/a | n/a |
| LLM-PACT | 18.37 +/- 10.11 | 20.2 | 4.2 | 0.862 | 5.63 | 0.880 | 0.990 | 0.010 | 0.010 |
| A-ToM-0 | 12.82 +/- 11.44 | 19.6 | 5.4 | 0.822 | 0.44 | 0.970 | 1.000 | 0.000 | 0.000 |
| A-ToM-1 | 13.67 +/- 11.12 | 19.6 | 5.2 | 0.829 | 0.48 | 0.950 | 1.000 | 0.000 | 0.000 |
| ECON-BNE | 12.78 +/- 11.45 | 19.6 | 5.4 | 0.822 | 0.26 | 0.960 | 1.000 | 0.000 | 0.000 |
| Oracle | 36.44 +/- 5.09 | 20.6 | 0.4 | 0.989 | 18.48 | 0.740 | n/a | n/a | n/a |
