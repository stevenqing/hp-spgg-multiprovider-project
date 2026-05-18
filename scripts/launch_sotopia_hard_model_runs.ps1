param(
    [string[]]$Models = @('gpt-5.4-nano-20260317', 'Kimi-K2.6', 'Llama-4-Maverick-17B-128E-Instruct-FP8'),
    [string[]]$Baselines = @('hpsmg_plus', 'llm_belief', 'llm_greedy', 'atom_tom1', 'econ_bne'),
    [int]$Turns = 6,
    [int]$Limit = 0
)

$ErrorActionPreference = 'Stop'

function Get-ModelSlug {
    param([string]$Model)
    switch ($Model) {
        'DeepSeek-V3.2' { return 'DeepSeek_V3_2' }
        'gpt-5.4-nano-20260317' { return 'gpt_5_4_nano_20260317' }
        'Kimi-K2.6' { return 'Kimi_K2_6' }
        'Llama-4-Maverick-17B-128E-Instruct-FP8' { return 'Llama_4_Maverick_17B_128E_Instruct_FP8' }
        default { return ($Model -replace '[^A-Za-z0-9]+', '_').Trim('_') }
    }
}

$env:SOTOPIA_STORAGE_BACKEND = 'local'
$env:LLM_HPGG_BACKEND = 'cloudgpt'
$env:LLM_HPGG_PLAYER_BACKEND = 'cloudgpt'
$env:LLM_HPGG_JUDGE_BACKEND = 'cloudgpt'
$env:CLOUDGPT_USE_AZURE_CLI = '1'
$env:CLOUDGPT_TIMEOUT = '120'
$env:CLOUDGPT_MAX_RETRIES = '0'
$env:LLM_HPGG_OFFLINE = '0'

New-Item -ItemType Directory -Force -Path 'analysis', 'logs' | Out-Null

foreach ($model in $Models) {
    $slug = Get-ModelSlug -Model $model
    foreach ($baseline in $Baselines) {
        $out = "analysis\sotopia_hard_official_${slug}_${baseline}_all70.json"
        if (Test-Path $out) {
            try {
                $existing = Get-Content $out -Raw | ConvertFrom-Json
                if ($existing.complete -eq $true) {
                    Write-Host "skip_complete model=$model baseline=$baseline out=$out"
                    continue
                }
            }
            catch {
                Write-Host "resume_unreadable model=$model baseline=$baseline out=$out"
            }
        }

        $running = [bool](Get-CimInstance Win32_Process | Where-Object {
            $_.CommandLine -like "*run_sotopia_hard_official*--baseline $baseline*--model $model*" -or
            ($_.CommandLine -like "*run_sotopia_hard_official*--baseline $baseline*" -and $_.CommandLine -like "*--out $out*")
        })
        if ($running) {
            Write-Host "already_running model=$model baseline=$baseline out=$out"
            continue
        }

        $stdout = "logs\sotopia_hard_official_${slug}_${baseline}_all70_stdout.log"
        $stderr = "logs\sotopia_hard_official_${slug}_${baseline}_all70_stderr.log"
        $args = @(
            '-u', '-m', 'llm_hpgg_sotopia.run_sotopia_hard_official',
            '--baseline', $baseline,
            '--model', $model,
            '--evaluator-model', $model,
            '--turns', [string]$Turns,
            '--limit', [string]$Limit,
            '--resume',
            '--out', $out
        )
        $process = Start-Process -FilePath '.venvs\sotopia-py312\Scripts\python.exe' -ArgumentList $args -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
        Write-Host ("started model={0} slug={1} baseline={2} pid={3} out={4}" -f $model, $slug, $baseline, $process.Id, $out)
    }
}