

# Optional: apply the migration after reviewing
# alembic upgrade head

# If alembic.ini is not in the current directory, specify it explicitly
# alembic -c "C:\path\to\your\project\alembic.ini" revision --autogenerate -m "Create user table"


# new-migration.ps1


# Ensure DATABASE_URL is set using the script located next to this file, regardless of current working directory
& (Join-Path $PSScriptRoot "set_db_url.ps1")

# Run alembic
alembic upgrade head
