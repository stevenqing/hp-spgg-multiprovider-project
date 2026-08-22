# CourierDispatch Matching Results

This folder contains the online personalized matching variant of CourierDispatch-Rules.

Integrated live figure bundle for the new F2/F3/F4/A2/A3 data is in [courier_matching_live_F2_F3_F4_A2_A3_bundle.md](courier_matching_live_F2_F3_F4_A2_A3_bundle.md).

The unified `w_LLM=0` F2 horizon/beta sweep and overshoot table are in [courier_matching_F2_beta_0p5_addendum.md](courier_matching_F2_beta_0p5_addendum.md).

The `w_LLM=0` addendum with `LLM-PSRL-verbal` and `Random` baselines is in [courier_matching_wllm0_verbal_random_baselines.md](courier_matching_wllm0_verbal_random_baselines.md).

The MaaSSim/FleetPy integration assessment is in [maassim_fleetpy_integration_plan.md](maassim_fleetpy_integration_plan.md), with prototype code in [../../llm_courier_dispatch_maassim](../../llm_courier_dispatch_maassim).

The original CourierDispatch setting asks the platform to choose one public candidate state. The matching variant makes the application closer to platform dispatch: each round samples an order pool, and the platform assigns one order to each driver. Drivers remain analytic stochastic rule-based agents with hidden operational rule tuples.

## Analytic Run

```powershell
uv run python -m llm_courier_dispatch.matching_dispatch --horizon 16 --seeds 5 --orders 4 --samples 2 --out-prefix courier_matching_s5h16_o4
```

## Setting

| Quantity | Value |
|---|---:|
| Drivers | 3 |
| Hidden rules | 4 binary rules |
| Orders per round | 4 |
| Horizon | 16 |
| Seeds | 5 |
| Planner value estimate | mean-field expected reward |
| Regret | online expected regret vs true-type oracle assignment for the same order pool |

The platform observes only neutral driver actions for assigned orders. PACT and Bayesian baselines update posteriors online after every assignment/action pair.

## Analytic Prototype Results

| Method | beta | Cumulative reward | Cumulative regret | P(true tuple) | Rule acc |
|---|---:|---:|---:|---:|---:|
| `oracle` | 0.0 | 13.314 | 0.000 | 1.000 | 1.000 |
| `pact_plus` | 0.1 | 11.484 | 1.562 | 0.846 | 0.960 |
| `map_greedy` | 0.0 | 11.633 | 1.927 | 0.603 | 0.888 |
| `joint_psrl` | 0.0 | 11.102 | 2.008 | 0.861 | 0.964 |
| `pact` | 0.0 | 10.517 | 2.272 | 0.670 | 0.910 |
| `psrl_notype` | 0.0 | 8.294 | 5.328 | 0.062 | 0.500 |
| `atom_tom1` | 0.0 | 7.759 | 5.027 | 0.062 | 0.500 |
| `random` | 0.0 | 6.823 | 6.269 | 0.062 | 0.500 |

## Analytic Readout

This variant better exposes the value of hidden-rule learning. The platform must personalize assignments across drivers, so knowing which driver avoids long trips, stays in familiar zones, prefers homeward orders, or requires surge pricing directly affects online regret.

`PACT+ beta=0.1` has the lowest non-oracle regret while maintaining strong rule recovery. A-ToM-1 and PSRL-NoType remain near the prior on hidden rules and incur much higher regret. MAP-Greedy obtains high reward in this small run but has weaker posterior recovery than PACT+, which is why the regret metric is the cleaner online-learning readout.

## All LLM-Backed Matching Methods

The headline live comparison uses the same LLM interface for every comparable method. Each method calls the live CloudGPT planner to output the driver-to-order assignment; methods differ only in the public context or belief summary passed to the LLM. PACT, MAP, and Joint-PSRL maintain structured hidden-rule posteriors and pass compact posterior summaries. Prompt-only and no-type baselines do not maintain numeric hidden-rule beliefs.

The table below is the completed random-pool, semantic-feature live run. New runs should prefer the masked/type-stress command in the diagnostic section below.

Run:

```powershell
$env:LLM_HPGG_BACKEND='cloudgpt'; $env:CLOUDGPT_ATTEMPTS='3'; $env:CLOUDGPT_TIMEOUT='30'; uv run python -m llm_courier_dispatch.live_matching_dispatch --backend cloudgpt --models gpt-5.4-mini-20260317,DeepSeek-V3.2,Kimi-K2.6,Llama-4-Maverick-17B-128E-Instruct-FP8 --live-methods live_pact,live_pact_plus,live_map_greedy,live_joint_psrl,live_psrl_notype,live_llm_greedy,live_llm_belief,live_atom_tom0,live_atom_tom1,live_atom_adaptive_hedge,live_econ_bne --horizon 8 --seeds 5 --orders 4 --pool-mode random --feature-mode semantic --concurrency 1 --out-prefix courier_matching_live_allmethods_s5h8_allmodels
```

Outputs:

- `courier_matching_live_allmethods_s5h8_allmodels_summary.json`
- `courier_matching_live_allmethods_s5h8_allmodels_summary.csv`
- `courier_matching_live_allmethods_s5h8_allmodels_rows.csv`

Lowest-regret method per model among rows with parse rate at least `0.90`:

