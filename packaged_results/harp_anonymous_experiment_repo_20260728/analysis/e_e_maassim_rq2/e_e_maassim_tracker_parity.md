# E-E MaaSSim Factored-vs-Explicit-Joint Tracker Parity

Scheme (i) is used: each fleet size is regenerated as a self-consistent closed-loop Nootdorp market. Both trackers consume the identical saved nearest-policy evidence stream in the identical order. Their profile-sampling RNGs are independent.

| n | lambda | factored utility | joint utility | joint - factored (95% CI) | max marginal TV | storage |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0 | 30.496 +/- 7.378 | not run | n/a | n/a | 128 vs 4,294,967,296 |
| 8 | 0.5 | -6.968 +/- 8.012 | not run | n/a | n/a | 128 vs 4,294,967,296 |
| 8 | 1 | -5.491 +/- 7.769 | not run | n/a | n/a | 128 vs 4,294,967,296 |

`peak_mem_bytes` is the exact maximum persistent float64 belief-array allocation, not process RSS. `mean_update_us` and `p95_update_us` time only the Bayesian update and normalization; marginalization for the TV diagnostic is excluded.

Joint n=6 run: not run (optional); joint n=8: not run by design (theoretical float64 table is 34,359,738,368 bytes).
