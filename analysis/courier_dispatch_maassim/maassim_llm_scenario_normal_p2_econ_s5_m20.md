# MaaSSim LLM Common-State Smoke

Model: `gpt-5.4-mini-20260317`. Prompt variant: `scored`. Seeds: `5`. Max active snapshots per seed: `20`.
Scenario: `normal`.
Utility penalties: driver_reject_penalty=`2.0`, passenger_reject_penalty=`0.5`.

LLM-family policies see a legal one-to-one assignment menu plus method-specific public, belief, history, or score context, then return JSON with `assignment_id` and copied `candidate_ids`.

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Oracle-match | LLM parse | LLM repair | LLM fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ECON-BNE | 28.81 +/- 7.97 | 19.6 | 5.4 | 0.822 | 1.28 | 0.900 | 1.000 | 0.000 | 0.000 |
