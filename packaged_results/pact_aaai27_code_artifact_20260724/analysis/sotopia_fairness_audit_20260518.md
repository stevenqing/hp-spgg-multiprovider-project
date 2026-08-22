# SOTOPIA Fairness Audit - 2026-05-18

This audit checks whether the reconstructed SOTOPIA-Hard all70 comparisons are fair enough to report.

## Audit Result

There are two distinct comparison tiers:

1. **Vanilla fair comparison**: `hpsmg_plus`, `llm_belief`, `llm_greedy`, `atom_tom1`, and `econ_bne`, all with `agent_strategy_profile=legacy`.
2. **SOTOPIA-adapted comparison**: `hpsmg_plus_sotopia_tuned`, a tuned HPSMG+ prompt/action profile compared against the available all70 baselines.

The vanilla tier is the strict apples-to-apples baseline comparison. The tuned tier is valid only if reported transparently as a SOTOPIA-specific adaptation/ablation, not hidden as vanilla HPSMG+.

## Metadata Fairness Checks

All all70 rows use:

- Same reconstructed SOTOPIA-Hard 70 cases within each model.
- Same acting model and evaluator model per row.
- Same evaluator family: CloudGPT SOTOPIA-dimension evaluator.
- Same target case count: 70.
- Same turn cap: 6.
- Same environment reconstruction and runner.

Observed metadata status:

| Model | Case set parity | Complete all70 | Evaluator parity | Turn cap |
| --- | --- | --- | --- | --- |
| DeepSeek-V3.2 | pass | pass | pass | pass |
| gpt-5.4-nano-20260317 | pass | pass | pass | pass |
| Kimi-K2.6 | pass | pass | pass | pass |
| Llama-4-Maverick-17B-128E-Instruct-FP8 | pass | pass | pass | pass |

Some legacy baselines terminate early on some cases, yielding `turns_completed` below 6. This is an outcome of the agent/environment interaction, not a different configured turn budget.

## Adaptation Parity Check

Adaptation parity does **not** pass for the tuned row:

- `hpsmg_plus_sotopia_tuned` uses `agent_strategy_profile=sotopia_tuned`.
- The non-HPSMG+ baselines use `agent_strategy_profile=legacy` in the current all70 files.
- Therefore, tuned HPSMG+ should not be described as the same comparison tier as vanilla baselines.

## Vanilla Fair Comparison

Higher mean overall is better.

| Model | Best vanilla method | Best vanilla score | Vanilla HPSMG+ score | Vanilla HPSMG+ rank |
| --- | --- | ---: | ---: | ---: |
| DeepSeek-V3.2 | HPSMG+ | 3.193878 | 3.193878 | 1/5 |
| gpt-5.4-nano-20260317 | ECON-BNE | 2.969388 | 2.685714 | 5/5 |
| Kimi-K2.6 | ECON-BNE | 2.448980 | 1.577551 | 4/5 |
| Llama-4-Maverick-17B-128E-Instruct-FP8 | ECON-BNE | 3.263265 | 3.153061 | 4/5 |

Conclusion: vanilla HPSMG+ is not consistently superior on SOTOPIA-Hard. It is strong on DeepSeek but weak/mixed on GPT, Kimi, and Llama.

## Tuned Adaptation Comparison

Higher mean overall is better.

| Model | HPSMG+ tuned | Best non-tuned baseline | Margin |
| --- | ---: | ---: | ---: |
| DeepSeek-V3.2 | 3.247959 | 3.193878 | +0.054081 |
| gpt-5.4-nano-20260317 | 2.980612 | 2.969388 | +0.011224 |
| Kimi-K2.6 | 2.807143 | 2.448980 | +0.358163 |
| Llama-4-Maverick-17B-128E-Instruct-FP8 | 3.308163 | 3.263265 | +0.044898 |

Conclusion: tuned HPSMG+ is top-ranked across all four backbones, but this is a SOTOPIA-adapted result. It should be reported separately and transparently.

## Recommended Paper Framing

Use two claims, not one blended claim:

1. **Strict fairness claim**: Under the vanilla SOTOPIA interface, HPSMG+ is mixed; it leads on DeepSeek but not across all backbones.
2. **Adaptation claim**: A transparent SOTOPIA-adapted HPSMG+ interface ranks first across all four backbones on reconstructed SOTOPIA-Hard all70.

Do not write: `HPSMG+ beats all baselines on SOTOPIA-Hard` without the `tuned/adapted` qualifier.

Safe wording:

> On reconstructed SOTOPIA-Hard, vanilla HPSMG+ is mixed across backbones. After adding a pre-specified SOTOPIA task-interface profile to HPSMG+, which we report separately as HPSMG+ tuned, the method ranks first across all four tested CloudGPT backbones. We provide both vanilla and tuned rows to make the adaptation explicit.

## Follow-up Fair Tuned Rerun

After this audit, we started the stricter alternative: a shared SOTOPIA task-interface wrapper for every baseline, not only HPSMG+.

The wrapper keeps each method's decision principle distinct but gives `llm_belief`, `llm_greedy`, `atom_tom1`, `econ_bne`, and `hpsmg_plus` the same `agent_strategy_profile=sotopia_tuned` interface. See `analysis/sotopia_tuned_all_baselines_fair_rerun_20260518.md` for the queue, smoke check, and reporting rule.

Until those all70 runs finish, the HPSMG+-only tuned table should remain labeled as an adaptation result rather than a fully fair tuned comparison.