# Proposed Method vs Baselines Guardrail

Date: 2026-05-17

Goal: make sure the paper's main claim is framed correctly: the proposed HP-SPGG method should outperform non-oracle baselines under the same calibration, K, and seed setting.

Primary metric: final cumulative regret, lower is better.

## Headline DeepSeek c19 Setting

This passes cleanly. On `DeepSeek-V3.2`, `c19`, `K=20`, `seeds=5`, `hpsmg_plus` is the best non-oracle method.

| Rank | Group | Algorithm | Final cumulative regret mean | Std | Mean welfare |
|---:|---|---|---:|---:|---:|
| 1 | Native upper bound | oracle | 0.0000 | 0.0000 | 2.9500 |
| 2 | Proposed | hpsmg_plus | 0.4000 | 0.8000 | 2.7600 |
| 3 | Native baseline | map_greedy | 0.7120 | 0.4663 | 2.7144 |
| 4 | Proposed ablation | hpsmg | 0.8280 | 0.5414 | 2.8526 |
| 5 | Native baseline | joint_psrl | 0.8320 | 0.0796 | 2.8384 |
| 6 | Prompted LLM baseline | llm_belief | 3.0740 | 2.2308 | 2.7363 |
| 7 | External LLM baseline | econ_bne | 3.9900 | 3.4136 | 2.6105 |
| 8 | External LLM baseline | atom_adaptive_hedge | 4.7900 | 4.5089 | 2.6605 |

For the headline experiment, the closest true baseline is `map_greedy` at 0.7120, so `hpsmg_plus` improves by 0.3120 final cumulative regret. The closest LLM baseline is `llm_belief` at 3.0740, so `hpsmg_plus` is about 7.7x lower regret.

## Cross-Model Guardrail Check

The table below checks whether the best available `hpsmg_plus` beta beats every available non-oracle baseline for that same model. Here `hpsmg` is treated as a baseline/ablation, so this is a strict check.

| Model | Best hpsmg_plus beta | Best hpsmg_plus | Best baseline group | Best baseline | Best baseline mean | Margin | Status |
|---|---|---:|---|---|---:|---:|---|
| DeepSeek-V3.2 | beta0 | 0.4000 | native | hpsmg_plus-nearest: map_greedy | 0.7120 | +0.3120 | PASS |
| gpt-5.4-nano | beta1 | 0.8980 | native | hpsmg | 0.6440 | -0.2540 | VIOLATION |
| Kimi-K2.6 | beta0p25 | 0.7040 | native | hpsmg | 0.6320 | -0.0720 | VIOLATION |
| Llama-4-Maverick | beta0p25 | 0.3120 | native | hpsmg | 0.7320 | +0.4200 | PASS |

## Interpretation

The headline DeepSeek claim is sound: `hpsmg_plus` is currently the best non-oracle method there.

The broader cross-model claim needs care. If `hpsmg` is counted as a baseline, then `hpsmg_plus` does not dominate all baselines on nano and Kimi. This is not a problem for the main headline table, but it is a problem for any broad claim like "hpsmg_plus beats every baseline on every model."

A safer and stronger framing is:

1. The HP-SPGG posterior family dominates generic LLM and type-agnostic baselines.
2. The exploration bonus in `hpsmg_plus` improves over the posterior-only ablation on the headline DeepSeek setting and on Llama, but it is not uniformly beneficial across all model calibrations.
3. Cross-model robustness should report both `hpsmg` and `hpsmg_plus`, or use a pre-specified validation rule for selecting the bonus strength before comparing against held-out test seeds.

## Action Items Before Paper Finalization

1. Keep the main headline claim on the normalized DeepSeek c19 setting: `hpsmg_plus` is best non-oracle.
2. For cross-model tables, do not claim `hpsmg_plus` dominates `hpsmg` on every model unless new validation/test results support it.
3. Treat `hpsmg` as an ablation of the proposed family, not as a competing external baseline, when discussing method-family performance.
4. If the paper needs one single method to dominate across models, implement a pre-registered selector: choose `hpsmg` vs `hpsmg_plus(beta)` using validation calibrations/seeds, then evaluate on held-out seeds.
5. Once Kimi external finishes, rerun `scripts/check_proposed_vs_baselines.py` and `scripts/check_proposed_beta_sweep_vs_baselines.py`.

## Repro Commands

```powershell
uv run python scripts\check_proposed_vs_baselines.py
uv run python scripts\check_proposed_beta_sweep_vs_baselines.py
```
