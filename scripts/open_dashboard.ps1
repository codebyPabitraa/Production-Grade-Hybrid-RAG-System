param(
    [string]$ReportsDir = "reports",
    [string]$Output = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Could not find virtual environment Python at $python"
}

$outputArgs = @()
if ($Output) {
    $outputArgs += "--output"
    $outputArgs += $Output
}

& $python (Join-Path $PSScriptRoot "generate_dashboard.py") --reports-dir $ReportsDir @outputArgs
$dashboardPath = if ($Output) { $Output } else { Join-Path $ReportsDir "benchmark_dashboard.html" }

Start-Process $dashboardPath
