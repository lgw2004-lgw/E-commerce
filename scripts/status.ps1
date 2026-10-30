$projectRoot = Split-Path -Parent $PSScriptRoot
try {
    $response = Invoke-RestMethod -Uri 'http://127.0.0.1:5670/api/v1/chat/db/list' -TimeoutSec 5
    Write-Host 'DB-GPT API is responding at http://127.0.0.1:5670'
    $response | ConvertTo-Json -Depth 6
} catch { Write-Host 'DB-GPT is not responding. Run start.cmd or check logs\server.stderr.log.' }
if (Test-Path -LiteralPath (Join-Path $projectRoot 'data\dataset-summary.json')) {
    Get-Content -LiteralPath (Join-Path $projectRoot 'data\dataset-summary.json') -Encoding UTF8
}