| Model | Best method | Reward | Regret | P(true) | Rule acc | Parse |
|---|---|---:|---:|---:|---:|---:|
| GPT-5.4-mini | `live_atom_adaptive_hedge` | 4.141 | 2.340 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_pact` | 3.278 | 2.633 | 0.424 | 0.805 | 0.925 |
| Kimi-K2.6 | `live_atom_tom0` | 3.551 | 2.741 | 0.062 | 0.500 | 0.975 |
| Llama-4-Maverick | `live_joint_psrl` | 4.042 | 2.255 | 0.447 | 0.834 | 1.000 |

Full all-method table, using mean final cumulative metrics over five seeds:

| Model | Method | Reward | Regret | P(true) | Rule acc | Parse |
|---|---|---:|---:|---:|---:|---:|
| GPT-5.4-mini | `live_pact` | 3.870 | 2.544 | 0.551 | 0.870 | 1.000 |
| GPT-5.4-mini | `live_pact_plus` | 4.066 | 2.650 | 0.626 | 0.875 | 1.000 |
| GPT-5.4-mini | `live_map_greedy` | 3.681 | 2.736 | 0.583 | 0.865 | 1.000 |
| GPT-5.4-mini | `live_joint_psrl` | 3.675 | 2.710 | 0.542 | 0.872 | 1.000 |
| GPT-5.4-mini | `live_psrl_notype` | 3.180 | 2.989 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_llm_greedy` | 3.499 | 2.818 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_llm_belief` | 3.237 | 2.769 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_atom_tom0` | 4.279 | 2.428 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_atom_tom1` | 3.017 | 3.321 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_atom_adaptive_hedge` | 4.141 | 2.340 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_econ_bne` | 3.225 | 3.031 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_pact` | 3.278 | 2.633 | 0.424 | 0.805 | 0.925 |
| DeepSeek-V3.2 | `live_pact_plus` | 3.414 | 3.226 | 0.604 | 0.870 | 0.975 |
| DeepSeek-V3.2 | `live_map_greedy` | 3.800 | 2.467 | 0.593 | 0.883 | 0.775 |
| DeepSeek-V3.2 | `live_joint_psrl` | 3.668 | 2.749 | 0.531 | 0.842 | 0.725 |
| DeepSeek-V3.2 | `live_psrl_notype` | 3.220 | 3.091 | 0.062 | 0.500 | 0.975 |
| DeepSeek-V3.2 | `live_llm_greedy` | 3.465 | 3.040 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_llm_belief` | 3.447 | 2.908 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_atom_tom0` | 3.503 | 2.785 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_atom_tom1` | 3.108 | 3.526 | 0.062 | 0.500 | 0.975 |
| DeepSeek-V3.2 | `live_atom_adaptive_hedge` | 3.355 | 3.117 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_econ_bne` | 3.637 | 2.771 | 0.062 | 0.500 | 0.975 |
| Kimi-K2.6 | `live_pact` | 4.362 | 2.373 | 0.610 | 0.894 | 0.625 |
| Kimi-K2.6 | `live_pact_plus` | 3.942 | 2.678 | 0.692 | 0.910 | 0.650 |
| Kimi-K2.6 | `live_map_greedy` | 3.625 | 2.787 | 0.513 | 0.853 | 0.675 |
| Kimi-K2.6 | `live_joint_psrl` | 4.049 | 2.332 | 0.634 | 0.895 | 0.450 |
| Kimi-K2.6 | `live_psrl_notype` | 3.451 | 2.856 | 0.062 | 0.500 | 0.725 |
| Kimi-K2.6 | `live_llm_greedy` | 2.870 | 3.252 | 0.062 | 0.500 | 0.950 |
| Kimi-K2.6 | `live_llm_belief` | 3.507 | 3.142 | 0.062 | 0.500 | 0.900 |
| Kimi-K2.6 | `live_atom_tom0` | 3.551 | 2.741 | 0.062 | 0.500 | 0.975 |
| Kimi-K2.6 | `live_atom_tom1` | 3.355 | 3.231 | 0.062 | 0.500 | 0.725 |
| Kimi-K2.6 | `live_atom_adaptive_hedge` | 4.094 | 2.394 | 0.062 | 0.500 | 0.600 |
| Kimi-K2.6 | `live_econ_bne` | 3.227 | 3.348 | 0.062 | 0.500 | 0.825 |
| Llama-4-Maverick | `live_pact` | 3.877 | 2.769 | 0.621 | 0.890 | 1.000 |
| Llama-4-Maverick | `live_pact_plus` | 3.315 | 3.024 | 0.587 | 0.876 | 1.000 |
| Llama-4-Maverick | `live_map_greedy` | 3.355 | 2.811 | 0.538 | 0.854 | 0.975 |
| Llama-4-Maverick | `live_joint_psrl` | 4.042 | 2.255 | 0.447 | 0.834 | 1.000 |
| Llama-4-Maverick | `live_psrl_notype` | 3.427 | 3.002 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_llm_greedy` | 3.313 | 3.036 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_llm_belief` | 3.673 | 2.594 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_atom_tom0` | 3.247 | 2.966 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_atom_tom1` | 3.861 | 2.648 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_atom_adaptive_hedge` | 3.499 | 2.894 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_econ_bne` | 3.472 | 2.839 | 0.062 | 0.500 | 1.000 |

Readout: when parse rates are reliable, posterior-bearing methods recover hidden rules while still using the LLM for assignment. DeepSeek's best reliable regret row is `live_pact`, and Llama's best reliable row is `live_joint_psrl`. GPT's prompt-style heuristics are strong on regret, but they remain at the prior on hidden rules. Kimi produces high-reward posterior rows, but many of them have parse rates below `0.90`; those rows should be treated as diagnostic until stricter JSON repair or constrained decoding is added.

