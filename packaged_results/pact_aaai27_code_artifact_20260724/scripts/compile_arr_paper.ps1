$ErrorActionPreference = 'Continue'
$env:Path = "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64;$env:Path"
$root = Join-Path $PSScriptRoot '..'
Set-Location (Join-Path $root 'arr_paper')
initexmf --set-config-value '[MPM]AutoInstall=1' 2>&1 | Out-Null
if (-not (Test-Path '..\logs')) { New-Item -ItemType Directory ..\logs | Out-Null }

Remove-Item main.aux,main.bbl,main.blg,main.log,main.out,main.toc,main.pdf -ErrorAction SilentlyContinue

function Run-Step($label, $exe, $argList) {
  Write-Host "=== $label ==="
  & $exe @argList 2>&1 | Tee-Object -FilePath "..\logs\arr_paper_$label.log" | Out-Null
  Write-Host "exit=$LASTEXITCODE"
}

Run-Step 'pdf1' 'pdflatex' @('-interaction=nonstopmode','main.tex')
Run-Step 'bib'  'bibtex'   @('main')
Run-Step 'pdf2' 'pdflatex' @('-interaction=nonstopmode','main.tex')
Run-Step 'pdf3' 'pdflatex' @('-interaction=nonstopmode','main.tex')

Write-Host "=== summary ==="
if (Test-Path main.pdf) { Get-Item main.pdf | Select-Object FullName,Length,LastWriteTime | Format-List } else { Write-Host 'NO main.pdf' }
$fatal = Select-String -Path main.log -Pattern '^\!' | Measure-Object | Select-Object -ExpandProperty Count
Write-Host "fatal_lines=$fatal"
Select-String -Path main.log -Pattern 'Output written|undefined references|There were' | ForEach-Object { $_.Line }
