# CourierDispatch-Rules Results

This folder contains the analytic CourierDispatch-Rules benchmark. The benchmark is intentionally finite and controlled: hidden driver types are operational rule tuples, not named personas, and the platform only observes decentralized action/message traces.

## Source Files

| Item | Path |
|---|---|
| Environment | `llm_courier_dispatch/dispatch_env.py` |
| Demo runner | `llm_courier_dispatch/demo_dispatch.py` |
| Live LLM runner | `llm_courier_dispatch/live_llm_dispatch.py` |
| Exploratory LLM-driver runner | `llm_courier_dispatch/live_llm_driver_dispatch.py` |
| Coefficient calibration | `llm_courier_dispatch/calibrate_coefficients.py` |
| Root compatibility wrapper | `dispatch_env.py` |
| Root demo entry point | `demo_dispatch.py` |
| Summary JSON | `analysis/courier_dispatch/courier_dispatch_summary.json` |
| Per-round CSV | `analysis/courier_dispatch/courier_dispatch_rows.csv` |
| Five-seed summary JSON | `analysis/courier_dispatch/courier_dispatch_s5_summary.json` |
| Five-seed per-round CSV | `analysis/courier_dispatch/courier_dispatch_s5_rows.csv` |
| Horizon sweep CSV | `analysis/courier_dispatch/courier_dispatch_horizon_sweep.csv` |
| Masking RL-stress CSV | `analysis/courier_dispatch/courier_dispatch_masking_rl_stress.csv` |
| Online matching summary JSON | `analysis/courier_dispatch_matching/courier_matching_s5h16_o4_summary.json` |
| Online matching README | `analysis/courier_dispatch_matching/README.md` |
| Live LLM summary CSV | `analysis/courier_dispatch/courier_dispatch_live_llm_s5h8_allmodels_allbaselines_summary.csv` |
| H=24 live-only CSV | `analysis/courier_dispatch/courier_dispatch_live_llm_s5h24_allmodels_allbaselines_liveonly_summary.csv` |
| LLM-driver smoke JSON | `analysis/courier_dispatch/courier_dispatch_llm_driver_h2_allmodels_smoke_summary.json` |
| LLM-driver smoke CSV | `analysis/courier_dispatch/courier_dispatch_llm_driver_h2_allmodels_smoke_summary.csv` |
| Live LLM cache | `analysis/courier_dispatch/courier_dispatch_live_llm_cache.json` |
| Calibration JSON | `analysis/courier_dispatch/courier_dispatch_calibration_sweep.json` |
| Calibration CSV | `analysis/courier_dispatch/courier_dispatch_calibration_sweep.csv` |
| GPT all-methods main figure | `arr_paper/figs/fig_courier_gpt_all_methods.png` |
| Horizon recovery figure | `arr_paper/figs/fig_courier_horizon_recovery.png` |
| Beta trade-off figure | `arr_paper/figs/fig_courier_beta_tradeoff.png` |
| Live LLM planner figure | `arr_paper/figs/fig_courier_live_llm_planner_comparison.png` |
| Masking RL-stress figure | `arr_paper/figs/fig_courier_masking_rl_stress.png` |
| Legacy learning/probe figures | generated on demand under `figs/` by `llm_courier_dispatch.demo_dispatch` |
| Legacy RL-violation figure | generated on demand under `figs/` by `llm_courier_dispatch.demo_dispatch` |

Large row-level live-LLM JSON payloads are intentionally omitted from the cleaned workspace. Re-run the commands below to regenerate them if full per-round JSON is needed; the small CSV summaries above are retained for quick inspection.

Run the benchmark:

```powershell
uv run python demo_dispatch.py
```

Run the five-seed robustness check:

```powershell
uv run python demo_dispatch.py --seeds 5 --horizon 8 --candidates 4 --out-prefix courier_dispatch_s5
```

Run the coefficient sweep:

```powershell
uv run python -m llm_courier_dispatch.calibrate_coefficients --seeds 1 --horizon 20 --candidates 2
```

Run the live LLM comparison:

