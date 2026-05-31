# Materialize OneDrive "online-only" placeholder files so Docker can read the build context.
# OneDrive reparse points cause: "failed to read dockerfile: invalid file request Dockerfile"

param(
    [string[]]$Paths = @("backend", "frontend", "docker"),
    [string[]]$RootFiles = @("docker-compose.yml", ".env.example")
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

function Restore-LocalFile {
    param([System.IO.FileInfo]$File)

    $temp = "$($File.FullName).hydrate-$([guid]::NewGuid().ToString('N'))"
    try {
        Copy-Item -LiteralPath $File.FullName -Destination $temp -Force
        Remove-Item -LiteralPath $File.FullName -Force
        Move-Item -LiteralPath $temp -Destination $File.FullName -Force
    } catch {
        if (Test-Path -LiteralPath $temp) {
            Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
        }
        throw
    }
}

$fixed = 0

foreach ($rel in $RootFiles) {
    $filePath = Join-Path $ProjectRoot $rel
    if (-not (Test-Path -LiteralPath $filePath)) { continue }
    $file = Get-Item -LiteralPath $filePath -Force
    if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        Restore-LocalFile -File $file
        $fixed++
    }
}

foreach ($rel in $Paths) {
    $root = Join-Path $ProjectRoot $rel
    if (-not (Test-Path -LiteralPath $root)) { continue }

    Get-ChildItem -LiteralPath $root -Recurse -File -Force | ForEach-Object {
        if ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            Restore-LocalFile -File $_
            $fixed++
        }
    }
}

if ($fixed -gt 0) {
    Write-Host "Materialized $fixed OneDrive placeholder file(s) for Docker."
}
