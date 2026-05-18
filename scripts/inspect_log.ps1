$env:Path = "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64;$env:Path"
Set-Location (Join-Path $PSScriptRoot '..\paper')
Get-Content main.log | Select-String -Pattern 'expansion|not loadable|cmr|cmbx|microtype|^!|^ ==>' | Select-Object -Last 40 | ForEach-Object { $_.Line }
