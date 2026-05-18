param(
    [string[]]$Models = @('gpt-5.4-nano-20260317', 'Kimi-K2.6', 'Llama-4-Maverick-17B-128E-Instruct-FP8'),
    [string[]]$Baselines = @('hpsmg_plus', 'llm_belief', 'llm_greedy', 'atom_tom1', 'econ_bne'),
    [int]$Turns = 6,
    [int]$Limit = 0,
    [int]$MaxConcurrent = 3,
    [int]$MaxAttempts = 20,
    [string]$LogPath = 'logs\sotopia_hard_official_model_queue.log'
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

function Test-CompleteResult {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $false }
    try {
        $json = Get-Content $Path -Raw | ConvertFrom-Json
        return ($json.complete -eq $true)
    }
    catch {
        return $false
    }
}

function Get-CheckpointText {
    param([object]$Job)
    if (-not (Test-Path $Job.Out)) { return 'waiting_for_first_case' }
    try {
        $json = Get-Content $Job.Out -Raw | ConvertFrom-Json
        return ("{0}/{1} complete={2} mean={3}" -f $json.case_count, $json.target_case_count, $json.complete, $json.summary.mean_overall)
    }
    catch {
        return 'read_error'
    }
}

function Write-QueueLog {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'), $Message
    Add-Content -Path $LogPath -Value $line -Encoding UTF8
    Write-Host $line
}

$env:SOTOPIA_STORAGE_BACKEND = 'local'
$env:LLM_HPGG_BACKEND = 'cloudgpt'
$env:LLM_HPGG_PLAYER_BACKEND = 'cloudgpt'
$env:LLM_HPGG_JUDGE_BACKEND = 'cloudgpt'
$env:CLOUDGPT_USE_AZURE_CLI = '1'
$env:CLOUDGPT_TIMEOUT = '120'
$env:CLOUDGPT_MAX_RETRIES = '2'
$env:LLM_HPGG_OFFLINE = '0'

New-Item -ItemType Directory -Force -Path 'analysis', 'logs', (Split-Path $LogPath) | Out-Null

$jobs = New-Object System.Collections.Generic.List[object]
foreach ($model in $Models) {
    $slug = Get-ModelSlug -Model $model
    foreach ($baseline in $Baselines) {
        $jobs.Add([pscustomobject]@{
            Model = $model
            Slug = $slug
            Baseline = $baseline
            Out = "analysis\sotopia_hard_official_${slug}_${baseline}_all70.json"
            Stdout = "logs\sotopia_hard_official_${slug}_${baseline}_all70_stdout.log"
            Stderr = "logs\sotopia_hard_official_${slug}_${baseline}_all70_stderr.log"
            Attempts = 0
            Process = $null
            Done = $false
            Failed = $false
        })
    }
}

Write-QueueLog ("queue_start jobs={0} max_concurrent={1}" -f $jobs.Count, $MaxConcurrent)

while ($true) {
    foreach ($job in $jobs) {
        if ($job.Done -or $job.Failed) { continue }
        if (Test-CompleteResult -Path $job.Out) {
            $job.Done = $true
            $job.Process = $null
            Write-QueueLog ("complete model={0} baseline={1} checkpoint={2}" -f $job.Model, $job.Baseline, (Get-CheckpointText -Job $job))
            continue
        }
        if ($null -ne $job.Process) {
            try { $job.Process.Refresh() } catch {}
            if ($job.Process.HasExited) {
                Write-QueueLog ("exited_incomplete model={0} baseline={1} exit={2} attempt={3} checkpoint={4}" -f $job.Model, $job.Baseline, $job.Process.ExitCode, $job.Attempts, (Get-CheckpointText -Job $job))
                $job.Process = $null
            }
        }
    }

    $active = @($jobs | Where-Object { (-not $_.Done) -and (-not $_.Failed) -and ($null -ne $_.Process) }).Count
    while ($active -lt $MaxConcurrent) {
        $next = $jobs | Where-Object { (-not $_.Done) -and (-not $_.Failed) -and ($null -eq $_.Process) } | Select-Object -First 1
        if ($null -eq $next) { break }
        if ($next.Attempts -ge $MaxAttempts) {
            $next.Failed = $true
            Write-QueueLog ("failed_max_attempts model={0} baseline={1} checkpoint={2}" -f $next.Model, $next.Baseline, (Get-CheckpointText -Job $next))
            continue
        }
        $args = @(
            '-u', '-m', 'llm_hpgg_sotopia.run_sotopia_hard_official',
            '--baseline', $next.Baseline,
            '--model', $next.Model,
            '--evaluator-model', $next.Model,
            '--turns', [string]$Turns,
            '--limit', [string]$Limit,
            '--resume',
            '--out', $next.Out
        )
        $next.Attempts += 1
        $next.Process = Start-Process -FilePath '.venvs\sotopia-py312\Scripts\python.exe' -ArgumentList $args -RedirectStandardOutput $next.Stdout -RedirectStandardError $next.Stderr -PassThru -WindowStyle Hidden
        $active += 1
        Write-QueueLog ("started model={0} baseline={1} pid={2} attempt={3} checkpoint={4}" -f $next.Model, $next.Baseline, $next.Process.Id, $next.Attempts, (Get-CheckpointText -Job $next))
    }

    $doneCount = @($jobs | Where-Object { $_.Done }).Count
    $failedCount = @($jobs | Where-Object { $_.Failed }).Count
    $active = @($jobs | Where-Object { (-not $_.Done) -and (-not $_.Failed) -and ($null -ne $_.Process) }).Count
    Write-QueueLog ("snapshot done={0}/{1} failed={2} active={3}" -f $doneCount, $jobs.Count, $failedCount, $active)

    if ($doneCount -eq $jobs.Count) {
        Write-QueueLog 'queue_complete all jobs done'
        exit 0
    }
    if (($active -eq 0) -and (($doneCount + $failedCount) -eq $jobs.Count)) {
        Write-QueueLog 'queue_finished_with_failures'
        exit 1
    }

    $event = Wait-Event -Timeout 45
    if ($event) { Remove-Event -EventIdentifier $event.EventIdentifier }
}