$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$runner = Join-Path $PSScriptRoot 'yuque_mcp.py'
$configured = & $python -c "from dotenv import dotenv_values; import sys; sys.exit(0 if (dotenv_values(sys.argv[1]).get('YUQUE_TOKEN') or '').strip() else 2)" (Join-Path $projectRoot '.env')
if ($LASTEXITCODE -eq 2) { Write-Host 'Yuque: YUQUE_TOKEN not configured; bridge not started.'; return }
if ($LASTEXITCODE -ne 0) { throw 'Failed to read Yuque configuration.' }
$listener = Get-NetTCPConnection -State Listen -LocalPort 5671 -ErrorAction SilentlyContinue
if ($listener) {
    $owner = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener[0].OwningProcess)"
    if (!$owner.CommandLine -or !$owner.CommandLine.Contains($runner)) { throw 'Port 5671 is used by another application.' }
    Write-Host 'Yuque MCP is already running: http://127.0.0.1:5671/mcp'
    return
}
New-Item -ItemType Directory -Path (Join-Path $projectRoot 'logs') -Force | Out-Null
$bridge = Start-Process -FilePath $python -ArgumentList @('-u', ('"' + $runner + '"')) -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot 'logs\yuque.stdout.log') -RedirectStandardError (Join-Path $projectRoot 'logs\yuque.stderr.log') -PassThru
$bridge.Id | Set-Content -LiteralPath (Join-Path $projectRoot 'data\yuque-mcp.pid')
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    if ($bridge.HasExited) { throw 'Yuque MCP stopped; see logs\yuque.stderr.log.' }
    if (Get-NetTCPConnection -State Listen -LocalPort 5671 -ErrorAction SilentlyContinue) {
        Write-Host 'Yuque MCP ready: http://127.0.0.1:5671/mcp'
        return
    }
    Start-Sleep -Milliseconds 500
}
throw 'Yuque MCP startup timed out; see logs\yuque.stderr.log.'
