$ErrorActionPreference = 'Stop'

$algorithms = @('atom_tom0', 'atom_tom1', 'atom_tom2', 'atom_adaptive_ftl', 'atom_adaptive_hedge', 'econ_bne')
$models = @(
    @{ Slug = 'gpt_5_4_nano_20260317'; Prompted = 'results\cloudgpt\E2_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz'; External = 'results\cloudgpt\E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz'; ExternalTrace = 'analysis\E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5_trace.json'; ExternalSummary = 'analysis\E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5_summary.md' },
    @{ Slug = 'Kimi_K2_6'; Prompted = 'results\cloudgpt\E2_llm_baselines_Kimi_K2_6_c19_K20_s5.npz'; External = 'results\cloudgpt\E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz'; ExternalTrace = 'analysis\E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5_trace.json'; ExternalSummary = 'analysis\E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5_summary.md' },
    @{ Slug = 'Llama_4_Maverick_17B_128E_Instruct_FP8'; Prompted = 'results\cloudgpt\E2_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz'; External = 'results\cloudgpt\E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz'; ExternalTrace = 'analysis\E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5_trace.json'; ExternalSummary = 'analysis\E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5_summary.md' }
)

function Get-RequiredPaths {
    $paths = @()
    foreach ($model in $models) {
        $paths += $model.Prompted
        foreach ($algorithm in $algorithms) {
            $paths += "results\cloudgpt\shards\E2_external_$($model.Slug)_c19_K20_s5_$algorithm.npz"
            $paths += "analysis\shards\E2_external_$($model.Slug)_c19_K20_s5_${algorithm}_trace.json"
        }
    }
    return $paths
}

function Write-ProgressLine {
    $promptedDone = ($models | Where-Object { Test-Path $_.Prompted } | Measure-Object).Count
    $shardDone = 0
    foreach ($model in $models) {
        foreach ($algorithm in $algorithms) {
            if (Test-Path "results\cloudgpt\shards\E2_external_$($model.Slug)_c19_K20_s5_$algorithm.npz") {
                $shardDone += 1
            }
        }
    }
    Write-Host "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))] postprocess_wait prompted=$promptedDone/3 external_shards=$shardDone/18"
}

$requiredPaths = Get-RequiredPaths
Write-ProgressLine
while (($requiredPaths | Where-Object { -not (Test-Path $_) } | Measure-Object).Count -gt 0) {
    $event = Wait-Event -Timeout 60
    if ($event) { Remove-Event -EventIdentifier $event.EventIdentifier }
    Write-ProgressLine
}

foreach ($model in $models) {
    $mergeArgs = @('scripts\merge_external_llm_shards.py')
    foreach ($algorithm in $algorithms) {
        $mergeArgs += '--shard'
        $mergeArgs += "results\cloudgpt\shards\E2_external_$($model.Slug)_c19_K20_s5_$algorithm.npz"
    }
    foreach ($algorithm in $algorithms) {
        $mergeArgs += '--shard-trace'
        $mergeArgs += "analysis\shards\E2_external_$($model.Slug)_c19_K20_s5_${algorithm}_trace.json"
    }
    $mergeArgs += '--algorithms'
    $mergeArgs += $algorithms
    $mergeArgs += '--seeds'
    $mergeArgs += '5'
    $mergeArgs += '--out'
    $mergeArgs += $model.External
    $mergeArgs += '--trace-out'
    $mergeArgs += $model.ExternalTrace
    uv run python @mergeArgs
    uv run python scripts\summarize_external_llm_baselines.py $model.External --out $model.ExternalSummary
}

uv run python -c "import numpy as np; from pathlib import Path; files=[('gpt_5_4_nano_20260317', r'results\cloudgpt\E2_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz'), ('Kimi_K2_6', r'results\cloudgpt\E2_llm_baselines_Kimi_K2_6_c19_K20_s5.npz'), ('Llama_4_Maverick_17B_128E_Instruct_FP8', r'results\cloudgpt\E2_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz')]; print('PROMPTED_FINALS'); [print(slug, [str(x) for x in np.load(path, allow_pickle=True)['algorithms']], np.round(np.load(path, allow_pickle=True)['cumulative_regret'][:,:,-1].mean(axis=1),4).tolist()) for slug,path in files]; files=[('gpt_5_4_nano_20260317', r'results\cloudgpt\E2_external_llm_baselines_gpt_5_4_nano_20260317_c19_K20_s5.npz'), ('Kimi_K2_6', r'results\cloudgpt\E2_external_llm_baselines_Kimi_K2_6_c19_K20_s5.npz'), ('Llama_4_Maverick_17B_128E_Instruct_FP8', r'results\cloudgpt\E2_external_llm_baselines_Llama_4_Maverick_17B_128E_Instruct_FP8_c19_K20_s5.npz')]; print('EXTERNAL_FINALS'); [print(slug, [str(x) for x in np.load(path, allow_pickle=True)['algorithms']], np.round(np.load(path, allow_pickle=True)['cumulative_regret'][:,:,-1].mean(axis=1),4).tolist()) for slug,path in files]"

Write-Host 'POSTPROCESS_DONE'