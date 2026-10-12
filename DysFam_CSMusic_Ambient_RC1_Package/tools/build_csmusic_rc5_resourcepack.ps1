param(
    [string]$ZipPath = 'D:/Minecraft Stuff/Minecraft Datapacks/CSMusic Sources/DysFam Music OGG Files.zip'
)
$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'build_csmusic_rc5.py') resourcepack --audio $ZipPath
if ($LASTEXITCODE -ne 0) { throw 'RC5 resource pack build failed.' }
