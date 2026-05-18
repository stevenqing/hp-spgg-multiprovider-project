param(
    [int]$WaitForPid = 30656,
    [string]$Model = 'gpt-4.1-mini-20250414',
    [string[]]$Baselines = @('hpsmg_plus', 'llm_belief', 'llm_greedy', 'atom_tom1', 'econ_bne'),
    [int]$Turns = 6,
    [int]$Limit = 20,
    [int]$MaxAttempts = 3,
    [string]$LogPath = 'logs\sotopia_hard_official_weak_model_after_queue.log'
)

$ErrorActionPreference = 'Stop'

function Get-ModelSlug {
    param([string]$ModelName)
    return ($ModelName -replace '[^A-Za-z0-9]+', '_').Trim('_')
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
    param([string]$Path)
    if (-not (Test-Path $Path)) { return 'waiting_for_first_case' }
    try {
        $json = Get-Content $Path -Raw | ConvertFrom-Json
        return ("{0}/{1} complete={2} mean={3}" -f $json.case_count, $json.target_case_count, $json.complete, $json.summary.mean_overall)
    }
    catch {
        return 'read_error'
    }
}

function Write-RunLog {
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

if ($WaitForPid -gt 0) {
    $process = Get-Process -Id $WaitForPid -ErrorAction SilentlyContinue
    if ($null -ne $process) {
        Write-RunLog ("waiting_for_pid={0} before starting model={1}" -f $WaitForPid, $Model)
        Wait-Process -Id $WaitForPid
    }
}

$slug = Get-ModelSlug -ModelName $Model
Write-RunLog ("weak_model_start model={0} limit={1} baselines={2}" -f $Model, $Limit, ($Baselines -join ','))

foreach ($baseline in $Baselines) {
    $out = "analysis\sotopia_hard_official_${slug}_${baseline}_limit${Limit}.json"
    $stdout = "logs\sotopia_hard_official_${slug}_${baseline}_limit${Limit}_stdout.log"
    $stderr = "logs\sotopia_hard_official_${slug}_${baseline}_limit${Limit}_stderr.log"
    if (Test-CompleteResult -Path $out) {
        Write-RunLog ("already_complete model={0} baseline={1} checkpoint={2}" -f $Model, $baseline, (Get-CheckpointText -Path $out))
        continue
    }

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        Write-RunLog ("started model={0} baseline={1} attempt={2} checkpoint={3}" -f $Model, $baseline, $attempt, (Get-CheckpointText -Path $out))
        $args = @(
            '-u', '-m', 'llm_hpgg_sotopia.run_sotopia_hard_official',
            '--baseline', $baseline,
            '--model', $Model,
            '--evaluator-model', $Model,
            '--turns', [string]$Turns,
            '--limit', [string]$Limit,
            '--resume',
            '--out', $out
        )
        $process = Start-Process -FilePath '.venvs\sotopia-py312\Scripts\python.exe' -ArgumentList $args -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
        Wait-Process -Id $process.Id
        $process.Refresh()
        Write-RunLog ("exited model={0} baseline={1} exit={2} attempt={3} checkpoint={4}" -f $Model, $baseline, $process.ExitCode, $attempt, (Get-CheckpointText -Path $out))
        if (Test-CompleteResult -Path $out) { break }
    }
}

Write-RunLog ("weak_model_complete model={0}" -f $Model)