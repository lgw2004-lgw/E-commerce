$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $projectRoot 'DB-GPT'
if (!(Test-Path -LiteralPath (Join-Path $source 'uv.lock'))) { throw 'The DB-GPT v0.8.2 source folder is missing.' }
uv run --no-project --python 3.11 (Join-Path $PSScriptRoot 'apply_upstream_patch.py')
if ($LASTEXITCODE -ne 0) { throw 'Source compatibility patch failed.' }
$env:UV_PROJECT_ENVIRONMENT = Join-Path $projectRoot '.venv'
$env:UV_LINK_MODE = 'copy'
Push-Location $source
try {
    uv sync --package dbgpt-app --no-dev --frozen --python 3.11
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
} finally { Pop-Location }
& (Join-Path $projectRoot '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'init_data.py')
if ($LASTEXITCODE -ne 0) { throw 'Sample data initialization failed.' }
