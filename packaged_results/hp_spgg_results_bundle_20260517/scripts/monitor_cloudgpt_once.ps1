param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$TaskName = "HP-SPGG-CloudGPT-Monitor"
)

$ErrorActionPreference = "Stop"
Set-Location $Root

$models = @(
    "gpt_5_4_nano_20260317",
    "gpt_5_5_20260424",
    "DeepSeek_V3_2",
    "Kimi_K2_6",
    "Llama_4_Maverick_17B_128E_Instruct_FP8"
)

function Get-CacheStatus {
    param([string]$Model)
    $path = Join-Path "logs" "cloudgpt_live_cache_$Model.jsonl"
    if (-not (Test-Path $path)) {
        return [pscustomobject]@{ Model = $Model; Cells = 0; CompletedProfiles = 0; LastWrite = "" }
    }
    $lines = Get-Content $path | Where-Object { $_.Trim().Length -gt 0 }
    $profiles = @()
    if ($lines.Count -gt 0) {
        $profiles = @(
            $lines |
                ForEach-Object { $_ | ConvertFrom-Json } |
                Group-Object -Property profile_index |
                Where-Object { $_.Count -ge 12 } |
                ForEach-Object { [int]$_.Name }
        )
    }
    $item = Get-Item $path
    return [pscustomobject]@{
        Model = $Model
        Cells = $lines.Count
        CompletedProfiles = $profiles.Count
        LastWrite = $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    }
}

function Get-LatestResultRows {
    $files = Get-ChildItem "analysis\calibration_cloudgpt_multi_model_fast4_8algos_*_summary.json" -ErrorAction SilentlyContinue
    $rows = foreach ($file in $files) {
        if ($file.BaseName -match "fast4_8algos_(.+)_c(\d+)_summary") {
            $model = $Matches[1]
            $cycle = [int]$Matches[2]
            $json = Get-Content $file.FullName -Raw | ConvertFrom-Json
            $best = $json.best_result
            $final = $best.final_regret
            [pscustomobject]@{
                Model = $model
                Cycle = $cycle
                Tid = [math]::Round([double]$json.tid_min_gap, 4)
                Beta = $best.beta
                HPSMGPlus = $final.hpsmg_plus
                HPSMG = $final.hpsmg
                Joint = $final.joint_psrl
                MAP = $final.map_greedy
                PSRLNoType = $final.psrl_notype
                IQLIndependent = $final.iql_independent_actions
                IQL = $final.iql
                Random = $final.random
                Oracle = $final.oracle
            }
        }
    }
    return @($rows | Group-Object Model | ForEach-Object { $_.Group | Sort-Object Cycle -Descending | Select-Object -First 1 } | Sort-Object Model)
}

function Add-MarkdownTable {
    param([System.Collections.IEnumerable]$Rows, [string[]]$Columns)
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("| " + ($Columns -join " | ") + " |")
    $lines.Add("| " + (($Columns | ForEach-Object { "---" }) -join " | ") + " |")
    foreach ($row in $Rows) {
        $values = foreach ($column in $Columns) { [string]$row.$column }
        $lines.Add("| " + ($values -join " | ") + " |")
    }
    return $lines
}

$now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$summaryCount = (Get-ChildItem "analysis\calibration_cloudgpt_multi_model_fast4_8algos_*_summary.json" -ErrorAction SilentlyContinue | Measure-Object).Count
$cacheRows = @($models | ForEach-Object { Get-CacheStatus -Model $_ })
$resultRows = Get-LatestResultRows
$latestRunLog = Get-ChildItem "logs\cloudgpt_multi_model_live_*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$runDone = $false
if ($latestRunLog) {
    $runDone = @((Get-Content $latestRunLog.FullName -Tail 80) | Where-Object { $_ -match "Done\. Transcript" }).Count -gt 0
}
$allComplete = $runDone

$latest = New-Object System.Collections.Generic.List[string]
$latest.Add("# CloudGPT Monitor Latest")
$latest.Add("")
$latest.Add("Updated: $now")
$latest.Add("")
$latest.Add("summary_count: $summaryCount")
$latest.Add("complete: $allComplete")
if ($latestRunLog) {
    $latest.Add("latest_run_log: $($latestRunLog.Name)")
}
$latest.Add("")
$latest.Add("## Cache Progress")
$latest.Add("")
foreach ($line in (Add-MarkdownTable -Rows $cacheRows -Columns @("Model", "Cells", "CompletedProfiles", "LastWrite"))) {
    $latest.Add($line)
}
$latest.Add("")
$latest.Add("## Latest Best Results")
$latest.Add("")
foreach ($line in (Add-MarkdownTable -Rows $resultRows -Columns @("Model", "Cycle", "Tid", "Beta", "HPSMGPlus", "HPSMG", "Joint", "MAP", "PSRLNoType", "IQLIndependent", "IQL", "Random", "Oracle"))) {
    $latest.Add($line)
}
$latest.Add("")
$latest.Add("## LLM-Based Baseline")
$latest.Add("")
$latest.Add("See analysis/llm_baseline_summary.md.")
$latest.Add("")

New-Item -ItemType Directory -Force -Path "analysis", "logs" | Out-Null
$latestPath = "analysis\cloudgpt_monitor_latest.md"
$logPath = "logs\cloudgpt_monitor_60s.log"
$latest | Set-Content -Path $latestPath -Encoding UTF8
Add-Content -Path $logPath -Value "[$now] summary_count=$summaryCount complete=$allComplete"
foreach ($row in $cacheRows) {
    Add-Content -Path $logPath -Value "[$now] $($row.Model) cells=$($row.Cells) completed_profiles=$($row.CompletedProfiles) last_write=$($row.LastWrite)"
}

if ($allComplete) {
    Set-Content -Path "analysis\cloudgpt_monitor_complete.flag" -Value $now -Encoding UTF8
    schtasks.exe /Delete /TN $TaskName /F 2>$null | Out-Null
}

Write-Host "monitor_latest=$latestPath"
Write-Host "monitor_log=$logPath"
Write-Host "summary_count=$summaryCount complete=$allComplete"