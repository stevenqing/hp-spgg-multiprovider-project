param(
    [string[]]$Baselines = @('hpsmg_plus', 'llm_belief', 'llm_greedy', 'atom_tom1', 'econ_bne'),
    [string]$ModelSlug = 'DeepSeek_V3_2',
    [string]$LogPath = 'logs\sotopia_hard_official_monitor.log'
)

$ErrorActionPreference = 'SilentlyContinue'

function Get-RunStatusLine {
    param([string]$Baseline)
    $path = "analysis\sotopia_hard_official_${ModelSlug}_${Baseline}_all70.json"
    if (-not (Test-Path $path)) {
        return "$Baseline checkpoint=waiting_for_first_case"
    }
    try {
        $json = Get-Content $path -Raw | ConvertFrom-Json
        $mtime = (Get-Item $path).LastWriteTime.ToString('HH:mm:ss')
        return ("{0} checkpoint={1}/{2} complete={3} mean={4} mtime={5}" -f $Baseline, $json.case_count, $json.target_case_count, $json.complete, $json.summary.mean_overall, $mtime)
    }
    catch {
        return "$Baseline checkpoint=read_error"
    }
}

function Write-Snapshot {
    $timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("[$timestamp]")
    foreach ($baseline in $Baselines) {
        $lines.Add((Get-RunStatusLine -Baseline $baseline))
    }
    $processCount = (Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run_sotopia_hard_official*' } | Measure-Object).Count
    $lines.Add("active_process_entries=$processCount")
    $lines.Add("")
    Add-Content -Path $LogPath -Value $lines -Encoding UTF8
}

function Test-AllComplete {
    foreach ($baseline in $Baselines) {
        $path = "analysis\sotopia_hard_official_${ModelSlug}_${baseline}_all70.json"
        if (-not (Test-Path $path)) { return $false }
        try {
            $json = Get-Content $path -Raw | ConvertFrom-Json
            if (-not $json.complete) { return $false }
        }
        catch {
            return $false
        }
    }
    return $true
}

New-Item -ItemType Directory -Force -Path (Split-Path $LogPath) | Out-Null
Write-Snapshot

$watcher = New-Object IO.FileSystemWatcher ((Resolve-Path 'analysis').Path)
$watcher.Filter = "sotopia_hard_official_${ModelSlug}_*_all70.json"
$watcher.IncludeSubdirectories = $false
$watcher.EnableRaisingEvents = $true

Register-ObjectEvent $watcher Changed -SourceIdentifier SotopiaHardChanged -Action { Write-Snapshot } | Out-Null
Register-ObjectEvent $watcher Created -SourceIdentifier SotopiaHardCreated -Action { Write-Snapshot } | Out-Null

while (-not (Test-AllComplete)) {
    $event = Wait-Event -Timeout 120
    if ($event) {
        Remove-Event -EventIdentifier $event.EventIdentifier
    }
    else {
        Write-Snapshot
    }
}

Write-Snapshot
Add-Content -Path $LogPath -Value "SOTOPIA hard monitor complete." -Encoding UTF8