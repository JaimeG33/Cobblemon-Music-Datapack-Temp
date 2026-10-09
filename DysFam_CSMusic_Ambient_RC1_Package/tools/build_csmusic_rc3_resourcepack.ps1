param(
    [string]$ZipPath = "C:\Users\Jaime\Downloads\DysFam Music OGG Files.zip"
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

# -------------------------------------------------------------------------
# CSMusic RC3 Cumulative Resource Pack Builder
#
# Builds all RC3 assets from csmusic_release_assets.csv with validated ZIP paths.

$PackageRoot = Split-Path -Parent $PSScriptRoot
$ManifestPath = Join-Path $PackageRoot "manifest\csmusic_release_assets.csv"
$TemplateRoot = Join-Path $PackageRoot "resourcepack_template"

$BuildRoot = Join-Path $PackageRoot "build_output\DysFam_CSMusic_RC3_ResourcePack"
$ZipOut = Join-Path $PackageRoot "build_output\DysFam_CSMusic_RC3_ResourcePack.zip"

$PackMcmetaSource = Join-Path $TemplateRoot "pack.mcmeta"

if (-not (Test-Path -LiteralPath $ZipPath)) {
    throw "Final OGG ZIP not found: $ZipPath"
}
if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Manifest not found: $ManifestPath"
}
if (-not (Test-Path -LiteralPath $PackMcmetaSource)) {
    throw "pack.mcmeta not found: $PackMcmetaSource"
}

$rows = @(Import-Csv -LiteralPath $ManifestPath)
if ($rows.Count -eq 0) {
    throw "Manifest is empty: $ManifestPath"
}

