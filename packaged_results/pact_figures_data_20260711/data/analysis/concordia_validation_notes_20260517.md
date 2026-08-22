# Concordia Validation Notes

Generated: 2026-05-17

## Current Status

| layer | artifact | status |
|---|---|---|
| Local Concordia source | `external/concordia` | available |
| Concordia isolated env | `.venvs/concordia-py314` | available |
| Offline adapter sweep | `analysis/concordia_baseline_choice_sweep_offline.json` | passed |
| Official offline puppet smoke | `analysis/concordia_pub_coordination_official_smoke.json` | passed |
| Live CloudGPT single call from Concordia venv | terminal check | passed, `reply=OK`, elapsed 19.89s |
| Live Concordia adapter sweep | `analysis/concordia_baseline_choice_sweep_DeepSeek_V3_2_live.json` | passed |
| Official live puppet max5 smoke | `analysis/concordia_pub_coordination_puppet_DeepSeek_V3_2_live_max5.json` | simulation loop and serialization passed; too few steps for final joint action |
| Compact live Pub Coordination s5 | `analysis/concordia_pub_coordination_compact_DeepSeek_V3_2_live_s5.md` | passed; first paper-facing numeric table |
| Compact mechanistic Pub Coordination s5 | `analysis/concordia_pub_coordination_compact_mechanistic_joint_s5.md` | passed; preferred Concordia compact table with mechanism baselines |
| Compact mechanistic Cape Town s100 | `analysis/concordia_pub_coordination_compact_capetown_mechanistic_joint_s100.md` | passed; strongest current Concordia validation margin |
| Compact mechanistic cross-task s30 | `analysis/concordia_compact_margin_summary.md` | passed; all 7 non-test Pub Coordination configs covered at 30 seeds, plus Cape Town at 100 seeds |
| Official live `london_mini` run | `analysis/concordia_pub_coordination_london_mini_DeepSeek_V3_2_live*.json` | too slow for first smoke; should be scheduled as a bounded long run |

## Live Adapter Sweep Result

All four adapter-level baselines produced valid finite choices through CloudGPT in the Concordia venv.

| model | baseline | choice |
|---|---|---|
| DeepSeek-V3.2 | llm_greedy | The Anchor |
| DeepSeek-V3.2 | llm_belief | The Anchor |
| DeepSeek-V3.2 | atom_tom1 | The Anchor |
| DeepSeek-V3.2 | econ_bne | The Anchor |

## Key Fix

The Concordia venv needed the CloudGPT runtime dependencies installed in addition to the local Concordia package:

```powershell
uv pip install --python .venvs\concordia-py314\Scripts\python.exe openai azure-identity msal
```

This has been added to `scripts/setup_phase2_external_envs.ps1`.

## Official Runner Observation

The official `run_pub_coordination` path is now live-call capable, but the full generative-agent loop is much more expensive than the adapter sweep. A `puppet` run with `--max-steps 5` completed and wrote output, but stopped before the decision stage, leaving `joint_action={}` and focal scores at 0.0. This is still useful as an integration smoke for the official loop; paper-facing results require enough steps to reach decision/scoring.

Use one of two routes next:

1. Short operational route: add a compact Pub Coordination runner that bypasses long conversation scenes and directly runs the decision stage for score collection.
2. Official-fidelity route: schedule `london_mini`/`london` as a long CloudGPT run with caching and progress logging, then summarize only completed scored episodes.

## Compact Mechanistic Result

The strongest current compact Concordia result is the harder `capetown` substrate with 3 venues, 6 focal players, and 100 seeds.

| method | episodes | focal_score_mean | focal_score_min_mean | coordination_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|
| oracle_joint | 100 | 1.2651 | 0.9508 | 0.9767 | 1.0000 |
| hpsmg_plus_joint_proxy | 100 | 1.2483 | 0.9550 | 0.9900 | 1.0000 |
| econ_bne_mech | 100 | 1.0423 | 0.7168 | 0.7233 | 1.0000 |
| atom_tom1_mech | 100 | 0.9830 | 0.5612 | 0.6750 | 1.0000 |
| hpsmg_plus_proxy | 100 | 0.9830 | 0.5612 | 0.6750 | 1.0000 |

Margin: `hpsmg_plus_joint_proxy` improves over the best non-oracle non-HPSMG baseline (`econ_bne_mech`) by 0.2061 focal score, while staying within 0.0168 of the oracle upper bound. This is now the main Concordia compact validation claim.

Cross-task margin summary: `analysis/concordia_compact_margin_summary.md`. The compact sweep now covers all 7 non-test Pub Coordination configs shipped in the local Concordia checkout (`london_mini`, `london`, `london_closures`, `edinburgh`, `edinburgh_closures`, `edinburgh_tough_friendship`, and `capetown`) at 30 seeds, plus the stronger `capetown` 100-seed run.

Top cross-task margins after the expanded sweep:

