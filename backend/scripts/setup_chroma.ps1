# Start ChromaDB server and verify connectivity.
# Usage (from project root):
#   .\backend\scripts\setup_chroma.ps1 [-Mode persistent|http]

param(
    [ValidateSet("persistent", "http")]
    [string]$Mode = "http"
)

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

if ($Mode -eq "http") {
    Write-Host "Starting ChromaDB server container..."
    docker compose -f docker/docker-compose.chroma.yml up -d

    Write-Host "Waiting for ChromaDB to become healthy..."
    $retries = 30
    for ($i = 1; $i -le $retries; $i++) {
        $health = docker inspect --format='{{.State.Health.Status}}' comm_intel_chromadb 2>$null
        if ($health -eq "healthy") {
            Write-Host "ChromaDB is healthy."
            break
        }
        Start-Sleep -Seconds 2
        if ($i -eq $retries) {
            throw "ChromaDB did not become healthy in time."
        }
    }
} else {
    Write-Host "Using persistent ChromaDB mode (local directory)."
    New-Item -ItemType Directory -Force -Path "$BackendRoot\chroma_data" | Out-Null
}

Set-Location $BackendRoot

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created backend/.env from .env.example"
}

$envContent = Get-Content ".env" -Raw
$envContent = $envContent -replace "CHROMA_MODE=.*", "CHROMA_MODE=$Mode"
Set-Content ".env" $envContent.TrimEnd()
Write-Host "Set CHROMA_MODE=$Mode in backend/.env"

Write-Host "Verifying ChromaDB..."
python scripts/verify_chroma.py

Write-Host "ChromaDB setup complete."
