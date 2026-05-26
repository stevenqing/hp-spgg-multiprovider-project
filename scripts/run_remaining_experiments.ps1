$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

New-Item -ItemType Directory -Force logs, analysis\joint_psrl_aware, analysis\true_shared_type, analysis\sotopia_intent_ablation | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$TranscriptPath = Join-Path $Root "logs\remaining_experiments_$Stamp.transcript.log"
Start-Transcript -Path $TranscriptPath -Force | Out-Null

try {
  $env:PYTHONPATH = "$Root;$Root\_archive\external\sotopia"
  $env:LLM_HPGG_BACKEND = "cloudgpt"

  $tiers = @("gpt5_nano", "kimi_k2", "llama_maverick")
  $ns = @(3, 4, 5)
  $Ks = @(50, 100)

  Write-Host "=== Phase 3.1: Joint-PSRL-Uniform/Aware extra backbones ==="
  foreach ($tier in $tiers) {
    foreach ($n in $ns) {
      foreach ($K in $Ks) {
        $cal = "results_phase2\e1_1_llm_tier\calibration_live_n${n}_${tier}.npy"
        $out = "analysis\joint_psrl_aware\E1_jointaware_n${n}_K${K}_${tier}_shared_type.npz"
        if (Test-Path $out) {
          Write-Host "SKIP existing $out"
          continue
        }
        Write-Host "RUN $out"
        uv run python -m llm_hpgg.run_experiment `
          --K $K --n $n --seeds 10 --beta 0.25 `
          --algos hpsmg joint_psrl_uniform joint_psrl_aware `
          --calibration $cal --out $out --matched-seeds `
          --prior-mode shared_type
      }
    }
  }
  uv run python scripts\summarize_joint_psrl_aware.py

  Write-Host "=== Phase 3.2: True shared-type DGP extra backbones ==="
  foreach ($tier in $tiers) {
    foreach ($n in $ns) {
      foreach ($K in $Ks) {
        $cal = "results_phase2\e1_1_llm_tier\calibration_live_n${n}_${tier}.npy"
        $out = "analysis\true_shared_type\E1_truesharedtype_n${n}_K${K}_${tier}_shared_type.npz"
        if (Test-Path $out) {
          Write-Host "SKIP existing $out"
          continue
        }
        Write-Host "RUN $out"
        uv run python -m llm_hpgg.run_experiment `
          --K $K --n $n --seeds 10 --beta 0.25 `
          --algos hpsmg joint_psrl_uniform joint_psrl_aware `
          --calibration $cal --out $out --matched-seeds `
          --prior-mode shared_type --true-type-mode shared_type
      }
    }
  }
  uv run python scripts\summarize_true_shared_type.py

  Write-Host "=== Phase 4.1: SOTOPIA donate_funds ablation ==="
  $cases = @(5, 6, 7, 8, 9)
  $jobs = @(
    @{slug="deepseek"; model="DeepSeek-V3.2"},
    @{slug="llama_maverick"; model="Llama-4-Maverick-17B-128E-Instruct-FP8"}
  )
  $variants = @("surrogate-only", "naive-belief", "hpsmg_plus")
  foreach ($job in $jobs) {
    foreach ($variant in $variants) {
      $slug = $job["slug"]
      $model = $job["model"]
      $variantSlug = $variant.Replace("-", "_")
      $out = "analysis\sotopia_intent_ablation\sotopia_intent_${slug}_${variantSlug}_donate_funds_s5.json"
      $skip = $false
      if (Test-Path $out) {
        try {
          $json = Get-Content $out -Raw | ConvertFrom-Json
          if ($json.complete -eq $true -and [int]$json.case_count -eq 5) { $skip = $true }
        } catch { $skip = $false }
      }
      if ($skip) {
        Write-Host "SKIP complete $out"
        continue
      }
      Write-Host "RUN/RESUME $out"
      uv run python -m llm_hpgg_sotopia.run_sotopia_hard_official `
        --baseline $variant --model $model --evaluator-model $model `
        --agent-strategy-profile sotopia_tuned --turns 6 --limit 0 `
        --case-indices $cases --concurrency 3 --resume `
        --benchmark-agents _archive\external\sotopia_data_probe\benchmark_agents.json `
        --episodes-jsonl _archive\external\sotopia_data_probe\sotopia_episodes_v1_hf.jsonl `
        --cache _archive\external\sotopia_data_probe\sotopia_hard_cases_cache.json `
        --out $out
    }
  }

  Write-Host "=== Phase 4.1: refresh SOTOPIA partial trajectories ==="
  uv run python scripts\run_sotopia_intent_partial_judge.py --concurrency 6

  Write-Host "=== Done remaining experiments ==="
} finally {
  Stop-Transcript | Out-Null
}