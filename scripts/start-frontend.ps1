$ErrorActionPreference = 'Stop'
$praxisRoot = Split-Path -Parent $PSScriptRoot
$praxisNodeDir = Join-Path $praxisRoot '.tools/node-v20.18.0-win-x64'
if (Test-Path -LiteralPath (Join-Path $praxisNodeDir 'node.exe')) {
    $env:PATH = "$praxisNodeDir;$env:PATH"
    Set-Location (Join-Path $praxisRoot 'frontend')
    & (Join-Path $praxisNodeDir 'node.exe') (Join-Path $praxisNodeDir 'node_modules/npm/bin/npm-cli.js') run dev
} else {
    Set-Location (Join-Path $praxisRoot 'frontend')
    npm run dev
}
