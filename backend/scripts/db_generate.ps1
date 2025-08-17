param(
    [Parameter(Mandatory = $true)]
    [string]$Message
)


# PowerShell
# 1) Navigate to the repository containing alembic.ini
#Set-Location -Path "..\"

# set db variable
.\set_db_url.ps1

cd ..

# 3) Generate the autogenerate migration for the User model
alembic revision --autogenerate -m $Message

# Optional: apply the migration after reviewing
# alembic upgrade head

# If alembic.ini is not in the current directory, specify it explicitly
# alembic -c "C:\path\to\your\project\alembic.ini" revision --autogenerate -m "Create user table"