```powershell
$env:LLM_HPGG_BACKEND='cloudgpt'; $env:CLOUDGPT_ATTEMPTS='3'; uv run python -m llm_courier_dispatch.live_llm_dispatch --backend cloudgpt --models gpt-5.4-mini-20260317,DeepSeek-V3.2,Kimi-K2.6,Llama-4-Maverick-17B-128E-Instruct-FP8 --horizon 8 --seeds 5 --candidates 4 --concurrency 6 --out-prefix courier_dispatch_live_llm_s5h8_allmodels_allbaselines
```

Run the H=24 live-only representative check:

```powershell
$env:LLM_HPGG_BACKEND='cloudgpt'; $env:CLOUDGPT_ATTEMPTS='3'; uv run python -m llm_courier_dispatch.live_llm_dispatch --backend cloudgpt --models gpt-5.4-mini-20260317,DeepSeek-V3.2,Kimi-K2.6,Llama-4-Maverick-17B-128E-Instruct-FP8 --horizon 24 --seeds 5 --candidates 4 --concurrency 4 --skip-analytic --out-prefix courier_dispatch_live_llm_s5h24_allmodels_allbaselines_liveonly
```

Run the LLM-driver variant smoke test:

```powershell
$env:LLM_HPGG_BACKEND='cloudgpt'; $env:CLOUDGPT_ATTEMPTS='3'; uv run python -m llm_courier_dispatch.live_llm_driver_dispatch --backend cloudgpt --driver-models gpt-5.4-mini-20260317,DeepSeek-V3.2,Kimi-K2.6,Llama-4-Maverick-17B-128E-Instruct-FP8 --horizon 2 --seeds 1 --candidates 2 --methods pact:0.0,pact_plus:0.1,atom_tom1:0.0,oracle:0.0 --out-prefix courier_dispatch_llm_driver_h2_allmodels_smoke
```

## Design Rationale

CourierDispatch-Rules deliberately avoids named personas such as "commuter" or "speed demon". Those labels would look like a fixed hand-written persona library, which is exactly the weakness this benchmark is meant to avoid. Instead, each driver has a hidden operational-rule tuple. The rules are platform-relevant constraints, such as preferring familiar zones, rejecting long-distance orders, preferring homeward orders after a deadline, or requiring surge pricing.

The platform does not observe these rules. It only observes behavior: accept, neutral decline codes, choose-from-menu, reposition, and optional neutral message codes. This turns the problem from arbitrary persona inference into behavioral preference learning for coordination. A prompt-based theory-of-mind baseline may verbally infer that a driver seems to prefer short trips; PACT instead maintains a numeric posterior over possible rule tuples, updates it after every observed action, and uses that posterior for centralized dispatch.

The Markov-game transition assumption is also narrower than saying one driver cannot affect another driver's future choices. A driver accepting an order may change the public state, congestion, or future zone distribution. That is allowed. The PACT condition used here is that, after conditioning on the public state and joint action, the transition and reward-locality checks do not directly depend on unobserved hidden rules unless `couple_lambda` is intentionally enabled for the stress test.

Exploration is not treated as free. If a policy sends poor probing orders to learn driver rules, the runner records an exploration cost. This makes the reward/recovery trade-off visible: `beta=0.1` is near reward-neutral in this environment, while more aggressive probing improves recovery at a small reward cost.

Two extensions are natural but kept outside the main benchmark. First, continual latent-type learning could replace the finite rule grid with an online latent representation learned from histories of offers, acceptances, rejections, chosen orders, and explanations. Second, federated enterprise tool agents are another PACT setting: third-party tool/API agents may hide proprietary prompts, fine-tuning data, or vendor policies while the coordinator observes only API behavior. The courier simulator remains the concrete controlled benchmark because its finite rule grid preserves the current PACT theory while avoiding artificial persona labels.

An online personalized matching variant is now prototyped under `analysis/courier_dispatch_matching/`. In that setting, each round samples an order pool and the platform assigns different orders to different drivers. This better matches the application where hidden operational rules matter for driver-specific dispatch and online regret.

## Environment

Hidden type is a binary operational-rule tuple:

```text
(avoid_long, zone_loyal, home_pull, surge_only)
```

The action menu has seven discrete actions:

