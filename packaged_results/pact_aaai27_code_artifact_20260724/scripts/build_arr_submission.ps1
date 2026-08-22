$ErrorActionPreference = 'Stop'
$root = Join-Path $PSScriptRoot '..'
$paperDir = Join-Path $root 'arr_paper'
$inputPdf = Join-Path $paperDir 'main.pdf'
$outputPdf = Join-Path $paperDir 'PACT_AAAI27.pdf'
$aliasPdf = Join-Path $paperDir 'PACT_AAAI27_submission.pdf'

if (-not (Test-Path $inputPdf)) {
    throw "Missing compiled full bundle: $inputPdf"
}

foreach ($command in @('pdfinfo', 'pdftotext', 'pdfseparate', 'pdfunite')) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Required PDF command not found: $command"
    }
}

$info = (& pdfinfo $inputPdf | Out-String)
if ($info -notmatch '(?m)^Pages:\s+(\d+)') {
    throw 'Could not determine PDF page count.'
}
$totalPages = [int]$Matches[1]
$appendixStart = $null
$checklistStart = $null

for ($page = 1; $page -le $totalPages; $page++) {
    $text = (& pdftotext -f $page -l $page $inputPdf - | Out-String)
    if (-not $appendixStart -and $text -match 'Claim-Organized Empirical Supplement') {
        $appendixStart = $page
    }
    if (-not $checklistStart -and $text -match 'Reproducibility Checklist') {
        $checklistStart = $page
    }
}

if (-not $appendixStart -or -not $checklistStart -or $checklistStart -le $appendixStart) {
    throw "Could not identify appendix/checklist boundaries (appendix=$appendixStart checklist=$checklistStart)."
}

$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("pact_submission_" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempDir | Out-Null
try {
    & pdfseparate $inputPdf (Join-Path $tempDir 'page-%d.pdf')
    if ($LASTEXITCODE -ne 0) { throw 'pdfseparate failed.' }

    $pages = @()
    for ($page = 1; $page -lt $appendixStart; $page++) {
        $pages += Join-Path $tempDir "page-$page.pdf"
    }
    for ($page = $checklistStart; $page -le $totalPages; $page++) {
        $pages += Join-Path $tempDir "page-$page.pdf"
    }

    Remove-Item $outputPdf -ErrorAction SilentlyContinue
    & pdfunite @pages $outputPdf
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $outputPdf)) {
        throw 'pdfunite failed.'
    }
    Copy-Item $outputPdf $aliasPdf -Force

    Write-Output ([ordered]@{
        status = 'complete'
        source_pages = $totalPages
        main_and_references = "1-$($appendixStart - 1)"
        checklist = "$checklistStart-$totalPages"
        output = $outputPdf
        alias = $aliasPdf
    } | ConvertTo-Json)
}
finally {
    Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}
