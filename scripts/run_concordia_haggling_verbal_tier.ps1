param(
  [Parameter(Mandatory=$true)][string]$Tier,
  [Parameter(Mandatory=$true)][string]$Model
)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
New-Item -ItemType Directory -Force logs, analysis\llm_psrl_verbal | Out-Null
$env:PYTHONPATH = "$Root;$Root\_archive\external\concordia"
$env:LLM_HPGG_BACKEND = "cloudgpt"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
Start-Transcript -Path "logs\concordia_haggling_verbal_${Tier}_$stamp.transcript.log" -Force | Out-Null
try {
  $out = "analysis\llm_psrl_verbal\concordia_haggling_fruitville_${Tier}_llmpsrl_s30.json"
  if (Test-Path $out) {
    try { $json = Get-Content $out -Raw | ConvertFrom-Json; if ($json.summary) { Write-Host "SKIP existing $out"; return } } catch {}
  }
  Write-Host "RUN Concordia haggling $Tier model=$Model"
  uv run python -m llm_hpgg_concordia.run_haggling_compact `
    --domain haggling --config fruitville --model $Model `
    --methods llm_psrl_verbal hpsmg_plus_joint_proxy oracle_joint oracle_focal `
    --seeds 30 --out $out
} finally { Stop-Transcript | Out-Null }