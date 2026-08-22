# MaaSSim LLM Common-State Smoke

Model: `gpt-5.4-mini-20260317`. Prompt variant: `scored`. Seeds: `5`. Max active snapshots per seed: `20`.
Scenario: `conflict_offer`.
Utility penalties: driver_reject_penalty=`5.0`, passenger_reject_penalty=`0.5`.

LLM-family policies see a legal one-to-one assignment menu plus method-specific public, belief, history, or score context, then return JSON with `assignment_id` and copied `candidate_ids`.

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Oracle-match | LLM parse | LLM repair | LLM fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | -71.71 +/- 15.65 | 11.8 | 18.8 | 0.399 | 1.66 | 0.920 | n/a | n/a | n/a |
| Random | -54.70 +/- 9.20 | 9.8 | 12.6 | 0.598 | 120.77 | 0.180 | n/a | n/a | n/a |
| LLM-PACT | 8.96 +/- 5.47 | 17.4 | 3.2 | 0.896 | 59.94 | 0.070 | 1.000 | 0.000 | 0.000 |
| LLM-belief | -22.80 +/- 10.17 | 15.2 | 10.0 | 0.677 | 25.82 | 0.290 | 1.000 | 0.000 | 0.000 |
| LLM-PSRL | -31.13 +/- 10.10 | 14.4 | 11.4 | 0.634 | 23.96 | 0.350 | 1.000 | 0.000 | 0.000 |
| A-ToM-0 | -30.34 +/- 11.90 | 14.2 | 11.2 | 0.639 | 22.23 | 0.330 | 1.000 | 0.000 | 0.000 |
| A-ToM-1 | -31.88 +/- 12.30 | 14.0 | 11.4 | 0.633 | 23.35 | 0.370 | 1.000 | 0.000 | 0.000 |
| ECON-BNE | -26.09 +/- 10.33 | 15.2 | 10.8 | 0.654 | 24.58 | 0.340 | 1.000 | 0.000 | 0.000 |
| Oracle | 30.70 +/- 5.99 | 21.6 | 1.0 | 0.970 | 38.10 | 0.290 | n/a | n/a | n/a |
