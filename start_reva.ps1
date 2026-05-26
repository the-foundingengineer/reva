# Reva Full System Orchestrator
# This script starts Ollama, Docker, Evolution API, Tunnel, and the Reva AI Engine.

$Root = $PSScriptRoot
$EvolutionDir = Join-Path $Root "evolution-api-native"
$VenvPath = Join-Path $Root "venv\Scripts\Activate.ps1"
$TunnelLog = Join-Path $Root "tunnel.log"

Clear-Host
Write-Host "==========================================" -ForegroundColor Green
Write-Host "   REVA AI SALES ENGINE - FULL STARTUP    " -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# 1. Ollama
Write-Host "`n[1/6] Checking AI Engine (Ollama)..." -ForegroundColor Cyan
if (!(Get-Process ollama -ErrorAction SilentlyContinue)) {
    Write-Host "     -> Starting Ollama..."
    Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
} else {
    Write-Host "     -> Ollama is already running."
}

# 2. Docker
Write-Host "[2/6] Starting Databases (Docker)..." -ForegroundColor Cyan
Set-Location -Path $EvolutionDir
docker compose up -d
Set-Location -Path $Root

# 3. Evolution API
Write-Host "[3/6] Starting Evolution API (New Window)..." -ForegroundColor Cyan
$EvoCommand = "Set-Location -Path '$EvolutionDir'; npm run dev:server"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $EvoCommand

# 4. Tunnel
Write-Host "[4/6] Establishing Public Tunnel..." -ForegroundColor Cyan
# Kill any existing ssh processes to avoid port conflicts
Get-Process ssh -ErrorAction SilentlyContinue | Stop-Process -Force
if (Test-Path $TunnelLog) { Remove-Item $TunnelLog -Force }

# Start tunnel and redirect output to log file
$TunnelCommand = "ssh -o StrictHostKeyChecking=no -R 80:127.0.0.1:8080 nokey@localhost.run > '$TunnelLog' 2>&1"
Start-Process powershell -ArgumentList "-Command", $TunnelCommand -WindowStyle Hidden

# 5. Extract URL & Webhook
Write-Host "     -> Waiting for tunnel URL..." -NoNewline
$TunnelURL = $null
$Timeout = 20
for ($i=0; $i -lt $Timeout; $i++) {
    Write-Host "." -NoNewline
    Start-Sleep -Seconds 1
    if (Test-Path $TunnelLog) {
        $Content = Get-Content $TunnelLog -Raw
        if ($Content -match "https://[a-z0-9]+\.lhr\.life") {
            # Extract the last match in case there are multiple
            $Matches = [regex]::Matches($Content, "https://[a-z0-9]+\.lhr\.life")
            $TunnelURL = $Matches[$Matches.Count - 1].Value
            break
        }
    }
}

if ($TunnelURL) {
    Write-Host "`n     -> Tunnel established: $TunnelURL" -ForegroundColor Green
    Write-Host "[5/6] Updating Telegram Webhook..." -ForegroundColor Cyan
    if (Test-Path $VenvPath) { . $VenvPath }
    python scripts/set_telegram_webhook.py $TunnelURL
} else {
    Write-Host "`n     -> WARNING: Could not extract tunnel URL. Webhook not updated." -ForegroundColor Yellow
    Write-Host "        You may need to run 'python scripts/set_telegram_webhook.py <URL>' manually."
}

# 6. Celery Worker & Flower
Write-Host "[6/8] Starting Background Workers (New Window)..." -ForegroundColor Cyan
$CeleryLog = Join-Path $Root "celery.log"
if (Test-Path $CeleryLog) { Remove-Item $CeleryLog -Force }
$CeleryCommand = "if (Test-Path '$VenvPath') { . '$VenvPath' }; celery -A app.workers.celery_app worker --loglevel=info --pool=solo > '$CeleryLog' 2>&1"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $CeleryCommand

Write-Host "[7/8] Starting Monitoring (Flower)..." -ForegroundColor Cyan
$FlowerCommand = "if (Test-Path '$VenvPath') { . '$VenvPath' }; celery -A app.workers.celery_app flower --port=5555"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $FlowerCommand

# 8. Reva AI Engine
Write-Host "[8/8] Launching Reva AI Engine (Current Window)..." -ForegroundColor Cyan
if (Test-Path $VenvPath) {
    . $VenvPath
}
Write-Host "------------------------------------------"
uvicorn app.main:app --reload --port 8080
