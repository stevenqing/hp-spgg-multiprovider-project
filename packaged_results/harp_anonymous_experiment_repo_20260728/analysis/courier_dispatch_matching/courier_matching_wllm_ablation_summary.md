# CourierDispatch Structured LLM Score-Weight Ablation

This ablation tests whether the structured-solver headline is driven by the LLM score adjustment rather than the structured posterior planner.

## Protocol

Fixed configuration:

- Environment: CourierDispatch-Rules matching, `pool_mode=type_stress`, `feature_mode=masked`
- Backend: `managed`
- Models: `gpt-5.4-mini-20260317`, `DeepSeek-V3.2`, `Kimi-K2.6`, `Llama-4-Maverick-17B-128E-Instruct-FP8`
- Horizon: `8`
- Seeds: `5`
- Orders per round: `4`
- Methods: all structured live methods
- PACT+ beta: `0.1`
- LLM score weights: `w_LLM=0.0` and headline `w_LLM=0.02`

Information-control note:

- In these headline runs, prompt/A-ToM baselines receive the public order pool, neutral action history, feature codebook, and method-specific belief/history instructions.
- They do not receive the full analytic reward and action-likelihood equations used by the structured posterior planner.
- Therefore the main comparison should be described as structured posterior planning versus prompt-only public-history baselines, not as an LLM with full simulator access.
- A follow-up diagnostic option, `--env-info-level full`, now adds the code-level environment equations and parameters to the LLM prompt while preserving hidden driver types. A small smoke run (`courier_matching_structured_live_fullenv_smoke_s1h2`) verifies that this path runs and parses at `1.000`; full-scale results should be generated before making any claim about full-environment-info LLM baselines.

Definition of strongest prompt/A-ToM baseline:

```text
min regret over live_llm_greedy, live_llm_belief, live_atom_tom0, live_atom_tom1,
live_atom_adaptive_hedge, live_econ_bne
```

`live_psrl_notype` is reported in the all-method table, but is not included in the strongest prompt/A-ToM baseline set.

Primary decision quantity:

```text
gap = regret(best prompt/A-ToM baseline) - regret(PACT+)
```

Positive gap means PACT+ has lower regret.

## Primary Gap Result

| Model | w_LLM | PACT+ regret | Best prompt/A-ToM | Prompt regret | Gap | Gap shrink vs w*=0.02 |
|---|---:|---:|---|---:|---:|---:|
| GPT-5.4-mini | 0.0 | 1.678 | A-ToM-1 | 5.033 | 3.355 | 0.133 |
| GPT-5.4-mini | 0.02 | 1.545 | A-ToM-1 | 5.033 | 3.489 | 0.000 |
| DeepSeek-V3.2 | 0.0 | 1.678 | LLM-Belief | 4.321 | 2.642 | 0.133 |
| DeepSeek-V3.2 | 0.02 | 1.545 | LLM-Belief | 4.321 | 2.776 | 0.000 |
| Kimi-K2.6 | 0.0 | 1.678 | A-ToM-Hedge | 4.278 | 2.600 | -0.034 |
| Kimi-K2.6 | 0.02 | 1.712 | A-ToM-Hedge | 4.278 | 2.566 | 0.000 |
| Llama-Maverick | 0.0 | 1.678 | A-ToM-Hedge | 4.872 | 3.194 | -0.040 |
| Llama-Maverick | 0.02 | 1.718 | A-ToM-Hedge | 4.872 | 3.154 | 0.000 |

Interpretation:

- Removing LLM score weight does not erase the PACT+ advantage.
- The largest shrink in the PACT+ gap is `0.133` cumulative regret, on GPT-5.4-mini and DeepSeek-V3.2.
- On Kimi-K2.6 and Llama-Maverick, the PACT+ gap is slightly larger at `w_LLM=0`.
- The advantage is therefore not driven by the bounded LLM score adjustment. It is driven by the structured posterior expected-value term plus PACT+ disagreement bonus.

## Requested Headline Role Table

