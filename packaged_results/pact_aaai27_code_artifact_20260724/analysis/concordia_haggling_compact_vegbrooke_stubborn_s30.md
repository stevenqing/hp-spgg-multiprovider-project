# Compact Concordia Haggling Results

Domain: `haggling`
Config: `vegbrooke_stubborn`
Seeds: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]`

| method | episodes | focal_score_mean | focal_score_min_mean | deal_score_mean | deal_min_score_mean | nash_product_mean | agreement_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| hpsmg_plus_joint_proxy | 30 | 1.1000 | 1.1000 | 0.5200 | 0.1333 | 0.1667 | 0.3533 | 1.0000 |
| hpsmg_plus_proxy | 30 | 1.1000 | 1.1000 | 0.5200 | 0.1333 | 0.1667 | 0.6200 | 1.0000 |
| econ_bne_mech | 30 | 0.9667 | 0.9667 | 0.4600 | 0.0667 | 0.1000 | 0.3667 | 1.0000 |
| atom_tom1_mech | 30 | 0.7667 | 0.7667 | 0.5200 | 0.0000 | 0.0000 | 0.6200 | 1.0000 |
| oracle_joint | 30 | -0.3333 | -0.3333 | 0.5200 | -0.5933 | 0.0000 | 0.3533 | 1.0000 |

## Information Fairness Audit

| method | mode | full_case | known_payoff_model | privileged_oracle_objective | comparable_baseline |
|---|---|---|---|---|---|
| atom_tom1_mech | centralized_full_case | true | true | false | true |
| econ_bne_mech | centralized_full_case | true | true | false | true |
| hpsmg_plus_proxy | centralized_full_case | true | true | false | true |
| hpsmg_plus_joint_proxy | centralized_full_case | true | true | false | true |
| oracle_joint | privileged_upper_bound | true | true | true | false |
