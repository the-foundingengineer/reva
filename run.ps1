# Reva Ecosystem Orchestrator
# This script starts all components required for the Reva Lead Qualification engine.

$Root = $PSScriptRoot
$EvolutionDir = Join-Path $Root "evolution-api-native"
$VenvPath = Join-Path $Root "venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "[1/4] Checking AI Engine (Ollama)..." -ForegroundColor Cyan
if (!(Get-Process ollama -ErrorAction SilentlyContinue)) {
    Write-Host "     -> Ollama is not running. Attempting to start..."
    Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 2
} else {
    Write-Host "     -> Ollama is already running."
}

Write-Host "[2/4] Starting Hybrid Databases..." -ForegroundColor Cyan
Set-Location -Path $EvolutionDir
docker compose up -d
Set-Location -Path $Root

Write-Host "[3/4] Launching Evolution API Server (New Window)..." -ForegroundColor Cyan
$Command = "Set-Location -Path '$EvolutionDir'; npm run dev:server"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $Command

Write-Host "[4/4] Launching Reva AI Engine (Current Window)..." -ForegroundColor Cyan
if (Test-Path $VenvPath) {
    . $VenvPath
}
uvicorn app.main:app --reload --port 8080