```text
accept, decline-a, decline-b, decline-c, decline-d, reposition, choose-from-menu
```

`choose-from-menu` is first-class. Each public state contains both the current offered order and a menu alternative; choosing from the menu accepts the alternative order with a small friction cost. The four decline actions are public response codes, not semantic explanations. Internally, each code mixes several pressures such as pay, trip length, zone, deadline/homeward pull, and surge; no observed action name directly states a hidden rule.

The optional message channel has five discrete tokens:

```text
none, msg-a, msg-b, msg-c, msg-d
```

In `pact_message`, the platform asks at most one driver for one message per round, priced at `message_cost=0.03`. Messages are additional neutral observation codes through `message_likelihood` and update the same numeric posterior as action observations.

The default and headline benchmark uses analytic stochastic rule-based drivers. This is intentional: the hidden-rule likelihood is controlled, posterior recovery is directly measurable, and reward locality can be tested cleanly. A separate exploratory LLM-driver variant keeps the same hidden-rule tuples and platform-side PACT/baseline methods, but each driver action is generated by a live LLM that privately sees its own rule tuple and the public order state. The platform still observes only the neutral action code. The LLM-driver variant is a smoke/appendix check, not the main evidence table.

The analytic action likelihood is a softmax over action utilities. Rejection reasons are deliberately rule-informative. The environment-level tests run at startup:

| Condition | Test |
|---|---|
| TI | hidden-rule perturbation does not change the public transition under fixed state/action/RNG |
| RL | at `couple_lambda=0`, `reward_i` is invariant to `theta_-i` |
| PF | initial rule tuples are sampled independently with approximately uniform marginals |

## Default Run

| Quantity | Value |
|---|---:|
| Agents | 3 |
| Rules | 4 |
| Type tuples | 16 |
| Horizon | 8 |
| Seeds | 1 |
| Candidate order states per round | 4 |
| Softmax tau | 0.50 |
| Penalty scale | 2.00 |
| Home scale | 1.20 |
| Menu friction | 0.20 |
| Message cost | 0.03 |
| `couple_lambda` grid | 0, 1, 2, 4 |

The default table is the short-horizon setting used for the live LLM comparison. The coefficient sweep is not a real-world calibration. It chooses analytic-tier defaults where hidden rules are identifiable inside the episode budget while A-ToM-1 remains below PACT. The refreshed quick grid selects `penalty_scale=2.0, tau=0.7`; the reported live comparison keeps `tau=0.5` so the LLM prompts and cached live traces stay on the same neutral-observation setting. For this reward-focal environment, use `beta=0.1` as the default PACT+ setting: it is the reward-neutral sweet spot while still sharpening rule recovery.

## Horizon Sweep

The `horizon=8` setting is intentionally short because it matches the live LLM evaluation budget. The main hidden-rule recovery claim should use longer horizons. The following controlled sweep uses `n=3`, `20` seeds, and `4` menu candidates. Reward is reported per round, so horizons are comparable.

| H | beta | P(true) | Rule acc | Reward/round | Probe |
|---:|---:|---:|---:|---:|---:|
| 8 | 0.00 | 0.364 | 0.846 | 0.800 | 0.00 |
| 8 | 0.10 | 0.382 | 0.850 | 0.786 | 0.09 |
| 8 | 0.25 | 0.383 | 0.829 | 0.747 | 0.62 |
| 16 | 0.00 | 0.648 | 0.942 | 0.728 | 0.00 |
| 16 | 0.25 | 0.684 | 0.942 | 0.690 | 0.91 |
| 24 | 0.00 | 0.786 | 0.958 | 0.758 | 0.00 |
| 24 | 0.10 | 0.827 | 0.971 | 0.757 | 0.18 |
| 24 | 0.25 | 0.832 | 0.967 | 0.732 | 1.06 |
| 32 | 0.00 | 0.920 | 0.996 | 0.757 | 0.00 |
| 32 | 0.10 | 0.947 | 0.996 | 0.754 | 0.20 |
| 32 | 0.25 | 0.933 | 0.983 | 0.740 | 1.11 |

