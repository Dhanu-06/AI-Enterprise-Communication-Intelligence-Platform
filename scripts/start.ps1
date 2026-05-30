# Start the full platform with Docker Compose
# Usage: .\scripts\start.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

Write-Host "Building and starting all services (first run may take 10-15 minutes)..."
docker compose up -d --build

Write-Host ""
Write-Host "Platform URLs:"
Write-Host "  Frontend:  http://localhost:3000"
Write-Host "  Backend:   http://localhost:8000"
Write-Host "  API Docs:  http://localhost:8000/docs"
Write-Host "  Health:    http://localhost:8000/api/v1/health"
Write-Host ""
Write-Host "View logs:  docker compose logs -f backend"
Write-Host "Stop:       docker compose down"
