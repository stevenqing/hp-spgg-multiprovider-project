# MaaSSim LLM Common-State Smoke

Model: `gpt-5.4-mini-20260317`. Prompt variant: `scored`. Seeds: `5`. Max active snapshots per seed: `20`.
Scenario: `normal`.
Utility penalties: driver_reject_penalty=`2.0`, passenger_reject_penalty=`0.5`.

LLM-family policies see a legal one-to-one assignment menu plus method-specific public, belief, history, or score context, then return JSON with `assignment_id` and copied `candidate_ids`.

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Oracle-match | LLM parse | LLM repair | LLM fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 28.90 +/- 8.34 | 19.6 | 5.4 | 0.822 | 1.66 | 0.920 | n/a | n/a | n/a |
| Random | -0.72 +/- 4.17 | 13.6 | 8.8 | 0.716 | 120.77 | 0.180 | n/a | n/a | n/a |
| LLM-PACT | 31.29 +/- 7.76 | 20.2 | 4.2 | 0.862 | 2.19 | 0.920 | 1.000 | 0.000 | 0.000 |
| LLM-belief | 28.27 +/- 7.47 | 19.4 | 5.2 | 0.829 | 3.50 | 0.890 | 1.000 | 0.000 | 0.000 |
| LLM-PSRL | 29.81 +/- 7.80 | 19.8 | 4.8 | 0.841 | 3.22 | 0.850 | 1.000 | 0.000 | 0.000 |
| A-ToM-1 | 28.97 +/- 8.01 | 19.6 | 5.4 | 0.822 | 0.20 | 0.980 | 1.000 | 0.000 | 0.000 |
| Oracle | 37.64 +/- 6.01 | 20.6 | 0.4 | 0.989 | 18.48 | 0.740 | n/a | n/a | n/a |
