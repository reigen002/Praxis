$ErrorActionPreference = 'Stop'
$praxisRoot = Split-Path -Parent $PSScriptRoot
$praxisNodeDir = Join-Path $praxisRoot '.tools/node-v20.18.0-win-x64'
$founderNode = Join-Path $praxisNodeDir 'node.exe'
if (Test-Path -LiteralPath $founderNode) {
    $env:PATH = "$praxisNodeDir;$env:PATH"
    $founderNpm = Join-Path $praxisNodeDir 'node_modules/npm/bin/npm-cli.js'
    Set-Location (Join-Path $praxisRoot 'frontend')
    & $founderNode $founderNpm install --cache (Join-Path $praxisRoot '.cache/npm') --no-audit --no-fund
} else {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'Install Node.js LTS from nodejs.org, reopen PowerShell, then rerun this script.' }
    Set-Location (Join-Path $praxisRoot 'frontend')
    npm install --cache (Join-Path $praxisRoot '.cache/npm') --no-audit --no-fund
}
if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
Write-Output 'Frontend dependencies installed. Return to Praxis and run scripts/start-frontend.ps1.'
