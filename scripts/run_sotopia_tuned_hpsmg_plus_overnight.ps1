param(
    [int]$Turns = 6,
    [int]$Limit = 0,
    [int]$MaxConcurrent = 2,
    [int]$MaxTotalSotopiaProcesses = 4,
    [int]$MaxAttempts = 12,
    [string]$LogPath = 'logs\sotopia_tuned_hpsmg_plus_overnight.log'
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

function Get-ExternalSotopiaProcessCount {
    $currentPid = $PID
    $children = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
           $_.CommandLine -like '*\.venvs\sotopia-py312\Scripts\python.exe*run_sotopia_hard_official*' -and
        $_.ProcessId -ne $currentPid
    })
    return $children.Count
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
Write-QueueLog ("overnight_start max_concurrent={0} max_total_sotopia_processes={1}" -f $MaxConcurrent, $MaxTotalSotopiaProcesses)

$jobs = New-Object System.Collections.Generic.List[object]

$pilotJobs = @(
    @{ Model = 'gpt-5.4-nano-20260317'; CaseIndices = @('12'); Out = 'analysis\sotopia_tuned_pilot_gpt_5_4_nano_20260317_hpsmg_plus_case12.json'; Name = 'pilot_gpt_case12' },
    @{ Model = 'Kimi-K2.6'; CaseIndices = @('2'); Out = 'analysis\sotopia_tuned_pilot_Kimi_K2_6_hpsmg_plus_case2.json'; Name = 'pilot_kimi_case2' },
    @{ Model = 'Llama-4-Maverick-17B-128E-Instruct-FP8'; CaseIndices = @('48'); Out = 'analysis\sotopia_tuned_pilot_Llama_4_Maverick_17B_128E_Instruct_FP8_hpsmg_plus_case48.json'; Name = 'pilot_llama_case48' }
)

foreach ($pilot in $pilotJobs) {
    $slug = Get-ModelSlug -Model $pilot.Model
    $jobs.Add([pscustomobject]@{
        Kind = 'pilot'
        Name = $pilot.Name
        Model = $pilot.Model
        Slug = $slug
        Baseline = 'hpsmg_plus'
        CaseIndices = $pilot.CaseIndices
        Out = $pilot.Out
        Stdout = "logs\sotopia_tuned_$($pilot.Name)_stdout.log"
        Stderr = "logs\sotopia_tuned_$($pilot.Name)_stderr.log"
        Attempts = 0
        Process = $null
        Done = $false
        Failed = $false
    })
}

$models = @(
    'DeepSeek-V3.2',
    'gpt-5.4-nano-20260317',
    'Kimi-K2.6',
    'Llama-4-Maverick-17B-128E-Instruct-FP8'
)

foreach ($model in $models) {
    $slug = Get-ModelSlug -Model $model
    $jobs.Add([pscustomobject]@{
        Kind = 'all70'
        Name = "all70_$slug"
        Model = $model
        Slug = $slug
        Baseline = 'hpsmg_plus'
        CaseIndices = @()
        Out = "analysis\sotopia_hard_official_${slug}_hpsmg_plus_sotopia_tuned_all70.json"
        Stdout = "logs\sotopia_tuned_${slug}_hpsmg_plus_all70_stdout.log"
        Stderr = "logs\sotopia_tuned_${slug}_hpsmg_plus_all70_stderr.log"
        Attempts = 0
        Process = $null
        Done = $false
        Failed = $false
    })
}

Write-QueueLog ("jobs_prepared count={0}" -f $jobs.Count)

while ($true) {
    foreach ($job in $jobs) {
        if ($job.Done -or $job.Failed) { continue }
        if (Test-CompleteResult -Path $job.Out) {
            $job.Done = $true
            $job.Process = $null
            Write-QueueLog ("complete kind={0} name={1} model={2} checkpoint={3}" -f $job.Kind, $job.Name, $job.Model, (Get-CheckpointText -Job $job))
            continue
        }
        if ($null -ne $job.Process) {
            try { $job.Process.Refresh() } catch {}
            if ($job.Process.HasExited) {
                Write-QueueLog ("exited_incomplete kind={0} name={1} model={2} exit={3} attempt={4} checkpoint={5}" -f $job.Kind, $job.Name, $job.Model, $job.Process.ExitCode, $job.Attempts, (Get-CheckpointText -Job $job))
                $job.Process = $null
            }
        }
    }

    $active = @($jobs | Where-Object { (-not $_.Done) -and (-not $_.Failed) -and ($null -ne $_.Process) }).Count
    while ($active -lt $MaxConcurrent) {
        $externalActive = Get-ExternalSotopiaProcessCount
        if (($externalActive + $active) -ge $MaxTotalSotopiaProcesses) {
            Write-QueueLog ("throttle external_active={0} tuned_active={1} max_total={2}" -f $externalActive, $active, $MaxTotalSotopiaProcesses)
            break
        }

        $next = $jobs | Where-Object { (-not $_.Done) -and (-not $_.Failed) -and ($null -eq $_.Process) } | Select-Object -First 1
        if ($null -eq $next) { break }
        if ($next.Attempts -ge $MaxAttempts) {
            $next.Failed = $true
            Write-QueueLog ("failed_max_attempts kind={0} name={1} model={2} checkpoint={3}" -f $next.Kind, $next.Name, $next.Model, (Get-CheckpointText -Job $next))
            continue
        }

        $args = @(
            '-u', '-m', 'llm_hpgg_sotopia.run_sotopia_hard_official',
            '--baseline', $next.Baseline,
            '--model', $next.Model,
            '--evaluator-model', $next.Model,
            '--agent-strategy-profile', 'sotopia_tuned',
            '--turns', [string]$Turns,
            '--out', $next.Out
        )
        if ($next.Kind -eq 'all70') {
            $args += @('--limit', [string]$Limit, '--resume')
        }
        if ($next.CaseIndices.Count -gt 0) {
            $args += @('--case-indices')
            $args += $next.CaseIndices
        }

        $next.Attempts += 1
        $next.Process = Start-Process -FilePath '.venvs\sotopia-py312\Scripts\python.exe' -ArgumentList $args -RedirectStandardOutput $next.Stdout -RedirectStandardError $next.Stderr -PassThru -WindowStyle Hidden
        $active += 1
        Write-QueueLog ("started kind={0} name={1} model={2} pid={3} attempt={4} out={5}" -f $next.Kind, $next.Name, $next.Model, $next.Process.Id, $next.Attempts, $next.Out)
    }

    $doneCount = @($jobs | Where-Object { $_.Done }).Count
    $failedCount = @($jobs | Where-Object { $_.Failed }).Count
    $active = @($jobs | Where-Object { (-not $_.Done) -and (-not $_.Failed) -and ($null -ne $_.Process) }).Count
    Write-QueueLog ("snapshot done={0}/{1} failed={2} tuned_active={3} external_active={4}" -f $doneCount, $jobs.Count, $failedCount, $active, (Get-ExternalSotopiaProcessCount))

    if ($doneCount -eq $jobs.Count) {
        Write-QueueLog 'overnight_complete all jobs done'
        exit 0
    }
    if (($active -eq 0) -and (($doneCount + $failedCount) -eq $jobs.Count)) {
        Write-QueueLog 'overnight_finished_with_failures'
        exit 1
    }

    $event = Wait-Event -Timeout 60
    if ($event) { Remove-Event -EventIdentifier $event.EventIdentifier }
}