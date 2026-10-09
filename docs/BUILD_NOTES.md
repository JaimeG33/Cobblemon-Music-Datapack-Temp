# Build Notes

## Critical datapack ZIP rule

Use the current `DysFam_CSMusic_Ambient_RC1_Package/tools/build_csmusic_rc4_datapack.ps1` and matching RC4 resource-pack builder. Historical RC2/RC3 builders remain in their branches and are unchanged; rebuild historical releases from their respective branches because the active source/manifest is cumulative.

A previous Windows ZIP had entries like:

`data\dysfam_music\csmusic\...`

Minecraft recognized `pack.mcmeta`, but CobbleSafari could not discover the CSMusic files. The permanent builder explicitly converts every entry to `/` paths and validates that zero backslashes remain.

## Historical RC2 counts

- 268 ambient sound events
- 18 generic battle audio segment events
- 286 resource sound events total
- 277 DysFam CSMusic track definitions (268 ambient + 9 battle)
- 1,016 generated base-species wild battle rules

The full species expansion does not add new OGG files. The resource pack only needs a rebuild because its RC2 description is updated from Prototype to Full.
## RC2 finalized baseline

RC2 generic wild battles are now the known-good baseline for future releases.

Future releases should preserve:

- all 1,016 generic base-species rules;
- priority 50 for generic wild battles;
- the forward-slash-safe datapack builder;
- ambient `battle: "never"` behavior.

Do not modify the generic battle layer when adding weather/village/structure music unless a regression requires it.

## RC4 cumulative build

RC4 adds 127 village tracks/events and 40 trigger rules while retaining RC1–RC3. Counts are 407 project tracks / 1,306 rules / 16 trigger files / 416 events and OGGs. CobbleSafari 0.3.4 defaults add 6 tracks / 4 rules / 3 files: expected runtime 413 / 1,310 / 19.

Run the two dedicated RC4 PowerShell builders; they write only RC4 output paths. The resource builder checks 416 manifest rows, source OGG headers and event/path agreement, then generates `sounds.json`. The datapack builder calculates and checks source counts before packaging. Both retain the forward-slash ZIP fix.

`tools/generate_csmusic_rc4.py` reproduces the approved source from the original workbook and inventory, using commit `dc15892` for the preserved RC3 manifest and Kitakami definition. It is scoped to RC4 and refuses unexpected manifest layers. `tools/validate_csmusic_rc4.py` compares runtime data and manifest records against that commit, checks workbook pools and installed structure resources, validates source/archive audio and evaluates a selection matrix. `tools/ValidateRc4Schema.java` checks the actual installed DTO, time-range and piece-pattern classes with Gson 2.11.0.

See [RC4 testing](RC4_VILLAGE_TESTING.md) for commands, artifact hashes, static results, installation and manual QA. Generated audio, ZIPs, Java classes and machine validation reports stay under ignored `build_output/`.
