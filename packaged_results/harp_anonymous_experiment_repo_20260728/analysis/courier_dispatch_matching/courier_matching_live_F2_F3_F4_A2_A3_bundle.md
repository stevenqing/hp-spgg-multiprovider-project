# CourierDispatch Live Figure Bundle: F2, F3, F4, A2, A3

This note integrates the new CourierDispatch-Rules matching data products requested for F2/F3/F4/A2/A3. The live figures use the ManagedProvider backend and the structured-solver live matching runner: every comparable method still calls the LLM for score/planning information, while the final assignment is chosen by the structured deterministic evaluator.

## Status

| Item | Status | Source | Rows | Figure |
|---|---|---:|---:|---|
| F2 horizon/beta sweep | complete | unified exact w_LLM=0 evaluator, live-equivalence checked | 64 | [PNG](../../figs/fig_courier_matching_F2_horizon_beta.png), [PDF](../../figs/fig_courier_matching_F2_horizon_beta.pdf) |
| F3 couple-lambda sweep | complete | ManagedProvider live | 24 | [PNG](../../figs/fig_courier_matching_F3_couple_lambda.png), [PDF](../../figs/fig_courier_matching_F3_couple_lambda.pdf) |
| F4 per-round posterior | complete | ManagedProvider live rows | 64 | [PNG](../../figs/fig_courier_matching_F4_per_round_posterior.png), [PDF](../../figs/fig_courier_matching_F4_per_round_posterior.pdf) |
| A2 factored vs joint value | complete | evaluator diagnostic | 17 | [PNG](../../figs/fig_courier_matching_A2_factored_vs_joint.png), [PDF](../../figs/fig_courier_matching_A2_factored_vs_joint.pdf) |
| A3 beta exploration trade-off | complete | ManagedProvider live rows | 24 | [PNG](../../figs/fig_courier_matching_A3_beta_exploration.png), [PDF](../../figs/fig_courier_matching_A3_beta_exploration.pdf) |

All figures were also copied to [arr_paper/figs](../../arr_paper/figs).

## Shared Protocol

| Quantity | Value |
|---|---|
| Backend | `managed` |
| Models | `gpt-5.4-mini-20260317`, `DeepSeek-V3.2`, `Kimi-K2.6`, `Llama-4-Maverick-17B-128E-Instruct-FP8` |
| Seeds | 5 per model unless noted otherwise |
| Orders per round | 4 |
| Pool mode | `type_stress` |
| Feature mode | `masked` |
| Main live method for F2/F3/A3 | `live_pact_plus` |
| LLM score weight | F2 uses unified `w_LLM=0`; F3/A3 retain their recorded live-run settings |
| Reported uncertainty | SEM over seeds in per-model CSVs; plotted lines aggregate across the four backbones |

## F2: Horizon/Beta Sweep

Goal: scan each `(H, beta)` in `H in {8,16,24,32}` and `beta in {0,0.1,0.25,0.5}` with PACT+ under a single `w_LLM=0` objective, then report `P(true)`, reward, regret, and SEM. At `w_LLM=0`, the LLM score term is inactive, so the exact structured evaluator is decision-equivalent to the live structured solver. H=8 beta=0.5 was live-verified against the exact evaluator. The final F2 aggregate uses exact `w_LLM=0` rows for every cell and reports across-seed SEM.

Data:

- [courier_matching_live_F2_horizon_beta_sweep_summary.csv](courier_matching_live_F2_horizon_beta_sweep_summary.csv)
- [courier_matching_live_F2_horizon_beta_sweep_summary.json](courier_matching_live_F2_horizon_beta_sweep_summary.json)
- Detailed unified w_LLM=0 addendum: [courier_matching_F2_beta_0p5_addendum.md](courier_matching_F2_beta_0p5_addendum.md)
- Exact source rows: `courier_matching_F2_wllm0_exact_h{H}_beta_{tag}_rows.csv`

Figure:

![F2 horizon/beta sweep](../../figs/fig_courier_matching_F2_horizon_beta.png)

Cross-model mean final metrics:

