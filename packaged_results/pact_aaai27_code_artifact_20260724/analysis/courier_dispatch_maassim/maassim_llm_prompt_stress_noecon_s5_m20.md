# MaaSSim LLM Common-State Smoke

Model: `gpt-5.4-mini-20260317`. Prompt variant: `scored`. Seeds: `5`. Max active snapshots per seed: `20`.
Utility penalties: driver_reject_penalty=`5.0`, passenger_reject_penalty=`0.5`.

LLM-family policies see a legal one-to-one assignment menu plus method-specific public, belief, history, or score context, then return JSON with `assignment_id` and copied `candidate_ids`.

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Oracle-match | LLM parse | LLM repair | LLM fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 12.70 +/- 11.83 | 19.6 | 5.4 | 0.822 | 1.66 | 0.920 | n/a | n/a | n/a |
| Random | -27.12 +/- 7.54 | 13.6 | 8.8 | 0.716 | 120.77 | 0.180 | n/a | n/a | n/a |
| LLM-PACT | 18.37 +/- 10.12 | 20.2 | 4.2 | 0.862 | 5.97 | 0.890 | 1.000 | 0.000 | 0.000 |
| LLM-belief | 13.47 +/- 9.94 | 19.4 | 5.0 | 0.835 | 3.06 | 0.920 | 1.000 | 0.000 | 0.000 |
| LLM-PSRL | 13.77 +/- 11.14 | 19.6 | 5.0 | 0.835 | 6.69 | 0.830 | 1.000 | 0.000 | 0.000 |
| A-ToM-0 | 12.67 +/- 11.34 | 19.6 | 5.4 | 0.822 | 1.46 | 0.920 | 1.000 | 0.000 | 0.000 |
| A-ToM-1 | 12.77 +/- 11.46 | 19.6 | 5.4 | 0.822 | 0.62 | 0.950 | 1.000 | 0.000 | 0.000 |
| Oracle | 36.44 +/- 5.09 | 20.6 | 0.4 | 0.989 | 18.48 | 0.740 | n/a | n/a | n/a |
