# E-E MaaSSim Factored-vs-Explicit-Joint Tracker Parity

Scheme (i) is used: each fleet size is regenerated as a self-consistent closed-loop Nootdorp market. Both trackers consume the identical saved nearest-policy evidence stream in the identical order. Their profile-sampling RNGs are independent.

| n | lambda | factored utility | joint utility | joint - factored (95% CI) | max marginal TV | storage |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0 | -8.460 +/- 6.028 | -6.611 +/- 6.327 | +1.849 [+0.192, +3.506] | 7.81e-16 | 32 vs 256 |
| 2 | 0.5 | -42.924 +/- 8.369 | -43.307 +/- 8.439 | -0.383 [-3.104, +2.338] | 7.81e-16 | 32 vs 256 |
| 2 | 1 | -52.488 +/- 8.598 | -52.374 +/- 9.375 | +0.114 [-2.870, +3.098] | 7.81e-16 | 32 vs 256 |
| 3 | 0 | -7.481 +/- 8.161 | -6.150 +/- 7.818 | +1.331 [-0.708, +3.370] | 2.47e-15 | 48 vs 4,096 |
| 3 | 0.5 | -53.485 +/- 6.623 | -56.524 +/- 7.283 | -3.039 [-7.237, +1.159] | 2.47e-15 | 48 vs 4,096 |
| 3 | 1 | -57.150 +/- 7.629 | -58.739 +/- 7.084 | -1.589 [-5.126, +1.948] | 2.47e-15 | 48 vs 4,096 |
| 4 | 0 | -7.141 +/- 8.333 | -8.516 +/- 9.015 | -1.375 [-3.901, +1.151] | 2.55e-14 | 64 vs 65,536 |
| 4 | 0.5 | -59.281 +/- 9.498 | -56.652 +/- 10.911 | +2.629 [-2.687, +7.945] | 2.55e-14 | 64 vs 65,536 |
| 4 | 1 | -60.362 +/- 8.604 | -60.734 +/- 9.534 | -0.372 [-4.081, +3.337] | 2.55e-14 | 64 vs 65,536 |
| 6 | 0 | 9.717 +/- 11.339 | not run | n/a | n/a | 96 vs 16,777,216 |
| 6 | 0.5 | -30.117 +/- 12.474 | not run | n/a | n/a | 96 vs 16,777,216 |
| 6 | 1 | -29.022 +/- 10.042 | not run | n/a | n/a | 96 vs 16,777,216 |
| 8 | 0 | 20.907 +/- 11.200 | not run | n/a | n/a | 128 vs 4,294,967,296 |
| 8 | 0.5 | -16.694 +/- 12.889 | not run | n/a | n/a | 128 vs 4,294,967,296 |
| 8 | 1 | -15.618 +/- 11.220 | not run | n/a | n/a | 128 vs 4,294,967,296 |

`peak_mem_bytes` is the exact maximum persistent float64 belief-array allocation, not process RSS. `mean_update_us` and `p95_update_us` time only the Bayesian update and normalization; marginalization for the TV diagnostic is excluded.

Joint n=6 run: not run (optional); joint n=8: not run by design (theoretical float64 table is 34,359,738,368 bytes).
