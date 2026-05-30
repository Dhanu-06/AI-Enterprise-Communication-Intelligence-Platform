$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot
docker compose down
Write-Host "All services stopped."
