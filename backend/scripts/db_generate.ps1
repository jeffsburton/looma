

# Optional: apply the migration after reviewing
# alembic upgrade head

# If alembic.ini is not in the current directory, specify it explicitly
# alembic -c "C:\path\to\your\project\alembic.ini" revision --autogenerate -m "Create user table"


# new-migration.ps1
param(
    [Parameter(Mandatory = $true)]
    [string]$Message
)

# Resolve paths relative to this script's location
$backendRoot = Split-Path -Path $PSScriptRoot -Parent

$versionsPath = Join-Path $backendRoot "alembic\versions"

# Get existing revisions (assuming filenames like 0001_*.py)
$existing = Get-ChildItem $versionsPath -Filter "*.py" |
    ForEach-Object {
        if ($_ -match '^(\d+)_') {
            [int]$matches[1]
        }
    }

if ($existing.Count -eq 0) {
    $next = 1
} else {
    $next = ($existing | Measure-Object -Maximum).Maximum + 1
}

# Zero-pad to 4 digits (0001, 0002, …)
$revId = $next.ToString("0000")

# Ensure DATABASE_URL is set using the script located next to this file, regardless of current working directory
& (Join-Path $PSScriptRoot "set_db_url.ps1")

# Run alembic
alembic revision --autogenerate -m $Message --rev-id $revId
