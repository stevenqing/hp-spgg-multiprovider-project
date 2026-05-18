param(
    [string[]]$ModelSlugs = @('gpt_5_4_nano_20260317', 'Kimi_K2_6', 'Llama_4_Maverick_17B_128E_Instruct_FP8'),
    [string[]]$Baselines = @('hpsmg_plus', 'llm_belief', 'llm_greedy', 'atom_tom1', 'econ_bne'),
    [string]$LogPath = 'logs\sotopia_hard_official_all_models_monitor.log'
)

$ErrorActionPreference = 'SilentlyContinue'

function Get-RunStatusLine {
    param([string]$ModelSlug, [string]$Baseline)
    $path = "analysis\sotopia_hard_official_${ModelSlug}_${Baseline}_all70.json"
    if (-not (Test-Path $path)) {
        return "$ModelSlug $Baseline checkpoint=waiting_for_first_case"
    }
    try {
        $json = Get-Content $path -Raw | ConvertFrom-Json
        $mtime = (Get-Item $path).LastWriteTime.ToString('HH:mm:ss')
        return ("{0} {1} checkpoint={2}/{3} complete={4} mean={5} mtime={6}" -f $ModelSlug, $Baseline, $json.case_count, $json.target_case_count, $json.complete, $json.summary.mean_overall, $mtime)
    }
    catch {
        return "$ModelSlug $Baseline checkpoint=read_error"
    }
}

function Write-Snapshot {
    $timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("[$timestamp]")
    foreach ($modelSlug in $ModelSlugs) {
        foreach ($baseline in $Baselines) {
            $lines.Add((Get-RunStatusLine -ModelSlug $modelSlug -Baseline $baseline))
        }
    }
    $processCount = (Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run_sotopia_hard_official*' } | Measure-Object).Count
    $lines.Add("active_process_entries=$processCount")
    $lines.Add("")
    Add-Content -Path $LogPath -Value $lines -Encoding UTF8
}

function Test-AllComplete {
    foreach ($modelSlug in $ModelSlugs) {
        foreach ($baseline in $Baselines) {
            $path = "analysis\sotopia_hard_official_${modelSlug}_${baseline}_all70.json"
            if (-not (Test-Path $path)) { return $false }
            try {
                $json = Get-Content $path -Raw | ConvertFrom-Json
                if (-not $json.complete) { return $false }
            }
            catch {
                return $false
            }
        }
    }
    return $true
}

New-Item -ItemType Directory -Force -Path (Split-Path $LogPath) | Out-Null
Write-Snapshot

$watcher = New-Object IO.FileSystemWatcher ((Resolve-Path 'analysis').Path)
$watcher.Filter = 'sotopia_hard_official_*_all70.json'
$watcher.IncludeSubdirectories = $false
$watcher.EnableRaisingEvents = $true

Register-ObjectEvent $watcher Changed -SourceIdentifier SotopiaHardAllModelsChanged -Action { Write-Snapshot } | Out-Null
Register-ObjectEvent $watcher Created -SourceIdentifier SotopiaHardAllModelsCreated -Action { Write-Snapshot } | Out-Null

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
Add-Content -Path $LogPath -Value 'SOTOPIA hard all-model monitor complete.' -Encoding UTF8