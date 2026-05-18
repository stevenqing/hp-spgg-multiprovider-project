# Scientific Integrity Audit: gpt-5.5 and Pub Coordination Proxy

Date: 2026-05-17

## Decision

Paper-facing results should report four LLM backbones: DeepSeek-V3.2, gpt-5.4-nano, Kimi-K2.6, and Llama-4-Maverick. The gpt-5.5 native artifacts are quarantined and excluded from generated numeric tables until they are recalibrated and rerun end to end.

Raw gpt-5.5 files remain in the workspace for provenance and debugging, but they should not be used as an independent model result.

## gpt-5.5 Audit

Compared files:

| Pair | Result |
|---|---|
| `calibration_cloudgpt_multi_model_fast4_8algos_gpt_5_4_nano_20260317_c19.npy` vs `calibration_cloudgpt_multi_model_fast4_8algos_gpt_5_5_20260424_c19.npy` | Same object schema, different file hash, reward tensor max absolute difference 0.82 |
| `results/cloudgpt/E2_gpt_5_4_nano_20260317_c19_<beta>.npz` vs `results/cloudgpt/E2_gpt_5_5_20260424_c19_<beta>.npz` | All Bayesian/native calibration-dependent algorithms have identical cumulative regret arrays for every beta checked |

Per-beta result comparison:

| beta | identical algorithms | different algorithms |
|---|---|---|
| beta0 | hpsmg_plus, hpsmg, joint_psrl, map_greedy, psrl_notype, oracle | iql, random |
| beta0p05 | hpsmg_plus, hpsmg, joint_psrl, map_greedy, psrl_notype, oracle | iql, random |
| beta0p1 | hpsmg_plus, hpsmg, joint_psrl, map_greedy, psrl_notype, oracle | iql, random |
| beta0p25 | hpsmg_plus, hpsmg, joint_psrl, map_greedy, psrl_notype, oracle | iql, random |
| beta0p5 | hpsmg_plus, hpsmg, joint_psrl, map_greedy, psrl_notype, oracle | iql, random |
| beta0p75 | hpsmg_plus, hpsmg, joint_psrl, map_greedy, psrl_notype, oracle | iql, random |
| beta1 | hpsmg_plus, hpsmg, joint_psrl, map_greedy, psrl_notype, oracle | iql, random |
| beta1p5 | hpsmg_plus, hpsmg, joint_psrl, map_greedy, psrl_notype, oracle | iql, random |

Interpretation: the calibration file itself is not a byte-for-byte copy, but the effective native experiment outputs are identical exactly where the algorithms depend on calibration. That is enough to disqualify the current gpt-5.5 artifacts as an independent model result.

## Pub Coordination Proxy Audit

Code inspection shows `choose_hpsmg_plus_proxy` does not delegate to `choose_atom_tom1_mech`.

The equality is structural in Pub Coordination:

- `choose_hpsmg_plus_proxy` chooses each player's best venue by `posterior_expected_score`.
- `choose_atom_tom1_mech` predicts each other player with `zero_order_favorite_choice`, then applies `best_response_score`.
- When favorite pubs are open, both objectives reduce to own favorite bonus plus relationship-weighted mass of others whose favorite venue equals the candidate venue.

Action-level comparison across existing Pub Coordination artifacts:

| Config/model | Seeds | hpsmg_plus_proxy equals atom_tom1_mech actions | hpsmg_plus_joint_proxy differs from proxy actions |
|---|---:|---:|---:|
| capetown none s100 | 100 | 100 | 89 |
| capetown none s30 | 30 | 30 | 29 |
| edinburgh_closures none s30 | 30 | 11 | 23 |
| edinburgh none s30 | 30 | 30 | 0 |
| edinburgh_tough_friendship none s30 | 30 | 30 | 0 |
| london_closures none s30 | 30 | 30 | 6 |
| london none s30 | 30 | 30 | 22 |
| london_mini none s30 | 30 | 30 | 16 |
| london_mini DeepSeek live s5 | 5 | 5 | 3 |
| london_mini gpt-5.4-nano live s5 | 5 | 5 | 3 |
| london_mini Llama live s5 | 5 | 5 | 3 |

Conclusion: this is not an implementation delegation bug. For Pub Coordination, report `hpsmg_plus_joint_proxy` as the proposed Concordia mechanism. Treat `hpsmg_plus_proxy` as a structurally collapsed ablation and footnote that it often coincides with A-ToM-1 in this narrow action space.

## Follow-Up

1. Recalibrate and rerun gpt-5.5 only if a fifth backbone is needed.
2. Keep the four-backbone story as the default paper-facing claim.
3. Use Concordia Pub Coordination headline numbers from `hpsmg_plus_joint_proxy`, not `hpsmg_plus_proxy`.