$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
Write-Host "=== process ==="
if (Test-Path logs\concordia_full_verbal.pid) {
  $pidValue = [int](Get-Content logs\concordia_full_verbal.pid -Raw)
  Get-Process -Id $pidValue -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime, HasExited | Format-Table -AutoSize
} else { Write-Host "no PID file" }
Write-Host "=== latest transcript tail ==="
$latest = Get-ChildItem logs\concordia_full_verbal_*.transcript.log -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latest) { Get-Content $latest.FullName -Tail 30 } else { Write-Host "no transcript" }
Write-Host "=== file counts ==="
[PSCustomObject]@{
  Pub=(Get-ChildItem analysis\llm_psrl_verbal\concordia_full_pub_*_llmpsrl.json -ErrorAction SilentlyContinue).Count
  Haggling=(Get-ChildItem analysis\llm_psrl_verbal\concordia_full_haggling_*_llmpsrl.json -ErrorAction SilentlyContinue).Count
  Expected=68
} | Format-Table -AutoSize