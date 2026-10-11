param(
    [ValidateSet('setup','audit','prepare','dry-run','smoke','structure','regression','capture','self-test',
                 'quick','representative','diagnostic','exhaustive','audio-devices','audio-capture','audio-identify','audio-benchmark','recover')]
    [string]$Mode = 'audit',
    [string]$Case = 'pallet_town',
    [int]$Duration = 30,
    [Nullable[int]]$DeviceIndex,
    [string]$Selection = 'dysfam_music:villages_lgpe_pallet_town',
    [string]$NegativeSelection = 'dysfam_music:villages_lgpe_lavender_town',
    [string]$Recording,
    [string]$RecoverReport,
    [switch]$Audio
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
    $HarnessMode = $Mode
    if ($Mode -eq 'recover') { $HarnessMode = 'capture' }
    $Arguments = @((Join-Path $PSScriptRoot 'harness.py'), $HarnessMode, '--case', $Case)
    if ($Mode -like 'audio-*') {
        $Arguments += @('--duration', $Duration, '--selection', $Selection, '--negative-selection', $NegativeSelection)
        if ($PSBoundParameters.ContainsKey('DeviceIndex')) { $Arguments += @('--device-index', $DeviceIndex.Value) }
        if ($Recording) { $Arguments += @('--recording', $Recording) }
    }
    if ($Audio) { $Arguments += '--audio' }
    if ($RecoverReport) { $Arguments += @('--recover-report', $RecoverReport) }
    & $TestPython @Arguments
}
exit $LASTEXITCODE
