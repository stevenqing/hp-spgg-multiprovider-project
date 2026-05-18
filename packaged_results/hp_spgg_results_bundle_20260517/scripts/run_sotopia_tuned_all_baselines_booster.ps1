param(
    [int]$Turns = 6,
    [int]$Limit = 0,
    [int]$MaxActiveJobs = 4,
    [int]$MaxAttempts = 8,
    [string]$LogPath = 'logs\sotopia_tuned_all_baselines_booster.log'
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true

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
        return ($json.complete -eq $true -and $json.case_count -eq $json.target_case_count)
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
        $caseCount = if ($null -ne $json.case_count) { $json.case_count } else { 'n/a' }
        $targetCount = if ($null -ne $json.target_case_count) { $json.target_case_count } else { 'n/a' }
        $mean = if ($null -ne $json.summary.mean_overall) { $json.summary.mean_overall } else { 'n/a' }
        return ("{0}/{1} complete={2} mean={3}" -f $caseCount, $targetCount, $json.complete, $mean)
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

function Get-ActiveOutPaths {
    $processes = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like '*run_sotopia_hard_official*' -and $_.CommandLine -like '*sotopia_tuned_all70.json*'
    })
    $paths = New-Object System.Collections.Generic.HashSet[string]
    foreach ($proc in $processes) {
        if ($proc.CommandLine -match '--out\s+([^\s]+sotopia_tuned_all70\.json)') {
            [void]$paths.Add(($Matches[1] -replace '/', '\'))
        }
    }
    return @($paths)
}

function Test-OutPathActive {
    param([string]$OutPath, [string[]]$ActiveOutPaths)
    $normalized = $OutPath -replace '/', '\'
    foreach ($activePath in $ActiveOutPaths) {
        if ($activePath.EndsWith($normalized) -or $normalized.EndsWith($activePath)) { return $true }
    }
    return $false
}

$env:SOTOPIA_STORAGE_BACKEND = 'local'
$env:LLM_HPGG_BACKEND = 'cloudgpt'
$env:LLM_HPGG_PLAYER_BACKEND = 'cloudgpt'
$env:LLM_HPGG_JUDGE_BACKEND = 'cloudgpt'
$env:CLOUDGPT_USE_AZURE_CLI = '1'
$env:CLOUDGPT_TIMEOUT = '180'
$env:CLOUDGPT_MAX_RETRIES = '2'
$env:LLM_HPGG_OFFLINE = '0'
$env:SOTOPIA_AGENT_STRATEGY_PROFILE = 'sotopia_tuned'

New-Item -ItemType Directory -Force -Path 'analysis', 'logs', (Split-Path $LogPath) | Out-Null

$models = @(
    'DeepSeek-V3.2',
    'gpt-5.4-nano-20260317',
    'Kimi-K2.6',
    'Llama-4-Maverick-17B-128E-Instruct-FP8'
)
$baselines = @('hpsmg_plus', 'llm_belief', 'llm_greedy', 'atom_tom1', 'econ_bne')

$jobs = New-Object System.Collections.Generic.List[object]
foreach ($model in $models) {
    $slug = Get-ModelSlug -Model $model
    foreach ($baseline in $baselines) {
        $jobs.Add([pscustomobject]@{
            Kind = 'all70'
            Name = "all70_${slug}_${baseline}_sotopia_tuned"
            Model = $model
            Slug = $slug
            Baseline = $baseline
            Out = "analysis\sotopia_hard_official_${slug}_${baseline}_sotopia_tuned_all70.json"
            Stdout = "logs\sotopia_booster_${slug}_${baseline}_all70_stdout.log"
            Stderr = "logs\sotopia_booster_${slug}_${baseline}_all70_stderr.log"
            Attempts = 0
            Process = $null
            Done = $false
            Failed = $false
        })
    }
}

Write-QueueLog ("booster_start max_active_jobs={0} jobs={1}" -f $MaxActiveJobs, $jobs.Count)

while ($true) {
    $activeOutPaths = @(Get-ActiveOutPaths)

    foreach ($job in $jobs) {
        if ($job.Done -or $job.Failed) { continue }
        if (Test-CompleteResult -Path $job.Out) {
            $job.Done = $true
            $job.Process = $null
            Write-QueueLog ("complete kind={0} name={1} model={2} baseline={3} checkpoint={4}" -f $job.Kind, $job.Name, $job.Model, $job.Baseline, (Get-CheckpointText -Job $job))
            continue
        }
        if ($null -ne $job.Process) {
            try { $job.Process.Refresh() } catch {}
            if ($job.Process.HasExited) {
                Write-QueueLog ("exited_incomplete kind={0} name={1} model={2} baseline={3} exit={4} attempt={5} checkpoint={6}" -f $job.Kind, $job.Name, $job.Model, $job.Baseline, $job.Process.ExitCode, $job.Attempts, (Get-CheckpointText -Job $job))
                $job.Process = $null
            }
        }
    }

    $managedActive = @($jobs | Where-Object { (-not $_.Done) -and (-not $_.Failed) -and ($null -ne $_.Process) }).Count
    $externalActive = @($jobs | Where-Object { (-not $_.Done) -and (-not $_.Failed) -and ($null -eq $_.Process) -and (Test-OutPathActive -OutPath $_.Out -ActiveOutPaths $activeOutPaths) }).Count
    $activeTotal = $managedActive + $externalActive

    while ($activeTotal -lt $MaxActiveJobs) {
        $activeOutPaths = @(Get-ActiveOutPaths)
        $next = $jobs | Where-Object {
            (-not $_.Done) -and (-not $_.Failed) -and ($null -eq $_.Process) -and (-not (Test-OutPathActive -OutPath $_.Out -ActiveOutPaths $activeOutPaths))
        } | Select-Object -First 1
        if ($null -eq $next) { break }
        if ($next.Attempts -ge $MaxAttempts) {
            $next.Failed = $true
            Write-QueueLog ("failed_max_attempts kind={0} name={1} model={2} baseline={3} checkpoint={4}" -f $next.Kind, $next.Name, $next.Model, $next.Baseline, (Get-CheckpointText -Job $next))
            continue
        }

        $args = @(
            '-u', '-m', 'llm_hpgg_sotopia.run_sotopia_hard_official',
            '--baseline', $next.Baseline,
            '--model', $next.Model,
            '--evaluator-model', $next.Model,
            '--agent-strategy-profile', 'sotopia_tuned',
            '--turns', [string]$Turns,
            '--limit', [string]$Limit,
            '--resume',
            '--out', $next.Out
        )

        $next.Attempts += 1
        $next.Process = Start-Process -FilePath '.venvs\sotopia-py312\Scripts\python.exe' -ArgumentList $args -RedirectStandardOutput $next.Stdout -RedirectStandardError $next.Stderr -PassThru -WindowStyle Hidden
        Write-QueueLog ("started kind={0} name={1} model={2} baseline={3} pid={4} attempt={5} out={6}" -f $next.Kind, $next.Name, $next.Model, $next.Baseline, $next.Process.Id, $next.Attempts, $next.Out)
        $activeTotal += 1
    }

    $doneCount = @($jobs | Where-Object { $_.Done }).Count
    $failedCount = @($jobs | Where-Object { $_.Failed }).Count
    $managedActive = @($jobs | Where-Object { (-not $_.Done) -and (-not $_.Failed) -and ($null -ne $_.Process) }).Count
    $activeOutPaths = @(Get-ActiveOutPaths)
    $externalActive = @($jobs | Where-Object { (-not $_.Done) -and (-not $_.Failed) -and ($null -eq $_.Process) -and (Test-OutPathActive -OutPath $_.Out -ActiveOutPaths $activeOutPaths) }).Count
    Write-QueueLog ("snapshot done={0}/{1} failed={2} managed_active={3} external_active_jobs={4} max_active_jobs={5}" -f $doneCount, $jobs.Count, $failedCount, $managedActive, $externalActive, $MaxActiveJobs)

    if ($doneCount -eq $jobs.Count) {
        Write-QueueLog 'booster_complete all jobs done'
        exit 0
    }
    if (($managedActive + $externalActive -eq 0) -and (($doneCount + $failedCount) -eq $jobs.Count)) {
        Write-QueueLog 'booster_finished_with_failures'
        exit 1
    }

    $event = Wait-Event -Timeout 30
    if ($event) { Remove-Event -EventIdentifier $event.EventIdentifier }
}