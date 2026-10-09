param(
    [string]$Repo = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

$ErrorActionPreference = "Stop"

$Package = Join-Path $Repo "DysFam_CSMusic_Ambient_RC1_Package"
$OutDir = Join-Path $Package "build_output"
$OutZip = Join-Path $OutDir "DysFam_CSMusic_RC3_Datapack.zip"
$Pack = Join-Path $Repo "pack.mcmeta"
$null = Get-Content -LiteralPath $Pack -Raw | ConvertFrom-Json
$Data = Join-Path $Repo "data"

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
if (Test-Path $OutZip) { Remove-Item $OutZip -Force }

$stream = [System.IO.File]::Open($OutZip,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::ReadWrite,[System.IO.FileShare]::None)

try {
    $zip = New-Object System.IO.Compression.ZipArchive($stream,[System.IO.Compression.ZipArchiveMode]::Create,$false)
    try {
        function Add-ZipFile([string]$Source,[string]$EntryName) {
            if ($EntryName -match '\\') { throw "Backslash in ZIP path: $EntryName" }
            $entry = $zip.CreateEntry($EntryName,[System.IO.Compression.CompressionLevel]::Optimal)
            $input = [System.IO.File]::OpenRead($Source)
            try {
                $output = $entry.Open()
                try { $input.CopyTo($output) } finally { $output.Dispose() }
            } finally { $input.Dispose() }
        }

        Add-ZipFile $Pack "pack.mcmeta"

        Get-ChildItem $Data -Recurse -File | ForEach-Object {
            $rel = $_.FullName.Substring($Data.Length).TrimStart('\','/')
            Add-ZipFile $_.FullName ("data/" + ($rel -replace '\\','/'))
        }
    }
    finally { $zip.Dispose() }
}
finally { $stream.Dispose() }

$check = [System.IO.Compression.ZipFile]::OpenRead($OutZip)
try {
    $names = @($check.Entries | ForEach-Object FullName)

    $required = @(
        "pack.mcmeta",
        "data/dysfam_music/csmusic/definition/weather.json",
        "data/dysfam_music/csmusic/weather_oras_heavy_rain.json",
        "data/dysfam_music/csmusic/weather_nps_shiver_snowfields_day.json",
        "data/dysfam_music/csmusic/weather_nps_shiver_snowfields_night.json",
        "data/dysfam_music/csmusic/definition/battle_default_gen1.json",
        "data/dysfam_music/csmusic/definition/battle_default_gen9.json",
        "data/dysfam_music/function/check.mcfunction",
        "data/minecraft/tags/function/load.json",
        "data/minecraft/tags/function/tick.json"
    )

    foreach ($r in $required) {
        if ($names -notcontains $r) { throw "ZIP missing $r" }
    }

    $bad = @($names | Where-Object { $_ -match '\\' })
    if ($bad.Count -gt 0) { throw "ZIP contains $($bad.Count) backslash path(s)." }

    Write-Host "ZIP validation passed."
    Write-Host "Entries: $($names.Count)"
    Write-Host "Backslashes: 0"
}
finally { $check.Dispose() }

Write-Host "SUCCESS"
Write-Host $OutZip
Write-Host "SHA256: $((Get-FileHash $OutZip -Algorithm SHA256).Hash)"
