# Compact Concordia Pub Coordination Results

Config: `london_mini`
Model: `gpt-5.4-nano-20260317`
Seeds: `[2, 3, 4]`

| method | episodes | focal_score_mean | focal_score_min_mean | coordination_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|
| hpsmg_plus_joint_proxy | 3 | 1.3333 | 1.1667 | 1.0000 | 1.0000 |
| llm_greedy | 3 | 1.3333 | 1.1667 | 1.0000 | 1.0000 |
| oracle_joint | 3 | 1.3333 | 1.1667 | 1.0000 | 1.0000 |
| econ_bne | 3 | 1.2083 | 1.0000 | 0.8333 | 1.0000 |
| atom_tom1 | 3 | 1.0139 | 0.7500 | 0.8333 | 1.0000 |
| atom_tom1_mech | 3 | 1.0139 | 0.9167 | 0.8333 | 1.0000 |
| econ_bne_mech | 3 | 1.0139 | 0.9167 | 0.8333 | 1.0000 |
| hpsmg_plus_proxy | 3 | 1.0139 | 0.9167 | 0.8333 | 1.0000 |
| llm_belief | 3 | 1.0139 | 0.7500 | 0.8333 | 1.0000 |

## Information Fairness Audit

| method | mode | all_preferences | full_relationship_matrix | known_payoff_model | privileged_oracle_objective | comparable_baseline |
|---|---|---|---|---|---|---|
| llm_greedy | decentralized_per_player_prompt | false | false | false | false | true |
| llm_belief | decentralized_per_player_prompt | false | false | false | false | true |
| atom_tom1 | decentralized_per_player_prompt | false | false | false | false | true |
| econ_bne | decentralized_per_player_prompt | false | false | false | false | true |
| atom_tom1_mech | centralized_full_case | true | true | true | false | true |
| econ_bne_mech | centralized_full_case | true | true | true | false | true |
| hpsmg_plus_proxy | centralized_full_case | true | true | true | false | true |
| hpsmg_plus_joint_proxy | centralized_full_case | true | true | true | false | true |
| oracle_joint | privileged_upper_bound | true | true | true | true | false |
