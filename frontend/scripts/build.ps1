# Build script for Vite/Vue frontend
# Usage: from repository root or frontend directory, run in PowerShell:
#   .\frontend\scripts\build.ps1

Param(
    [switch]$Install
)

# Resolve script directory to frontend root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Split-Path -Parent $ScriptDir

Push-Location $FrontendDir

if ($Install) {
    Write-Host "Installing dependencies with npm ci..." -ForegroundColor Cyan
    npm ci
}

Write-Host "Building production bundle (vite build)..." -ForegroundColor Cyan
npm run build

$Dist = Join-Path $FrontendDir 'dist'
if (Test-Path $Dist) {
    Write-Host "Build complete. Output: $Dist" -ForegroundColor Green
} else {
    Write-Host "Build failed: dist directory not found." -ForegroundColor Red
    exit 1
}

Pop-Location
