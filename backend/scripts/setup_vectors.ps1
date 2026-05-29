# Recommended: HTTP Docker ChromaDB + vector reindex from PostgreSQL.
# Usage (from project root):
#   .\backend\scripts\setup_vectors.ps1

$ErrorActionPreference = "Stop"

$BackendRoot = Split-Path $PSScriptRoot -Parent
$ProjectRoot = Split-Path $BackendRoot -Parent

& "$BackendRoot\scripts\setup_chroma.ps1" -Mode http

Set-Location $BackendRoot
Write-Host "Reindexing email vectors from PostgreSQL..."
python scripts/reindex_chroma.py

Write-Host "Vector store setup complete (HTTP Docker mode)."
