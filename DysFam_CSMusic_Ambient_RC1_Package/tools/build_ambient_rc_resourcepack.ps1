param(
    [string]$ZipPath = "C:\Users\Jaime\Downloads\DysFam Music OGG Files.zip"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression

$PackageRoot = Split-Path -Parent $PSScriptRoot
$ManifestPath = Join-Path $PackageRoot "manifest\ambient_rc_assets.csv"
$TemplateRoot = Join-Path $PackageRoot "resourcepack_template"
$BuildRoot = Join-Path $PackageRoot "build_output\DysFam_CSMusic_Ambient_RC1_ResourcePack"
$ZipOut = Join-Path $PackageRoot "build_output\DysFam_CSMusic_Ambient_RC1_ResourcePack.zip"

if (-not (Test-Path -LiteralPath $ZipPath)) {
    throw "Final OGG ZIP not found: $ZipPath"
}
if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Manifest not found: $ManifestPath"
}

if (Test-Path -LiteralPath $BuildRoot) {
    Remove-Item -LiteralPath $BuildRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $BuildRoot | Out-Null
Copy-Item -LiteralPath (Join-Path $TemplateRoot "pack.mcmeta") -Destination $BuildRoot
Copy-Item -LiteralPath (Join-Path $TemplateRoot "assets") -Destination $BuildRoot -Recurse

$rows = Import-Csv -LiteralPath $ManifestPath
$zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)

try {
    $lookup = @{}
    foreach ($entry in $zip.Entries) {
        $lookup[$entry.FullName] = $entry
    }

    $copied = 0
    $missing = New-Object System.Collections.Generic.List[string]

    foreach ($row in $rows) {
        $source = $row.Source_ZIP_Path
        if (-not $lookup.ContainsKey($source)) {
            $missing.Add($source)
            continue
        }

        $destRel = $row.Destination_OGG_Path -replace '/', '\'
        $destination = Join-Path $BuildRoot $destRel
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
        $copied++
    }

    Write-Host ""
    Write-Host "Copied $copied of $($rows.Count) ambient OGG files."

    if ($missing.Count -gt 0) {
        Write-Host ""
        Write-Warning "$($missing.Count) source files were not found in the final OGG ZIP:"
        $missing | ForEach-Object { Write-Host "  $_" }
        throw "Resource pack build stopped because source files are missing."
    }
}
finally {
    $zip.Dispose()
}

if (Test-Path -LiteralPath $ZipOut) {
    Remove-Item -LiteralPath $ZipOut -Force
}
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $BuildRoot,
    $ZipOut,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

Write-Host ""
Write-Host "SUCCESS"
Write-Host "Resource pack folder:"
Write-Host "  $BuildRoot"
Write-Host "Resource pack ZIP:"
Write-Host "  $ZipOut"
