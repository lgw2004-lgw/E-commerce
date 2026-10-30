$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $projectRoot 'data\server.pid'
$runner = Join-Path $PSScriptRoot 'run_server.py'
& (Join-Path $PSScriptRoot 'stop_yuque.ps1')
if (!(Test-Path -LiteralPath $pidFile)) { Write-Host 'No recorded server process.'; exit 0 }
$serverPid = [int](Get-Content -LiteralPath $pidFile)
$server = Get-CimInstance Win32_Process -Filter "ProcessId=$serverPid"
if (!$server) { Write-Host 'Recorded server process has already exited.'; exit 0 }
if (!$server.CommandLine -or !$server.CommandLine.Contains($runner)) {
    throw 'Recorded PID belongs to a different application; no process was stopped.'
}
$allProcesses = @(Get-CimInstance Win32_Process)
function Stop-ProjectTree([int]$processId) {
    foreach ($child in $allProcesses | Where-Object { $_.ParentProcessId -eq $processId }) {
        Stop-ProjectTree $child.ProcessId
    }
    Stop-Process -Id $processId -ErrorAction SilentlyContinue
}
Stop-ProjectTree $serverPid
Remove-Item -LiteralPath $pidFile -ErrorAction SilentlyContinue
Write-Host 'DB-GPT stopped. Databases and source files were preserved.'
