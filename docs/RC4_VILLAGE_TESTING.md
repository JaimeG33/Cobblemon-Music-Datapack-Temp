# RC4 Villages — Built / Awaiting Gameplay QA

Implemented and statically validated on 2026-10-09, on `rc4-villages` from RC3 commit `dc15892`. Both local release ZIPs are ready for manual installation. Minecraft was not launched or modified by this work; RC4 is not yet Complete / Working.

## Implemented behavior

- All 13 BCA villages: default/fighting use basic pools; dark/fairy use magic pools; ice uses cold pools.
- Terralith fortified village uses basic pools; fortified desert village uses hot pools.
- All seven CobbleTowns settlements use their workbook songs. Twinleaf uses Day/Night versions at ticks 0–11999 / 12000–23999.
- Ecruteak uses HGSS - Ecruteak City. The nonlegendary traditional village keeps ambient music.
- Lavender Town's Pokémon Tower uses LGPE - Pokemon Tower. Both tower and town remain priority 30; tower is index 0 and town index 1 in `villages_cobbletowns.json`.
- Pallet Town's laboratory keeps LGPE - Pallet Town. Center/mart overrides remain deferred to RC5.

All village rules require the Overworld and `battle: "never"`. Priority is ambient 10 < villages 30 < weather 40 < generic wild battles 50. Ordinary rain adds no weather override. The existing weather and 1,016 species battle rules are preserved.

See [exact structure map](RC4_STRUCTURE_MUSIC_MAP.md), [audio inventory](RC4_AUDIO_INVENTORY.md) and [original compatibility audit](RC4_DATAPACK_AUDIT.md).

## Release artifacts and hashes

Build-output directory:

`D:/Minecraft Stuff/Minecraft Datapacks/DysFam_CSMusic_Ambient_RC1_Datapack/DysFam_CSMusic_Ambient_RC1_Package/build_output/`

| File in that directory | Bytes | SHA256 |
|---|---:|---|
| `DysFam_CSMusic_RC4_Datapack.zip` | 136,888 | `5794C062C2664D6E92C68B398A28F5C08FF243D6A5809962E80D4F96E775E138` |
| `DysFam_CSMusic_RC4_ResourcePack.zip` | 1,113,810,492 | `B8E056EC48176AC2156359E2E9D868D4E05A0DC1A1A38DA846525F31E20D939F` |

The resource pack is approximately 1.04 GiB. These hashes identify this local build; regenerated ZIPs can have different entry timestamps and therefore different hashes. RC3 builders and existing RC3 release outputs were not overwritten. Build outputs, extracted audio and the external source archive are excluded from Git.

## Independently calculated counts

| Metric | DysFam RC4 | Installed total with unchanged CobbleSafari 0.3.4 defaults |
|---|---:|---:|
| Music definitions | 407 | 413 |
| Trigger rules | 1,306 | 1,310 |
| Trigger files | 16 | 19 |
| DysFam sound events / OGGs | 416 | 416 DysFam events / OGGs; mod sounds separate |

RC4 adds 127 tracks/events and 40 village rules. Kitakami is reused with `village_magic_night` appended to its existing `underground_lush` tag. Pool sizes: basic 35 day / 29 night, magic 15 / 16, cold 12 / 7, hot 9 / 8.

## Static validation completed

- Both dedicated PowerShell builders completed and passed their ZIP checks. Datapack has 432 entries; resource pack has 418 entries. Every path uses forward slashes and each archive has root `pack.mcmeta`.
- All JSON parsed with duplicate-key rejection. The actual installed CobbleSafari trigger DTO deserialized all 16 files / 1,306 rules using Gson 2.11.0.
- The actual `CsMusicTimeRange` passed 128 checks at 0, 11999, 12000 and 23999 across the 32 village time-window rules. The actual piece-pattern class included the tower template and excluded Lavender's center.
- Every village structure and the tower template/pool location resolves in the installed archives. No broad village tags or unsupported condition fields were introduced.
- Pool memberships and named assignments match the original Villages sheet, with the documented spelling translations, ignored D32 typo and approved Twinleaf expansion.
- All 289 RC3 manifest rows match baseline records. All 299 otherwise unchanged root data files match RC3 after Git line-ending normalization. Kitakami has only its approved tag addition; the status function only updates declared release/count information. All 1,016 unique battle species rules remain intact at priority 50.
- Root and historical mirror file sets and bytes match, including metadata. The actual datapack ZIP matches those source bytes.
- Both ZIPs passed complete CRC checks. All 416 packaged OGGs have OGG/Vorbis identification headers and exactly match their authoritative source ZIP bytes. Every event and every track sound reference resolves; no duplicate IDs/events/paths or empty referenced pools were found.
- FFmpeg fully decoded 18 audio samples without errors: one per generic day/night pool, all named settlement/Ecruteak assignments, both Twinleaf files and Pokémon Tower. Other tracks were checked by source equality, headers and ZIP CRC rather than full decoding.
- Installed bytecode confirmed descending priority then ascending source key. The loader's key recipe is `definition:<file path>#<index>`; tower index 0 sorts before town index 1. An independent model passed 448 dimension/battle/weather/time/structure combinations, including tower precedence, Twinleaf boundaries and nonlegendary ambient fallback. This is static evidence; it does not simulate Minecraft chunk loading or audio playback.

