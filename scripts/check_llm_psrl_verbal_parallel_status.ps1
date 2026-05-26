$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
Write-Host "=== processes ==="
if (Test-Path logs\llm_psrl_verbal_parallel_jobs.json) {
  $jobs = Get-Content logs\llm_psrl_verbal_parallel_jobs.json -Raw | ConvertFrom-Json
  $rows = @()
  foreach ($job in $jobs) {
    $p = Get-Process -Id ([int]$job.Pid) -ErrorAction SilentlyContinue
    $rows += [PSCustomObject]@{Kind=$job.Kind; Tier=$job.Tier; Pid=$job.Pid; Running=($p -ne $null)}
  }
  $rows | Sort-Object Kind,Tier | Format-Table -AutoSize
} else { Write-Host "no jobs json" }
Write-Host "=== HP files ==="
if (Test-Path analysis\llm_psrl_verbal\summary.csv) {
  Import-Csv analysis\llm_psrl_verbal\summary.csv | Where-Object {$_.algorithm -eq 'llm_psrl_verbal'} | Sort-Object tier,{[int]$_.n} | Format-Table tier,n,@{N='mean';E={[math]::Round([double]$_.mean_cumulative_regret,3)}},sample_success_rate,update_success_rate -AutoSize
}
[PSCustomObject]@{HpFiles=(Get-ChildItem analysis\llm_psrl_verbal\E_llmpsrl_n*_K20_*.npz -ErrorAction SilentlyContinue).Count; HpExpected=16} | Format-Table -AutoSize
Write-Host "=== Concordia haggling files ==="
$rows=@(); foreach($f in Get-ChildItem analysis\llm_psrl_verbal\concordia_haggling_fruitville_*_llmpsrl_s30.json -ErrorAction SilentlyContinue){try{$j=Get-Content $f.FullName -Raw|ConvertFrom-Json;$m=($j.summary|Where-Object method -eq 'llm_psrl_verbal').focal_score_mean;$rows += [PSCustomObject]@{File=$f.Name; Mean=[math]::Round([double]$m,3)}}catch{}}; if($rows.Count){$rows|Sort-Object File|Format-Table -AutoSize}else{Write-Host "none"}
Write-Host "=== SOTOPIA files ==="
$rows=@(); foreach($f in Get-ChildItem analysis\llm_psrl_verbal\sotopia_hard_*_llm_psrl_verbal_all70.json -ErrorAction SilentlyContinue){try{$j=Get-Content $f.FullName -Raw|ConvertFrom-Json;$rows += [PSCustomObject]@{File=$f.Name; Cases=$j.case_count; Complete=$j.complete; Mean=if($j.summary.mean_overall -ne $null){[math]::Round([double]$j.summary.mean_overall,3)}else{$null}}}catch{}}; if($rows.Count){$rows|Sort-Object File|Format-Table -AutoSize}else{Write-Host "none"}