## Why PACT Is Not Always Best Yet

The all-method live table should not be read as a clean PACT-failure result. It exposes three benchmark-design issues.

First, the random order pool has weak assignment margins. A quick oracle-vs-prior diagnostic on the random pool gives a mean top-2 oracle margin of about `0.026` expected reward per round. That means many assignments are near-ties, so LLM assignment noise can dominate the benefit of a better posterior.

Second, public feature names are semantically strong. The LLM sees fields such as `long_trip`, `leaves_zone`, `home_ward`, and `surge`. Even without a numeric hidden-rule posterior, GPT-style prompt heuristics can use common-sense dispatch logic and do well on regret while staying at prior rule recovery (`P(true)=0.062`, rule accuracy `0.500`).

Third, the current PACT+ exploration bonus improves rule recovery but can hurt short-horizon regret. On the strengthened stress pool, a small beta sweep showed higher beta increased rule recovery but worsened regret; beta `0.0` was better on short-horizon regret than larger beta values.

Two changes have now been implemented. First, the runner supports a `type_stress` pool mode. It constructs high-value orders that each violate a different operational rule and low-value fallback orders. This makes hidden-rule knowledge more valuable: the quick prior-regret diagnostic rises from about `2.6` to `4.5` cumulative regret over `H=8`. Second, the live runner supports `--feature-mode masked`, which replaces semantic public fields such as `long_trip`, `leaves_zone`, `home_ward`, and `surge` with neutral codes `f0..f3`, numeric fields `x0..x2`, and masked posterior rule codes `r0..r3`.

Analytic smoke command:

```powershell
uv run python -m llm_courier_dispatch.matching_dispatch --pool-mode type_stress --horizon 16 --seeds 5 --orders 4 --samples 4 --methods oracle:0.0,pact:0.0,pact_plus:0.1,map_greedy:0.0,joint_psrl:0.0,psrl_notype:0.0,atom_tom1:0.0,random:0.0 --out-prefix courier_matching_type_stress_s5h16_o4
```

In this stress setting, posterior methods separate clearly from no-type and prompt-only baselines: `joint_psrl` regret `2.710`, `map_greedy` `3.014`, `pact_plus` `3.177`, and `pact` `3.642`, compared with `atom_tom1` `8.002`, `psrl_notype` `9.708`, and `random` `9.897`. This is a better environment for showing the value of hidden-rule learning, though PACT's decision rule still needs tuning to beat MAP/Joint-PSRL on regret.

Completed masked live stress run:

```powershell
$env:LLM_HPGG_BACKEND='cloudgpt'; $env:CLOUDGPT_ATTEMPTS='3'; $env:CLOUDGPT_TIMEOUT='30'; uv run python -m llm_courier_dispatch.live_matching_dispatch --backend cloudgpt --models gpt-5.4-mini-20260317,DeepSeek-V3.2,Kimi-K2.6,Llama-4-Maverick-17B-128E-Instruct-FP8 --live-methods live_pact,live_pact_plus,live_map_greedy,live_joint_psrl,live_psrl_notype,live_llm_greedy,live_llm_belief,live_atom_tom0,live_atom_tom1,live_atom_adaptive_hedge,live_econ_bne --horizon 8 --seeds 5 --orders 4 --pool-mode type_stress --feature-mode masked --concurrency 1 --out-prefix courier_matching_live_masked_type_stress_s5h8_allmodels
```

Outputs:

- `courier_matching_live_masked_type_stress_s5h8_allmodels_summary.json`
- `courier_matching_live_masked_type_stress_s5h8_allmodels_summary.csv`
- `courier_matching_live_masked_type_stress_s5h8_allmodels_rows.csv`

PACT+ now uses a confidence- and time-gated exploration coefficient. The effective exploration weight is high only when posterior confidence is low and the episode is still early; later rounds primarily exploit the learned posterior.

Lowest-regret method per model among rows with parse rate at least `0.90`:

