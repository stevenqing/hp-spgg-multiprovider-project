$ErrorActionPreference = 'Stop'

$workspace = (Resolve-Path '.').Path
$env:LLM_HPGG_BACKEND = 'cloudgpt'
$env:CLOUDGPT_USE_AZURE_CLI = '1'
$env:CLOUDGPT_TIMEOUT = '90'
$env:EXTERNAL_LLM_CALL_RETRIES = '12'
$env:EXTERNAL_LLM_RETRY_BASE_SECONDS = '2'

$models = @(
    @{ Slug = 'gpt_5_4_nano_20260317'; Model = 'gpt-5.4-nano-20260317'; Calibration = 'calibration_cloudgpt_multi_model_fast4_8algos_gpt_5_4_nano_20260317_c19.npy' },
    @{ Slug = 'Kimi_K2_6'; Model = 'Kimi-K2.6'; Calibration = 'calibration_cloudgpt_multi_model_fast4_8algos_Kimi_K2_6_c19.npy' },
    @{ Slug = 'Llama_4_Maverick_17B_128E_Instruct_FP8'; Model = 'Llama-4-Maverick-17B-128E-Instruct-FP8'; Calibration = 'calibration_cloudgpt_multi_model_fast4_8algos_Llama_4_Maverick_17B_128E_Instruct_FP8_c19.npy' }
)

$algorithms = @('atom_tom0', 'atom_tom1', 'atom_tom2', 'atom_adaptive_ftl', 'atom_adaptive_hedge', 'econ_bne')
$jobs = @()

foreach ($model in $models) {
    foreach ($algorithm in $algorithms) {
        $out = "results\cloudgpt\shards\E2_external_$($model.Slug)_c19_K20_s5_$algorithm.npz"
        $trace = "analysis\shards\E2_external_$($model.Slug)_c19_K20_s5_${algorithm}_trace.json"
        $cache = "logs\external_llm_cache_$($model.Slug)_$algorithm.json"
        $jobs += Start-Job -Name "$($model.Slug)_$algorithm" -ScriptBlock {
            param($workspace, $algorithm, $calibration, $out, $trace, $cache, $modelName)
            Set-Location $workspace
            $env:LLM_HPGG_BACKEND = 'cloudgpt'
            $env:CLOUDGPT_USE_AZURE_CLI = '1'
            $env:CLOUDGPT_TIMEOUT = '90'
            $env:EXTERNAL_LLM_CALL_RETRIES = '12'
            $env:EXTERNAL_LLM_RETRY_BASE_SECONDS = '2'
            uv run python -m llm_hpgg.run_external_llm_baselines --K 20 --n 3 --seeds 5 --seed-indices 0 1 2 3 4 --algos $algorithm --calibration $calibration --out $out --trace-out $trace --cache $cache --model $modelName --econ-rounds 3
        } -ArgumentList $workspace, $algorithm, $model.Calibration, $out, $trace, $cache, $model.Model
        Write-Host "started $($model.Slug) $algorithm"
    }
}

while (($jobs | Where-Object { $_.State -in @('Running', 'NotStarted') }).Count -gt 0) {
    $done = (Get-ChildItem 'results\cloudgpt\shards\E2_external_*_c19_K20_s5_*.npz' -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike '_smoke*' } | Measure-Object).Count
    $running = ($jobs | Where-Object { $_.State -eq 'Running' }).Count
    $failed = ($jobs | Where-Object { $_.State -eq 'Failed' }).Count
    Write-Host "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))] solo_external_done=$done/18 running_jobs=$running failed_jobs=$failed"
    Wait-Job -Job $jobs -Any -Timeout 60 | Out-Null
}

foreach ($job in $jobs) {
    Write-Host "===== $($job.Name) $($job.State) ====="
    Receive-Job -Job $job
}

$finalDone = (Get-ChildItem 'results\cloudgpt\shards\E2_external_*_c19_K20_s5_*.npz' -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike '_smoke*' } | Measure-Object).Count
Write-Host "SOLO_EXTERNAL_DONE outputs=$finalDone/18"