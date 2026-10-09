# RC4 implementation proposal — review before implementation

Research completed 2026-10-09. No RC4 runtime files, builds or installations have been made. This proposal uses the authoritative Villages sheet, the [exact structure map](RC4_STRUCTURE_MUSIC_MAP.md), and [audio inventory](RC4_AUDIO_INVENTORY.md).

## Decisions before implementation

1. **Twinleaf:** workbook I25 names one track, while the source archive supplies Day and Night. Recommend time-based Day/Night assignments, consistent with the existing 0–12000 / 12000–24000 convention. Selecting one version for all times is also possible. The counts below assume both.
2. **Nonlegendary traditional village:** no assignment exists in the Villages sheet. Recommend leaving it on ambient; explicitly extend Ecruteak music to it only if requested. This need not block RC4 if we follow the source as written.

Pokémon Tower can preserve village priority 30 through deliberate rule ordering in CobbleSafari 0.3.4. No priority change is needed. Original CobbleTowns repairs and required-pack policy are separate changes requiring user review; village music can be tested with the already enabled pack despite its documented loot defect.

## Expected runtime files

Use repository-root `data/dysfam_music/csmusic/` as the source and mirror every change to `DysFam_CSMusic_Ambient_RC1_Package/datapack/data/dysfam_music/csmusic/`.

| Proposed change | Contents |
|---|---|
| `definition/villages_generic.json` | 30 rules: two time windows for each of 13 BCA and two Terralith structures |
| `definition/villages_cobbletowns.json` | 9 rules: tower, six towns with one song each, Twinleaf day/night |
| `definition/villages_legendary_monuments.json` | 1 exact Ecruteak rule |
| `villages_<normalized_song>.json` | 127 new track definitions using inventory IDs and exact loop events |
| Existing `villages_sv_kitakami.json` | Append `village_magic_night`; retain existing `underground_lush` tag |
| Cumulative `manifest/csmusic_release_assets.csv` | Append 127 rows; preserve all 289 RC3 rows; `full_loop`, village layer, `RC4` |
| Root and mirrored `pack.mcmeta` | Update cumulative release description; retain Minecraft 1.21.1 datapack format |
| Resource template `pack.mcmeta` | Update release description; retain appropriate resource pack format |
| New RC4 builders in package `tools/` | Adapt forward-slash-safe RC3 builders; separate RC4 output names and expected counts |
| Release/build/testing docs | Record new counts and gameplay results after implementation |

Track definitions use `loop` and `tags`; pool rules use `tag`. Named location rules use `music`. Every rule uses `priority: 30`, `dimension: "minecraft:overworld"` and `battle: "never"`. `structure` and `structure_piece` are scalar strings; `time_range` is a two-element integer array. There is no supported radius, structure-list, negated-piece or specificity field in the inspected schema.

Proposed generic rule, using actual supported fields:

```json
{
  "tag": "village_basic_day",
  "priority": 30,
  "when": {
    "dimension": "minecraft:overworld",
    "battle": "never",
    "structure": "bca:village/default_small",
    "time_range": [0, 12000]
  }
}
```

## Tower and overlap precedence

In `villages_cobbletowns.json`, put the exact Lavender Tower piece rule at index 0 and the Lavender Town rule at index 1. Both have priority 30. The tower rule additionally requires parent `cobbletowns:lavender_town` and piece `cobbletowns:lavender_town/buildings/pokemon_tower`.

The installed manager sorts matching sources by descending priority, then ascending source key. The loader derives that key from the trigger-file identifier and rule index. These two rules in the same file therefore produce deterministic tower-first ordering. Keep both indices fixed and verify them during QA. This is explicit ordering, not an automatic preference for the narrower condition. Avoid later reordering that changes these keys. If a future implementation uses multiple files, their names also affect equal-priority ordering.

All proposed village files have stable names. Any unexpected overlap between settlements should be recorded using diagnostics; equal-priority choice follows the source key and does not merge pools. RC5 center/mart priority 42 and RC6 special structure priority 41 will supersede village 30 when implemented. Weather 40 and wild battle 50 retain their current behavior; ordinary rain adds no RC3 override.

