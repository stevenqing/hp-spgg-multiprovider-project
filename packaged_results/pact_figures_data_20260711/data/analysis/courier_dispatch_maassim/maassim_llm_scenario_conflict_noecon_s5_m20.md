# MaaSSim LLM Common-State Smoke

Model: `gpt-5.4-mini-20260317`. Prompt variant: `scored`. Seeds: `5`. Max active snapshots per seed: `20`.
Scenario: `conflict_offer`.
Utility penalties: driver_reject_penalty=`5.0`, passenger_reject_penalty=`0.5`.

LLM-family policies see a legal one-to-one assignment menu plus method-specific public, belief, history, or score context, then return JSON with `assignment_id` and copied `candidate_ids`.

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Oracle-match | LLM parse | LLM repair | LLM fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | -108.48 +/- 9.62 | 6.8 | 24.2 | 0.230 | 1.66 | 0.920 | n/a | n/a | n/a |
| Random | -59.15 +/- 9.61 | 8.8 | 13.2 | 0.577 | 120.77 | 0.180 | n/a | n/a | n/a |
| LLM-PACT | 8.79 +/- 4.84 | 16.4 | 3.2 | 0.896 | 64.86 | 0.050 | 1.000 | 0.000 | 0.000 |
| LLM-belief | -30.90 +/- 4.20 | 13.6 | 10.8 | 0.654 | 34.51 | 0.220 | 1.000 | 0.000 | 0.000 |
| LLM-PSRL | -32.93 +/- 7.23 | 13.6 | 11.2 | 0.643 | 30.57 | 0.220 | 1.000 | 0.000 | 0.000 |
| A-ToM-0 | -49.21 +/- 4.71 | 11.6 | 13.8 | 0.560 | 26.84 | 0.310 | 1.000 | 0.000 | 0.000 |
| A-ToM-1 | -42.43 +/- 3.21 | 12.6 | 12.8 | 0.594 | 31.04 | 0.280 | 1.000 | 0.000 | 0.000 |
| Oracle | 22.44 +/- 4.72 | 18.6 | 1.4 | 0.956 | 49.57 | 0.170 | n/a | n/a | n/a |
