# HP-SPGG Baseline Implementation Audit

Last updated: 2026-05-17

This note records a web-backed audit of the newly integrated HP-SPGG baselines. The goal is to distinguish canonical implementations from HP-SPGG-specific adaptations, so the paper does not overclaim that lightweight comparison baselines are full reproductions of external systems.

## External references checked

| Baseline family | Paper / reference | Code reference found | Key external algorithm description |
|---|---|---|---|
| PSRL | Osband, Russo, Van Roy, "(More) Efficient Reinforcement Learning via Posterior Sampling", arXiv:1306.0940 | `remosasso/PSDRL` for a deep PSRL variant | Update posterior over environments/MDPs, sample one model from the posterior at the start of an episode, follow the optimal policy for that sampled model. |
| IQL | Tan, "Multi-Agent Reinforcement Learning: Independent versus Cooperative Agents", ICML 1993 | `KoussyAyoub/Multi-Agent-Reinforcement-Learning-system` | Each agent maintains its own Q estimate, uses exploration/exploitation, and updates from its own observed reward. |
| Adaptive ToM | Mu et al., "Adaptive Theory of Mind for LLM-based Multi-Agent Coordination", arXiv:2603.16264 / AAAI 2026 | `ChunjiangMonkey/Adaptive-ToM` | Implements 0/1/2-order ToM and adaptive ToM agents, estimates partner ToM order from prior interactions, and evaluates on coordination games, grid navigation, and Overcooked. |
| ECON | Xie et al., "From Debate to Equilibrium: Belief-Driven Multi-Agent LLM Reasoning via Bayesian Nash Equilibrium", arXiv:2506.08292 / ICML 2025 | `tmlr-group/ECON` | Multi-LLM coordination as an incomplete-information game; BNE-style belief coordination, belief network, mixer, local-to-global architecture, and learned reward components. |

## Implementation status in this repository

| Method | Current status | Completeness judgment | Action needed before paper claim |
|---|---|---|---|
| `hpsmg_plus` | HP-SPGG native proposed method with posterior expected welfare plus uncertainty/type-discrimination bonus. | Native implementation, no external paper to replicate. | OK as proposed method. |
| `hpsmg` | HP-SPGG native posterior sampler without bonus. | Native implementation, no external paper to replicate. | OK as ablation. |
| `joint_psrl` | Maintains an explicit joint posterior table over all hidden type profiles, samples one joint type profile, then chooses the welfare-maximizing action profile for that sampled type profile. | Complete PSRL-style adaptation for this stateless hidden-type benchmark. Storage accounting now reflects the full joint type table. | OK as explicit joint posterior PSRL baseline. |
| `map_greedy` | Uses the MAP hidden type for each player and greedily chooses the best profile. | Correct as a standard MAP greedy decision baseline. It is not a named external algorithm requiring a dedicated GitHub reproduction. | OK; label as MAP greedy baseline. |
| `psrl_notype` | Samples hidden types uniformly each round and never updates type beliefs. | Correct as a HP-SPGG ablation, not an external paper algorithm. | OK; label as type-agnostic PSRL-style ablation. |
| `iql_independent_actions` | Each player maintains its own Q values over its own contribution actions, uses epsilon-greedy action selection independently, and updates from its own observed reward. | Canonical independent-action IQL adaptation for HP-SPGG, aligned with Tan-style independent Q-learning. | OK as the primary IQL baseline. |
| `iql` / `joint_profile_iql` | Keeps one Q vector per player over joint action profiles, chooses by epsilon-greedy on summed Q, and updates each player's value for the chosen joint profile. | Useful HP-SPGG coordinator ablation, but not canonical decentralized IQL. | Keep as an auxiliary joint-profile Q baseline, not the primary IQL claim. |
| `random` | Uniform random joint action profile. | Complete sanity baseline. | OK. |
| `oracle` | Chooses the welfare-maximizing profile with access to the true hidden type profile. | Complete upper-bound baseline. | OK. |
| `llm_greedy` | Prompts one LLM coordinator to directly choose a joint contribution profile from public history. | Valid lightweight LLM coordinator baseline. Not a reproduction of ECON, A-ToM, or another full LLM coordination paper. | OK only if described as a lightweight prompted LLM baseline. |
| `llm_belief` | Prompts one LLM coordinator to infer personas from history and choose a joint contribution profile. | Valid lightweight belief / ToM-style LLM baseline. Not a full A-ToM or ECON implementation. | OK only if described as a proxy / analogue. For full comparison, implement A-ToM and/or ECON adapters separately. |
| `atom_tom0` | HP-SPGG adapter of A-ToM zero-order agent. Each player chooses its own contribution from public history without nested partner reasoning. | Complete HP-SPGG adaptation of the A-ToM 0th-order agent pattern. | OK as A-ToM family baseline. |
| `atom_tom1` | HP-SPGG adapter of A-ToM first-order agent. Each player predicts other players with a zero-order model before choosing its own action. | Complete HP-SPGG adaptation of the A-ToM 1st-order agent pattern. | OK as A-ToM family baseline. |
| `atom_tom2` | HP-SPGG adapter of A-ToM second-order agent. Each player predicts other players with a first-order model before choosing its own action. | Complete HP-SPGG adaptation of the A-ToM 2nd-order agent pattern. | OK as A-ToM family baseline. |
| `atom_adaptive_ftl` | HP-SPGG adapter of Adaptive ToM using Follow-the-Leader over 0/1/2-order ToM predictions. | Complete HP-SPGG adaptation of the official A-ToM online selection idea. | OK as A-ToM family baseline. |
| `atom_adaptive_hedge` | HP-SPGG adapter of Adaptive ToM using Hedge weights over 0/1/2-order ToM predictions. | Complete HP-SPGG adaptation of the official A-ToM online selection idea. | OK as A-ToM family baseline. |
| `econ_bne` | HP-SPGG adapter of ECON with coordinator strategy, executor responses, repeated BNE-style commitment refinement, convergence check, and final joint contribution commitment. | Complete HP-SPGG inference adapter for ECON's coordinator/executor/BNE-refinement structure. It does not import ECON's PyTorch learner because HP-SPGG evaluation is an online benchmark rather than their MATH/SVAMP training setup. | OK as ECON-family HP-SPGG baseline; describe as an HP-SPGG adapter of ECON, not a verbatim copy of their training stack. |

