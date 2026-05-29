# Start PostgreSQL and run Alembic migrations.
# Usage (from project root):
#   .\backend\scripts\setup_database.ps1

$ErrorActionPreference = "Stop"

$BackendRoot = Split-Path $PSScriptRoot -Parent
$ProjectRoot = Split-Path $BackendRoot -Parent

Set-Location $ProjectRoot

Write-Host "Starting PostgreSQL container..."
docker compose -f docker/docker-compose.postgres.yml up -d

Write-Host "Waiting for PostgreSQL to become healthy..."
$retries = 30
for ($i = 1; $i -le $retries; $i++) {
    $health = docker inspect --format='{{.State.Health.Status}}' comm_intel_postgres 2>$null
    if ($health -eq "healthy") {
        Write-Host "PostgreSQL is healthy."
        break
    }
    Start-Sleep -Seconds 2
    if ($i -eq $retries) {
        throw "PostgreSQL did not become healthy in time."
    }
}

Set-Location "$ProjectRoot\backend"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created backend/.env from .env.example"
}

Write-Host "Running Alembic migrations..."
alembic upgrade head

Write-Host "Verifying database connection..."
python scripts/verify_database.py --schema

Write-Host "Database setup complete."