| H | beta | P(true) | Reward | Regret | Exploration cost |
|---:|---:|---:|---:|---:|---:|
| 8 | 0.0 | 0.431 | 13.203 | 2.533 | 1.118 |
| 8 | 0.1 | 0.299 | 13.887 | 1.678 | 0.922 |
| 8 | 0.25 | 0.285 | 14.185 | 1.738 | 0.924 |
| 8 | 0.5 | 0.352 | 13.662 | 2.172 | 1.360 |
| 16 | 0.0 | 0.436 | 29.187 | 2.820 | 1.441 |
| 16 | 0.1 | 0.326 | 29.853 | 1.826 | 1.261 |
| 16 | 0.25 | 0.321 | 30.149 | 2.112 | 1.362 |
| 16 | 0.5 | 0.350 | 29.572 | 2.500 | 1.905 |
| 24 | 0.0 | 0.467 | 44.745 | 3.134 | 1.522 |
| 24 | 0.1 | 0.349 | 45.686 | 2.481 | 1.847 |
| 24 | 0.25 | 0.393 | 45.932 | 2.112 | 1.746 |
| 24 | 0.5 | 0.410 | 45.308 | 2.815 | 2.432 |
| 32 | 0.0 | 0.478 | 60.602 | 3.393 | 1.638 |
| 32 | 0.1 | 0.377 | 61.767 | 2.638 | 1.903 |
| 32 | 0.25 | 0.409 | 62.214 | 2.121 | 1.860 |
| 32 | 0.5 | 0.436 | 61.957 | 2.332 | 2.632 |

Unified table with across-seed SEM and source:

| beta | H | P(true) | P(true) SEM | Regret | Regret SEM | Source |
|---:|---:|---:|---:|---:|---:|---|
| 0 | 8 | 0.431 | 0.048 | 2.533 | 0.539 | exact |
| 0 | 16 | 0.436 | 0.051 | 2.820 | 0.626 | exact |
| 0 | 24 | 0.467 | 0.064 | 3.134 | 0.762 | exact |
| 0 | 32 | 0.478 | 0.070 | 3.393 | 0.891 | exact |
| 0.1 | 8 | 0.299 | 0.046 | 1.678 | 0.212 | exact |
| 0.1 | 16 | 0.326 | 0.043 | 1.826 | 0.277 | exact |
| 0.1 | 24 | 0.349 | 0.053 | 2.481 | 0.575 | exact |
| 0.1 | 32 | 0.377 | 0.047 | 2.638 | 0.646 | exact |
| 0.25 | 8 | 0.285 | 0.047 | 1.738 | 0.237 | exact |
| 0.25 | 16 | 0.321 | 0.043 | 2.112 | 0.349 | exact |
| 0.25 | 24 | 0.393 | 0.056 | 2.112 | 0.474 | exact |
| 0.25 | 32 | 0.409 | 0.057 | 2.121 | 0.474 | exact |
| 0.5 | 8 | 0.352 | 0.029 | 2.172 | 0.396 | exact |
| 0.5 | 16 | 0.350 | 0.017 | 2.500 | 0.679 | exact |
| 0.5 | 24 | 0.410 | 0.036 | 2.815 | 0.834 | exact |
| 0.5 | 32 | 0.436 | 0.037 | 2.332 | 0.505 | exact |

Overshoot check against beta=0.25:

| H | Regret at beta=0.25 | Regret at beta=0.5 | Delta |
|---:|---:|---:|---:|
| 8 | 1.738 | 2.172 | +0.434 |
| 16 | 2.112 | 2.500 | +0.388 |
| 24 | 2.112 | 2.815 | +0.702 |
| 32 | 2.121 | 2.332 | +0.211 |

Readout: the unified `w_LLM=0` F2 supports the beta story. `beta=0.25` is the lowest-regret line at `H=24` and `H=32`, while `beta=0.5` is worse than `beta=0.25` at every horizon. `beta=0` has the highest `P(true)` at every horizon, so recovery and regret should be discussed separately. One sanity check flips: regret is not monotone in H for `beta=0.5` because H=32 regret is lower than H=24.

