# Compact Concordia Pub Coordination Results

Config: `london_mini`
Model: `none`
Seeds: `[0, 1, 2, 3, 4]`

| method | episodes | focal_score_mean | focal_score_min_mean | coordination_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|
| hpsmg_plus_joint_proxy | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 |
| oracle_joint | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 |
| atom_tom1_mech | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 |
| econ_bne_mech | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 |
| hpsmg_plus_proxy | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 |

## Information Fairness Audit

| method | mode | all_preferences | full_relationship_matrix | known_payoff_model | privileged_oracle_objective | comparable_baseline |
|---|---|---|---|---|---|---|
| atom_tom1_mech | centralized_full_case | true | true | true | false | true |
| econ_bne_mech | centralized_full_case | true | true | true | false | true |
| hpsmg_plus_proxy | centralized_full_case | true | true | true | false | true |
| hpsmg_plus_joint_proxy | centralized_full_case | true | true | true | false | true |
| oracle_joint | privileged_upper_bound | true | true | true | true | false |