## Count expectations

| Metric | RC3 repository | Proposed RC4 repository | Installed runtime including unchanged CobbleSafari defaults |
|---|---:|---:|---:|
| Track definitions | 280 | 407 | 413 |
| Rules | 1,266 | 1,306 | 1,310 |
| Trigger files | 13 | 16 | 19 |
| DysFam sound events / OGGs | 289 | 416 | 416 DysFam events; bundled mod sounds separate |

These counts assume both Twinleaf tracks, no nonlegendary rule, one tower rule and exactly three new trigger files. Selecting one Twinleaf track gives 406 repository tracks, 1,305 rules, 415 events, and runtime totals 412 tracks / 1,309 rules / 19 files. An added nonlegendary assignment changes rule counts; use an existing track if the user chooses Ecruteak for it.

## Build commands after review and implementation

Create dedicated RC4 scripts first; these commands are proposed and have **not** been run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\DysFam_CSMusic_Ambient_RC1_Package\tools\build_csmusic_rc4_datapack.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\DysFam_CSMusic_Ambient_RC1_Package\tools\build_csmusic_rc4_resourcepack.ps1" -ZipPath "C:\Users\Jaime\Downloads\DysFam Music OGG Files.zip"
```

Expected outputs are `build_output/DysFam_CSMusic_RC4_Datapack.zip` and `build_output/DysFam_CSMusic_RC4_ResourcePack.zip` under the existing package. RC3 outputs must remain usable; do not run an RC3 script against the expanded manifest, whose existing 289-row assertion will reject it. Generate `sounds.json` from the cumulative manifest as the working RC3 builder does, rather than relying on the old template sound list.

## Required build validation

- Preserve all 1,016 generic species rules at priority 50 and all ambient/weather trigger files byte-for-byte. The Kitakami definition changes only by adding its village tag.
- Verify exact root/mirror file parity, including metadata, and valid JSON for every new file.
- Compare song memberships with the workbook ranges and research inventory. One definition per unique track; shared tracks get multiple tags; no empty pool or accidental duplicate definition/event/path.
- Ensure every rule resolves to an existing track or nonempty pool. Validate exact structure IDs against archives and template IDs against actual pool `location` values, without broad village tags.
- Ensure each manifest source exists and begins with an OGG header, all generated events resolve to packaged OGGs, and stream flags are retained.
- Validate both ZIPs independently: root `pack.mcmeta`, no backslashes, correct entry counts, required cumulative files, parseable `sounds.json`, matching hashes/content and SHA256 release hashes.
- After load, check the log for the expected totals, zero rejected CSMusic files, unresolved IDs/tags/pools and missing sound errors. Treat the pre-existing Lentimas loot error separately and retain it in QA notes.

## Minimal gameplay QA

1. In the chosen test world, verify `/datapack list enabled`: one cumulative DysFam RC4 datapack plus intended CobbleTowns; enable only its matching resource pack. Restart after any worldgen activation change. Use newly generated locations when needed.
2. Test one basic BCA, one fighting, one dark, one fairy, one ice, both Terralith villages, and Ecruteak at ground level. Check day and night, with transitions at 11999/12000 and 23999/0; verify reported pool and song membership. Static archive checks cover the remaining size variants, with runtime spot checks as available.
3. Visit all seven named towns and confirm their exact assignments. Test Twinleaf day/night if approved. Pallet lab should retain Pallet Town until a future building override is added.
4. Enter Lavender Tower, leave into Lavender Town, then re-enter. Capture `/cobblesafari csmusic structures` and `/cobblesafari csmusic current` to prove the piece rule wins at priority 30 and the town rule resumes.
5. For a generic village and a named town, test center, edge, outside and above, recording X/Y/Z and bounds/piece fields. Music follows 3D generated bounds. If normal arbitration disagrees with diagnostics after travel, observe through a cache refresh before investigating.
6. Test ordinary rain, thunder, snow day/night in an ice village, wild battle during village music and battle during weather. Expect ambient 10 < village 30 < weather 40 < wild battle 50, with return to the currently matching condition after the override ends.

Rapid dimension-hopping overlap and GUI test automation remain deferred as requested.
