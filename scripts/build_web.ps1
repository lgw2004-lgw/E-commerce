$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$web = Join-Path $projectRoot 'DB-GPT\web'
$env:NEXT_TELEMETRY_DISABLED = '1'
$env:NODE_OPTIONS = '--max-old-space-size=4096'
Push-Location $web
try {
    & node 'node_modules/next/dist/bin/next' build --no-lint
    if ($LASTEXITCODE -ne 0) { throw '前端构建失败。' }
    & node 'node_modules/next/dist/bin/next' export
    if ($LASTEXITCODE -ne 0) { throw '静态页面导出失败。' }
    Write-Host "中文前端已构建：$web\out"
} finally { Pop-Location }
