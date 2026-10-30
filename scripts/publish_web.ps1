$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$source = Join-Path $projectRoot 'DB-GPT\web\out'
$target = Join-Path $projectRoot 'DB-GPT\packages\dbgpt-app\src\dbgpt_app\static\web'
$stage = $target + '.chinese-stage'
$backup = Join-Path $projectRoot ('work\chinese-ui-backup\static-web-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
foreach ($candidate in @($source, $target, $stage, $backup)) {
    $resolved = [IO.Path]::GetFullPath($candidate)
    if (!$resolved.StartsWith($projectRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "发布路径超出项目目录：$resolved"
    }
}
foreach ($required in @('index.html', 'construct\app\index.html', '_next')) {
    if (!(Test-Path -LiteralPath (Join-Path $source $required))) { throw "缺少构建产物：$required" }
}
if (Test-Path -LiteralPath $stage) { throw "暂存目录已存在，请先检查：$stage" }
New-Item -ItemType Directory -Path $stage | Out-Null
Get-ChildItem -LiteralPath $source -Force | Copy-Item -Destination $stage -Recurse -Force
& (Join-Path $PSScriptRoot 'stop.ps1')
if (!$?) { throw '停止服务失败，尚未替换页面。' }
New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force | Out-Null
Move-Item -LiteralPath $target -Destination $backup
Move-Item -LiteralPath $stage -Destination $target
Write-Host "已发布中文前端。旧版备份：$backup"
& (Join-Path $PSScriptRoot 'start.ps1') -NoBrowser
