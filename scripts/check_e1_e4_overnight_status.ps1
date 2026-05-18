param([string]$LogPath = 'logs\e1_e4_overnight.log')

$ErrorActionPreference = 'Stop'
Write-Host '== E1-E4 log tail =='
if (Test-Path $LogPath) { Get-Content $LogPath -Tail 80 } else { Write-Host "missing_log=$LogPath" }

Write-Host ''
Write-Host '== E1-E4 process =='
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run_e1_e4_overnight*' } | Select-Object ProcessId,ParentProcessId,CreationDate,CommandLine | Format-Table -Wrap

Write-Host ''
Write-Host '== E1-E4 result files =='
Get-ChildItem results\e1_e4 -File -ErrorAction SilentlyContinue | Select-Object Name,Length,LastWriteTime | Sort-Object Name | Format-Table -AutoSize

Write-Host ''
Write-Host '== E1-E4 analysis files =='
Get-ChildItem analysis,tables,figs -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^E[1-4]_' } | Select-Object Directory,Name,Length,LastWriteTime | Sort-Object Directory,Name | Format-Table -AutoSize