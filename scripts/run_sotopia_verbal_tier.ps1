param(
  [Parameter(Mandatory=$true)][string]$Tier,
  [Parameter(Mandatory=$true)][string]$Model
)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
New-Item -ItemType Directory -Force logs, analysis\llm_psrl_verbal | Out-Null
$env:PYTHONPATH = "$Root;$Root\_archive\external\sotopia"
$env:LLM_HPGG_BACKEND = "cloudgpt"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
Start-Transcript -Path "logs\sotopia_verbal_${Tier}_$stamp.transcript.log" -Force | Out-Null
try {
  $out = "analysis\llm_psrl_verbal\sotopia_hard_${Tier}_llm_psrl_verbal_all70.json"
  $skip = $false
  if (Test-Path $out) {
    try { $json = Get-Content $out -Raw | ConvertFrom-Json; if ($json.complete -eq $true -and [int]$json.case_count -eq 70) { $skip = $true } } catch { $skip = $false }
  }
  if ($skip) { Write-Host "SKIP complete $out"; return }
  Write-Host "RUN/RESUME SOTOPIA $Tier model=$Model"
  uv run python -m llm_hpgg_sotopia.run_sotopia_hard_official `
    --baseline llm-psrl-verbal --model $Model --evaluator-model $Model `
    --agent-strategy-profile sotopia_tuned --turns 6 --limit 70 `
    --concurrency 3 --resume `
    --benchmark-agents _archive\external\sotopia_data_probe\benchmark_agents.json `
    --episodes-jsonl _archive\external\sotopia_data_probe\sotopia_episodes_v1_hf.jsonl `
    --cache _archive\external\sotopia_data_probe\sotopia_hard_cases_cache.json `
    --out $out
} finally { Stop-Transcript | Out-Null }