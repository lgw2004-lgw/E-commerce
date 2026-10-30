$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $projectRoot 'data\yuque-mcp.pid'
$runner = Join-Path $PSScriptRoot 'yuque_mcp.py'
if (!(Test-Path -LiteralPath $pidFile)) { return }
$bridgePid = [int](Get-Content -LiteralPath $pidFile)
$bridge = Get-CimInstance Win32_Process -Filter "ProcessId=$bridgePid"
if ($bridge) {
    if (!$bridge.CommandLine -or !$bridge.CommandLine.Contains($runner)) { throw 'Yuque PID belongs to another application.' }
    Stop-Process -Id $bridgePid
}
Remove-Item -LiteralPath $pidFile
Write-Host 'Yuque MCP stopped.'
