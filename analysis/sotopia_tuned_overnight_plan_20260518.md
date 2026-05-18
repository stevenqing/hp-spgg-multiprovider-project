# SOTOPIA Tuned HPSMG+ Overnight Plan - 2026-05-18

## Goal

Run the SOTOPIA-specific `sotopia_tuned` wrapper for `hpsmg_plus` without changing the legacy/core method and without overwriting existing all70 results.

## Safety Rules

- Keep legacy SOTOPIA outputs unchanged.
- Write all tuned outputs to new `*_hpsmg_plus_sotopia_tuned_*` files.
- Use `--resume` for all all70 runs.
- Use local SOTOPIA storage and CloudGPT for player/evaluator calls.
- Keep tuned concurrency controlled while the existing legacy queue is still active.

## Run Order

1. Targeted live pilots:
   - GPT case index 12: `revenge_plot` failure mode.
   - Kimi case index 2: bargaining/generic-fallback failure mode.
   - Llama case index 48: ownership/verification failure mode.
2. Full all70 tuned HPSMG+ runs:
   - `DeepSeek-V3.2`
   - `gpt-5.4-nano-20260317`
   - `Kimi-K2.6`
   - `Llama-4-Maverick-17B-128E-Instruct-FP8`

## Expected Output Files

- `analysis/sotopia_tuned_pilot_gpt_5_4_nano_20260317_hpsmg_plus_case12.json`
- `analysis/sotopia_tuned_pilot_Kimi_K2_6_hpsmg_plus_case2.json`
- `analysis/sotopia_tuned_pilot_Llama_4_Maverick_17B_128E_Instruct_FP8_hpsmg_plus_case48.json`
- `analysis/sotopia_hard_official_DeepSeek_V3_2_hpsmg_plus_sotopia_tuned_all70.json`
- `analysis/sotopia_hard_official_gpt_5_4_nano_20260317_hpsmg_plus_sotopia_tuned_all70.json`
- `analysis/sotopia_hard_official_Kimi_K2_6_hpsmg_plus_sotopia_tuned_all70.json`
- `analysis/sotopia_hard_official_Llama_4_Maverick_17B_128E_Instruct_FP8_hpsmg_plus_sotopia_tuned_all70.json`

## Monitoring

- Main log: `logs/sotopia_tuned_hpsmg_plus_overnight.log`
- Per-job stdout/stderr logs: `logs/sotopia_tuned_*_stdout.log`, `logs/sotopia_tuned_*_stderr.log`

Morning checks:

```powershell
Get-Content logs\sotopia_tuned_hpsmg_plus_overnight.log -Tail 80
Get-ChildItem analysis -File | Where-Object { $_.Name -like '*sotopia*' -and $_.Name -like '*tuned*' } | Select-Object Name,Length,LastWriteTime
```