The local machine-readable report is `build_output/RC4_STATIC_VALIDATION.json`. The installed CobbleSafari JAR SHA256 is `B773074B7C66C4A92646B038D366FAFBBEF7750133B8615BCEB462E61EF0F008`.

## Source changes

| New or modified source | Change |
|---|---|
| `data/dysfam_music/csmusic/definition/villages_generic.json` | New 30 generic village rules |
| `data/dysfam_music/csmusic/definition/villages_cobbletowns.json` | New 9 town/tower rules; fixed tower/town indices |
| `data/dysfam_music/csmusic/definition/villages_legendary_monuments.json` | New Ecruteak rule |
| `data/dysfam_music/csmusic/villages_*.json` | 127 new definitions; exact filenames follow the track-ID column in the inventory CSV |
| `data/dysfam_music/csmusic/villages_sv_kitakami.json` | Preserve original loop/tags and add village tag |
| `data/dysfam_music/function/check.mcfunction` | RC4 expected status/counts |
| Root `pack.mcmeta` | RC4 QA description; datapack format remains 48 |
| Historical package `datapack/` | Mirror every runtime-source change above |
| Package `manifest/csmusic_release_assets.csv` | Append 127 rows; preserve all existing records |
| Package `resourcepack_template/pack.mcmeta` | RC4 QA description; resource format remains 34 |
| Package `tools/build_csmusic_rc4_datapack.ps1`, `build_csmusic_rc4_resourcepack.ps1` | New dedicated cumulative builders |
| Package `tools/generate_csmusic_rc4.py`, `validate_csmusic_rc4.py`, `ValidateRc4Schema.java` | Reproduction, regression/archive/workbook checks, installed-class schema checks |
| README and release/build/research/testing documentation | Current status, approved decisions and QA results |

The original manifest row for Kitakami retains its historical `Pool_Tags` value to preserve RC3 records; the playable JSON definition owns the added village tag. New manifest rows record their generic village tags. Named tracks need no pool tag because their rules select `music` directly.

## Rebuild and validate

From repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\DysFam_CSMusic_Ambient_RC1_Package\tools\build_csmusic_rc4_datapack.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\DysFam_CSMusic_Ambient_RC1_Package\tools\build_csmusic_rc4_resourcepack.ps1"
python .\DysFam_CSMusic_Ambient_RC1_Package\tools\validate_csmusic_rc4.py --report .\DysFam_CSMusic_Ambient_RC1_Package\build_output\RC4_STATIC_VALIDATION.json
```

The resource builder defaults to `C:/Users/Jaime/Downloads/DysFam Music OGG Files.zip`; use `-ZipPath` for another location. The Python validator supports `--repo`, `--workbook`, `--audio`, `--profile` and optional `--ffmpeg`. The validation above used FFmpeg at `D:/Minecraft Stuff/ModrinthApp/profiles/Cobblemon Freedom Frontiers/config/trueadaptivemusic/ffmpeg_binaries/ffmpeg.exe`; passing that path reproduces full decoding of the same 18 samples. Without `--ffmpeg`, the report explicitly contains an empty decoded-sample list.

Installed-class checks with Java 21 (adjust library paths if moved):

```powershell
$rc4ClassPath = "D:\Minecraft Stuff\ModrinthApp\profiles\DysFam Cobblemon 2.0 6.0.0\mods\cobblesafari-fabric-1.21.1-0.3.4.jar;D:\Minecraft Stuff\ModrinthApp\meta\libraries\com\google\code\gson\gson\2.11.0\gson-2.11.0.jar"
javac -cp $rc4ClassPath -d ".\DysFam_CSMusic_Ambient_RC1_Package\build_output\schema_check" ".\DysFam_CSMusic_Ambient_RC1_Package\tools\ValidateRc4Schema.java"
java -cp ".\DysFam_CSMusic_Ambient_RC1_Package\build_output\schema_check;$rc4ClassPath" ValidateRc4Schema ".\data\dysfam_music\csmusic\definition"
```

## Manual installation

1. Exit the test world. Keep the old RC3 ZIPs as backups. Copy the RC4 datapack ZIP, still zipped, into the chosen test world's `datapacks/` folder. Copy the RC4 resource ZIP into the profile's `resourcepacks/` folder.
2. In Minecraft Resource Packs, enable the RC4 resource pack and disable older DysFam/ToaRex music resource packs. Keep unrelated resource packs and world-generation datapacks enabled.
3. Load the world and check available/enabled datapacks. Disable only the old CSMusic datapack and enable RC4 if it did not enable automatically:

```mcfunction
/datapack list available
/datapack list enabled
/datapack disable "file/DysFam_CSMusic_RC3_Datapack.zip"
/datapack enable "file/DysFam_CSMusic_RC4_Datapack.zip"
/reload
/function dysfam_music:check
/cobblesafari csmusic list
/cobblesafari csmusic current
```

Use the exact old ID from `/datapack list enabled` if testing a world with RC2 or a differently named older music pack. Keep CobbleTowns, BCA, Terralith and Legendary Monuments enabled. Do not use a blanket disable command. Check the load log for **413 definitions, 1,310 rules, 19 files**, zero skipped definitions and zero rejected CSMusic files.

CobbleTowns is already enabled in the researched RC3 test save. In another world, verify its selection first; if changing worldgen activation, restart the world before locating towns and use unexplored locations. Enabling worldgen does not regenerate already explored chunks.

## Essential gameplay checks

Use `/weather clear` first so priority-40 weather does not mask village music. At each ground-level location, run:

```mcfunction
/cobblesafari csmusic structures
/cobblesafari csmusic current
```

Require bounds containment, and piece containment for the tower; a structure merely listed nearby is insufficient. Record XYZ including Y if a result is unexpected. Allow normal arbitration/crossfade time.

1. **Generic categories:** visit BCA default, dark or fairy, ice, and both Terralith fortified villages. Confirm basic, magic, cold and hot pool selection during day/night. Fighting shares basic; fairy/dark share magic. Use `/time set 11999`, `12000`, `23999`, `0` to check both boundaries in one representative generic village.
2. **Named music:** confirm Pallet, Lavender, Cherrygrove, Pacifidlog, Floaroma, Lentimas and Ecruteak songs against the structure map. The Pallet laboratory must still play Pallet Town. Nonlegendary traditional villages must fall back to ambient in clear weather.
3. **Twinleaf:** check its Day track at 0 and 11999, Night at 12000 and 23999, then return to 0. This is the main named-town boundary check.
4. **Pokémon Tower:** enter the tower, exit into Lavender Town, then re-enter. Expect tower track → Lavender Town track → tower track, all at priority 30. Capture the exact piece ID and `current` output.
5. **Bounds:** test center, edge, outside and above one village. Expect village music only while inside the generated 3D bounds; outside/above should return to the applicable ambient/weather music.
6. **Weather and battle:** in a village, ordinary rain retains village music; thunder selects Heavy Rain. In an ice village, local snow selects RC3 Snow Day/Night. Start a wild battle while village music plays, then while weather plays. Expect priority-50 generation battle music, followed by the currently matching village/weather track after battle. Clear weather should restore village music while still inside bounds.
7. **Regression:** check one ordinary ambient area and one generation battle outside a village. No village rule should match in Nether/End.

Useful locate commands (substitute another confirmed size variant as needed):

```mcfunction
/locate structure bca:village/default_small
/locate structure bca:village/dark_small
/locate structure bca:village/ice_small
/locate structure terralith:fortified_village
/locate structure terralith:fortified_desert_village
/locate structure legendarymonuments:traditional_village/ecruteak
/locate structure legendarymonuments:traditional_village/nonlegendary
/locate structure cobbletowns:pallet_town
/locate structure cobbletowns:lavender_town
/locate structure cobbletowns:cherrygrove_city
/locate structure cobbletowns:pacifidlog_town
/locate structure cobbletowns:twinleaf_town
/locate structure cobbletowns:floaroma_town
/locate structure cobbletowns:lentimas_town
```

Choose a safe ground-level Y when traveling to a locate result; flying above a town can fail its bounds check.

## Optional exhaustive checks and known limitations

Optional: visit all BCA size variants, test both dark and fairy plus fighting villages, repeat weather/battle transitions in several named towns, and listen through additional tracks in each pool. The static checks cover all IDs and pool memberships; manual QA need not wait through every song to establish selection.

The original CobbleTowns metadata inconsistency/trailing `z` and Lentimas `minecraft:grass` loot-table defect were left untouched. A pre-existing loot error is distinct from a new CSMusic rejection. Village containment remains a 3D generated bounding-box test with the existing 600-tick structure cache; this release adds no proximity radius. Diagnostics inspect separately from normal cached arbitration, so record discrepancies and observe through a cache refresh if needed.

No center/mart overrides, rapid dimension-hopping fix or GUI automation were added. RC4 can be marked Complete / Working only after the user confirms the essential gameplay checks.
