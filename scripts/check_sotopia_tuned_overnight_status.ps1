param(
    [string]$LogPath = 'logs\sotopia_tuned_hpsmg_plus_overnight.log'
)

$ErrorActionPreference = 'Stop'

Write-Host '== tuned queue log tail =='
if (Test-Path $LogPath) {
    Get-Content $LogPath -Tail 80
}
else {
    Write-Host "missing_log=$LogPath"
}

Write-Host ''
Write-Host '== tuned queue processes =='
Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -like '*run_sotopia_tuned_hpsmg_plus_overnight*' -or
    $_.CommandLine -like '*hpsmg_plus_sotopia_tuned*' -or
    $_.CommandLine -like '*sotopia_tuned_pilot*'
} | Select-Object ProcessId,ParentProcessId,CreationDate,CommandLine | Format-Table -Wrap

Write-Host ''
Write-Host '== tuned outputs =='
$files = Get-ChildItem analysis -File -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -like '*sotopia*' -and $_.Name -like '*tuned*' -and $_.Extension -eq '.json'
} | Sort-Object Name

$rows = foreach ($file in $files) {
    $status = 'unreadable'
    try {
        $json = Get-Content $file.FullName -Raw | ConvertFrom-Json
        $caseCount = if ($null -ne $json.case_count) { $json.case_count } else { 'n/a' }
        $targetCount = if ($null -ne $json.target_case_count) { $json.target_case_count } else { 'n/a' }
        $mean = if ($null -ne $json.summary.mean_overall) { $json.summary.mean_overall } else { 'n/a' }
        $status = "complete=$($json.complete) cases=$caseCount/$targetCount mean=$mean"
    }
    catch {}
    [pscustomobject]@{
        Name = $file.Name
        Length = $file.Length
        LastWriteTime = $file.LastWriteTime
        Status = $status
    }
}
$rows | Format-Table -AutoSize

Write-Host ''
Write-Host '== tuned job logs =='
Get-ChildItem logs -File -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -like 'sotopia_tuned_*'
} | Select-Object Name,Length,LastWriteTime | Sort-Object LastWriteTime -Descending | Select-Object -First 20 | Format-Table -AutoSize