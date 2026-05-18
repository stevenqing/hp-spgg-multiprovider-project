$ErrorActionPreference = 'Continue'
$env:Path = "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64;$env:Path"
Set-Location (Join-Path $PSScriptRoot '..\paper')
initexmf --set-config-value '[MPM]AutoInstall=1' 2>&1 | Out-Null
$out = pdflatex -interaction=nonstopmode main.tex 2>&1
$out | Select-Object -Last 80
Write-Host "===EXIT $LASTEXITCODE==="
