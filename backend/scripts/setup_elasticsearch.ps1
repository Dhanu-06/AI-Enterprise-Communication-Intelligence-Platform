# Start Elasticsearch and initialize index template + index.
# Usage (from project root):
#   .\backend\scripts\setup_elasticsearch.ps1

$ErrorActionPreference = "Stop"

$BackendRoot = Split-Path $PSScriptRoot -Parent
$ProjectRoot = Split-Path $BackendRoot -Parent

Set-Location $ProjectRoot

Write-Host "Ensuring Docker network exists..."
docker network inspect comm_intel_network 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    docker network create comm_intel_network | Out-Null
    Write-Host "Created network: comm_intel_network"
}

Write-Host "Starting Elasticsearch container..."
docker compose -f docker/docker-compose.elasticsearch.yml up -d

Write-Host "Waiting for Elasticsearch to become healthy..."
$retries = 40
for ($i = 1; $i -le $retries; $i++) {
    $health = docker inspect --format='{{.State.Health.Status}}' comm_intel_elasticsearch 2>$null
    if ($health -eq "healthy") {
        Write-Host "Elasticsearch is healthy."
        break
    }
    Start-Sleep -Seconds 3
    if ($i -eq $retries) {
        throw "Elasticsearch did not become healthy in time."
    }
}

Set-Location $BackendRoot

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created backend/.env from .env.example"
}

Write-Host "Initializing Elasticsearch index template and index..."
python scripts/verify_elasticsearch.py --template

Write-Host "Elasticsearch setup complete."
