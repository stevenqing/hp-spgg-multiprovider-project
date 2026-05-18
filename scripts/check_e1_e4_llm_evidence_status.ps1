param([string]$LogPath = 'logs\e1_e4_llm_evidence_overnight.log')

$ErrorActionPreference = 'Stop'
Write-Host '== E1-E4 LLM log tail =='
if (Test-Path $LogPath) { Get-Content $LogPath -Tail 80 } else { Write-Host "missing_log=$LogPath" }

Write-Host ''
Write-Host '== E1-E4 LLM process =='
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run_e1_e4_llm_evidence_overnight*' -or $_.CommandLine -like '*build_hp_spgg_scaling_live_calibration*' -or $_.CommandLine -like '*llm_hpgg.calibration_live*' } | Select-Object ProcessId,ParentProcessId,CreationDate,CommandLine | Format-Table -Wrap

Write-Host ''
Write-Host '== E1-E4 LLM outputs =='
Get-ChildItem results\e1_e4_llm -File -ErrorAction SilentlyContinue | Select-Object Name,Length,LastWriteTime | Sort-Object Name | Format-Table -AutoSize

Write-Host ''
Write-Host '== E1-E4 LLM reports =='
Get-ChildItem analysis -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^(E[1-4].*llm|E[123].*live_report|E1_c19_.*live_report)' } | Select-Object Name,Length,LastWriteTime | Sort-Object Name | Format-Table -AutoSize