This table reports exactly four roles per model and score-weight setting: PACT+, PACT, strongest prompt baseline, and strongest A-ToM baseline. Prompt baselines are selected from `live_llm_greedy`, `live_llm_belief`, and `live_econ_bne`. A-ToM baselines are selected from `live_atom_tom0`, `live_atom_tom1`, and `live_atom_adaptive_hedge`.

| w_LLM | Model | Role | Method | Regret +/- SEM | P(true) +/- SEM | Rule acc +/- SEM |
|---:|---|---|---|---:|---:|---:|
| 0.0 | GPT-5.4-mini | PACT+ | PACT+ | 1.678 +/- 0.212 | 0.299 +/- 0.046 | 0.744 +/- 0.023 |
| 0.0 | GPT-5.4-mini | PACT | PACT | 2.533 +/- 0.539 | 0.431 +/- 0.048 | 0.807 +/- 0.028 |
| 0.0 | GPT-5.4-mini | Best prompt | LLM-Greedy | 5.269 +/- 0.428 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.0 | GPT-5.4-mini | Best A-ToM | A-ToM-1 | 5.033 +/- 0.308 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.0 | DeepSeek-V3.2 | PACT+ | PACT+ | 1.678 +/- 0.212 | 0.299 +/- 0.046 | 0.744 +/- 0.023 |
| 0.0 | DeepSeek-V3.2 | PACT | PACT | 2.533 +/- 0.539 | 0.431 +/- 0.048 | 0.807 +/- 0.028 |
| 0.0 | DeepSeek-V3.2 | Best prompt | LLM-Belief | 4.321 +/- 0.747 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.0 | DeepSeek-V3.2 | Best A-ToM | A-ToM-1 | 4.713 +/- 0.851 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.0 | Kimi-K2.6 | PACT+ | PACT+ | 1.678 +/- 0.212 | 0.299 +/- 0.046 | 0.744 +/- 0.023 |
| 0.0 | Kimi-K2.6 | PACT | PACT | 2.533 +/- 0.539 | 0.431 +/- 0.048 | 0.807 +/- 0.028 |
| 0.0 | Kimi-K2.6 | Best prompt | ECON-BNE | 4.459 +/- 0.912 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.0 | Kimi-K2.6 | Best A-ToM | A-ToM-Hedge | 4.278 +/- 0.673 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.0 | Llama-Maverick | PACT+ | PACT+ | 1.678 +/- 0.212 | 0.299 +/- 0.046 | 0.744 +/- 0.023 |
| 0.0 | Llama-Maverick | PACT | PACT | 2.533 +/- 0.539 | 0.431 +/- 0.048 | 0.807 +/- 0.028 |
| 0.0 | Llama-Maverick | Best prompt | LLM-Belief | 5.185 +/- 0.287 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.0 | Llama-Maverick | Best A-ToM | A-ToM-Hedge | 4.872 +/- 0.349 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.02 | GPT-5.4-mini | PACT+ | PACT+ | 1.545 +/- 0.198 | 0.275 +/- 0.051 | 0.726 +/- 0.024 |
| 0.02 | GPT-5.4-mini | PACT | PACT | 2.209 +/- 0.320 | 0.361 +/- 0.053 | 0.784 +/- 0.026 |
| 0.02 | GPT-5.4-mini | Best prompt | LLM-Greedy | 5.269 +/- 0.428 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.02 | GPT-5.4-mini | Best A-ToM | A-ToM-1 | 5.033 +/- 0.308 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.02 | DeepSeek-V3.2 | PACT+ | PACT+ | 1.545 +/- 0.198 | 0.275 +/- 0.051 | 0.726 +/- 0.024 |
| 0.02 | DeepSeek-V3.2 | PACT | PACT | 2.300 +/- 0.371 | 0.405 +/- 0.036 | 0.800 +/- 0.025 |
| 0.02 | DeepSeek-V3.2 | Best prompt | LLM-Belief | 4.321 +/- 0.747 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.02 | DeepSeek-V3.2 | Best A-ToM | A-ToM-1 | 4.713 +/- 0.851 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.02 | Kimi-K2.6 | PACT+ | PACT+ | 1.712 +/- 0.214 | 0.293 +/- 0.045 | 0.741 +/- 0.023 |
| 0.02 | Kimi-K2.6 | PACT | PACT | 2.123 +/- 0.298 | 0.393 +/- 0.036 | 0.790 +/- 0.024 |
| 0.02 | Kimi-K2.6 | Best prompt | ECON-BNE | 4.459 +/- 0.912 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.02 | Kimi-K2.6 | Best A-ToM | A-ToM-Hedge | 4.278 +/- 0.673 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.02 | Llama-Maverick | PACT+ | PACT+ | 1.718 +/- 0.321 | 0.291 +/- 0.061 | 0.748 +/- 0.032 |
| 0.02 | Llama-Maverick | PACT | PACT | 2.269 +/- 0.302 | 0.323 +/- 0.069 | 0.768 +/- 0.031 |
| 0.02 | Llama-Maverick | Best prompt | LLM-Belief | 5.185 +/- 0.287 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |
| 0.02 | Llama-Maverick | Best A-ToM | A-ToM-Hedge | 4.872 +/- 0.349 | 0.062 +/- 0.000 | 0.500 +/- 0.000 |

