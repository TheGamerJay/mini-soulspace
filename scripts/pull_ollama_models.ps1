# Mini SoulSpace — Ollama model puller.
# Pulls every model referenced in ai/configs/models.json.
#
# Requires the Ollama CLI (https://ollama.com) to be installed and running.
#
# Usage (from the repository root):
#   ./scripts/pull_ollama_models.ps1

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $repoRoot "ai\configs\models.json"

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Error "Ollama CLI not found. Install it from https://ollama.com and try again."
    exit 1
}

if (-not (Test-Path $configPath)) {
    Write-Error "Model config not found at $configPath"
    exit 1
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$models = $config.models.PSObject.Properties | ForEach-Object { $_.Value.name }

foreach ($model in $models) {
    Write-Host "==> Pulling $model" -ForegroundColor Cyan
    ollama pull $model
}

Write-Host "==> All models pulled." -ForegroundColor Green
