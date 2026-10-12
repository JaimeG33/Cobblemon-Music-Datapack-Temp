param(
    [ValidateSet('dry-run','smoke','structure','regression','capture','representative','audio-devices','recover')]
    [string]$Mode = 'dry-run',
    [string]$Case = 'rc5_desert_pyramid',
    [string]$RecoverReport,
    [switch]$Audio,
    [switch]$AtCurrentPosition
)
$ErrorActionPreference = 'Stop'
$TestPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $TestPython)) { throw 'Run testing/run.ps1 setup first.' }
$HarnessMode = if ($Mode -eq 'recover') { 'capture' } else { $Mode }
$Rc5Arguments = @((Join-Path $PSScriptRoot 'harness.py'), $HarnessMode,
                  '--config', (Join-Path $PSScriptRoot 'config_rc5.json'), '--case', $Case)
if ($Audio) { $Rc5Arguments += '--audio' }
if ($AtCurrentPosition) { $Rc5Arguments += '--at-current-position' }
if ($RecoverReport) { $Rc5Arguments += @('--recover-report', $RecoverReport) }
& $TestPython @Rc5Arguments
exit $LASTEXITCODE
