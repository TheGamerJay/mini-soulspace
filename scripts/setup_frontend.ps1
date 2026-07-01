# Mini SoulSpace — frontend setup script.
# Installs frontend dependencies.
#
# Usage (from the repository root):
#   ./scripts/setup_frontend.ps1

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $repoRoot "frontend"

Write-Host "==> Setting up frontend in $frontend" -ForegroundColor Cyan
Set-Location $frontend

Write-Host "==> Installing npm dependencies" -ForegroundColor Cyan
npm install

Write-Host "==> Frontend setup complete." -ForegroundColor Green
Write-Host "    Start it with:" -ForegroundColor Green
Write-Host "      cd frontend; npm run dev" -ForegroundColor Green
