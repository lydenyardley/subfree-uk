$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}
$Log = Join-Path $Root "build\price-refresh.log"
& $Python "build\price_refresh.py" *>> $Log
exit $LASTEXITCODE