| config | episodes | hpsmg_plus_joint_proxy | best non-oracle baseline | margin | oracle gap |
|---|---:|---:|---:|---:|---:|
| london_mini | 30 | 1.3083 | 1.0764 | 0.2319 | 0.0083 |
| capetown | 100 | 1.2483 | 1.0423 | 0.2061 | 0.0168 |
| capetown | 30 | 1.2472 | 1.0439 | 0.2033 | 0.0287 |
| edinburgh_closures | 30 | 1.2083 | 1.0865 | 0.1218 | 0.0174 |
| london | 30 | 1.3167 | 1.2017 | 0.1150 | 0.0188 |

`edinburgh` and `edinburgh_tough_friendship` are retained in the margin summary as useful negative/easy controls: all non-oracle mechanisms collapse to the same focal-score mean there, so they do not support a separation claim.

## Compact Haggling and Multi-Item Haggling Results

The validation now includes 9 additional official Concordia bargaining configs at 30 seeds. For these tasks, the main comparison metric is Nash product, with focal-min score used to track whether gains come from fairer deals rather than only higher average focal score.

Summary artifact: `analysis/concordia_haggling_margin_summary.md`.

| domain | config | episodes | hpsmg_plus_joint_proxy Nash | best non-oracle baseline | baseline Nash | Nash margin | min-score margin |
|---|---:|---:|---:|---|---:|---:|---:|
| haggling_multi_item | vegbrooke | 30 | 5.1000 | econ_bne_mech | 4.7833 | 0.3167 | 0.6333 |
| haggling_multi_item | fruitville_gullible | 30 | 5.0889 | econ_bne_mech | 4.7778 | 0.3111 | 0.0667 |
| haggling | fruitville | 30 | 3.8222 | econ_bne_mech | 3.5611 | 0.2611 | 0.6667 |
| haggling_multi_item | fruitville_multi | 30 | 4.8000 | econ_bne_mech | 4.5500 | 0.2500 | 0.5000 |
| haggling | vegbrooke_stubborn | 30 | 0.1667 | econ_bne_mech | 0.1000 | 0.0667 | 0.1333 |
| haggling | vegbrooke | 30 | 0.2694 | econ_bne_mech | 0.2139 | 0.0556 | 0.5000 |

The remaining three coverage/control configs tie the strongest baseline in this compact setting: single-item `fruitville_gullible`, single-item `vegbrooke_strange_game`, and multi-item `cumulative_score`.

The compact `london_mini` run with seeds `[0, 1, 2, 3, 4]` now includes mechanism-level Concordia adapters. `atom_tom1_mech` and `econ_bne_mech` are deterministic best-response mechanism baselines; `hpsmg_plus_joint_proxy` is the centralized posterior-guided joint recommendation used as the proposed Concordia proxy.

| method | episodes | focal_score_mean | focal_score_min_mean | coordination_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|
| hpsmg_plus_joint_proxy | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 |
| oracle_joint | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 |
| atom_tom1_mech | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 |
| econ_bne_mech | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 |
| hpsmg_plus_proxy | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 |

Interpretation: the joint posterior-guided proxy reaches the oracle focal-score mean on this compact substrate and improves by 0.1917 over the mechanistic A-ToM/ECON adapters. This is the strongest current Concordia compact result.

Information fairness: this is the preferred comparison table because `atom_tom1_mech`, `econ_bne_mech`, `hpsmg_plus_proxy`, and `hpsmg_plus_joint_proxy` are all centralized full-case methods. They all receive access to the same complete sampled case fields: all person preferences, all venue options, closed venues, and the full relationship matrix. They are also allowed to use the same known Pub Coordination payoff model. `oracle_joint` is retained only as a privileged upper bound because it optimizes the evaluation objective directly. The older live prompt-only table is not directly comparable to the centralized mechanism table because each prompted player only saw its own private favorite and its own relationship statements.

## Compact Live Prompt-Only Result

The compact `london_mini` live prompt runs now cover DeepSeek-V3.2, GPT-5.4 Nano, and Llama-4 Maverick with the same seeds `[0, 1, 2, 3, 4]` and the same method list. These runs verify model-specific Concordia behavior through CloudGPT; the preferred paper-facing comparison remains the fair mechanism table above because it gives centralized baselines the same full information.

| model | best prompt baseline | best prompt focal mean | hpsmg_plus_joint_proxy focal mean | oracle focal mean | source |
|---|---|---:|---:|---:|---|
| DeepSeek-V3.2 | atom_tom1 / econ_bne / llm_belief / llm_greedy | 0.8250 | 1.3000 | 1.3000 | `analysis/concordia_pub_coordination_compact_DeepSeek_V3_2_live_s5.json` |
| gpt-5.4-nano-20260317 | econ_bne | 1.1250 | 1.3000 | 1.3000 | `analysis/concordia_pub_coordination_compact_gpt_5_4_nano_20260317_live_s5.json` |
| Llama-4-Maverick-17B-128E-Instruct-FP8 | atom_tom1 / econ_bne / llm_belief / llm_greedy | 0.8250 | 1.3000 | 1.3000 | `analysis/concordia_pub_coordination_compact_Llama_4_Maverick_17B_128E_Instruct_FP8_live_s5.json` |

