# CourierDispatch w_LLM=0 Baseline Addendum: LLM-PSRL-verbal and Random

This note integrates the two additional CourierDispatch-Rules baselines requested to align the method set with the HP-SPGG cross-model figure: `LLM-PSRL-verbal` and `Random`. The run keeps the current headline setting fixed so the new rows are directly comparable and mergeable with the existing `w_LLM=0` structured-solver headline run.

## Fixed Configuration

| Quantity | Value |
|---|---|
| Backend | `managed` |
| Models | `DeepSeek-V3.2`, `gpt-5.4-mini-20260317`, `Kimi-K2.6`, `Llama-4-Maverick-17B-128E-Instruct-FP8` |
| Horizon | `H=8` |
| Seeds | `5`, same seed set as headline run |
| Pool mode | `type_stress` |
| Feature mode | `masked` |
| Orders per round | `4` |
| Hidden rule space | `|Theta|=16` per driver |
| LLM score weight | `w_LLM=0` |
| Temperature | `0.2`, matching the live LLM baseline setting |
| Metrics | cumulative regret, `P(true rule tuple)`, per-rule accuracy, assignment parse rate, verbal readout parse rate |

## Baseline Semantics

### Random

`live_random` chooses a legal driver-order assignment uniformly at random each round. It has no belief state and makes no LLM call.

Type recovery is reported by convention only:

| Metric | Value |
|---|---:|
| `P(true rule tuple)` | `1/|Theta| = 0.0625` |
| Rule accuracy | `0.5` |
| Flag | `no_type_estimate_floor_by_construction` |

This row should be rendered as a floor reference, not as a scored type-estimation method.

### LLM-PSRL-verbal

`live_llm_psrl_verbal` is the direct verbal-belief foil for PACT. It keeps one natural-language belief note per driver. Each round, the model sees the public history for each driver, the current order/menu pool, and the current belief notes. It then updates the notes, verbally commits to a Thompson-sampling-style hidden-rule hypothesis, and outputs one legal assignment.

No numeric posterior is stored for this method. Recovery is measured through an explicit readout call: after each round, the model is asked to output a binary point estimate for `(avoid_long, zone_loyal, home_pull, surge_only)` from each driver's current belief note. The run logs:

| Quantity | Meaning |
|---|---|
| `live_score_parse_ok_rate` | assignment JSON/format parse success |
| `type_readout_parse_rate` | rule tuple readout parse success |
| `type_estimate_flag` | `verbal_point_estimate` when readout succeeds |
| `P(true rule tuple)` | `1` if all four readout bits match truth, else `0`, averaged over drivers/seeds |
| Rule accuracy | fraction of matching rule bits, averaged over drivers/seeds |

## Implementation Status

| File | Change |
|---|---|
| [../../llm_courier_dispatch/live_structured_matching_dispatch.py](../../llm_courier_dispatch/live_structured_matching_dispatch.py) | Added `live_random`, `live_llm_psrl_verbal`, verbal notes, verbal assignment parsing, readout parsing, and type-estimate flags |
| [../../scripts/merge_courier_matching_structured_summaries.py](../../scripts/merge_courier_matching_structured_summaries.py) | Added reusable merger for appending supplement baseline runs to the existing headline summary |
| [../../scripts/plot_courier_matching_llm_backend_main.py](../../scripts/plot_courier_matching_llm_backend_main.py) | Added labels/colors/family bands for `LLM-PSRL-verbal` and `Random`, plus `--summary` and `--out-name` |

Compile check passed:

```powershell
uv run python -m compileall llm_courier_dispatch/live_structured_matching_dispatch.py scripts/merge_courier_matching_structured_summaries.py scripts/plot_courier_matching_llm_backend_main.py
```

## Output Files

Standalone new-baseline run:

- [courier_matching_structured_live_wllm0_verbal_random_s5h8_allmodels_summary.csv](courier_matching_structured_live_wllm0_verbal_random_s5h8_allmodels_summary.csv)
- [courier_matching_structured_live_wllm0_verbal_random_s5h8_allmodels_summary.json](courier_matching_structured_live_wllm0_verbal_random_s5h8_allmodels_summary.json)
- [courier_matching_structured_live_wllm0_verbal_random_s5h8_allmodels_rows.csv](courier_matching_structured_live_wllm0_verbal_random_s5h8_allmodels_rows.csv)

Merged with the existing `w_LLM=0` headline run:

- [courier_matching_structured_live_wllm0_with_verbal_random_s5h8_allmodels_summary.csv](courier_matching_structured_live_wllm0_with_verbal_random_s5h8_allmodels_summary.csv)
- [courier_matching_structured_live_wllm0_with_verbal_random_s5h8_allmodels_summary.json](courier_matching_structured_live_wllm0_with_verbal_random_s5h8_allmodels_summary.json)
- [courier_matching_structured_live_wllm0_with_verbal_random_s5h8_allmodels_rows.csv](courier_matching_structured_live_wllm0_with_verbal_random_s5h8_allmodels_rows.csv)

Merged figure:

- [../../figs/fig_courier_matching_llm_backend_wllm0_with_verbal_random.png](../../figs/fig_courier_matching_llm_backend_wllm0_with_verbal_random.png)
- [../../figs/fig_courier_matching_llm_backend_wllm0_with_verbal_random.pdf](../../figs/fig_courier_matching_llm_backend_wllm0_with_verbal_random.pdf)
- [../../arr_paper/figs/fig_courier_matching_llm_backend_wllm0_with_verbal_random.png](../../arr_paper/figs/fig_courier_matching_llm_backend_wllm0_with_verbal_random.png)
- [../../arr_paper/figs/fig_courier_matching_llm_backend_wllm0_with_verbal_random.pdf](../../arr_paper/figs/fig_courier_matching_llm_backend_wllm0_with_verbal_random.pdf)

![Merged w_LLM=0 figure with LLM-PSRL-verbal and Random](../../figs/fig_courier_matching_llm_backend_wllm0_with_verbal_random.png)

## New Baseline Results

Standalone new-baseline final metrics:

| Model | Method | Reward | Regret | P(true) | Rule acc | Assignment parse | Readout parse | Flag |
|---|---|---:|---:|---:|---:|---:|---:|---|
| DeepSeek-V3.2 | `live_llm_psrl_verbal` | 11.477 | 4.725 | 0.0667 | 0.467 | 0.725 | 1.000 | `verbal_point_estimate` |
| DeepSeek-V3.2 | `live_random` | 10.882 | 5.049 | 0.0625 | 0.500 | 1.000 | 1.000 | `no_type_estimate_floor_by_construction` |
| GPT-5.4-mini | `live_llm_psrl_verbal` | 11.255 | 4.424 | 0.0667 | 0.533 | 1.000 | 1.000 | `verbal_point_estimate` |
| GPT-5.4-mini | `live_random` | 10.882 | 5.049 | 0.0625 | 0.500 | 1.000 | 1.000 | `no_type_estimate_floor_by_construction` |
| Kimi-K2.6 | `live_llm_psrl_verbal` | 12.329 | 3.937 | 0.1333 | 0.533 | 0.725 | 0.983 | `verbal_point_estimate` |
| Kimi-K2.6 | `live_random` | 10.882 | 5.049 | 0.0625 | 0.500 | 1.000 | 1.000 | `no_type_estimate_floor_by_construction` |
| Llama-Maverick | `live_llm_psrl_verbal` | 12.141 | 3.721 | 0.0667 | 0.467 | 1.000 | 0.958 | `verbal_point_estimate` |
| Llama-Maverick | `live_random` | 10.882 | 5.049 | 0.0625 | 0.500 | 1.000 | 1.000 | `no_type_estimate_floor_by_construction` |

## Merged Headline Coverage

The merged summary has `52` rows: `4 models x 13 methods`.

| Check | Result |
|---|---:|
| Models | 4 |
| Methods per model | 13 |
| Total merged summary rows | 52 |
| Total merged per-round rows | 2080 |
| Random recovery floor | `P(true)=0.0625`, `rule_acc=0.5` |
| Random type flag | `no_type_estimate_floor_by_construction` |
| LLM-PSRL-verbal readout parse range | `0.958` to `1.000` |
| LLM-PSRL-verbal assignment parse range | `0.725` to `1.000` |

## Readout

`Random` behaves exactly as intended: it is backbone-invariant, has floor recovery by construction, and sits as a lower-bound reference.

`LLM-PSRL-verbal` is a useful foil. It beats Random on regret for all four backbones, with the strongest regret among the new rows on Llama and Kimi. However, its extracted type recovery remains close to floor in this run. The method is therefore not matching numeric PACT-style posterior recovery, which is the desired contrast for the verbal-vs-numeric belief claim.

The main caveat is parse reliability for the assignment step: DeepSeek and Kimi have assignment parse rate `0.725`, while GPT and Llama have `1.000`. Readout parse itself is high across all backbones. In the paper table or figure caption, the `LLM-PSRL-verbal` row should retain parse-rate metadata rather than being treated as a parse-clean structured solver row.

## Reproduction Commands

Run the two new baselines:

```powershell
$env:LLM_HPGG_BACKEND='managed'; $env:MANAGED_PROVIDER_ATTEMPTS='3'; $env:MANAGED_PROVIDER_TIMEOUT='30'; uv run python -m llm_courier_dispatch.live_structured_matching_dispatch --backend managed --models DeepSeek-V3.2,gpt-5.4-mini-20260317,Kimi-K2.6,Llama-4-Maverick-17B-128E-Instruct-FP8 --live-methods live_llm_psrl_verbal,live_random --seeds 5 --horizon 8 --orders 4 --pool-mode type_stress --feature-mode masked --concurrency 4 --temperature 0.2 --llm-score-weight 0 --out-prefix courier_matching_structured_live_wllm0_verbal_random_s5h8_allmodels
```

Merge into the existing `w_LLM=0` headline run:

```powershell
uv run python scripts/merge_courier_matching_structured_summaries.py --inputs courier_matching_structured_live_expected_pact_wllm0_masked_type_stress_s5h8_allmodels_summary.json courier_matching_structured_live_wllm0_verbal_random_s5h8_allmodels_summary.json --out-prefix courier_matching_structured_live_wllm0_with_verbal_random_s5h8_allmodels
```

Regenerate the merged headline figure:

```powershell
uv run python scripts/plot_courier_matching_llm_backend_main.py --summary analysis/courier_dispatch_matching/courier_matching_structured_live_wllm0_with_verbal_random_s5h8_allmodels_summary.json --out-name fig_courier_matching_llm_backend_wllm0_with_verbal_random
```
