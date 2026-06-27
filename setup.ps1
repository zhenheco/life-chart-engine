# setup.ps1 — Windows setup for life-chart-engine (CPython 3.12 venv + deps)
#
# WHY 3.12: kept aligned with the Unix setup and CI-tested runtime. The
# astronomy-engine does not require compiling native astronomy libraries.
#
# Usage:  ./setup.ps1     then    ./start-web.ps1   (web UI)  or  ./life-chart.ps1 --help
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$venv = Join-Path $here ".venv"

# locate uv
$uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
if (-not $uv) { $uv = Join-Path $HOME ".local\bin\uv.exe" }
if (-not (Test-Path $uv)) {
  Write-Host "uv not found. Install it first:" -ForegroundColor Yellow
  Write-Host '  irm https://astral.sh/uv/install.ps1 | iex'
  exit 1
}

Write-Host "==> Creating venv (CPython 3.12) at $venv"
& $uv venv --python 3.12 $venv
# uv occasionally fails the first managed-Python download with a
# "minor version link" error; a second attempt succeeds.
if ($LASTEXITCODE -ne 0) { & $uv venv --python 3.12 $venv }

Write-Host "==> Installing dependencies"
& $uv pip install --python "$venv\Scripts\python.exe" -r (Join-Path $here "requirements.txt")
if ($LASTEXITCODE -ne 0) { Write-Error "dependency install failed"; exit 1 }

Write-Host "==> Smoke test"
$env:PYTHONUTF8 = "1"
& "$venv\Scripts\python.exe" (Join-Path $here "scripts\chart_engine.py") --json `
  --name "Setup Test" --gender 女 --date 1990-06-15 --time 08:30 `
  --tz 8 --lat 25.0 --lon 121.5 --target 2025-01-01 | Out-Null
if ($LASTEXITCODE -eq 0) {
  Write-Host "OK - engine runs." -ForegroundColor Green
  Write-Host ""
  Write-Host "Start the web UI:   ./start-web.ps1     (opens http://127.0.0.1:8765)"
  Write-Host "Or the CLI:         ./life-chart.ps1 --help"
} else {
  Write-Error "smoke test failed"
}
