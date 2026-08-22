# Compact Concordia Haggling Results

Domain: `haggling_multi_item`
Config: `fruitville_multi`
Seeds: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]`

| method | episodes | focal_score_mean | focal_score_min_mean | deal_score_mean | deal_min_score_mean | nash_product_mean | agreement_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| hpsmg_plus_joint_proxy | 30 | 4.4000 | 3.9667 | 4.4000 | 1.9833 | 4.8000 | 1.0000 | 1.0000 |
| hpsmg_plus_proxy | 30 | 4.4000 | 3.9667 | 4.4000 | 1.9833 | 4.8000 | 1.0000 | 1.0000 |
| econ_bne_mech | 30 | 4.4000 | 3.4667 | 4.4000 | 1.7333 | 4.5500 | 1.0000 | 1.0000 |
| atom_tom1_mech | 30 | 3.9333 | 0.0000 | 3.9333 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| oracle_joint | 30 | 4.4000 | -0.5333 | 4.4000 | -0.2667 | 0.0000 | 1.0000 | 1.0000 |

## Information Fairness Audit

| method | mode | full_case | known_payoff_model | privileged_oracle_objective | comparable_baseline |
|---|---|---|---|---|---|
| atom_tom1_mech | centralized_full_case | true | true | false | true |
| econ_bne_mech | centralized_full_case | true | true | false | true |
| hpsmg_plus_proxy | centralized_full_case | true | true | false | true |
| hpsmg_plus_joint_proxy | centralized_full_case | true | true | false | true |
| oracle_joint | privileged_upper_bound | true | true | true | false |