| Model | Best method | Reward | Regret | P(true) | Rule acc | Parse |
|---|---|---:|---:|---:|---:|---:|
| GPT-5.4-mini | `live_llm_belief` | 12.014 | 3.973 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_econ_bne` | 11.623 | 4.473 | 0.062 | 0.500 | 1.000 |
| Kimi-K2.6 | `live_atom_tom0` | 11.492 | 4.886 | 0.062 | 0.500 | 0.950 |
| Llama-4-Maverick | `live_llm_greedy` | 11.654 | 4.687 | 0.062 | 0.500 | 1.000 |

Best posterior-bearing method per model, without filtering out low-parse rows:

| Model | Best posterior method | Reward | Regret | P(true) | Rule acc | Parse | Reliable? |
|---|---|---:|---:|---:|---:|---:|---|
| GPT-5.4-mini | `live_map_greedy` | 11.012 | 4.652 | 0.506 | 0.836 | 1.000 | yes |
| DeepSeek-V3.2 | `live_joint_psrl` | 11.428 | 4.632 | 0.527 | 0.872 | 0.650 | no |
| Kimi-K2.6 | `live_pact` | 11.194 | 4.574 | 0.457 | 0.841 | 0.425 | no |
| Llama-4-Maverick | `live_pact` | 10.731 | 4.703 | 0.564 | 0.846 | 1.000 | yes |

Reliable-row group comparison, using only rows with parse rate at least `0.90`:

| Model | Group | Reliable rows | Mean reward | Mean regret | Mean P(true) | Mean rule acc |
|---|---|---:|---:|---:|---:|---:|
| GPT-5.4-mini | posterior-bearing | 4 | 10.420 | 5.422 | 0.495 | 0.846 |
| GPT-5.4-mini | prompt/no-type | 7 | 10.777 | 5.082 | 0.062 | 0.500 |
| DeepSeek-V3.2 | posterior-bearing | 0 | n/a | n/a | n/a | n/a |
| DeepSeek-V3.2 | prompt/no-type | 6 | 10.871 | 5.069 | 0.062 | 0.500 |
| Kimi-K2.6 | posterior-bearing | 0 | n/a | n/a | n/a | n/a |
| Kimi-K2.6 | prompt/no-type | 2 | 11.054 | 5.048 | 0.062 | 0.500 |
| Llama-4-Maverick | posterior-bearing | 4 | 10.700 | 5.039 | 0.545 | 0.861 |
| Llama-4-Maverick | prompt/no-type | 7 | 10.998 | 5.072 | 0.062 | 0.500 |

Full masked/type-stress all-method table, using mean final cumulative metrics over five seeds:

| Model | Method | Reward | Regret | P(true) | Rule acc | Parse |
|---|---|---:|---:|---:|---:|---:|
| GPT-5.4-mini | `live_pact` | 10.570 | 5.283 | 0.431 | 0.830 | 1.000 |
| GPT-5.4-mini | `live_pact_plus` | 9.980 | 5.692 | 0.517 | 0.858 | 1.000 |
| GPT-5.4-mini | `live_map_greedy` | 11.012 | 4.652 | 0.506 | 0.836 | 1.000 |
| GPT-5.4-mini | `live_joint_psrl` | 10.118 | 6.061 | 0.526 | 0.858 | 1.000 |
| GPT-5.4-mini | `live_psrl_notype` | 9.920 | 5.669 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_llm_greedy` | 11.050 | 5.039 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_llm_belief` | 12.014 | 3.973 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_atom_tom0` | 10.838 | 4.946 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_atom_tom1` | 10.357 | 5.398 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_atom_adaptive_hedge` | 10.861 | 5.102 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_econ_bne` | 10.401 | 5.447 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_pact` | 11.112 | 5.010 | 0.609 | 0.890 | 0.850 |
| DeepSeek-V3.2 | `live_pact_plus` | 11.300 | 5.007 | 0.567 | 0.883 | 0.875 |
| DeepSeek-V3.2 | `live_map_greedy` | 10.701 | 5.385 | 0.506 | 0.858 | 0.850 |
| DeepSeek-V3.2 | `live_joint_psrl` | 11.428 | 4.632 | 0.527 | 0.872 | 0.650 |
| DeepSeek-V3.2 | `live_psrl_notype` | 10.272 | 5.206 | 0.062 | 0.500 | 0.725 |
| DeepSeek-V3.2 | `live_llm_greedy` | 10.551 | 5.050 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_llm_belief` | 11.111 | 5.299 | 0.062 | 0.500 | 0.950 |
| DeepSeek-V3.2 | `live_atom_tom0` | 10.945 | 4.933 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_atom_tom1` | 10.103 | 5.644 | 0.062 | 0.500 | 0.950 |
| DeepSeek-V3.2 | `live_atom_adaptive_hedge` | 10.894 | 5.018 | 0.062 | 0.500 | 0.925 |
| DeepSeek-V3.2 | `live_econ_bne` | 11.623 | 4.473 | 0.062 | 0.500 | 1.000 |
| Kimi-K2.6 | `live_pact` | 11.194 | 4.574 | 0.457 | 0.841 | 0.425 |
| Kimi-K2.6 | `live_pact_plus` | 11.094 | 5.202 | 0.481 | 0.852 | 0.400 |
| Kimi-K2.6 | `live_map_greedy` | 11.517 | 4.636 | 0.396 | 0.821 | 0.600 |
| Kimi-K2.6 | `live_joint_psrl` | 11.355 | 4.645 | 0.532 | 0.860 | 0.325 |
| Kimi-K2.6 | `live_psrl_notype` | 10.326 | 5.197 | 0.062 | 0.500 | 0.775 |
| Kimi-K2.6 | `live_llm_greedy` | 10.616 | 5.210 | 0.062 | 0.500 | 1.000 |
| Kimi-K2.6 | `live_llm_belief` | 11.712 | 4.079 | 0.062 | 0.500 | 0.650 |
| Kimi-K2.6 | `live_atom_tom0` | 11.492 | 4.886 | 0.062 | 0.500 | 0.950 |
| Kimi-K2.6 | `live_atom_tom1` | 10.297 | 5.270 | 0.062 | 0.500 | 0.675 |
| Kimi-K2.6 | `live_atom_adaptive_hedge` | 11.035 | 4.939 | 0.062 | 0.500 | 0.625 |
| Kimi-K2.6 | `live_econ_bne` | 10.957 | 5.158 | 0.062 | 0.500 | 0.650 |
| Llama-4-Maverick | `live_pact` | 10.731 | 4.703 | 0.564 | 0.846 | 1.000 |
| Llama-4-Maverick | `live_pact_plus` | 10.754 | 5.303 | 0.568 | 0.883 | 1.000 |
| Llama-4-Maverick | `live_map_greedy` | 10.915 | 4.833 | 0.584 | 0.874 | 1.000 |
| Llama-4-Maverick | `live_joint_psrl` | 10.400 | 5.318 | 0.464 | 0.842 | 1.000 |
| Llama-4-Maverick | `live_psrl_notype` | 11.325 | 4.956 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_llm_greedy` | 11.654 | 4.687 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_llm_belief` | 10.652 | 5.083 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_atom_tom0` | 11.577 | 4.701 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_atom_tom1` | 10.730 | 5.310 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_atom_adaptive_hedge` | 10.574 | 5.276 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_econ_bne` | 10.478 | 5.488 | 0.062 | 0.500 | 1.000 |

