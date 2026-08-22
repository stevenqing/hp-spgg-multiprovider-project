# Compact Concordia Haggling Results

Domain: `haggling`
Config: `vegbrooke`
Seeds: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]`

| method | episodes | focal_score_mean | focal_score_min_mean | deal_score_mean | deal_min_score_mean | nash_product_mean | agreement_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| hpsmg_plus_joint_proxy | 30 | 1.9833 | 0.9333 | 0.6611 | 0.1944 | 0.2694 | 0.3917 | 1.0000 |
| hpsmg_plus_proxy | 30 | 1.9833 | 0.9333 | 0.6611 | 0.1944 | 0.2694 | 0.6750 | 1.0000 |
| econ_bne_mech | 30 | 1.7333 | 0.4333 | 0.5778 | 0.1389 | 0.2139 | 0.3833 | 1.0000 |
| atom_tom1_mech | 30 | 1.9833 | 0.2667 | 0.6611 | 0.0000 | 0.0000 | 0.6750 | 1.0000 |
| oracle_joint | 30 | 1.9833 | -3.3667 | 0.6611 | -0.6833 | 0.0000 | 0.3917 | 1.0000 |

## Information Fairness Audit

| method | mode | full_case | known_payoff_model | privileged_oracle_objective | comparable_baseline |
|---|---|---|---|---|---|
| atom_tom1_mech | centralized_full_case | true | true | false | true |
| econ_bne_mech | centralized_full_case | true | true | false | true |
| hpsmg_plus_proxy | centralized_full_case | true | true | false | true |
| hpsmg_plus_joint_proxy | centralized_full_case | true | true | false | true |
| oracle_joint | privileged_upper_bound | true | true | true | false |
