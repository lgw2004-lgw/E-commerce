param([switch]$Online, [switch]$Offline, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if ($Online -and $Offline) { throw 'Use either -Online or -Offline, not both.' }
$envFile = Join-Path $projectRoot '.env'
if (!$Offline -and !$Online -and (Test-Path -LiteralPath $envFile) -and (Test-Path -LiteralPath (Join-Path $projectRoot 'configs\online-model.toml'))) {
    $Online = [bool](@(Get-Content -LiteralPath $envFile | Where-Object { $_ -match '^\s*LLM_API_KEY\s*=\s*\S+' }).Count)
}
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$runner = Join-Path $PSScriptRoot 'run_server.py'
$pidFile = Join-Path $projectRoot 'data\server.pid'
if (!(Test-Path -LiteralPath $python)) { throw 'Python environment missing. Run scripts\install.ps1 first.' }
& (Join-Path $PSScriptRoot 'start_yuque.ps1')
$listener = Get-NetTCPConnection -State Listen -LocalPort 5670 -ErrorAction SilentlyContinue
if ($listener) {
    $owner = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener[0].OwningProcess)"
    if (!$owner.CommandLine -or !$owner.CommandLine.Contains($runner)) {
        throw 'Port 5670 is used by another application. No process was stopped.'
    }
    Write-Host 'DB-GPT is already running at http://127.0.0.1:5670'
    if (!$NoBrowser) { Start-Process 'http://127.0.0.1:5670' }
    exit 0
}
if ($Online -and !(Test-Path -LiteralPath (Join-Path $projectRoot 'configs\online-model.toml'))) {
    throw 'Copy configs\online-model.toml.example to configs\online-model.toml and configure .env first.'
}
& $python (Join-Path $PSScriptRoot 'init_data.py')
if ($LASTEXITCODE -ne 0) { throw 'Sample data initialization failed.' }
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$arguments = @('-u', ('"' + $runner + '"'))
if ($Online) { $arguments += '--online' }
$server = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory (Join-Path $projectRoot 'DB-GPT') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot 'logs\server.stdout.log') -RedirectStandardError (Join-Path $projectRoot 'logs\server.stderr.log') -PassThru
$server.Id | Set-Content -LiteralPath $pidFile
Write-Host "Starting DB-GPT (PID $($server.Id)). First startup can take about a minute."
$ready = $false
for ($attempt = 0; $attempt -lt 120; $attempt++) {
    if ($server.HasExited) {
        Get-Content -LiteralPath (Join-Path $projectRoot 'logs\server.stderr.log') -Tail 35
        throw 'DB-GPT stopped before becoming ready.'
    }
    try {
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:5670/api/v1/chat/db/list' -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) { $ready = $true; break }
    } catch { }
    Start-Sleep -Seconds 1
}
if (!$ready) { throw 'Startup timed out. See logs\server.stderr.log; the process was left running for diagnosis.' }
& $python (Join-Path $PSScriptRoot 'register_datasource.py')
if ($LASTEXITCODE -ne 0) { throw 'Datasource registration failed.' }
Write-Host 'Ready: http://127.0.0.1:5670'
if ($Online) {
    Write-Host 'Datasource: ecommerce_demo. Online model configuration is active.'
} else {
    Write-Host 'Datasource: ecommerce_demo. UI/database-only mode is active.'
}
if (!$NoBrowser) { Start-Process 'http://127.0.0.1:5670' }
