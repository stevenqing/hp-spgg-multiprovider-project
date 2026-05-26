$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
New-Item -ItemType Directory -Force logs, analysis\llm_psrl_verbal | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$TranscriptPath = Join-Path $Root "logs\crosssubstrate_llm_psrl_verbal_$Stamp.transcript.log"
Start-Transcript -Path $TranscriptPath -Force | Out-Null

try {
  $env:PYTHONPATH = "$Root;$Root\_archive\external\sotopia;$Root\_archive\external\concordia"
  $env:LLM_HPGG_BACKEND = "cloudgpt"
  $modelMap = @{
    deepseek       = "DeepSeek-V3.2"
    gpt5_nano      = "gpt-5.4-nano-20260317"
    kimi_k2        = "Kimi-K2.6"
    llama_maverick = "Llama-4-Maverick-17B-128E-Instruct-FP8"
  }

  Write-Host "=== Concordia Pub Coordination london_mini s5 ==="
  foreach ($tier in $modelMap.Keys) {
    $model = $modelMap[$tier]
    $out = "analysis\llm_psrl_verbal\concordia_pub_london_mini_${tier}_llmpsrl_s5.json"
    if (Test-Path $out) {
      try { $json = Get-Content $out -Raw | ConvertFrom-Json; if ($json.summary) { Write-Host "SKIP existing $out"; continue } } catch {}
    }
    Write-Host "RUN $out"
    uv run python -m llm_hpgg_concordia.run_pub_coordination_compact `
      --config london_mini --model $model `
      --methods llm_psrl_verbal hpsmg_plus_joint_proxy oracle_joint `
      --seeds 5 --out $out
  }

  Write-Host "=== Concordia Haggling fruitville s30 ==="
  foreach ($tier in $modelMap.Keys) {
    $model = $modelMap[$tier]
    $out = "analysis\llm_psrl_verbal\concordia_haggling_fruitville_${tier}_llmpsrl_s30.json"
    if (Test-Path $out) {
      try { $json = Get-Content $out -Raw | ConvertFrom-Json; if ($json.summary) { Write-Host "SKIP existing $out"; continue } } catch {}
    }
    Write-Host "RUN $out"
    uv run python -m llm_hpgg_concordia.run_haggling_compact `
      --domain haggling --config fruitville --model $model `
      --methods llm_psrl_verbal hpsmg_plus_joint_proxy oracle_joint oracle_focal `
      --seeds 30 --out $out
  }

  Write-Host "=== SOTOPIA-Hard all70 llm_psrl_verbal ==="
  foreach ($tier in $modelMap.Keys) {
    $model = $modelMap[$tier]
    $out = "analysis\llm_psrl_verbal\sotopia_hard_${tier}_llm_psrl_verbal_all70.json"
    $skip = $false
    if (Test-Path $out) {
      try {
        $json = Get-Content $out -Raw | ConvertFrom-Json
        if ($json.complete -eq $true -and [int]$json.case_count -eq 70) { $skip = $true }
      } catch { $skip = $false }
    }
    if ($skip) { Write-Host "SKIP complete $out"; continue }
    Write-Host "RUN/RESUME $out"
    uv run python -m llm_hpgg_sotopia.run_sotopia_hard_official `
      --baseline llm-psrl-verbal --model $model --evaluator-model $model `
      --agent-strategy-profile sotopia_tuned --turns 6 --limit 70 `
      --concurrency 2 --resume `
      --benchmark-agents _archive\external\sotopia_data_probe\benchmark_agents.json `
      --episodes-jsonl _archive\external\sotopia_data_probe\sotopia_episodes_v1_hf.jsonl `
      --cache _archive\external\sotopia_data_probe\sotopia_hard_cases_cache.json `
      --out $out
  }

  Write-Host "=== Done cross-substrate llm_psrl_verbal ==="
} finally {
  Stop-Transcript | Out-Null
}