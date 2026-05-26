param(
  [string]$OnlyTier = ""
)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
New-Item -ItemType Directory -Force logs, analysis\llm_psrl_verbal | Out-Null
$env:PYTHONPATH = "$Root;$Root\_archive\external\concordia"
$env:LLM_HPGG_BACKEND = "cloudgpt"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
Start-Transcript -Path "logs\concordia_full_verbal_$Stamp.transcript.log" -Force | Out-Null

try {
  $models = @{
    deepseek       = "DeepSeek-V3.2"
    gpt5_nano      = "gpt-5.4-nano-20260317"
    kimi_k2        = "Kimi-K2.6"
    llama_maverick = "Llama-4-Maverick-17B-128E-Instruct-FP8"
  }
  $pub = @(
    @{key="capetown_s100"; config="capetown"; seeds=100},
    @{key="capetown_s30"; config="capetown"; seeds=30},
    @{key="edinburgh_s30"; config="edinburgh"; seeds=30},
    @{key="edinburgh_closures_s30"; config="edinburgh_closures"; seeds=30},
    @{key="edinburgh_tough_friendship_s30"; config="edinburgh_tough_friendship"; seeds=30},
    @{key="london_s30"; config="london"; seeds=30},
    @{key="london_closures_s30"; config="london_closures"; seeds=30},
    @{key="london_mini_s30"; config="london_mini"; seeds=30}
  )
  $hagSingle = @("fruitville", "fruitville_gullible", "vegbrooke", "vegbrooke_stubborn", "vegbrooke_strange_game")
  $hagMulti = @("fruitville_multi", "fruitville_gullible", "vegbrooke", "cumulative_score")

  $tiersToRun = @($models.Keys)
  if ($OnlyTier) { $tiersToRun = @($OnlyTier) }
  foreach ($tier in $tiersToRun) {
    $model = $models[$tier]
    foreach ($item in $pub) {
      $out = "analysis\llm_psrl_verbal\concordia_full_pub_$($item.key)_${tier}_llmpsrl.json"
      if (Test-Path $out) { Write-Host "SKIP existing $out"; continue }
      Write-Host "RUN pub $($item.key) $tier"
      uv run python -m llm_hpgg_concordia.run_pub_coordination_compact `
        --config $item.config --model $model --methods llm_psrl_verbal --seeds $item.seeds --out $out
    }
    foreach ($config in $hagSingle) {
      $out = "analysis\llm_psrl_verbal\concordia_full_haggling_${config}_${tier}_llmpsrl.json"
      if (Test-Path $out) { Write-Host "SKIP existing $out"; continue }
      Write-Host "RUN haggling $config $tier"
      uv run python -m llm_hpgg_concordia.run_haggling_compact `
        --domain haggling --config $config --model $model --methods llm_psrl_verbal --seeds 30 --out $out
    }
    foreach ($config in $hagMulti) {
      $out = "analysis\llm_psrl_verbal\concordia_full_haggling_multi_item_${config}_${tier}_llmpsrl.json"
      if (Test-Path $out) { Write-Host "SKIP existing $out"; continue }
      Write-Host "RUN haggling_multi_item $config $tier"
      uv run python -m llm_hpgg_concordia.run_haggling_compact `
        --domain haggling_multi_item --config $config --model $model --methods llm_psrl_verbal --seeds 30 --out $out
    }
  }
  if (-not $OnlyTier) {
    Write-Host "=== regenerate Concordia radar ==="
    uv run python scripts\plot_fig_concordia_main_v4.py
  }
  Write-Host "=== Done Concordia full verbal ==="
} finally {
  Stop-Transcript | Out-Null
}