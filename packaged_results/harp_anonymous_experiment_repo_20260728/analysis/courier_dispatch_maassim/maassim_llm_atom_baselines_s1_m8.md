# MaaSSim LLM Common-State Smoke

Model: `gpt-5.4-mini-20260317`. Prompt variant: `scored`. Seeds: `1`. Max active snapshots per seed: `8`.

LLM-family policies see a legal one-to-one assignment menu plus method-specific public, belief, history, or score context, then return JSON with `assignment_id` and copied `candidate_ids`.

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Oracle-match | LLM parse | LLM repair | LLM fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 8.62 +/- 0.00 | 8.0 | 3.0 | 0.786 | 2.00 | 0.875 | n/a | n/a | n/a |
| Random | 7.41 +/- 0.00 | 9.0 | 2.0 | 0.857 | 66.25 | 0.125 | n/a | n/a | n/a |
| PACT | 11.23 +/- 0.00 | 9.0 | 2.0 | 0.857 | 7.62 | 0.875 | n/a | n/a | n/a |
| LLM-scored | 11.23 +/- 0.00 | 9.0 | 2.0 | 0.857 | 7.62 | 0.875 | 1.000 | 0.000 | 0.000 |
| A-ToM-0 | 10.77 +/- 0.00 | 9.0 | 3.0 | 0.786 | 0.00 | 0.875 | 1.000 | 0.000 | 0.000 |
| A-ToM-1 | 10.66 +/- 0.00 | 9.0 | 3.0 | 0.786 | 0.00 | 1.000 | 1.000 | 0.000 | 0.000 |
| A-ToM-Hedge | 10.66 +/- 0.00 | 9.0 | 3.0 | 0.786 | 0.00 | 1.000 | 1.000 | 0.000 | 0.000 |
| ECON-BNE | 10.66 +/- 0.00 | 9.0 | 3.0 | 0.786 | 4.12 | 0.875 | 1.000 | 0.000 | 0.000 |
| Oracle | 16.00 +/- 0.00 | 10.0 | 0.0 | 1.000 | 18.50 | 0.625 | n/a | n/a | n/a |