if ($rows.Count -ne 289) { throw "RC3 requires 289 manifest rows." }
$null = Get-Content -LiteralPath $PackMcmetaSource -Raw | ConvertFrom-Json
# Verify the recursive cleanup target is exactly the intended build folder.
$expectedBuildRoot = [IO.Path]::GetFullPath((Join-Path $PackageRoot "build_output\DysFam_CSMusic_RC3_ResourcePack"))
if ([IO.Path]::GetFullPath($BuildRoot) -ne $expectedBuildRoot) { throw "Unexpected build cleanup path." }
if ((Test-Path -LiteralPath $BuildRoot) -and ((Get-Item -LiteralPath $BuildRoot).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Build directory must not be a link." }
# Start from a completely clean folder.
if (Test-Path -LiteralPath $BuildRoot) {
    Remove-Item -LiteralPath $BuildRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $BuildRoot | Out-Null

# Only copy pack.mcmeta from the old template.
Copy-Item -LiteralPath $PackMcmetaSource -Destination (Join-Path $BuildRoot "pack.mcmeta")

# Open the authoritative OGG library ZIP.
$sourceZip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)

try {
    $lookup = @{}
    foreach ($entry in $sourceZip.Entries) {
        # Source manifest paths use standard ZIP forward slashes.
        $lookup[$entry.FullName] = $entry
    }

    $copied = 0
    $missing = New-Object System.Collections.Generic.List[string]
    $eventDefs = [ordered]@{}
    $expectedZipEntries = New-Object System.Collections.Generic.List[string]

    foreach ($row in $rows) {
        $source = [string]$row.Source_ZIP_Path
        $destRel = ([string]$row.Destination_OGG_Path) -replace '\\', '/'
        $destRel = $destRel.TrimStart('/')

        if ([string]::IsNullOrWhiteSpace($source)) {
            throw "Manifest row has an empty Source_ZIP_Path."
        }
        if ([string]::IsNullOrWhiteSpace($destRel)) {
            throw "Manifest row has an empty Destination_OGG_Path."
        }

        # Destination must be a Minecraft resource path in our namespace.
        $prefix = "assets/dysfam_music/sounds/"
        if (-not $destRel.StartsWith($prefix, [System.StringComparison]::Ordinal)) {
            throw "Unexpected destination path in manifest: $destRel"
        }
        if (-not $destRel.EndsWith(".ogg", [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Destination is not an OGG file: $destRel"
        }

        if (-not $lookup.ContainsKey($source)) {
            $missing.Add($source)
            continue
        }

        # Write the OGG into the clean build folder.
        $windowsDestRel = $destRel -replace '/', '\'
        $destination = Join-Path $BuildRoot $windowsDestRel
        $parent = Split-Path -Parent $destination
        New-Item -ItemType Directory -Force -Path $parent | Out-Null

        $inputStream = $lookup[$source].Open()
        try {
            $outputStream = [System.IO.File]::Create($destination)
            try {
                $inputStream.CopyTo($outputStream)
            }
            finally {
                $outputStream.Dispose()
            }
        }
        finally {
            $inputStream.Dispose()
        }

        # Derive the Minecraft sound event from the destination path.
        # Example:
        # assets/dysfam_music/sounds/music/biomes/xy_route_2.ogg
        # -> event key: music/biomes/xy_route_2
        $eventPath = $destRel.Substring($prefix.Length)
        $eventPath = $eventPath.Substring(0, $eventPath.Length - 4)

        if ($eventDefs.Contains($eventPath)) {
            throw "Duplicate generated sound event: $eventPath"
        }

        $eventDefs[$eventPath] = [ordered]@{
            sounds = @(
                [ordered]@{
                    name   = "dysfam_music:$eventPath"
                    stream = $true
                }
            )
        }

        $expectedZipEntries.Add($destRel)
        $copied++
    }

    Write-Host ""
    Write-Host "Copied $copied of $($rows.Count) cumulative OGG files."

    if ($missing.Count -gt 0) {
        Write-Host ""
        Write-Warning "$($missing.Count) source files were not found in the final OGG ZIP:"
        $missing | ForEach-Object { Write-Host "  $_" }
        throw "Resource pack build stopped because source files are missing."
    }

    if ($copied -ne $rows.Count) {
        throw "Copied OGG count does not match manifest count."
    }

    # Recreate sounds.json from scratch, matching the format of the working
    # two-track debug resource pack.
    $soundsDir = Join-Path $BuildRoot "assets\dysfam_music"
    New-Item -ItemType Directory -Force -Path $soundsDir | Out-Null

    $soundsJsonPath = Join-Path $soundsDir "sounds.json"
    $jsonText = $eventDefs | ConvertTo-Json -Depth 8

    # Important: UTF-8 without BOM.
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($soundsJsonPath, $jsonText, $utf8NoBom)

    # Confirm the generated JSON can be parsed again.
    $null = Get-Content -LiteralPath $soundsJsonPath -Raw | ConvertFrom-Json

    Write-Host "Generated $($eventDefs.Count) sound events."
}
finally {
    $sourceZip.Dispose()
}

# -------------------------------------------------------------------------
# Create the finished ZIP explicitly, entry-by-entry.
# Do NOT use Compress-Archive or CreateFromDirectory here.
# Every archive entry is normalized to Minecraft-style forward slashes.
# -------------------------------------------------------------------------

if (Test-Path -LiteralPath $ZipOut) {
    Remove-Item -LiteralPath $ZipOut -Force
}

$outStream = [System.IO.File]::Open(
    $ZipOut,
    [System.IO.FileMode]::CreateNew,
    [System.IO.FileAccess]::ReadWrite,
    [System.IO.FileShare]::None
)

try {
    $outZip = New-Object System.IO.Compression.ZipArchive(
        $outStream,
        [System.IO.Compression.ZipArchiveMode]::Create,
        $false
    )

    try {
        $files = Get-ChildItem -LiteralPath $BuildRoot -Recurse -File

        foreach ($file in $files) {
            $relative = $file.FullName.Substring($BuildRoot.Length).TrimStart('\', '/')
            $entryName = $relative -replace '\\', '/'

            if ($entryName.Contains("\")) {
                throw "Backslash survived ZIP path normalization: $entryName"
            }

            $zipEntry = $outZip.CreateEntry(
                $entryName,
                [System.IO.Compression.CompressionLevel]::Optimal
            )

            $input = [System.IO.File]::OpenRead($file.FullName)
            try {
                $output = $zipEntry.Open()
                try {
                    $input.CopyTo($output)
                }
                finally {
                    $output.Dispose()
                }
            }
            finally {
                $input.Dispose()
            }
        }
    }
    finally {
        $outZip.Dispose()
    }
}
finally {
    $outStream.Dispose()
}

# -------------------------------------------------------------------------
# Validate the actual ZIP Minecraft will receive.
# -------------------------------------------------------------------------

$checkZip = [System.IO.Compression.ZipFile]::OpenRead($ZipOut)

try {
    $names = @($checkZip.Entries | ForEach-Object { $_.FullName })

    $badSeparators = @($names | Where-Object { $_ -match '\\' })
    if ($badSeparators.Count -gt 0) {
        throw "ZIP contains Windows-style backslash paths: $($badSeparators -join ', ')"
    }

    if ($names -notcontains "pack.mcmeta") {
        throw "ZIP validation failed: pack.mcmeta is missing from the ZIP root."
    }

    if ($names -notcontains "assets/dysfam_music/sounds.json") {
        throw "ZIP validation failed: assets/dysfam_music/sounds.json is missing."
    }

    foreach ($expected in $expectedZipEntries) {
        if ($names -notcontains $expected) {
            throw "ZIP validation failed: missing expected file $expected"
        }
    }

    $oggCount = @($names | Where-Object { $_.EndsWith(".ogg", [System.StringComparison]::OrdinalIgnoreCase) }).Count
    if ($oggCount -ne $rows.Count) {
        throw "ZIP validation failed: expected $($rows.Count) OGGs, found $oggCount."
    }

    Write-Host ""
    Write-Host "ZIP validation passed."
    Write-Host "  Sound events: $($eventDefs.Count)"
    Write-Host "  OGG files:    $oggCount"
    Write-Host "  Backslashes:  0"
}
finally {
    $checkZip.Dispose()
}

$hash = Get-FileHash -LiteralPath $ZipOut -Algorithm SHA256

Write-Host ""
Write-Host "SUCCESS"
Write-Host "Resource pack folder:"
Write-Host "  $BuildRoot"
Write-Host "Resource pack ZIP:"
Write-Host "  $ZipOut"
Write-Host "SHA256:"
Write-Host "  $($hash.Hash)"