## Bottom line

The integrated suite is valid for HP-SPGG benchmarking if named carefully:

1. The Bayesian/type-aware methods and ablations are appropriate for the HP-SPGG hidden-type repeated public-goods setting.
2. `joint_psrl` now explicitly maintains the full joint posterior table, so the storage comparison is no longer only notional.
3. `iql_independent_actions` is now the canonical independent-action IQL baseline; `iql` remains as an auxiliary joint-profile Q baseline.
4. `llm_greedy` and `llm_belief` are lightweight executable LLM baselines.
5. Full HP-SPGG adapters for A-ToM and ECON are now implemented in `llm_hpgg/run_external_llm_baselines.py`.

## Recommended next implementation pass

Before final paper tables, do one of the following:

1. Completed: added canonical `iql_independent_actions`, added explicit `joint_psrl` posterior storage, and kept the old `iql` as a joint-profile Q baseline.
2. Completed: added separate A-ToM and ECON adapters, using their official GitHub repositories as templates.

## Validation

Offline smoke test completed over all six external algorithms:

```powershell
uv run python -m llm_hpgg.run_external_llm_baselines --K 2 --n 3 --seeds 1 --algos atom_tom0 atom_tom1 atom_tom2 atom_adaptive_ftl atom_adaptive_hedge econ_bne --calibration calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19.npy --out results\cloudgpt\E2_external_llm_baselines_smoke_K2_s1.npz --trace-out analysis\E2_external_llm_baselines_smoke_trace.json --cache logs\external_llm_baseline_smoke_cache.json --offline
```

Tiny live CloudGPT smoke test completed for one A-ToM variant and ECON:

```powershell
uv run python -m llm_hpgg.run_external_llm_baselines --K 1 --n 3 --seeds 1 --algos atom_tom0 econ_bne --calibration calibration_cloudgpt_multi_model_fast4_8algos_DeepSeek_V3_2_c19.npy --out results\cloudgpt\E2_external_llm_baselines_live_smoke_K1_s1.npz --trace-out analysis\E2_external_llm_baselines_live_smoke_trace.json --cache logs\external_llm_baseline_live_smoke_cache.json --model DeepSeek-V3.2 --econ-rounds 2
```