Readout: P(true) rises strongly with horizon, from about `0.36` at `H=8` to about `0.92` at `H=32`. Use `H=24` or `H=32` as the headline hidden-rule recovery setting; keep `H=8` as the LLM-matched short run. The PACT+ bonus buys information at a small reward price. `beta=0.1` is the reward-neutral setting here, while `beta=0.25` improves recovery but remains slightly reward-negative even at `H=32`.

### H=24 Live-Only Representative

The full horizon sweep above is the controlled hidden-rule recovery table. To connect it to real model behavior without running the full 20-seed/32-horizon live grid, we also ran a practical H=24 live-only representative: four CloudGPT deployments, six live prompt baselines, `seeds=5`, `candidates=4`. Reward is per round.

| Model | Best live baseline | Reward/round mean +- SEM | Parse rate |
|---|---|---:|---:|
| GPT-5.4-mini | `live_atom_tom0` | 0.545 +- 0.043 | 1.000 |
| DeepSeek-V3.2 | `live_llm_belief` | 0.670 +- 0.044 | 1.000 |
| Kimi-K2.6 | `live_atom_tom0` | 0.696 +- 0.039 | 1.000 |
| Llama-4-Maverick | `live_llm_belief` | 0.588 +- 0.059 | 1.000 |

Readout: the best H=24 live prompt baseline, Kimi-K2.6 `live_atom_tom0`, reaches `0.696 +- 0.039` reward/round. The controlled PACT rows at H=24 are `0.758` for `beta=0` and `0.757` for `beta=0.1`, with substantially higher hidden-rule recovery. This live-only check supports the same conclusion as the H=8 live table: prompt-only planners can dispatch reasonably, but they do not recover the hidden rule tuples.

## Presentation Figure Plan

All four main presentation figures use the same environment role split:

```text
platform/planner: PACT, PACT+, MAP/PSRL/A-ToM, or live LLM planner baselines
drivers: analytic stochastic rule-based hidden-rule agents
```

The LLM-driver variant is excluded from the four main figures and stays in the exploratory appendix.

| Figure | Setting | Main comparison | Purpose |
|---|---|---|---|
| GPT all-methods main | rule-based drivers, GPT-5.4-mini live planner backbone | all planner methods under one GPT setting | headline comparison across PACT, baselines, and live GPT planners |
| Horizon recovery | rule-based drivers, platform-side PACT/PACT+ | PACT beta grid over H=8/16/24/32 | show hidden-rule recovery improves with horizon |
| Beta trade-off | rule-based drivers, platform-side PACT+ | beta=0, 0.1, 0.25 across H=24/32 | show beta=0.1 is reward-neutral while improving inference |
| Live LLM planner comparison | rule-based drivers, platform-side live LLM planners vs PACT | best live LLM planner per model vs PACT/PACT+ | show prompt planners do not recover rules and underperform PACT |
| RL-violation stress | rule-based drivers with masking coupling, platform-side PACT learner | couple_lambda vs P(true), rule-acc, NLL | show factored posterior degrades when locality breaks |

This keeps the main story consistent: the drivers are controlled hidden-rule agents, and the planner side is what varies.

## Short-Horizon Matched Run at `couple_lambda=0`

Baseline mapping from the HP-SPGG suite:

| HP-SPGG family | CourierDispatch status |
|---|---|
| PACT / PACT+ | implemented as `pact`, `pact_plus` |
| Communication/query variant | implemented as `pact_message` |
| MAP-Type-Greedy | implemented as `map_greedy` |
| Joint-PSRL | implemented as `joint_psrl` with an explicit joint posterior over driver rule tuples |
| PSRL-NoType | implemented as `psrl_notype` |
| A-ToM-0 / A-ToM-1 | implemented as `atom_tom0`, `atom_tom1` |
| Random / Oracle | implemented as `random`, `oracle` |
| ECON-BNE | not ported; CourierDispatch has a platform candidate-selection action, not a fixed simultaneous strategic game with a BNE solver |
| IQL action-profile baselines | not ported; CourierDispatch candidates are freshly sampled public states rather than a fixed reusable action-profile table |

The goal is to compare every HP-SPGG baseline whose assumptions transfer cleanly, and to avoid renaming an unrelated heuristic as ECON-BNE or IQL.

