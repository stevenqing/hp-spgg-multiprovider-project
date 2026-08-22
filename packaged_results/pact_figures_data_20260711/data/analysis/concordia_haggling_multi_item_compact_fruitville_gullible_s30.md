# Compact Concordia Haggling Results

Domain: `haggling_multi_item`
Config: `fruitville_gullible`
Seeds: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]`

| method | episodes | focal_score_mean | focal_score_min_mean | deal_score_mean | deal_min_score_mean | nash_product_mean | agreement_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| hpsmg_plus_joint_proxy | 30 | 6.7667 | 6.7667 | 4.5444 | 2.0000 | 5.0889 | 1.0000 | 1.0000 |
| hpsmg_plus_proxy | 30 | 6.7667 | 6.7667 | 4.5444 | 2.0000 | 5.0889 | 1.0000 | 1.0000 |
| econ_bne_mech | 30 | 6.7000 | 6.7000 | 4.5444 | 1.6889 | 4.7778 | 1.0000 | 1.0000 |
| oracle_joint | 30 | 6.3000 | 6.3000 | 4.5444 | -0.3111 | 0.0000 | 1.0000 | 1.0000 |
| atom_tom1_mech | 30 | 5.6667 | 5.6667 | 3.9667 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |

## Information Fairness Audit

| method | mode | full_case | known_payoff_model | privileged_oracle_objective | comparable_baseline |
|---|---|---|---|---|---|
| atom_tom1_mech | centralized_full_case | true | true | false | true |
| econ_bne_mech | centralized_full_case | true | true | false | true |
| hpsmg_plus_proxy | centralized_full_case | true | true | false | true |
| hpsmg_plus_joint_proxy | centralized_full_case | true | true | false | true |
| oracle_joint | privileged_upper_bound | true | true | true | false |