Rows below the parse reliability threshold:

| Model | Method | Reward | Regret | P(true) | Rule acc | Parse |
|---|---|---:|---:|---:|---:|---:|
| DeepSeek-V3.2 | `live_joint_psrl` | 11.428 | 4.632 | 0.527 | 0.872 | 0.650 |
| DeepSeek-V3.2 | `live_map_greedy` | 10.701 | 5.385 | 0.506 | 0.858 | 0.850 |
| DeepSeek-V3.2 | `live_pact` | 11.112 | 5.010 | 0.609 | 0.890 | 0.850 |
| DeepSeek-V3.2 | `live_pact_plus` | 11.300 | 5.007 | 0.567 | 0.883 | 0.875 |
| DeepSeek-V3.2 | `live_psrl_notype` | 10.272 | 5.206 | 0.062 | 0.500 | 0.725 |
| Kimi-K2.6 | `live_atom_adaptive_hedge` | 11.035 | 4.939 | 0.062 | 0.500 | 0.625 |
| Kimi-K2.6 | `live_atom_tom1` | 10.297 | 5.270 | 0.062 | 0.500 | 0.675 |
| Kimi-K2.6 | `live_econ_bne` | 10.957 | 5.158 | 0.062 | 0.500 | 0.650 |
| Kimi-K2.6 | `live_joint_psrl` | 11.355 | 4.645 | 0.532 | 0.860 | 0.325 |
| Kimi-K2.6 | `live_llm_belief` | 11.712 | 4.079 | 0.062 | 0.500 | 0.650 |
| Kimi-K2.6 | `live_map_greedy` | 11.517 | 4.636 | 0.396 | 0.821 | 0.600 |
| Kimi-K2.6 | `live_pact` | 11.194 | 4.574 | 0.457 | 0.841 | 0.425 |
| Kimi-K2.6 | `live_pact_plus` | 11.094 | 5.202 | 0.481 | 0.852 | 0.400 |
| Kimi-K2.6 | `live_psrl_notype` | 10.326 | 5.197 | 0.062 | 0.500 | 0.775 |

Readout: the two environment fixes worked for hidden-rule evidence but did not make PACT dominate regret. In the masked/type-stress run, posterior-bearing methods are the only rows that move above prior rule recovery (`P(true)=0.062`, rule accuracy `0.500`), reaching roughly `P(true)=0.40-0.61` and rule accuracy `0.82-0.89`. However, the best reliable regret rows are still prompt/no-type methods on every model, and several strong posterior rows for DeepSeek and Kimi have parse rates below `0.90`. This means the current benchmark should report regret and rule recovery jointly: prompt planners can still exploit masked numerical regularities without learning hidden rules, while posterior methods learn the rules but need better exploitation and stricter parse control.

## Structured-Solver Live Matching

The direct live runner above still gives the final assignment decision to the LLM. That is intentionally comparable across methods, but it is not the same structural object as HP-SPGG-COM: PACT's posterior becomes a prompt feature rather than the input to a value evaluator. The solver-backed runner restores that path while preserving the requirement that every comparable method calls the LLM.

In `live_structured_matching_dispatch`, every method calls the LLM each round for a bounded driver-order score matrix. The final assignment is then selected by deterministic enumeration over feasible assignments. Posterior-bearing methods use their structured posterior value as the main objective, with a small bounded LLM score adjustment. Prompt/no-type baselines use the LLM score matrix as their decision signal. This separates three quantities that were entangled in the direct runner: hidden-rule recovery, LLM score extraction, and assignment optimization.

Smoke tests completed:

- GPT all-method one-round smoke: `11/11 failed=0`, score parse `1.000` for all methods.
- Four-model all-method one-round smoke after parser repair: `44/44 failed=0`, score parse `1.000` for all rows.

Completed structured live stress run:

```powershell
$env:LLM_HPGG_BACKEND='cloudgpt'; $env:CLOUDGPT_ATTEMPTS='3'; $env:CLOUDGPT_TIMEOUT='30'; uv run python -m llm_courier_dispatch.live_structured_matching_dispatch --backend cloudgpt --models gpt-5.4-mini-20260317,DeepSeek-V3.2,Kimi-K2.6,Llama-4-Maverick-17B-128E-Instruct-FP8 --seeds 5 --horizon 8 --orders 4 --pool-mode type_stress --feature-mode masked --concurrency 4 --out-prefix courier_matching_structured_live_masked_type_stress_s5h8_allmodels
```

The run completed `220/220 failed=0`. It was started with one worker and cache-resumed with `--concurrency 4`; the final summary uses the same cache and out-prefix.

Outputs:

- `courier_matching_structured_live_masked_type_stress_s5h8_allmodels_summary.json`
- `courier_matching_structured_live_masked_type_stress_s5h8_allmodels_summary.csv`
- `courier_matching_structured_live_masked_type_stress_s5h8_allmodels_rows.csv`

Lowest-regret method per model:

| Model | Best method | Group | Reward | Regret | P(true) | Rule acc | Score parse |
|---|---|---|---:|---:|---:|---:|---:|
| GPT-5.4-mini | `live_joint_psrl` | posterior | 13.504 | 2.521 | 0.447 | 0.817 | 1.000 |
| DeepSeek-V3.2 | `live_joint_psrl` | posterior | 13.553 | 2.329 | 0.378 | 0.805 | 1.000 |
| Kimi-K2.6 | `live_joint_psrl` | posterior | 13.489 | 2.543 | 0.455 | 0.841 | 1.000 |
| Llama-4-Maverick | `live_map_greedy` | posterior | 13.424 | 2.589 | 0.396 | 0.787 | 1.000 |

Best prompt/no-type row per model:

| Model | Best prompt/no-type method | Reward | Regret | P(true) | Rule acc | Score parse |
|---|---|---:|---:|---:|---:|---:|
| GPT-5.4-mini | `live_psrl_notype` | 11.200 | 4.936 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_llm_belief` | 11.438 | 4.321 | 0.062 | 0.500 | 1.000 |
| Kimi-K2.6 | `live_atom_adaptive_hedge` | 11.344 | 4.278 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_atom_adaptive_hedge` | 10.995 | 4.872 | 0.062 | 0.500 | 1.000 |

Group comparison:

| Model | Group | Rows | Mean reward | Mean regret | Mean P(true) | Mean rule acc | Mean parse |
|---|---|---:|---:|---:|---:|---:|---:|
| GPT-5.4-mini | posterior-bearing | 4 | 13.039 | 2.816 | 0.455 | 0.826 | 1.000 |
| GPT-5.4-mini | prompt/no-type | 7 | 10.608 | 5.232 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | posterior-bearing | 4 | 13.320 | 2.578 | 0.436 | 0.824 | 1.000 |
| DeepSeek-V3.2 | prompt/no-type | 7 | 10.981 | 4.809 | 0.062 | 0.500 | 1.000 |
| Kimi-K2.6 | posterior-bearing | 4 | 13.185 | 2.698 | 0.421 | 0.821 | 1.000 |
| Kimi-K2.6 | prompt/no-type | 7 | 10.871 | 4.734 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | posterior-bearing | 4 | 13.406 | 2.707 | 0.480 | 0.834 | 1.000 |
| Llama-4-Maverick | prompt/no-type | 7 | 10.472 | 5.334 | 0.062 | 0.500 | 0.996 |

Full structured-solver all-method table:

| Model | Method | Reward | Regret | P(true) | Rule acc | Score parse |
|---|---|---:|---:|---:|---:|---:|
| GPT-5.4-mini | `live_pact` | 13.155 | 2.831 | 0.535 | 0.852 | 1.000 |
| GPT-5.4-mini | `live_pact_plus` | 12.992 | 3.054 | 0.516 | 0.860 | 1.000 |
| GPT-5.4-mini | `live_map_greedy` | 12.506 | 2.860 | 0.323 | 0.776 | 1.000 |
| GPT-5.4-mini | `live_joint_psrl` | 13.504 | 2.521 | 0.447 | 0.817 | 1.000 |
| GPT-5.4-mini | `live_psrl_notype` | 11.200 | 4.936 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_llm_greedy` | 10.950 | 5.269 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_llm_belief` | 10.371 | 5.387 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_atom_tom0` | 10.344 | 5.388 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_atom_tom1` | 10.585 | 5.033 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_atom_adaptive_hedge` | 10.437 | 5.213 | 0.062 | 0.500 | 1.000 |
| GPT-5.4-mini | `live_econ_bne` | 10.369 | 5.401 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_pact` | 13.579 | 2.455 | 0.475 | 0.832 | 1.000 |
| DeepSeek-V3.2 | `live_pact_plus` | 13.692 | 2.702 | 0.485 | 0.857 | 1.000 |
| DeepSeek-V3.2 | `live_map_greedy` | 12.458 | 2.825 | 0.406 | 0.802 | 1.000 |
| DeepSeek-V3.2 | `live_joint_psrl` | 13.553 | 2.329 | 0.378 | 0.805 | 1.000 |
| DeepSeek-V3.2 | `live_psrl_notype` | 11.310 | 4.786 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_llm_greedy` | 11.619 | 4.419 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_llm_belief` | 11.438 | 4.321 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_atom_tom0` | 11.039 | 4.722 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_atom_tom1` | 10.898 | 4.713 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_atom_adaptive_hedge` | 9.975 | 5.766 | 0.062 | 0.500 | 1.000 |
| DeepSeek-V3.2 | `live_econ_bne` | 10.589 | 4.939 | 0.062 | 0.500 | 1.000 |
| Kimi-K2.6 | `live_pact` | 13.150 | 2.669 | 0.371 | 0.798 | 1.000 |
| Kimi-K2.6 | `live_pact_plus` | 13.521 | 2.891 | 0.484 | 0.857 | 1.000 |
| Kimi-K2.6 | `live_map_greedy` | 12.581 | 2.689 | 0.375 | 0.786 | 1.000 |
| Kimi-K2.6 | `live_joint_psrl` | 13.489 | 2.543 | 0.455 | 0.841 | 1.000 |
| Kimi-K2.6 | `live_psrl_notype` | 11.399 | 4.698 | 0.062 | 0.500 | 1.000 |
| Kimi-K2.6 | `live_llm_greedy` | 11.313 | 4.591 | 0.062 | 0.500 | 1.000 |
| Kimi-K2.6 | `live_llm_belief` | 9.621 | 5.310 | 0.062 | 0.500 | 1.000 |
| Kimi-K2.6 | `live_atom_tom0` | 10.934 | 4.926 | 0.062 | 0.500 | 1.000 |
| Kimi-K2.6 | `live_atom_tom1` | 10.747 | 4.874 | 0.062 | 0.500 | 1.000 |
| Kimi-K2.6 | `live_atom_adaptive_hedge` | 11.344 | 4.278 | 0.062 | 0.500 | 1.000 |
| Kimi-K2.6 | `live_econ_bne` | 10.742 | 4.459 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_pact` | 13.426 | 2.777 | 0.468 | 0.838 | 1.000 |
| Llama-4-Maverick | `live_pact_plus` | 13.385 | 2.697 | 0.486 | 0.845 | 1.000 |
| Llama-4-Maverick | `live_map_greedy` | 13.424 | 2.589 | 0.396 | 0.787 | 1.000 |
| Llama-4-Maverick | `live_joint_psrl` | 13.390 | 2.766 | 0.572 | 0.865 | 1.000 |
| Llama-4-Maverick | `live_psrl_notype` | 11.140 | 5.039 | 0.062 | 0.500 | 0.975 |
| Llama-4-Maverick | `live_llm_greedy` | 10.149 | 5.565 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_llm_belief` | 10.503 | 5.185 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_atom_tom0` | 10.170 | 5.412 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_atom_tom1` | 9.983 | 5.740 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_atom_adaptive_hedge` | 10.995 | 4.872 | 0.062 | 0.500 | 1.000 |
| Llama-4-Maverick | `live_econ_bne` | 10.365 | 5.522 | 0.062 | 0.500 | 1.000 |