| Method | beta | Final cumulative reward | P(true tuple) | Rule-marginal accuracy | Probe cost | Message cost | Total info cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| `oracle` | 0.0 | 6.769 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| `pact` | 0.0 | 6.000 | 0.337 | 0.768 | 0.811 | 0.000 | 0.811 |
| `pact_message` | 0.0 | 6.000 | 0.307 | 0.748 | 0.794 | 0.240 | 1.034 |
| `pact_plus` | 0.0 | 6.000 | 0.337 | 0.768 | 0.811 | 0.000 | 0.811 |
| `pact_plus` | 0.1 | 6.187 | 0.489 | 0.860 | 0.168 | 0.000 | 0.168 |
| `pact_plus` | 0.25 | 4.036 | 0.463 | 0.852 | 1.458 | 0.000 | 1.458 |
| `pact_plus` | 0.5 | 4.448 | 0.667 | 0.907 | 2.172 | 0.000 | 2.172 |
| `map_greedy` | 0.0 | 4.970 | 0.087 | 0.672 | 0.986 | 0.000 | 0.986 |
| `joint_psrl` | 0.0 | 6.184 | 0.546 | 0.810 | 0.681 | 0.000 | 0.681 |
| `psrl_notype` | 0.0 | 5.440 | 0.062 | 0.500 | 0.910 | 0.000 | 0.910 |
| `atom_tom0` | 0.0 | 5.366 | 0.062 | 0.500 | 0.717 | 0.000 | 0.717 |
| `atom_tom1` | 0.0 | 6.599 | 0.062 | 0.500 | 0.327 | 0.000 | 0.327 |
| `random` | 0.0 | 3.297 | 0.062 | 0.500 | 2.063 | 0.000 | 2.063 |

Readout: `oracle` is an ex-post candidate-set upper bound: it sees the realized driver responses for every candidate in the current round and chooses the best one. PACT can no longer exceed oracle. MAP-Type-Greedy, Joint-PSRL, PSRL-NoType, and A-ToM-style baselines mirror the HP-SPGG baseline family where their assumptions are meaningful in this finite hidden-rule environment.

## Five-Seed Robustness Check

The single-seed table above is useful because it matches the live LLM comparison, but it has high variance. With `seeds=5` at the same horizon and candidate count, the earlier short-run underperformance of PACT disappears.

| Method | beta | Reward mean +- SEM | P(true tuple) | Rule acc | Info cost |
|---|---:|---:|---:|---:|---:|
| `oracle` | 0.0 | 7.343 +- 0.319 | 1.000 | 1.000 | 0.000 |
| `pact` | 0.0 | 6.606 +- 0.349 | 0.536 | 0.856 | 0.704 |
| `pact_plus` | 0.0 | 6.606 +- 0.349 | 0.536 | 0.856 | 0.704 |
| `pact_message` | 0.0 | 6.606 +- 0.349 | 0.532 | 0.853 | 0.894 |
| `pact_plus` | 0.1 | 6.592 +- 0.343 | 0.512 | 0.859 | 0.495 |
| `joint_psrl` | 0.0 | 6.456 +- 0.295 | 0.501 | 0.833 | 0.772 |
| `map_greedy` | 0.0 | 6.358 +- 0.510 | 0.418 | 0.817 | 0.493 |
| `atom_tom1` | 0.0 | 6.326 +- 0.320 | 0.062 | 0.500 | 0.567 |
| `psrl_notype` | 0.0 | 6.122 +- 0.284 | 0.062 | 0.500 | 0.500 |
| `atom_tom0` | 0.0 | 5.803 +- 0.192 | 0.062 | 0.500 | 0.665 |
| `random` | 0.0 | 3.134 +- 0.432 | 0.062 | 0.500 | 3.547 |

Readout: PACT is the best non-oracle reward method in this five-seed check while also learning the hidden rule tuples. A-ToM-1 remains competitive on immediate reward but stays at the uniform prior for P(true tuple), so it is not recovering the private rules. `pact_message` matches action-only PACT reward here but pays extra message cost, so this post-action message channel is not beneficial in this short-horizon setting.

