# MaaSSim Common-State Replay Evaluation

All policies are evaluated on the same exogenous queue snapshots from the nearest Persona v2 main trajectory and the same saved persona maps.

| Policy | Seeds | Oracle-match | Extra wait/snapshot | Served | Driver rejects | Passenger rejects | Driver rule acc |
|---|---:|---:|---:|---:|---:|---:|---:|
| Wait-oracle | 10 | 1.000 | 0.00 +/- 0.00 | 29.4 | 25.4 | 9.3 | 0.731 |
| Nearest | 10 | 0.906 | 3.06 +/- 1.71 | 30.4 | 26.0 | 9.2 | 0.732 |
| Random | 10 | 0.231 | 108.86 +/- 6.49 | 20.4 | 30.6 | 14.6 | 0.745 |
| PACT | 10 | 0.991 | 0.00 +/- 0.00 | 29.6 | 25.3 | 9.2 | 0.731 |
| PACT+ | 10 | 0.988 | 0.00 +/- 0.00 | 29.7 | 25.2 | 9.2 | 0.731 |
| Oracle | 10 | 0.991 | 0.00 +/- 0.00 | 29.6 | 25.3 | 9.2 | 0.731 |

Closest to wait oracle on common states: `Wait-oracle`.