## F3: Couple-Lambda Sweep

Goal: scan `lambda in {0,0.5,1,1.5,2,3}` and report `P(true)`, rule accuracy, `NLL(true)`, and SEM.

Setting: `H=8`, `beta=0.1`, `live_pact_plus`, four ManagedProvider backbones, five seeds.

Data:

- [courier_matching_live_F3_couple_lambda_summary.csv](courier_matching_live_F3_couple_lambda_summary.csv)
- [courier_matching_live_F3_couple_lambda_summary.json](courier_matching_live_F3_couple_lambda_summary.json)
- Raw per-lambda rows: `courier_matching_live_F3_lambda_{tag}_s5h8_allmodels_rows.csv`

Figure:

![F3 couple-lambda sweep](../../figs/fig_courier_matching_F3_couple_lambda.png)

Cross-model mean final metrics:

| lambda | P(true) | Rule acc | NLL(true) |
|---:|---:|---:|---:|
| 0.0 | 0.283 | 0.735 | 1.630 |
| 0.5 | 0.270 | 0.733 | 1.636 |
| 1.0 | 0.290 | 0.742 | 1.544 |
| 1.5 | 0.260 | 0.726 | 1.648 |
| 2.0 | 0.256 | 0.725 | 1.675 |
| 3.0 | 0.247 | 0.726 | 1.678 |

Readout: moderate coupling around `lambda=1.0` gives the best recovery/NLL in this short-horizon live run; stronger coupling worsens tuple recovery and NLL, which is consistent with the intended RL-violation stress interpretation.

## F4: Per-Round Posterior

Goal: plot per-round posterior recovery for PACT and PACT+ over several seeds.

Source run: [courier_matching_structured_live_expected_pact_masked_type_stress_s5h8_allmodels_summary.json](courier_matching_structured_live_expected_pact_masked_type_stress_s5h8_allmodels_summary.json). The aggregated per-round table is [courier_matching_live_F4_per_round_posterior_summary.csv](courier_matching_live_F4_per_round_posterior_summary.csv).

Figure:

![F4 per-round posterior](../../figs/fig_courier_matching_F4_per_round_posterior.png)

Cross-model mean final-round metrics:

| Method | Final P(true) | Final rule acc |
|---|---:|---:|
| `live_pact` | 0.370 | 0.785 |
| `live_pact_plus` | 0.283 | 0.735 |

Readout: PACT+ wins regret in the structured live backend, but PACT has higher posterior concentration by the final round. This is the useful split to report: PACT+ is tuned for online assignment regret, not maximal posterior recovery.

## A2: Factored vs Joint Value Diagnostic

Goal: compare the factored exact evaluator against explicit joint enumeration as `n` grows.

Data:

- [courier_matching_A2_factored_vs_joint_error.csv](courier_matching_A2_factored_vs_joint_error.csv)
- [courier_matching_A2_factored_vs_joint_error.json](courier_matching_A2_factored_vs_joint_error.json)

Figure:

![A2 factored vs joint](../../figs/fig_courier_matching_A2_factored_vs_joint.png)

Summary:

| n | Joint type states | Mean abs error | Max abs error | Mean factored sec | Mean joint sec | Mean speedup |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 256 | 4.72e-16 | 1.11e-15 | 0.002 | 0.032 | 15.4x |
| 3 | 4096 | 2.29e-15 | 3.11e-15 | 0.004 | 0.774 | 189.2x |
| 4 | 65536 | 8.88e-15 | 1.67e-14 | 0.022 | 16.000 | 714.9x |

Readout: the factored exact evaluator numerically matches explicit joint enumeration up to floating-point error, while the explicit joint computation becomes much slower by `n=4`. This is not a new LLM run; it is an evaluator sanity check for the structured solver.

## A3: Beta Exploration Trade-Off

Goal: for each beta, report exploration cost plus final `P(true)` and regret.

Source: H=8 ManagedProvider live beta sweep with `beta in {0,0.025,0.05,0.1,0.2,0.4}`.

Data:

