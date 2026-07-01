# Mini SoulSpace — backend setup script.
# Creates a virtual environment and installs backend dependencies.
#
# Usage (from the repository root):
#   ./scripts/setup_backend.ps1

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $repoRoot "backend"

Write-Host "==> Setting up backend in $backend" -ForegroundColor Cyan
Set-Location $backend

if (-not (Test-Path ".venv")) {
    Write-Host "==> Creating virtual environment (.venv)" -ForegroundColor Cyan
    python -m venv .venv
}

$python = Join-Path $backend ".venv\Scripts\python.exe"

Write-Host "==> Upgrading pip" -ForegroundColor Cyan
& $python -m pip install --upgrade pip

Write-Host "==> Installing dependencies (requirements-dev.txt)" -ForegroundColor Cyan
& $python -m pip install -r requirements-dev.txt

if (-not (Test-Path (Join-Path $repoRoot ".env"))) {
    Write-Host "==> Creating .env from .env.example" -ForegroundColor Yellow
    Copy-Item (Join-Path $repoRoot ".env.example") (Join-Path $repoRoot ".env")
}

Write-Host "==> Backend setup complete." -ForegroundColor Green
Write-Host "    Start it with:" -ForegroundColor Green
Write-Host "      cd backend; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload" -ForegroundColor Green
