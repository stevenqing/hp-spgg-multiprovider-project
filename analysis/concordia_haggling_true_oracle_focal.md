# Concordia Haggling True Focal Oracle

This table recomputes `oracle_focal`, the true upper reference for the reported Haggling metric `focal_score_mean`. It directly maximizes focal payoff under full information, rather than total buyer+seller surplus.

| Config | oracle_focal | PACT+ | best non-oracle | oracle_joint focal | gap vs PACT+ |
|---|---:|---:|---:|---:|---:|
| fruitville (single) | 7.822 | 7.822 | hpsmg_plus_joint_proxy 7.822 | 7.822 | 0.000 |
| fruitville gullible (single) | 13.400 | 7.400 | econ_bne_mech 7.400 | 7.000 | 6.000 |
| vegbrooke (single) | 1.983 | 1.983 | hpsmg_plus_joint_proxy 1.983 | 1.983 | 0.000 |
| vegbrooke stubborn | 9.267 | 1.100 | hpsmg_plus_joint_proxy 1.100 | -0.333 | 8.167 |
| vegbrooke strange | 0.000 | 0.000 | econ_bne_mech 0.000 | 0.000 | 0.000 |
| fruitville multi | 4.400 | 4.400 | hpsmg_plus_joint_proxy 4.400 | 4.400 | 0.000 |
| fruitville gullible (multi) | 14.600 | 6.767 | hpsmg_plus_joint_proxy 6.767 | 6.300 | 7.833 |
| vegbrooke (multi) | 4.550 | 4.550 | hpsmg_plus_joint_proxy 4.550 | 4.550 | 0.000 |
| cumulative score (multi) | 12.000 | 6.000 | econ_bne_mech 6.000 | 5.600 | 6.000 |

Interpretation:

- `oracle_focal` is never below any retained non-oracle method on these Haggling configs; it ties only where all relevant methods already attain the focal optimum.
- The earlier `oracle_joint` focal values can be lower because that method optimizes total surplus, not focal payoff.
- These values are deterministic, call-free recomputations from the compact Haggling action/payoff model in the current runner, with the historical JSONs used for non-oracle comparison rows.
