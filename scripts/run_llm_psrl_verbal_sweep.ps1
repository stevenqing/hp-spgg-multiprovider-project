$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
New-Item -ItemType Directory -Force logs, analysis\llm_psrl_verbal | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$TranscriptPath = Join-Path $Root "logs\llm_psrl_verbal_sweep_$Stamp.transcript.log"
Start-Transcript -Path $TranscriptPath -Force | Out-Null

try {
  $env:PYTHONPATH = $Root
  $env:LLM_HPGG_BACKEND = "cloudgpt"
  $modelMap = @{
    deepseek       = "DeepSeek-V3.2"
    gpt5_nano      = "gpt-5.4-nano-20260317"
    kimi_k2        = "Kimi-K2.6"
    llama_maverick = "Llama-4-Maverick-17B-128E-Instruct-FP8"
  }
  foreach ($tier in "deepseek", "gpt5_nano", "kimi_k2", "llama_maverick") {
    foreach ($n in 3, 4, 5, 6) {
      $model = $modelMap[$tier]
      $env:LLM_PSRL_VERBAL_MODEL = $model
      $cal = "results_phase2\e1_1_llm_tier\calibration_live_n${n}_${tier}.npy"
      $out = "analysis\llm_psrl_verbal\E_llmpsrl_n${n}_K20_${tier}.npz"
      if (Test-Path $out) {
        Write-Host "SKIP existing $out"
        continue
      }
      Write-Host "RUN $tier n=$n model=$model -> $out"
      uv run python -m llm_hpgg.run_experiment `
        --K 20 --n $n --seeds 5 --beta 0.25 `
        --algos hpsmg hpsmg_plus llm_psrl_verbal `
        --calibration $cal --out $out --matched-seeds `
        --verbal-model $model
      uv run python scripts\summarize_llm_psrl_verbal.py
    }
  }
  uv run python scripts\summarize_llm_psrl_verbal.py
  Write-Host "=== Done llm_psrl_verbal sweep ==="
} finally {
  Stop-Transcript | Out-Null
}