Readout: this setting behaves like the intended HP-SPGG-style structural comparison. Once the LLM call is converted into bounded score advice and the final assignment is selected by a deterministic solver, the best method on every model is posterior-bearing. Posterior-bearing methods reduce mean regret by roughly two points versus prompt/no-type baselines while also recovering hidden rules. This confirms that the earlier direct-assignment failure mode was mostly a setting/interface issue: PACT's belief was being exposed as prompt text, not used as the decision-relevant value state.

### Expected-Value PACT Update

After the first structured-solver run, PACT still used a Thompson-sampled type tuple for exploitation. That was weaker than the HP-SPGG-style belief-to-value path. PACT and PACT+ now use exact factored posterior expected value for exploitation, with a vectorized evaluator over the finite type grid. MAP-Greedy and Joint-PSRL keep their original semantics.

Analytic type-stress result after this update:

| Method | Regret | Reward | P(true) | Rule acc |
|---|---:|---:|---:|---:|
| `oracle` | 0.000 | 31.279 | 1.000 | 1.000 |
| `pact_plus` | 1.826 | 29.853 | 0.326 | 0.758 |
| `joint_psrl` | 2.710 | 29.394 | 0.648 | 0.891 |
| `pact` | 2.820 | 29.187 | 0.436 | 0.811 |
| `map_greedy` | 3.014 | 28.529 | 0.410 | 0.810 |
| `atom_tom1` | 8.002 | 23.946 | 0.062 | 0.500 |
| `psrl_notype` | 9.708 | 22.421 | 0.062 | 0.500 |
| `random` | 9.897 | 21.879 | 0.062 | 0.500 |

Completed structured live stress run with expected-value PACT:

```powershell
$env:LLM_HPGG_BACKEND='cloudgpt'; $env:CLOUDGPT_ATTEMPTS='3'; $env:CLOUDGPT_TIMEOUT='30'; uv run python -m llm_courier_dispatch.live_structured_matching_dispatch --backend cloudgpt --models gpt-5.4-mini-20260317,DeepSeek-V3.2,Kimi-K2.6,Llama-4-Maverick-17B-128E-Instruct-FP8 --seeds 5 --horizon 8 --orders 4 --pool-mode type_stress --feature-mode masked --concurrency 4 --out-prefix courier_matching_structured_live_expected_pact_masked_type_stress_s5h8_allmodels
```

The run completed `220/220 failed=0`. It reused the existing structured LLM score cache and rewrote only the solver-side decision rows and summaries.

Outputs:

- `courier_matching_structured_live_expected_pact_masked_type_stress_s5h8_allmodels_summary.json`
- `courier_matching_structured_live_expected_pact_masked_type_stress_s5h8_allmodels_summary.csv`
- `courier_matching_structured_live_expected_pact_masked_type_stress_s5h8_allmodels_rows.csv`

Lowest-regret method per model after the update:

| Model | Best method | Reward | Regret | P(true) | Rule acc | Score parse |
|---|---|---:|---:|---:|---:|---:|
| GPT-5.4-mini | `live_pact_plus` | 14.264 | 1.545 | 0.275 | 0.726 | 1.000 |
| DeepSeek-V3.2 | `live_pact_plus` | 14.264 | 1.545 | 0.275 | 0.726 | 1.000 |
| Kimi-K2.6 | `live_pact_plus` | 13.859 | 1.712 | 0.293 | 0.741 | 1.000 |
| Llama-4-Maverick | `live_pact_plus` | 14.378 | 1.718 | 0.291 | 0.748 | 1.000 |

Posterior-bearing method comparison:

| Model | Method | Reward | Regret | P(true) | Rule acc | Score parse |
|---|---|---:|---:|---:|---:|---:|
| GPT-5.4-mini | `live_pact` | 13.607 | 2.209 | 0.361 | 0.784 | 1.000 |
| GPT-5.4-mini | `live_pact_plus` | 14.264 | 1.545 | 0.275 | 0.726 | 1.000 |
| GPT-5.4-mini | `live_joint_psrl` | 13.504 | 2.521 | 0.447 | 0.817 | 1.000 |
| GPT-5.4-mini | `live_map_greedy` | 12.506 | 2.860 | 0.323 | 0.776 | 1.000 |
| DeepSeek-V3.2 | `live_pact` | 13.447 | 2.300 | 0.405 | 0.800 | 1.000 |
| DeepSeek-V3.2 | `live_pact_plus` | 14.264 | 1.545 | 0.275 | 0.726 | 1.000 |
| DeepSeek-V3.2 | `live_joint_psrl` | 13.553 | 2.329 | 0.378 | 0.805 | 1.000 |
| DeepSeek-V3.2 | `live_map_greedy` | 12.458 | 2.825 | 0.406 | 0.802 | 1.000 |
| Kimi-K2.6 | `live_pact` | 13.740 | 2.123 | 0.393 | 0.790 | 1.000 |
| Kimi-K2.6 | `live_pact_plus` | 13.859 | 1.712 | 0.293 | 0.741 | 1.000 |
| Kimi-K2.6 | `live_joint_psrl` | 13.489 | 2.543 | 0.455 | 0.841 | 1.000 |
| Kimi-K2.6 | `live_map_greedy` | 12.581 | 2.689 | 0.375 | 0.786 | 1.000 |
| Llama-4-Maverick | `live_pact` | 13.182 | 2.269 | 0.323 | 0.768 | 1.000 |
| Llama-4-Maverick | `live_pact_plus` | 14.378 | 1.718 | 0.291 | 0.748 | 1.000 |
| Llama-4-Maverick | `live_joint_psrl` | 13.390 | 2.766 | 0.572 | 0.865 | 1.000 |
| Llama-4-Maverick | `live_map_greedy` | 13.424 | 2.589 | 0.396 | 0.787 | 1.000 |

Readout: expected-value exploitation fixes the remaining PACT positioning issue. `live_pact_plus` is now the lowest-regret method on every model, and plain `live_pact` beats or essentially ties `live_joint_psrl` on three of four models. The tradeoff is that PACT+ achieves lower regret with lower final rule recovery than Joint-PSRL, so the result should be framed as regret-optimal exploitation under learned posterior rather than maximum type identification.

Four-model CloudGPT beta sweep:

```powershell
$env:LLM_HPGG_BACKEND='cloudgpt'; $env:CLOUDGPT_ATTEMPTS='3'; $env:CLOUDGPT_TIMEOUT='30'; $betas=@('0.0','0.025','0.05','0.1','0.2','0.4'); foreach ($b in $betas) { $tag=$b.Replace('.','p'); uv run python -m llm_courier_dispatch.live_structured_matching_dispatch --backend cloudgpt --models gpt-5.4-mini-20260317,DeepSeek-V3.2,Kimi-K2.6,Llama-4-Maverick-17B-128E-Instruct-FP8 --live-methods live_pact_plus --seeds 5 --horizon 8 --orders 4 --pool-mode type_stress --feature-mode masked --concurrency 4 --pact-plus-beta $b --out-prefix courier_matching_structured_live_expected_pact_beta_${tag}_s5h8_allmodels }
```

Each beta run completed `20/20 failed=0`. Score parse is `1.000` for every beta/model row. The sweep summary and figure are:

- `courier_matching_structured_live_expected_pact_beta_sweep_s5h8_allmodels_summary.json`
- `courier_matching_structured_live_expected_pact_beta_sweep_s5h8_allmodels_summary.csv`
- `figs/fig_courier_matching_llm_backend_beta_sweep.png`
- `figs/fig_courier_matching_llm_backend_beta_sweep.pdf`

Best beta by model in this sweep:

| Model | Best beta | Regret | Reward | Rule acc |
|---|---:|---:|---:|---:|
| GPT-5.4-mini | 0.05 | 1.528 | 14.381 | 0.737 |
| DeepSeek-V3.2 | 0.05 | 1.542 | 14.368 | 0.737 |
| Kimi-K2.6 | 0.05 | 1.661 | 14.004 | 0.754 |
| Llama-4-Maverick | 0.05 | 1.578 | 14.527 | 0.729 |

Readout: `beta=0.05` is the most stable setting across all four live LLM backends. Moving from `0.0` to `0.05` sharply reduces regret, while larger beta values start to give back regret; rule recovery is highest at low beta and partially recovers again at larger beta, showing the intended exploitation/recovery tradeoff.

Remaining next steps:

- Keep random pools as robustness checks and use `type_stress` as the main matching stress table.
- Add constrained decoding or stronger JSON repair for the direct-assignment runner before treating its low-parse posterior rows as headline results.
- Tune PACT's exploitation rule against MAP/Joint-PSRL and the prompt/no-type planners; the new PACT+ gate fixes always-on exploration, but it does not by itself guarantee lowest short-horizon regret.
- Report regret and rule recovery jointly; prompt heuristics can have low regret in semantically easy pools but do not learn hidden rules.

## Status

This is the first online matching prototype. It uses a mean-field expected-reward approximation for fast assignment scoring. A larger version should add vectorized exact assignment values or a controlled Monte Carlo estimator before replacing the main CourierDispatch tables.