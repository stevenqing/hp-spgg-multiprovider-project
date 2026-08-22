# MaaSSim Nearest-Optimality Diagnostic

Compares each policy's controlled assignment against an oracle that minimizes immediate pickup wait over the same candidate pairs in each snapshot.

| Policy | Seeds | Exact-match rate | Extra wait / snapshot | Candidate pairs | Evaluated assignments | Total extra wait |
|---|---:|---:|---:|---:|---:|---:|
| Nearest | 10 | 0.906 | 3.06 +/- 1.71 | 8.48 | 40.99 | 153.9 |
| Random | 10 | 0.257 | 115.74 +/- 5.44 | 7.66 | 32.95 | 5533.0 |
| PACT | 10 | 0.994 | 0.00 +/- 0.00 | 8.64 | 53.04 | 0.0 |
| PACT+ | 10 | 0.990 | 0.00 +/- 0.00 | 8.63 | 53.03 | 0.0 |
| Oracle | 10 | 0.994 | 0.00 +/- 0.00 | 8.64 | 53.04 | 0.0 |

Closest to immediate wait oracle: `PACT` with extra wait per snapshot `0.00`.
