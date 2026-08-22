# SOTOPIA Tuned All-Baseline Fair Rerun

Date: 2026-05-18

## Rationale

The previous tuned SOTOPIA result only applied `agent_strategy_profile=sotopia_tuned` to HPSMG+. That is useful as an adaptation result, but it is not a strict apples-to-apples tuned comparison against vanilla baselines.

We therefore changed the SOTOPIA agent wrapper so every baseline can run under the same SOTOPIA-tuned task interface:

- same decoding profile: `max_tokens=280`, `temperature=0.0`
- same longer observation/history context
- same SOTOPIA scoring guardrails
- same no-premature-`leave` behavior when `speak` is available
- same concrete-offer/action cleanup and fallback logic
- baseline-specific decision principle preserved inside the shared wrapper

## Baselines

The fair tuned comparison covers:

- `hpsmg_plus_sotopia_tuned`
- `llm_belief_sotopia_tuned`
- `llm_greedy_sotopia_tuned`
- `atom_tom1_sotopia_tuned`
- `econ_bne_sotopia_tuned`

## Models

The rerun covers the same four CloudGPT backbones:

- `DeepSeek-V3.2`
- `gpt-5.4-nano-20260317`
- `Kimi-K2.6`
- `Llama-4-Maverick-17B-128E-Instruct-FP8`

## Smoke Check

A one-case smoke run completed for `DeepSeek-V3.2` + `llm_greedy_sotopia_tuned`:

- output: `analysis/sotopia_hard_official_smoke_DeepSeek_V3_2_llm_greedy_sotopia_tuned_limit1.json`
- case count: 1
- mean overall: 3.5

## Overnight Queue

Queue script:

- `scripts/run_sotopia_tuned_all_baselines_overnight.ps1`

Started command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_sotopia_tuned_all_baselines_overnight.ps1 -MaxConcurrent 2 -MaxTotalSotopiaProcesses 4 -LogPath logs\sotopia_tuned_all_baselines_overnight.log
```

The script skips already complete tuned HPSMG+ all70 outputs and runs the missing tuned baselines with `--agent-strategy-profile sotopia_tuned`.

## Reporting Rule

Until this all-baseline tuned rerun finishes, paper-facing SOTOPIA claims should remain split:

- vanilla fair comparison: report the legacy-profile all70 table
- old HPSMG+-only tuned adaptation: report only as a separate adaptation result
- all-baseline tuned fair comparison: report after all `*_sotopia_tuned_all70.json` files complete