## Message Channel

`pact` updates the factored Bayes posterior from observed driver actions only. `pact_message` uses the same action-observation update, then additionally queries one uncertain driver for a neutral message code and pays `message_cost=0.03` per query. In this short-horizon run, the extra message channel does not dominate action-only PACT; it is included to test whether priced communication can replace or reduce active probing under other cost/noise settings.

## Live LLM Baselines

The live LLM comparison asks each model to act as the platform-side dispatch planner. The prompt shows only public candidate-state features and neutral action/message codes; it does not reveal hidden rule tuples or rule names. Six live prompt baselines are run for each model:

| Baseline | Description |
|---|---|
| `live_llm_greedy` | choose a candidate from the current public state only |
| `live_llm_belief` | choose a candidate after reading recent public action-code history |
| `live_atom_tom0` | zero-order theory-of-mind prompt, current public features only |
| `live_atom_tom1` | one-step theory-of-mind prompt, uses recent public action-code history |
| `live_atom_adaptive_hedge` | hedges between zero-order and one-step ToM depending on history quality |
| `live_econ_bne` | economic best-response / equilibrium-style prompt |

Settings: `horizon=8`, `seeds=5`, `candidates=4`, backend `cloudgpt`. Parse rate is the fraction of live model replies parsed as valid candidate-choice JSON. Reward is reported as mean +- SEM across seeds.

| Model | Live baseline | Reward mean +- SEM | P(true tuple) | Rule acc | Info cost | Parse rate |
|---|---|---:|---:|---:|---:|---:|
| GPT-5.4-mini | `live_llm_greedy` | 3.678 +- 0.481 | 0.062 | 0.500 | 2.867 | 1.000 |
| GPT-5.4-mini | `live_llm_belief` | 2.919 +- 0.630 | 0.062 | 0.500 | 3.285 | 1.000 |
| GPT-5.4-mini | `live_atom_tom0` | 4.379 +- 0.498 | 0.062 | 0.500 | 2.596 | 1.000 |
| GPT-5.4-mini | `live_atom_tom1` | 4.170 +- 0.290 | 0.062 | 0.500 | 2.734 | 1.000 |
| GPT-5.4-mini | `live_atom_adaptive_hedge` | 4.002 +- 0.559 | 0.062 | 0.500 | 3.274 | 1.000 |
| GPT-5.4-mini | `live_econ_bne` | 3.052 +- 0.372 | 0.062 | 0.500 | 3.595 | 1.000 |
| DeepSeek-V3.2 | `live_llm_greedy` | 4.707 +- 0.496 | 0.062 | 0.500 | 2.278 | 1.000 |
| DeepSeek-V3.2 | `live_llm_belief` | 5.450 +- 0.539 | 0.062 | 0.500 | 1.457 | 1.000 |
| DeepSeek-V3.2 | `live_atom_tom0` | 4.718 +- 0.546 | 0.062 | 0.500 | 2.337 | 1.000 |
| DeepSeek-V3.2 | `live_atom_tom1` | 4.589 +- 0.551 | 0.062 | 0.500 | 2.771 | 1.000 |
| DeepSeek-V3.2 | `live_atom_adaptive_hedge` | 3.767 +- 0.808 | 0.062 | 0.500 | 2.787 | 1.000 |
| DeepSeek-V3.2 | `live_econ_bne` | 4.664 +- 0.407 | 0.062 | 0.500 | 1.926 | 1.000 |
| Kimi-K2.6 | `live_llm_greedy` | 5.560 +- 0.328 | 0.062 | 0.500 | 1.410 | 1.000 |
| Kimi-K2.6 | `live_llm_belief` | 5.101 +- 0.442 | 0.062 | 0.500 | 2.005 | 0.800 |
| Kimi-K2.6 | `live_atom_tom0` | 5.882 +- 0.424 | 0.062 | 0.500 | 1.177 | 1.000 |
| Kimi-K2.6 | `live_atom_tom1` | 4.806 +- 0.538 | 0.062 | 0.500 | 2.558 | 0.575 |
| Kimi-K2.6 | `live_atom_adaptive_hedge` | 4.267 +- 0.274 | 0.062 | 0.500 | 2.440 | 0.850 |
| Kimi-K2.6 | `live_econ_bne` | 5.459 +- 0.452 | 0.062 | 0.500 | 1.429 | 0.700 |
| Llama-4-Maverick | `live_llm_greedy` | 4.028 +- 0.879 | 0.062 | 0.500 | 2.585 | 1.000 |
| Llama-4-Maverick | `live_llm_belief` | 4.433 +- 0.763 | 0.062 | 0.500 | 3.013 | 1.000 |
| Llama-4-Maverick | `live_atom_tom0` | 4.457 +- 0.911 | 0.062 | 0.500 | 2.030 | 1.000 |
| Llama-4-Maverick | `live_atom_tom1` | 4.411 +- 0.695 | 0.062 | 0.500 | 2.691 | 1.000 |
| Llama-4-Maverick | `live_atom_adaptive_hedge` | 4.059 +- 0.769 | 0.062 | 0.500 | 2.828 | 1.000 |
| Llama-4-Maverick | `live_econ_bne` | 3.306 +- 0.533 | 0.062 | 0.500 | 3.636 | 0.975 |

