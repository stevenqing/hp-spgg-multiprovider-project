# E1-E4 LLM Evidence Runbook - 2026-05-18

This is the live-LLM evidence version. It differs from the fast calibrated simulation run: reward cells for E1 refresh and E2/E3 scaling are scored by CloudGPT live judge calls and saved as live calibration tensors.

## Evidence Tier

- E1: model-specific c19 calibration refresh using CloudGPT live judge calls, then posterior concentration is measured on the refreshed live tensor.
- E2: type-space scaling with Llama as judge; each type-count calibration uses live judge scores on representative action profiles.
- E3: n-agent scaling with Llama as judge; each n-agent calibration uses live judge scores on representative action profiles.
- E4: prior recovery on refreshed DeepSeek live c19 calibration.

The default overnight run uses `ProfileCount=19`, so each calibration scores 19 representative joint-action profiles live. Non-scored cells retain the deterministic fallback from the same scaling game, and reports record exactly which profile indices were scored.

## Smoke Test

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_e1_e4_llm_evidence_smoke.ps1
```

Smoke runs one live profile for E2 and one live profile for E3. It is intended only to prove CloudGPT path, cache, parsing, analysis, and plotting work.

## Overnight Run

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_e1_e4_llm_evidence_overnight.ps1 -ProfileCount 19 -Workers 2
```

## Monitoring

```powershell
.\scripts\check_e1_e4_llm_evidence_status.ps1
```

## Outputs

- Raw NPZ: `results/e1_e4_llm/`
- Live calibration tensors: `calibration/e1_e4_llm/`
- Live calibration reports: `analysis/E*_live_report.json`
- Figures: `figs/*_llm.png`
- Tables: `tables/*_llm.csv`
- Numeric summaries: `analysis/*_llm_summary.json`

## Claim Safety

Use the phrase `live LLM-judge calibrated HP-SPGG evidence`, not `full live multi-agent dialogue`, unless a separate player-dialogue run is added. E2/E3 are live-scored calibration experiments, not every profile is live-scored unless `ProfileCount` is raised to the full profile count.