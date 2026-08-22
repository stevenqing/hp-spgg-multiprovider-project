# MaaSSim PACT Persona-Mechanism Replay

All variants use the same nearest Persona v2 queue snapshots and saved persona maps. PACT variants share one assignment objective; only the driver-persona belief source changes.

PACT utility weights: serve_value=3.0, wait_weight=0.01, driver_reject_penalty=2.0, passenger_reject_penalty=0.5.

| Variant | Belief source | Seeds | Utility | Served | Driver rejects | Driver accept | Extra wait/snapshot | Policy P(true) | Policy rule acc |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Nearest | none | 10 | 11.03 +/- 10.88 | 30.4 | 26.0 | 0.634 | 3.06 +/- 1.71 | n/a | n/a |
| Random | none | 10 | -33.94 +/- 11.62 | 20.4 | 30.6 | 0.563 | 108.86 +/- 6.49 | n/a | n/a |
| PACT-prior | uniform prior | 10 | 11.11 +/- 10.74 | 29.8 | 25.1 | 0.635 | 0.45 +/- 0.19 | 0.062 | 0.500 |
| PACT-shuffled | learned posterior, shuffled across drivers | 10 | 6.87 +/- 9.55 | 29.0 | 26.5 | 0.609 | 17.56 +/- 2.11 | 0.056 | 0.521 |
| PACT | learned posterior | 10 | 27.61 +/- 11.65 | 33.3 | 18.5 | 0.740 | 16.25 +/- 2.72 | 0.247 | 0.720 |
| Oracle | true hidden persona | 10 | 38.92 +/- 11.17 | 34.7 | 13.2 | 0.822 | 26.84 +/- 3.75 | 1.000 | 1.000 |

Mechanism readout:
- PACT improves realized utility over PACT-prior by 16.50.
- PACT closes 59.3% of the prior-to-oracle utility gap.
- PACT-shuffled tests whether the learned posterior must stay attached to the correct driver persona.
