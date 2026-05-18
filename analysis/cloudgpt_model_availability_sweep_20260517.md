# CloudGPT Model Availability for HP-SPGG Sweep

Last updated: 2026-05-17

Probe artifact: `analysis/cloudgpt_model_probe_sweep_candidates_20260517.jsonl`

## Current Probe Result

| Model | Probe status | Reply | c19 calibration exists | Suggested use |
| --- | --- | --- | --- | --- |
| `DeepSeek-V3.2` | ok | `OK` | yes | headline reference; already complete at K20/seeds=5 |
| `gpt-5.4-nano-20260317` | ok | `OK` | yes | primary cross-model sweep |
| `Kimi-K2.6` | ok | empty reply | yes | primary cross-model sweep |
| `Llama-4-Maverick-17B-128E-Instruct-FP8` | ok | `OK` | yes | primary cross-model sweep |
| `gpt-5.5-20260424` | ok | empty reply | yes | optional; existing report has parse-failure caveats |
| `gpt-5.4-mini-20260317` | ok | `OK` | no | optional only after calibration/native layer |
| `gpt-5.3-chat-20260303` | ok | empty reply | no | optional only after calibration/native layer |
| `gpt-5.2-chat-20260210` | ok | empty reply | no | optional only after calibration/native layer |
| `gpt-4.1-mini-20250414` | ok | `OK` | no | optional cheaper reference after calibration/native layer |
| `Kimi-K2.5` | ok | empty reply | no | optional Kimi-family sensitivity after calibration/native layer |
| `Llama-3.3-70B-Instruct` | ok | `OK` | no | optional Llama-family sensitivity after calibration/native layer |
| `gpt-5.4-pro-20260305` | failed | unsupported operation | no | do not use for this sweep |
| `Kimi-K2-Thinking` | failed | unknown model | no | do not use for this sweep |

Grok remains excluded from the active sweep per user preference and prior unstable probe behavior.

## Immediate Sweep Set

These models are both currently callable and already have native c19 calibrations, so we can run prompted LLM and external A-ToM/ECON layers without first rebuilding calibration:

1. `gpt-5.4-nano-20260317`
2. `Kimi-K2.6`
3. `Llama-4-Maverick-17B-128E-Instruct-FP8`

Optional fourth model:

4. `gpt-5.5-20260424`, if we want an additional GPT-family point and are comfortable documenting the parse-failure caveat from the existing native report.

## Recommended Order

1. Run prompted LLM baselines for the three primary models at K20/seeds=5.
2. Summarize cross-model prompted LLM vs native c19.
3. Run external A-ToM/ECON for the same three primary models if budget/time allows.
4. Only then consider optional models without c19 calibration.