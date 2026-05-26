$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
Write-Host "=== process ==="
if (Test-Path logs\llm_psrl_verbal.pid) {
  $pidValue = [int](Get-Content logs\llm_psrl_verbal.pid -Raw)
  Get-Process -Id $pidValue -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime, HasExited | Format-Table -AutoSize
} else { Write-Host "no PID file" }
Write-Host "=== latest transcript tail ==="
$latest = Get-ChildItem logs\llm_psrl_verbal_sweep_*.transcript.log -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latest) { Get-Content $latest.FullName -Tail 30 } else { Write-Host "no transcript" }
Write-Host "=== files ==="
$files = Get-ChildItem analysis\llm_psrl_verbal\E_llmpsrl_n*_K20_*.npz -ErrorAction SilentlyContinue
[PSCustomObject]@{CompletedFiles=$files.Count; ExpectedFiles=16} | Format-Table -AutoSize
if (Test-Path analysis\llm_psrl_verbal\summary.csv) {
  Import-Csv analysis\llm_psrl_verbal\summary.csv | Where-Object {$_.algorithm -eq 'llm_psrl_verbal'} | Sort-Object tier,{[int]$_.n} | Format-Table tier,n,@{N='mean';E={[math]::Round([double]$_.mean_cumulative_regret,3)}},sample_success_rate,update_success_rate -AutoSize
}