## PACT+ Assignment Consistency And Counterfactual Flip Rate

End-to-end assignment consistency compares the realized PACT+ trajectories under `w_LLM=0.0` and `w_LLM=0.02`:

| Model | Same assignments / decisions | Rate |
|---|---:|---:|
| GPT-5.4-mini | 33/40 | 0.825 |
| DeepSeek-V3.2 | 33/40 | 0.825 |
| Kimi-K2.6 | 38/40 | 0.950 |
| Llama-Maverick | 21/40 | 0.525 |
| Overall | 125/160 | 0.781 |

The cleaner counterfactual replay fixes the headline `w_LLM=0.02` trajectory state, posterior, order pool, and cached LLM score matrix, then removes only the LLM score term from the argmax objective. This directly measures whether `llm_score_weight * LLMScore(a)` changes the chosen assignment.

| Model | Argmax flips / decisions | Flip rate |
|---|---:|---:|
| GPT-5.4-mini | 1/40 | 0.025 |
| DeepSeek-V3.2 | 1/40 | 0.025 |
| Kimi-K2.6 | 1/40 | 0.025 |
| Llama-Maverick | 6/40 | 0.150 |
| Overall | 9/160 | 0.056 |

Interpretation: under fixed trajectory states, removing the LLM score term changes only `5.6%` of PACT+ decisions overall. This supports the claim that the headline PACT+ advantage is carried by posterior expected value plus the PACT+ disagreement bonus, not by direct LLM score steering.

## Recovery And Regret Table