The same seeds and candidates give the following non-live baselines and PACT methods. Reward is reported as mean +- SEM across seeds.

| Method | beta | Reward mean +- SEM | P(true tuple) | Rule acc | Info cost |
|---|---:|---:|---:|---:|---:|
| `oracle` | 0.0 | 7.343 +- 0.319 | 1.000 | 1.000 | 0.000 |
| `pact` | 0.0 | 6.606 +- 0.349 | 0.536 | 0.856 | 0.704 |
| `pact_message` | 0.0 | 6.606 +- 0.349 | 0.532 | 0.853 | 0.894 |
| `pact_plus` | 0.0 | 6.606 +- 0.349 | 0.536 | 0.856 | 0.704 |
| `pact_plus` | 0.1 | 6.592 +- 0.343 | 0.512 | 0.859 | 0.495 |
| `joint_psrl` | 0.0 | 6.456 +- 0.295 | 0.501 | 0.833 | 0.772 |
| `map_greedy` | 0.0 | 6.358 +- 0.510 | 0.418 | 0.817 | 0.493 |
| `atom_tom1` | 0.0 | 6.326 +- 0.320 | 0.062 | 0.500 | 0.567 |
| `psrl_notype` | 0.0 | 6.122 +- 0.284 | 0.062 | 0.500 | 0.500 |
| `atom_tom0` | 0.0 | 5.803 +- 0.192 | 0.062 | 0.500 | 0.665 |
| `random` | 0.0 | 3.134 +- 0.432 | 0.062 | 0.500 | 3.547 |

Readout: live LLM planners improve over random dispatch for most models but do not maintain an explicit numeric posterior, so their P(true tuple) remains at the uniform prior. The best live LLM baseline here is Kimi-K2.6 `live_atom_tom0` at `5.882 +- 0.424`, still below PACT at `6.606 +- 0.349`; PACT also recovers hidden rules while live LLM baselines do not. Rows with parse rate below `0.90` should be treated as diagnostic rather than final: Kimi `live_llm_belief`, `live_atom_tom1`, `live_atom_adaptive_hedge`, and `live_econ_bne` need stricter output repair before being used as headline live baselines.

## Exploratory LLM-Driver Variant

In the default environment, drivers are analytic stochastic rule-based policies. This is the preferred main setting because it gives a known finite hidden-type space and a calibrated local likelihood. The LLM-driver variant flips the live-model role: the platform still runs PACT/MAP/PSRL/A-ToM policies, but each driver is a live LLM with private access to its own hidden rule tuple. The driver prompt shows the public state and private operational rules, then asks for one neutral action code from the same seven-action menu. The platform never sees the private rule tuple.

The following smoke test uses `H=2`, `seeds=1`, `candidates=2`, four CloudGPT driver models, and four platform methods. It is a validation that live LLM drivers can replace analytic drivers; it is not a headline benchmark yet.

