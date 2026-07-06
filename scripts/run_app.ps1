param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
if (Test-Path .\.venv\Scripts\Activate.ps1) {
    .\.venv\Scripts\Activate.ps1
}

python .\scripts\run_app.py --host $BindHost --port $Port