| w_LLM | Model | Method | Regret +/- SEM | P(true) +/- SEM | Rule acc +/- SEM | Parse |
|---:|---|---|---:|---:|---:|---:|
| 0.0 | GPT-5.4-mini | PACT+ | 1.678 +/- 0.212 | 0.299 +/- 0.046 | 0.744 +/- 0.023 | 1.000 |
| 0.0 | GPT-5.4-mini | PACT | 2.533 +/- 0.539 | 0.431 +/- 0.048 | 0.807 +/- 0.028 | 1.000 |
| 0.0 | GPT-5.4-mini | Joint-PSRL | 2.115 +/- 0.374 | 0.437 +/- 0.097 | 0.817 +/- 0.047 | 1.000 |
| 0.0 | GPT-5.4-mini | MAP-Greedy | 2.881 +/- 0.239 | 0.368 +/- 0.116 | 0.789 +/- 0.048 | 1.000 |
| 0.0 | GPT-5.4-mini | PSRL-NoType | 4.689 +/- 0.734 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | GPT-5.4-mini | LLM-Greedy | 5.269 +/- 0.428 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | GPT-5.4-mini | LLM-Belief | 5.387 +/- 0.631 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | GPT-5.4-mini | A-ToM-0 | 5.388 +/- 0.231 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | GPT-5.4-mini | A-ToM-1 | 5.033 +/- 0.308 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | GPT-5.4-mini | A-ToM-Hedge | 5.213 +/- 0.433 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | GPT-5.4-mini | ECON-BNE | 5.401 +/- 0.343 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | DeepSeek-V3.2 | PACT+ | 1.678 +/- 0.212 | 0.299 +/- 0.046 | 0.744 +/- 0.023 | 1.000 |
| 0.0 | DeepSeek-V3.2 | PACT | 2.533 +/- 0.539 | 0.431 +/- 0.048 | 0.807 +/- 0.028 | 1.000 |
| 0.0 | DeepSeek-V3.2 | Joint-PSRL | 2.115 +/- 0.374 | 0.437 +/- 0.097 | 0.817 +/- 0.047 | 1.000 |
| 0.0 | DeepSeek-V3.2 | MAP-Greedy | 2.881 +/- 0.239 | 0.368 +/- 0.116 | 0.789 +/- 0.048 | 1.000 |
| 0.0 | DeepSeek-V3.2 | PSRL-NoType | 4.689 +/- 0.734 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | DeepSeek-V3.2 | LLM-Greedy | 4.419 +/- 0.515 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | DeepSeek-V3.2 | LLM-Belief | 4.321 +/- 0.747 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | DeepSeek-V3.2 | A-ToM-0 | 4.722 +/- 0.345 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | DeepSeek-V3.2 | A-ToM-1 | 4.713 +/- 0.851 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | DeepSeek-V3.2 | A-ToM-Hedge | 5.766 +/- 0.750 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | DeepSeek-V3.2 | ECON-BNE | 4.939 +/- 0.533 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | Kimi-K2.6 | PACT+ | 1.678 +/- 0.212 | 0.299 +/- 0.046 | 0.744 +/- 0.023 | 1.000 |
| 0.0 | Kimi-K2.6 | PACT | 2.533 +/- 0.539 | 0.431 +/- 0.048 | 0.807 +/- 0.028 | 1.000 |
| 0.0 | Kimi-K2.6 | Joint-PSRL | 2.115 +/- 0.374 | 0.437 +/- 0.097 | 0.817 +/- 0.047 | 1.000 |
| 0.0 | Kimi-K2.6 | MAP-Greedy | 2.881 +/- 0.239 | 0.368 +/- 0.116 | 0.789 +/- 0.048 | 1.000 |
| 0.0 | Kimi-K2.6 | PSRL-NoType | 4.689 +/- 0.734 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | Kimi-K2.6 | LLM-Greedy | 4.591 +/- 0.452 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | Kimi-K2.6 | LLM-Belief | 5.310 +/- 0.712 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | Kimi-K2.6 | A-ToM-0 | 4.926 +/- 0.543 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | Kimi-K2.6 | A-ToM-1 | 4.874 +/- 0.436 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | Kimi-K2.6 | A-ToM-Hedge | 4.278 +/- 0.673 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | Kimi-K2.6 | ECON-BNE | 4.459 +/- 0.912 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | Llama-Maverick | PACT+ | 1.678 +/- 0.212 | 0.299 +/- 0.046 | 0.744 +/- 0.023 | 1.000 |
| 0.0 | Llama-Maverick | PACT | 2.533 +/- 0.539 | 0.431 +/- 0.048 | 0.807 +/- 0.028 | 1.000 |
| 0.0 | Llama-Maverick | Joint-PSRL | 2.115 +/- 0.374 | 0.437 +/- 0.097 | 0.817 +/- 0.047 | 1.000 |
| 0.0 | Llama-Maverick | MAP-Greedy | 2.881 +/- 0.239 | 0.368 +/- 0.116 | 0.789 +/- 0.048 | 1.000 |
| 0.0 | Llama-Maverick | PSRL-NoType | 4.689 +/- 0.734 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 0.975 |
| 0.0 | Llama-Maverick | LLM-Greedy | 5.565 +/- 0.548 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | Llama-Maverick | LLM-Belief | 5.185 +/- 0.287 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | Llama-Maverick | A-ToM-0 | 5.412 +/- 0.614 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | Llama-Maverick | A-ToM-1 | 5.740 +/- 0.809 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | Llama-Maverick | A-ToM-Hedge | 4.872 +/- 0.349 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |
| 0.0 | Llama-Maverick | ECON-BNE | 5.522 +/- 0.373 | 0.062 +/- 0.000 | 0.500 +/- 0.000 | 1.000 |

The full CSV also includes the `w_LLM=0.02` rows.