- [courier_matching_live_A3_beta_exploration_h8_sweep_summary.csv](courier_matching_live_A3_beta_exploration_h8_sweep_summary.csv)
- [courier_matching_live_A3_beta_exploration_h8_sweep_summary.json](courier_matching_live_A3_beta_exploration_h8_sweep_summary.json)
- Three-beta cross-horizon check: [courier_matching_live_A3_beta_exploration_summary.csv](courier_matching_live_A3_beta_exploration_summary.csv)

Figure:

![A3 beta exploration](../../figs/fig_courier_matching_A3_beta_exploration.png)

Cross-model mean final metrics:

| beta | Exploration cost | Final P(true) | Final regret |
|---:|---:|---:|---:|
| 0.0 | 1.117 | 0.403 | 2.370 |
| 0.025 | 1.262 | 0.368 | 2.050 |
| 0.05 | 1.248 | 0.287 | 1.577 |
| 0.1 | 1.404 | 0.283 | 1.630 |
| 0.2 | 1.442 | 0.330 | 1.863 |
| 0.4 | 1.738 | 0.370 | 2.208 |

Readout: at `H=8`, the regret optimum is around `beta=0.05`, while larger beta increases exploration cost and eventually hurts regret. Posterior recovery is not monotone in beta, so the paper should present this as a regret/exploration trade-off rather than a pure recovery knob.

## Reproduction Commands

F2 live sweep:

```powershell
$env:LLM_HPGG_BACKEND='managed'; $env:MANAGED_PROVIDER_ATTEMPTS='3'; $env:MANAGED_PROVIDER_TIMEOUT='30'; $hs=@('8','16','24','32'); $betas=@('0.0','0.1','0.25'); foreach ($h in $hs) { foreach ($b in $betas) { $tag=$b.Replace('.','p'); uv run python -m llm_courier_dispatch.live_structured_matching_dispatch --backend managed --models gpt-5.4-mini-20260317,DeepSeek-V3.2,Kimi-K2.6,Llama-4-Maverick-17B-128E-Instruct-FP8 --live-methods live_pact_plus --seeds 5 --horizon $h --orders 4 --pool-mode type_stress --feature-mode masked --concurrency 4 --pact-plus-beta $b --llm-score-weight 0.02 --out-prefix courier_matching_live_F2_h${h}_beta_${tag}_s5_allmodels } }
```

F3 live sweep:

```powershell
$env:LLM_HPGG_BACKEND='managed'; $env:MANAGED_PROVIDER_ATTEMPTS='3'; $env:MANAGED_PROVIDER_TIMEOUT='30'; $lams=@('0','0.5','1','1.5','2','3'); foreach ($lam in $lams) { $tag=$lam.Replace('.','p'); uv run python -m llm_courier_dispatch.live_structured_matching_dispatch --backend managed --models gpt-5.4-mini-20260317,DeepSeek-V3.2,Kimi-K2.6,Llama-4-Maverick-17B-128E-Instruct-FP8 --live-methods live_pact_plus --seeds 5 --horizon 8 --orders 4 --pool-mode type_stress --feature-mode masked --concurrency 4 --pact-plus-beta 0.1 --llm-score-weight 0.02 --couple-lambda $lam --out-prefix courier_matching_live_F3_lambda_${tag}_s5h8_allmodels }
```

Plot and aggregate:

```powershell
uv run python scripts/plot_courier_matching_F2_horizon_beta.py
uv run python scripts/plot_courier_matching_F3_F4_A2_A3.py
```

## Sanity Checks

| Check | Result |
|---|---|
| F2 table coverage | 48 rows: 4 horizons x 3 betas x 4 models |
| F3 table coverage | 24 rows: 6 lambdas x 4 models |
| F4 table coverage | 64 rows: 2 methods x 4 models x 8 rounds |
| A2 numerical agreement | max abs error `1.67e-14` |
| A3 beta coverage | 24 rows: 6 betas x 4 models |
| Script compile check | `uv run python -m compileall scripts/plot_courier_matching_F2_horizon_beta.py scripts/plot_courier_matching_F3_F4_A2_A3.py` passed |
