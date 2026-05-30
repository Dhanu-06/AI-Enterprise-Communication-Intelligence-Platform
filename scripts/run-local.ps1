# Run backend + frontend locally WITHOUT Docker
# Prerequisites: PostgreSQL installed, Python 3.11+, Node 20+
# Usage: .\scripts\run-local.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$Backend = Join-Path $ProjectRoot "backend"
$Frontend = Join-Path $ProjectRoot "frontend"

Write-Host "=== Local run (no Docker) ===" -ForegroundColor Cyan
Write-Host "Ensure PostgreSQL is running and backend\.env is configured."
Write-Host "See RUN-WITHOUT-DOCKER.md for full steps."
Write-Host ""

# Backend venv
if (-not (Test-Path "$Backend\.venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv "$Backend\.venv"
}

Write-Host "Installing backend dependencies (may take several minutes)..."
& "$Backend\.venv\Scripts\pip.exe" install -r "$Backend\requirements.txt" -q

if (-not (Test-Path "$Backend\.env")) {
    Copy-Item "$Backend\.env.example" "$Backend\.env"
    Write-Host "Created backend\.env — set POSTGRES_* and ELASTICSEARCH_ENABLED=false if no ES"
}

Write-Host "Running database migrations..."
Push-Location $Backend
& .\.venv\Scripts\alembic.exe upgrade head
Pop-Location

if (-not (Test-Path "$Frontend\node_modules")) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $Frontend
    npm install
    Pop-Location
}

if (-not (Test-Path "$Frontend\.env.local")) {
    Copy-Item "$Frontend\.env.example" "$Frontend\.env.local"
}

Write-Host ""
Write-Host "Starting backend on http://localhost:8000 ..." -ForegroundColor Green
Write-Host "Starting frontend on http://localhost:3000 ..." -ForegroundColor Green
Write-Host "Press Ctrl+C in each window to stop."
Write-Host ""

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Backend'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
)

Start-Sleep -Seconds 3

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Frontend'; npm run dev"
)
