# MaaSSim LLM Common-State Smoke

Model: `gpt-5.4-mini-20260317`. Prompt variant: `scored`. Seeds: `2`. Max active snapshots per seed: `12`.
Scenario: `conflict_offer`.
Utility penalties: driver_reject_penalty=`5.0`, passenger_reject_penalty=`0.5`.

LLM-family policies see a legal one-to-one assignment menu plus method-specific public, belief, history, or score context, then return JSON with `assignment_id` and copied `candidate_ids`.

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Oracle-match | LLM parse | LLM repair | LLM fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | -70.25 +/- 0.75 | 3.0 | 15.0 | 0.189 | 1.12 | 0.917 | n/a | n/a | n/a |
| Random | -38.27 +/- 5.07 | 4.5 | 8.0 | 0.566 | 106.54 | 0.167 | n/a | n/a | n/a |
| LLM-PACT | 0.39 +/- 3.11 | 9.0 | 2.5 | 0.864 | 37.00 | 0.042 | 1.000 | 0.000 | 0.000 |
| LLM-belief | -13.48 +/- 0.56 | 8.0 | 5.0 | 0.730 | 27.92 | 0.125 | 1.000 | 0.000 | 0.000 |
| LLM-PSRL | -26.76 +/- 14.64 | 7.5 | 7.5 | 0.598 | 25.54 | 0.208 | 1.000 | 0.000 | 0.000 |
| A-ToM-0 | -38.80 +/- 12.38 | 6.0 | 9.5 | 0.484 | 20.29 | 0.292 | 1.000 | 0.000 | 0.000 |
| A-ToM-1 | -24.03 +/- 5.14 | 7.5 | 7.0 | 0.623 | 23.46 | 0.250 | 1.000 | 0.000 | 0.000 |
| ECON-BNE | -44.48 +/- 10.81 | 5.5 | 10.5 | 0.430 | 15.12 | 0.333 | 1.000 | 0.000 | 0.000 |
| Oracle | 9.18 +/- 3.32 | 9.0 | 0.5 | 0.972 | 36.38 | 0.083 | n/a | n/a | n/a |
