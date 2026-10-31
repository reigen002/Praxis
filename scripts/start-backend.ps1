$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
uv run --frozen --cache-dir .cache/uv python -m uvicorn praxis.api:app --host 127.0.0.1 --port 8000
