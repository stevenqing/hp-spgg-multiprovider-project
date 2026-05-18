param(
    [string[]]$Backends = @("anthropic", "openai", "google", "qwen3"),
    [switch]$SkipE2,
    [switch]$SkipE3,
    [switch]$SkipE4,
    [switch]$SkipAudit
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

New-Item -ItemType Directory -Force -Path logs, analysis, figs, tables | Out-Null

foreach ($backend in $Backends) {
    New-Item -ItemType Directory -Force -Path "results/$backend" | Out-Null
    $env:LLM_HPGG_BACKEND = $backend

    Write-Host "[E1] calibration: $backend"
    uv run python calibration.py --backend $backend --out "calibration_$backend.npy" 2>&1 | Tee-Object -FilePath "logs/E1_$backend.log"

    if (-not $SkipAudit) {
        Write-Host "[E5] persona audit: $backend"
        uv run python audit_personas.py --backend $backend --out "logs/E5_audit_$backend.txt" 2>&1 | Tee-Object -FilePath "logs/E5_$backend.log"
    }

    if (-not $SkipE2) {
        Write-Host "[E2] sanity: $backend"
        uv run python run_experiment.py --K 10 --n 3 --seeds 2 --beta 1.0 `
            --algos hpsmg_plus hpsmg oracle random `
            --calibration "calibration_$backend.npy" `
            --out "results/$backend/E2_sanity.npz" 2>&1 | Tee-Object -FilePath "logs/E2_$backend.log"
    }

    if (-not $SkipE3) {
        Write-Host "[E3] main: $backend"
        uv run python run_experiment.py --K 30 --n 3 --seeds 5 --beta 1.0 `
            --algos hpsmg_plus hpsmg joint_psrl map_greedy psrl_notype iql_independent_actions iql random oracle `
            --calibration "calibration_$backend.npy" `
            --out "results/$backend/E3_main.npz" 2>&1 | Tee-Object -FilePath "logs/E3_$backend.log"
    }

    if (-not $SkipE4) {
        Write-Host "[E4] trap calibration: $backend"
        uv run python build_trap_calibration.py --in "calibration_$backend.npy" --out "calibration_${backend}_trap.npy" 2>&1 | Tee-Object -FilePath "logs/E4_trap_calibration_$backend.log"

        Write-Host "[E4] trap experiment: $backend"
        uv run python run_experiment.py --K 50 --n 3 --seeds 8 --beta 1.0 `
            --algos hpsmg_plus hpsmg oracle `
            --calibration "calibration_${backend}_trap.npy" `
            --out "results/$backend/E4_trap.npz" 2>&1 | Tee-Object -FilePath "logs/E4_$backend.log"
    }
}

if (-not $SkipE3) {
    Write-Host "[plot] E3"
    uv run python plot_results.py --inputs results/*/E3_main.npz --output figs/E3_cross_provider.pdf --summary analysis/E3_summary.json --table tables/E3_cross_provider_regret.tex
}

if (-not $SkipE4) {
    Write-Host "[plot] E4"
    uv run python plot_results.py --inputs results/*/E4_trap.npz --output figs/E4_burn_in_cross.pdf --summary analysis/E4_summary.json --table tables/E4_burn_in.tex
}

Write-Host "benchmark complete"
