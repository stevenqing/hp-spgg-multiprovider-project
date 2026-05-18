# Compact Concordia Pub Coordination Results

Config: `london_mini`
Model: `none`
Seeds: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]`

| method | episodes | focal_score_mean | focal_score_min_mean | coordination_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|
| oracle_joint | 30 | 1.3167 | 1.1333 | 0.9500 | 1.0000 |
| hpsmg_plus_joint_proxy | 30 | 1.3083 | 1.1167 | 0.9667 | 1.0000 |
| econ_bne_mech | 30 | 1.0764 | 0.9417 | 0.8333 | 1.0000 |
| atom_tom1_mech | 30 | 1.0639 | 0.9056 | 0.8500 | 1.0000 |
| hpsmg_plus_proxy | 30 | 1.0639 | 0.9056 | 0.8500 | 1.0000 |

## Information Fairness Audit

| method | mode | all_preferences | full_relationship_matrix | known_payoff_model | privileged_oracle_objective | comparable_baseline |
|---|---|---|---|---|---|---|
| atom_tom1_mech | centralized_full_case | true | true | true | false | true |
| econ_bne_mech | centralized_full_case | true | true | true | false | true |
| hpsmg_plus_proxy | centralized_full_case | true | true | true | false | true |
| hpsmg_plus_joint_proxy | centralized_full_case | true | true | true | false | true |
| oracle_joint | privileged_upper_bound | true | true | true | true | false |
