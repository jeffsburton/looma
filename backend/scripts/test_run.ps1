# Run backend tests from any working directory
# Resolve paths relative to this script's location
$backendRoot = Split-Path -Path $PSScriptRoot -Parent

# Environment for Python and DB
$env:PYTHONPATH = $backendRoot

# Build a sqlite URL with a normalized path (forward slashes for SQLAlchemy URI)
$dbPath = Join-Path -Path $backendRoot -ChildPath 'test.db'
$dbUriPath = $dbPath -replace '\\','/'
$env:DATABASE_URL = "sqlite+aiosqlite:///$dbUriPath"

Write-Host "Running Looma backend tests..." -ForegroundColor Green
$testsPath = Join-Path $backendRoot 'tests'
pytest $testsPath -v --tb=short

if ($LASTEXITCODE -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
} else {
    Write-Host "Some tests failed!" -ForegroundColor Red
}