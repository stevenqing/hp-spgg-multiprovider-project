# HP-SPGG Results Bundle

Created: 2026-05-17

This folder is a packaging snapshot of the HP-SPGG experiment outputs and reproducibility artifacts.

## Contents

| Directory/File | Contents |
|---|---|
| `results/` | Raw `.npz` experiment outputs, including native, prompted LLM, external LLM, and shard results. |
| `results_phase2/` | Phase 2 result directory snapshot. Currently empty in this bundle. |
| `analysis/` | Markdown summaries, JSON traces, run logs, coverage notes, and result interpretation documents. |
| `tables/` | LaTeX tables for paper/report use. |
| `figs/` | Generated figures/PDFs. |
| `scripts/` | Reproducibility and postprocessing scripts used to summarize, merge, and validate outputs. |
| `logs/` | LLM/cache/log snapshots used during long CloudGPT runs. |
| `FILELIST.txt` | Full file list for this bundle. |

## Primary Entry Points

- `analysis/results_index.md`: single index for all result files and paper-ready artifacts.
- `analysis/all_numeric_results.md`: numeric-only consolidated result tables.
- `analysis/overall_results_summary.md`: current narrative summary of the experiment state.
- `analysis/proposed_vs_baselines_guardrail_20260517.md`: guardrail for claims about the proposed method vs baselines.
- `analysis/model_performance_available_20260517.md`: current cross-model performance analysis using completed results.
- `analysis/E2_native_vs_llm_baselines_stats.md`: headline statistics table.

## Notes

- This is a snapshot taken while the Kimi external LLM sweep was still running. Completed Kimi external shards available at snapshot time are included, but later finished shards will need a refreshed bundle.
- The headline DeepSeek c19 K20/s5 results are complete and included.
- The generated `FILELIST.txt` can be used to audit exactly what is in the bundle.
