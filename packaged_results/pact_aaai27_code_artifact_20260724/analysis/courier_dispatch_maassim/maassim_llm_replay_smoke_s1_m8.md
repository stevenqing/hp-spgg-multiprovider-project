# MaaSSim LLM Common-State Smoke

Model: `gpt-5.4-mini-20260317`. Seeds: `1`. Max active snapshots per seed: `8`.

LLM sees public MaaSSim candidate features and current learned driver-persona belief marginals, then returns JSON candidate IDs.

| Policy | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Oracle-match | LLM parse | LLM fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | 8.62 +/- 0.00 | 8.0 | 3.0 | 0.786 | 2.00 | 0.875 | n/a | n/a |
| Random | 7.41 +/- 0.00 | 9.0 | 2.0 | 0.857 | 66.25 | 0.125 | n/a | n/a |
| PACT | 11.23 +/- 0.00 | 9.0 | 2.0 | 0.857 | 7.62 | 0.875 | n/a | n/a |
| LLM | 12.33 +/- 0.00 | 10.0 | 1.0 | 0.929 | 40.62 | 0.250 | 0.875 | 0.125 |
| Oracle | 16.00 +/- 0.00 | 10.0 | 0.0 | 1.000 | 18.50 | 0.625 | n/a | n/a |
