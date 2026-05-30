# Check tools required to run the platform
$ErrorActionPreference = "Continue"

Write-Host "=== Prerequisites Check ===" -ForegroundColor Cyan

function Test-Command($name) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) {
        Write-Host "[OK] $name" -ForegroundColor Green
        return $true
    }
    Write-Host "[MISSING] $name" -ForegroundColor Red
    return $false
}

$dockerOk = Test-Command "docker"
$composeOk = Test-Command "docker"
if ($dockerOk) {
    try {
        docker compose version | Out-Null
        Write-Host "[OK] docker compose" -ForegroundColor Green
    } catch {
        Write-Host "[MISSING] docker compose plugin" -ForegroundColor Red
        $composeOk = $false
    }
}

Test-Command "python" | Out-Null
Test-Command "node" | Out-Null
Test-Command "npm" | Out-Null

Write-Host ""
Write-Host "=== Port availability (must be free for default setup) ===" -ForegroundColor Cyan
$ports = @(3000, 5432, 8000, 8001, 9200)
foreach ($port in $ports) {
    $inUse = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($inUse) {
        Write-Host "[IN USE] Port $port" -ForegroundColor Yellow
    } else {
        Write-Host "[FREE]   Port $port" -ForegroundColor Green
    }
}

Write-Host ""
if (-not $dockerOk) {
    Write-Host "Install Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Write-Host "For local dev without Docker app containers, you still need Docker for Postgres/ES/Chroma OR install them manually." -ForegroundColor Yellow
}
