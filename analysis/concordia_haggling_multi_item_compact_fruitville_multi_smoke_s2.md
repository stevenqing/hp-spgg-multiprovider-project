# Compact Concordia Haggling Results

Domain: `haggling_multi_item`
Config: `fruitville_multi`
Seeds: `[0, 1]`

| method | episodes | focal_score_mean | focal_score_min_mean | deal_score_mean | deal_min_score_mean | nash_product_mean | agreement_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| hpsmg_plus_joint_proxy | 2 | 4.2500 | 4.0000 | 4.2500 | 2.0000 | 4.5000 | 1.0000 | 1.0000 |
| hpsmg_plus_proxy | 2 | 4.2500 | 4.0000 | 4.2500 | 2.0000 | 4.5000 | 1.0000 | 1.0000 |
| econ_bne_mech | 2 | 4.2500 | 3.0000 | 4.2500 | 1.5000 | 4.0000 | 1.0000 | 1.0000 |
| atom_tom1_mech | 2 | 3.7500 | 0.0000 | 3.7500 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| oracle_joint | 2 | 4.2500 | -1.0000 | 4.2500 | -0.5000 | 0.0000 | 1.0000 | 1.0000 |

## Information Fairness Audit

| method | mode | full_case | known_payoff_model | privileged_oracle_objective | comparable_baseline |
|---|---|---|---|---|---|
| atom_tom1_mech | centralized_full_case | true | true | false | true |
| econ_bne_mech | centralized_full_case | true | true | false | true |
| hpsmg_plus_proxy | centralized_full_case | true | true | false | true |
| hpsmg_plus_joint_proxy | centralized_full_case | true | true | false | true |
| oracle_joint | privileged_upper_bound | true | true | true | false |