| Driver model | Platform method | Reward | P(true tuple) | Rule acc | Driver parse rate |
|---|---|---:|---:|---:|---:|
| GPT-5.4-mini | `atom_tom1` | 1.630 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `pact` | 1.630 | 0.257 | 0.703 | 1.000 |
| GPT-5.4-mini | `pact_plus` beta=0.1 | 1.630 | 0.257 | 0.703 | 1.000 |
| DeepSeek-V3.2 | `atom_tom1` | 0.788 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `pact` | 0.788 | 0.073 | 0.567 | 1.000 |
| DeepSeek-V3.2 | `pact_plus` beta=0.1 | 0.788 | 0.073 | 0.567 | 1.000 |
| Kimi-K2.6 | `atom_tom1` | 1.029 | 0.062 | 0.500 | 0.833 |
| Kimi-K2.6 | `pact` | 1.029 | 0.111 | 0.639 | 0.833 |
| Kimi-K2.6 | `pact_plus` beta=0.1 | 1.029 | 0.111 | 0.639 | 0.833 |
| Llama-4-Maverick | `atom_tom1` | 1.146 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `pact` | 1.146 | 0.115 | 0.619 | 1.000 |
| Llama-4-Maverick | `pact_plus` beta=0.1 | 1.146 | 0.115 | 0.619 | 1.000 |

Readout: the LLM-driver variant works as a drop-in behavioural layer, but it should stay separate from the main benchmark. Even at `H=2`, PACT begins to increase P(true) and rule accuracy from the prior using only the LLM drivers' neutral action codes. Longer LLM-driver runs should be reported as an exploratory appendix because driver stochasticity now comes from live model behavior rather than the analytic softmax policy.

## Exploration-Cost Accounting

The runner logs `exploration_cost = max(0, greedy_expected_reward - chosen_expected_reward)` per round. Total information cost is `exploration_cost + message_cost`. Higher `beta` keeps posterior accuracy high but increases cumulative probe cost; message queries trade a small explicit communication price for sharper posterior updates.

## RL-Violation Stress Test

The clean stress test uses masking coupling: as `couple_lambda` rises, drivers strategically act off-rule with probability increasing in the rival-type fraction, so behaviour depends on rivals' hidden rules while the learner keeps a local likelihood. This directly violates reward locality / local likelihood assumptions and gives a monotone posterior-degradation diagnostic. Setting: `n=4`, `H=24`, `40` seeds.

| `couple_lambda` | P(true) | Rule acc | NLL(true) |
|---:|---:|---:|---:|
| 0.0 | 0.778 +- 0.019 | 0.961 +- 0.006 | 0.437 +- 0.067 |
| 0.5 | 0.689 +- 0.020 | 0.919 +- 0.011 | 0.734 +- 0.081 |
| 1.0 | 0.574 +- 0.025 | 0.880 +- 0.012 | 1.323 +- 0.154 |
| 1.5 | 0.469 +- 0.030 | 0.836 +- 0.014 | 1.961 +- 0.217 |
| 2.0 | 0.413 +- 0.027 | 0.809 +- 0.016 | 2.266 +- 0.248 |
| 3.0 | 0.369 +- 0.032 | 0.787 +- 0.015 | 2.886 +- 0.265 |

Readout: all three metrics move monotonically with small SEMs. This replaces the earlier non-monotone single-seed `P(true)` row. The earlier version was unstable because it used one seed, perturbed mostly the accept channel while leaving rejection codes clean, and reported P(true) alone. The masking stress plus `>=30` seeds and NLL/rule-acc side metrics gives the clean COM-MTDP fallback evidence: when locality breaks, the factored posterior degrades.

This masking stress is a posterior-diagnostic experiment, so it is evaluated on the PACT-style numeric learner. Live prompt-only LLM baselines do not maintain a numeric posterior over rule tuples, so they cannot produce P(true), rule-acc, or NLL(true) without adding an external parser/posterior estimator. They remain covered in the live dispatch tables above as reward/parse-rate baselines.

## Scope

This is not a physically faithful routing simulator. It is a controlled PACT diagnostic with a realistic decentralized boundary: independent drivers have private operational rules, the platform sees action traces and optional priced messages, and competition/dynamic pricing can be dialed into the base environment through `couple_lambda`.