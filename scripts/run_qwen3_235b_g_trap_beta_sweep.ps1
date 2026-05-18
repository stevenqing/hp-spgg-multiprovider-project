param(
    [int]$Workers = 4,
    [int]$Samples = 1,
    [int]$CellBudget = 0,
    [int]$K = 50,
    [int]$Seeds = 8
)

$ErrorActionPreference = "Stop"

if (-not $env:DEEPINFRA_API_KEY) {
    throw "DEEPINFRA_API_KEY is not set. Set it before running the Qwen3-235B live calibration."
}

$model = "Qwen/Qwen3-235B-A22B"
$slug = "qwen3_235b_a22b"
$calibration = "calibration_${slug}_trap_live.npy"
$report = "analysis\${slug}_g_trap_live_calibration_report.json"
$cache = "logs\${slug}_g_trap_live_calibration_cache.jsonl"
$resultDir = "results\qwen3_235b"
$csvOut = "analysis\g_trap_beta_sweep_qwen3_235b_hpsmg_plus.csv"
$mdOut = "analysis\g_trap_beta_sweep_qwen3_235b.md"

New-Item -ItemType Directory -Force -Path "analysis", "logs", $resultDir | Out-Null

$env:LLM_HPGG_BACKEND = "qwen3"
$env:LLM_HPGG_PLAYER_MODEL = $model
$env:LLM_HPGG_JUDGE_MODEL = $model
$env:GTRAP_SWEEP_K = [string]$K
$env:GTRAP_SWEEP_SEEDS = [string]$Seeds

uv run python -m llm_hpgg.calibration_live `
    --backend qwen3 `
    --judge-model $model `
    --trap `
    --n 3 `
    --samples $Samples `
    --max-profiles 0 `
    --cell-budget $CellBudget `
    --workers $Workers `
    --out $calibration `
    --report $report `
    --cache $cache `
    --save-every 24

$betas = @("0", "0.3", "1", "3", "10")
foreach ($beta in $betas) {
    $betaSlug = $beta.Replace(".", "p")
    uv run python -m llm_hpgg.run_experiment `
        --K $K `
        --n 3 `
        --seeds $Seeds `
        --beta $beta `
        --algos hpsmg_plus hpsmg oracle `
        --calibration $calibration `
        --out "${resultDir}\G_trap_beta${betaSlug}_K${K}_s${Seeds}.npz" `
        --player-model $model `
        --judge-model $model
}

$py = @'
import csv
import json
import os
from pathlib import Path

import numpy as np

model = "Qwen/Qwen3-235B-A22B"
provider = "qwen3_235b"
rounds = int(os.environ["GTRAP_SWEEP_K"])
seed_count = int(os.environ["GTRAP_SWEEP_SEEDS"])
betas = [("0", "0"), ("0.3", "0p3"), ("1", "1"), ("3", "3"), ("10", "10")]
result_dir = Path("results/qwen3_235b")
rows = []
summary = []
for beta, slug in betas:
    path = result_dir / f"G_trap_beta{slug}_K{rounds}_s{seed_count}.npz"
    data = np.load(path, allow_pickle=True)
    algorithms = [str(value) for value in data["algorithms"]]
    index = algorithms.index("hpsmg_plus")
    finals = np.asarray(data["cumulative_regret"], dtype=float)[index, :, -1]
    summary.append((beta, float(finals.mean()), float(finals.std(ddof=0)), finals, path.as_posix()))
    for seed, value in enumerate(finals):
        rows.append({
            "provider": provider,
            "model": model,
            "graph": "G_trap",
            "beta": beta,
            "algorithm": "hpsmg_plus",
            "seed": seed,
            "K": int(data["K"]),
            "final_cumulative_regret": f"{float(value):.8f}",
            "source": path.as_posix(),
        })

csv_path = Path("analysis/g_trap_beta_sweep_qwen3_235b_hpsmg_plus.csv")
with csv_path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

lines = [
    "# G_trap Beta Sweep: Qwen3-235B",
    "",
    f"Single model: `{model}`.",
    "",
    "Metric: final cumulative regret on `G_trap`; lower is better.",
    "",
    f"Configuration: `K={rounds}`, `seeds={seed_count}`, beta grid `{{0, 0.3, 1, 3, 10}}`, algorithm `hpsmg_plus`.",
    "",
    "## Summary",
    "",
    "| beta | mean final regret | std | source |",
    "|---:|---:|---:|---|",
]
for beta, mean, std, finals, source in summary:
    lines.append(f"| {beta} | {mean:.4f} | {std:.4f} | `{source}` |")
lines.extend([
    "",
    "## Per-Seed Matrix",
    "",
    "| beta | seed0 | seed1 | seed2 | seed3 | seed4 | seed5 | seed6 | seed7 | mean | std |",
    "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
])
for beta, mean, std, finals, source in summary:
    lines.append("| " + beta + " | " + " | ".join(f"{value:.4f}" for value in finals) + f" | {mean:.4f} | {std:.4f} |")
Path("analysis/g_trap_beta_sweep_qwen3_235b.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(csv_path)
print("analysis/g_trap_beta_sweep_qwen3_235b.md")
'@
uv run python -c $py

$bundle = "packaged_results\hp_spgg_results_bundle_20260517"
if (Test-Path $bundle) {
    New-Item -ItemType Directory -Force -Path (Join-Path $bundle "results\qwen3_235b") | Out-Null
    Copy-Item $calibration (Join-Path $bundle $calibration) -Force
    Copy-Item $report (Join-Path $bundle "analysis\$(Split-Path $report -Leaf)") -Force
    Copy-Item $csvOut (Join-Path $bundle "analysis\$(Split-Path $csvOut -Leaf)") -Force
    Copy-Item $mdOut (Join-Path $bundle "analysis\$(Split-Path $mdOut -Leaf)") -Force
    Copy-Item "$resultDir\G_trap_beta*_K${K}_s${Seeds}.npz" (Join-Path $bundle "results\qwen3_235b") -Force
    Get-ChildItem $bundle -Recurse -File | ForEach-Object { $_.FullName.Substring((Resolve-Path $bundle).Path.Length + 1) } | Sort-Object | Set-Content -Path (Join-Path $bundle "FILELIST.txt") -Encoding UTF8
}