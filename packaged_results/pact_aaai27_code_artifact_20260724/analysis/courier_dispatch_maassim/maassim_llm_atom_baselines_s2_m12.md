# MaaSSim LLM Common-State Smoke

Model: `gpt-5.4-mini-20260317`. Prompt variant: `scored`. Seeds: `2`. Max active snapshots per seed: `12`.

LLM-family policies see a legal one-to-one assignment menu plus method-specific public, belief, history, or score context, then return JSON with `assignment_id` and copied `candidate_ids`.

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Oracle-match | LLM parse | LLM repair | LLM fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 7.21 +/- 6.59 | 9.0 | 5.0 | 0.727 | 1.12 | 0.917 | n/a | n/a | n/a |
| Random | -2.80 +/- 5.21 | 7.0 | 5.0 | 0.731 | 106.54 | 0.167 | n/a | n/a | n/a |
| PACT | 8.52 +/- 5.29 | 9.5 | 4.5 | 0.754 | 2.54 | 0.958 | n/a | n/a | n/a |
| LLM-scored | 8.52 +/- 5.29 | 9.5 | 4.5 | 0.754 | 2.54 | 0.958 | 1.000 | 0.000 | 0.000 |
| A-ToM-0 | 8.29 +/- 5.51 | 9.5 | 5.0 | 0.727 | 0.46 | 0.917 | 1.000 | 0.000 | 0.000 |
| A-ToM-1 | 8.21 +/- 5.55 | 9.5 | 5.0 | 0.727 | 1.67 | 0.833 | 1.000 | 0.000 | 0.000 |
| A-ToM-Hedge | 8.23 +/- 5.57 | 9.5 | 5.0 | 0.727 | 0.00 | 1.000 | 1.000 | 0.000 | 0.000 |
| ECON-BNE | 8.21 +/- 5.55 | 9.5 | 5.0 | 0.727 | 1.54 | 0.917 | 1.000 | 0.000 | 0.000 |
| Oracle | 16.15 +/- 2.15 | 10.0 | 0.0 | 1.000 | 22.62 | 0.583 | n/a | n/a | n/a |