The original compact DeepSeek-V3.2 table is retained below for detailed method-level scores.

| method | episodes | focal_score_mean | focal_score_min_mean | coordination_rate_mean | valid_action_rate_mean |
|---|---:|---:|---:|---:|---:|
| oracle_joint | 5 | 1.3000 | 1.1000 | 1.0000 | 1.0000 |
| hpsmg_plus_proxy | 5 | 1.1083 | 0.9500 | 0.8000 | 1.0000 |
| atom_tom1 | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 |
| econ_bne | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 |
| llm_belief | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 |
| llm_greedy | 5 | 0.8250 | 0.6500 | 0.6000 | 1.0000 |

Interpretation: on this compact Concordia Pub Coordination validation, the posterior-guided proxy is the best non-oracle method and improves focal-score mean by 0.2833 over the directly prompted/social-reasoning LLM baselines.

Caveat: the four prompt-only baselines (`llm_greedy`, `llm_belief`, `atom_tom1`, `econ_bne`) collapsed to identical joint actions on all five seeds, so their equal scores are expected from the payoff function. This table supports a narrower claim: the posterior-guided proxy beats prompt-only Concordia decision variants on this compact substrate. It should not be described as a full implementation-level A-ToM/ECON defeat without differentiated mechanistic baselines or a stronger external implementation.

Action diagnostic: `analysis/concordia_compact_action_diagnostics.md`.

Additional live adapter sweeps also passed for GPT-5.4 Nano and Llama-4 Maverick: `analysis/concordia_baseline_choice_sweep_gpt_5_4_nano_20260317_live.json` and `analysis/concordia_baseline_choice_sweep_Llama_4_Maverick_17B_128E_Instruct_FP8_live.json`. Both models now also have the same official `puppet --max-steps 5` smoke and the same split compact artifacts (`s2`, `s3_seed2_4`, combined `s5`) as DeepSeek-V3.2.

## Validation Strategy

Use Concordia as a public external validation layer, not as a replacement for the HP-SPGG controlled benchmark.

1. Adapter-level validation:
   - Run `llm_hpgg_concordia.run_concordia_baselines` with CloudGPT.
   - Purpose: verify that each baseline family can make a valid Concordia social-choice action through the same provider stack.
   - Output: choice validity, selected venue, raw model reply.

2. Official simulation smoke:
   - Run `llm_hpgg_concordia.run_pub_coordination` on `puppet` and then `london_mini`.
   - Purpose: verify that the official Concordia simulation loop, model adapter, embedder, scoring, and serialization work together.
   - Use small `--max-steps` first; full generative-agent settings can be slow because each scene step triggers model calls.

3. Paper-facing Pub Coordination experiment:
   - Substrate: `examples.games.pub_coordination.configs.london_mini`, then `london` or `edinburgh`.
   - Models: `DeepSeek-V3.2`, `gpt-5.4-nano-20260317`, and `Llama-4-Maverick-17B-128E-Instruct-FP8` have matched Concordia live compact artifacts. `Kimi-K2.6` remains available for HP-SPGG cross-model checks but was not requested for this Concordia parity pass.
   - Baselines: Concordia generic agent, `llm_greedy`, `llm_belief`, A-ToM, ECON, and HP-SPGG posterior-guided recommendation when implemented.
   - Metrics: mean focal score, minimum focal score, coordination rate, valid-action rate, and average score gap to the best observed joint action.

4. Mixed-motive follow-up:
   - Use a haggling or labor-style Concordia game after Pub Coordination is stable.
   - Purpose: test whether the method helps beyond symmetric coordination.

## Commands

Adapter-level live sweep:

```powershell
$env:LLM_HPGG_BACKEND='cloudgpt'
$env:CLOUDGPT_USE_AZURE_CLI='1'
$env:CLOUDGPT_TIMEOUT='90'
$env:LLM_HPGG_OFFLINE='0'
.venvs\concordia-py314\Scripts\python.exe `
  -m llm_hpgg_concordia.run_concordia_baselines `
  --model DeepSeek-V3.2 `
  --out analysis\concordia_baseline_choice_sweep_DeepSeek_V3_2_live.json
```

Official Pub Coordination smoke:

```powershell
$env:LLM_HPGG_BACKEND='cloudgpt'
$env:CLOUDGPT_USE_AZURE_CLI='1'
$env:CLOUDGPT_TIMEOUT='90'
$env:LLM_HPGG_OFFLINE='0'
.venvs\concordia-py314\Scripts\python.exe `
  -m llm_hpgg_concordia.run_pub_coordination `
  --config london_mini `
  --model DeepSeek-V3.2 `
  --max-steps 20 `
  --out analysis\concordia_pub_coordination_london_mini_DeepSeek_V3_2_live_max20.json
```

## Next Implementation Step

Extend the compact runner to a second public Concordia substrate, preferably haggling or a labor/collective-action style task, then repeat the same `focal_score_mean`, `focal_score_min_mean`, `coordination_rate_mean`, and `valid_action_rate_mean` reporting pattern.