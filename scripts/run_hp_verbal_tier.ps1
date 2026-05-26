param(
  [Parameter(Mandatory=$true)][string]$Tier,
  [Parameter(Mandatory=$true)][string]$Model
)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
New-Item -ItemType Directory -Force logs, analysis\llm_psrl_verbal | Out-Null
$env:PYTHONPATH = $Root
$env:LLM_HPGG_BACKEND = "cloudgpt"
$env:LLM_PSRL_VERBAL_MODEL = $Model
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
Start-Transcript -Path "logs\hp_verbal_${Tier}_$stamp.transcript.log" -Force | Out-Null
try {
  foreach ($n in 3,4,5,6) {
    $cal = "results_phase2\e1_1_llm_tier\calibration_live_n${n}_${Tier}.npy"
    $out = "analysis\llm_psrl_verbal\E_llmpsrl_n${n}_K20_${Tier}.npz"
    if (Test-Path $out) { Write-Host "SKIP existing $out"; continue }
    Write-Host "RUN HP $Tier n=$n model=$Model"
    uv run python -m llm_hpgg.run_experiment `
      --K 20 --n $n --seeds 5 --beta 0.25 `
      --algos hpsmg hpsmg_plus llm_psrl_verbal `
      --calibration $cal --out $out --matched-seeds `
      --verbal-model $Model
    uv run python scripts\summarize_llm_psrl_verbal.py
  }
} finally { Stop-Transcript | Out-Null }