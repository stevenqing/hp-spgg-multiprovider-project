# CourierDispatch F2 Unified w_LLM=0 Horizon/Beta Sweep

This note replaces the earlier mixed-source F2 sweep with one consistent `w_LLM=0` objective for all four beta lines. It includes the requested `beta=0.5` overshoot line and the full `4 betas x 4 horizons` table.

## Why This Replaces the Mixed F2

The previous F2 aggregate mixed sources: `beta in {0,0.1,0.25}` came from older live rows with `llm_score_weight=0.02`, while `beta=0.5` was computed under `w_LLM=0`. That is not a clean comparison. The current F2 CSV and figure now use `w_LLM=0` for every beta and horizon.

At `w_LLM=0`, the LLM score term is inactive in the structured objective, so the exact structured evaluator is decision-equivalent to the live structured solver. This was explicitly checked at `H=8, beta=0.5`: the CloudGPT live row and exact evaluator matched on reward, regret, `P(true)`, and rule accuracy.

## Fixed Configuration

| Quantity | Value |
|---|---|
| Method | PACT+ structured solver |
| Objective | `w_LLM=0` |
| beta grid | `{0, 0.1, 0.25, 0.5}` |
| Horizons | `H in {8,16,24,32}` |
| Seeds | `5`, same seed set as previous F2 |
| Backbones | `gpt-5.4-mini-20260317`, `DeepSeek-V3.2`, `Kimi-K2.6`, `Llama-4-Maverick-17B-128E-Instruct-FP8` |
| Pool mode | `type_stress` |
| Feature mode | `masked` |
| Orders per round | `4` |
| Hidden rule space | `|Theta|=16` per driver |
| Source used in final table | `exact` for every cell, with `H=8,beta=0.5` live-equivalence verified |
| Error bars | Across-seed SEM, copied into each backbone row because `w_LLM=0` makes backbones decision-equivalent |

## Output Files

Unified F2 summary and figure:

- [courier_matching_live_F2_horizon_beta_sweep_summary.csv](courier_matching_live_F2_horizon_beta_sweep_summary.csv)
- [courier_matching_live_F2_horizon_beta_sweep_summary.json](courier_matching_live_F2_horizon_beta_sweep_summary.json)
- [../../figs/fig_courier_matching_F2_horizon_beta.png](../../figs/fig_courier_matching_F2_horizon_beta.png)
- [../../figs/fig_courier_matching_F2_horizon_beta.pdf](../../figs/fig_courier_matching_F2_horizon_beta.pdf)
- [../../arr_paper/figs/fig_courier_matching_F2_horizon_beta.png](../../arr_paper/figs/fig_courier_matching_F2_horizon_beta.png)
- [../../arr_paper/figs/fig_courier_matching_F2_horizon_beta.pdf](../../arr_paper/figs/fig_courier_matching_F2_horizon_beta.pdf)

Exact source rows:

- `courier_matching_F2_wllm0_exact_h{H}_beta_{tag}_rows.csv`
- `courier_matching_F2_wllm0_exact_h{H}_beta_{tag}_summary.json`

Aggregation and plotting scripts:

- [../../scripts/aggregate_courier_matching_F2_horizon_beta.py](../../scripts/aggregate_courier_matching_F2_horizon_beta.py)
- [../../scripts/plot_courier_matching_F2_horizon_beta.py](../../scripts/plot_courier_matching_F2_horizon_beta.py)

## Unified Table

One row per `(beta, H)`. The reported SEM is across seeds, not across backbones.

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

## Updated F2 Figure

![F2 unified w_LLM=0 horizon/beta sweep](../../figs/fig_courier_matching_F2_horizon_beta.png)

The F2 aggregate has `64` rows: `4 horizons x 4 betas x 4 backbone slots`. The backbone slots are retained for figure compatibility, but all rows are exact `w_LLM=0` source rows.

## Sanity Checks

| Check | Result | Status |
|---|---|---|
| `beta=0.25` has lowest regret at `H=24` | `2.112`, lower than `0`, `0.1`, and `0.5` | pass |
| `beta=0.25` has lowest regret at `H=32` | `2.121`, lower than `0`, `0.1`, and `0.5` | pass |
| `beta=0.5` worse than `beta=0.25` at every H | Deltas: `+0.434`, `+0.388`, `+0.702`, `+0.211` | pass |
| `beta=0` highest `P(true)` at every H | True for all four horizons | pass |
| regret rises with H for every beta | True for `0`, `0.1`, `0.25`; false for `0.5` because regret drops from `2.815` at H=24 to `2.332` at H=32 | flag |

Overshoot detail:

| H | Regret at beta=0.25 | Regret at beta=0.5 | Delta |
|---:|---:|---:|---:|
| 8 | 1.738 | 2.172 | +0.434 |
| 16 | 2.112 | 2.500 | +0.388 |
| 24 | 2.112 | 2.815 | +0.702 |
| 32 | 2.121 | 2.332 | +0.211 |

Readout: the unified `w_LLM=0` F2 supports the main beta story. `beta=0.25` is the best long-horizon trade-off at `H=24` and `H=32`, while `beta=0.5` overshoots and worsens regret at every horizon. `beta=0` remains best for posterior concentration, which is useful to report separately from regret. The only caveat is that regret is not monotone in H for `beta=0.5`; do not state monotone H-growth for every beta without this exception.

## Reproduction Commands

Run the exact `w_LLM=0` grid:

```powershell
$betas=@('0.0','0.1','0.25','0.5'); $hs=@('8','16','24','32'); foreach ($b in $betas) { $tag=$b.Replace('.','p'); foreach ($h in $hs) { uv run python -m llm_courier_dispatch.matching_dispatch --pool-mode type_stress --horizon $h --seeds 5 --orders 4 --samples 4 --methods pact_plus:$b --out-prefix courier_matching_F2_wllm0_exact_h${h}_beta_${tag} } }
```

Aggregate and redraw F2:

```powershell
uv run python scripts/aggregate_courier_matching_F2_horizon_beta.py
uv run python scripts/plot_courier_matching_F2_horizon_beta.py
```
