param(
    [ValidateSet('setup','audit','prepare','dry-run','smoke','structure','regression','capture','self-test')]
    [string]$Mode = 'audit',
    [string]$Case = 'pallet_town'
)
$ErrorActionPreference = 'Stop'
$TestPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if ($Mode -eq 'setup') {
    if (-not (Test-Path -LiteralPath $TestPython)) { python -m venv (Join-Path $PSScriptRoot '.venv') }
    & $TestPython -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
} elseif ($Mode -eq 'self-test') {
    & $TestPython -m unittest discover -s $PSScriptRoot -v
} else {
    if (-not (Test-Path -LiteralPath $TestPython)) { throw 'Run .\testing\run.ps1 setup first.' }
    & $TestPython (Join-Path $PSScriptRoot 'harness.py') $Mode --case $Case
}
exit $LASTEXITCODE
