# Run comprehensive tests from backend directory
$base = Get-Location
$env:PYTHONPATH = "$PWD"
$env:DATABASE_URL = "sqlite+aiosqlite:///$PWD/test.db"

Write-Host "Running Looma backend tests..." -ForegroundColor Green
pytest .\tests -v --tb=short

if ($LASTEXITCODE -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
} else {
    Write-Host "Some tests failed!" -ForegroundColor Red
}