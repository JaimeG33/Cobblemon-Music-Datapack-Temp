# RC5 structures research

Planning only, 2026-10-11. Baseline `codex/csmusic-test-harness` at `6a974fb509dcd58603cf17e7b7d54df48742dab5`. No gameplay, world edits, production edits or release builds performed. Archive verification does not establish runtime generation or containment.

## Sources and audit method

- Assignment authority: `C:/Users/Jaime/Downloads/CSMusic_Reference_Excel_Files/Music Pack Conditions & Music(2)_2.xlsx`, Structures. SHA256 `149a704b54b27ed608c6a988dbaa3708660c738e9675320dc4e9374d3e5e5143`.
- Historical companion: same directory, `DysFam_CSMusic_Master_Implementation_Mapping_v3(2)_2.xlsx`. Inspected sheet list and Known Structures A3:I8. It contains village/building diagnostics, not the final general-structure assignments. Its `bcavillage:default_small` shorthand is superseded by installed RC4 evidence. Do not import old statuses or priorities.
- Audio: `D:/Minecraft Stuff/Minecraft Datapacks/CSMusic Sources/DysFam Music OGG Files.zip`. The previous Downloads path is missing. Read ZIP directory and individual OGG headers only; no bulk extraction.
- Installed profile: `D:/Minecraft Stuff/ModrinthApp/profiles/DysFam Cobblemon 2.0 6.0.0`.
- Installed Minecraft data: `D:/Minecraft Stuff/ModrinthApp/meta/versions/1.21.1-0.19.3/1.21.1-0.19.3.jar`. The suffix denotes this cached launcher version; inspected resources are Minecraft 1.21.1. It is evidence for vanilla resources, not a claim about the active Fabric loader version.
- Read existing RC4 research, build notes, source definitions, release manifest, installed RC4 resource ZIP, and `testing/FINAL_GAMEPLAY_SESSION_RESULTS.md`.
- Read workbook OOXML directly, retaining cell addresses and labels. Mapping CSV is a research table, not a production manifest. Semicolon-separated piece IDs represent separate candidate rules, not supported JSON array syntax.

Primary evidence is installed archive content. Supplemental [Legendary Monuments author page](https://modrinth.com/mod/legendary-monuments) credits the towers, lakes, Snowpoint Temple and Spear Pillar, but currently describes a newer release; it cannot prove installed 8.1 IDs. No upstream names were substituted for missing installed IDs.

## Reconciled scope

| Measure | Result |
|---|---:|
| General condition cells in A/B/C/D/G | 47 |
| Music assignment blocks | 33 |
| Distinct song labels | 32 |
| A: verified whole-structure conditions | 38 |
| B: structure-piece cases | 5 |
| C: dimension/area-only cases established | 0 |
| D: unavailable/unresolved cases | 4 |
| Unique verified whole/parent structure IDs | 39 |
| Conditions with a verified whole/parent ID | 43 |
| Conditions already fully handled by RC4 music | 0 |

The 43 include three lake-interior rows whose parent ID is verified but whose interior detection is not. Two tower rows share Ecruteak's parent, and each inside/outside lake pair shares a parent. Hence 39 unique IDs, not 43 independent structures. Five B rows need runtime containment checks: two towers have exact template mappings; three lake interiors remain semantic candidates. One D row is explicitly future-version; three have unresolved provider/version. Six rows need deeper investigation (three lakes plus three missing landmarks); tower checks are routine validation rather than unknown IDs.

E3:E6 Pokecenters and F3:F6 shops are RC6 and excluded. Worksheet priority labels `4` do not replace technical priority 41. Original spellings are retained: `Ampitheater` C3, `Dragon Spiral Tower` C19, `Thalic Pyramid` A9, `Trial Chamber` A29. XY - Scary House appears in two assignment groups, explaining 33 groups versus 32 songs.

## Installed archives

All paths below are under profile `mods/`, except vanilla above.

| Archive | SHA256 |
|---|---|
| Cobblemon-fabric-1.7.3+1.21.1.jar | `f7c25955176badc444ad6211fc556514fedbdba776227f105fe899f8819d74e3` |
| legendarymonuments-fabric-1.21.1-8.1-Love_for_All.jar | `64c04db1d9757c52d2cc805cdc242688db8c3d837a17500593c5095b666783b3` |
| mega_showdown-fabric-1.9.5+1.7.3+1.21.1.jar | `69b1a0ed9c3a3910b894ec2ba798f5ec6663ac09b80fbb202654b20918a5f328` |
| Terralith_1.21.x_v2.6.2.jar | `9cd4d402fde0f523e5b430ac8fd479ce05aea7a50fe0c8c26901f5f769272214` |
| Minecraft cached client JAR | `499f6897d1837516680f3114072d8106e11c9adcd933fe5cf051b551089b0c99` |

Targeted scan of 211 enabled-extension mod JARs, 49 profile ZIPs and four saved-world ZIPs found no duplicate root definitions of the mapped structure resources. All 31 mod parent resources plus eight vanilla resources were found. This checks root archive resources, not arbitrary Java registration, nested optional packs, loose world folders, or live pack ordering. Existing final gameplay report records relevant mod packs and Terralith custom structures enabled; recheck the chosen world after approval.

## Exact mapping and unusual cases

The complete 47-row [mapping](RC5_STRUCTURES_MAPPING.csv) is authoritative for this research. Each row includes original condition/music cells, exact audio member and CRC, registration state, IDs, dimension, evidence, compatibility and blocker.

### Vanilla and dimension distinctions

Use `minecraft:bastion_remnant`, `desert_pyramid`, `jungle_pyramid`, `end_city`, `mansion`, `fortress`, `stronghold`, `trial_chambers` (namespace repeated as needed). Resource names are not always display names: woodland mansion is `mansion`, not `woodland_mansion`; trial chambers is plural.

Thalic Pyramid is `legendarymonuments:thalic_pyramid`, despite being listed in the Vanilla column. Its biome `legendarymonuments:plains_of_death` is injected into **Overworld**, verified by `data/legendarymonuments/lithostitched/biome_injector/plains_of_death.json` and the Overworld biome tag.

Nether: bastion, fortress, Heatran Cave. End: End City, Eternatus Cocoon, Hoopa Pyramid. Remaining resolved locations are expected Overworld placements based on their worldgen biome selectors/injectors. Dimension is a supported condition; avoid extra biome constraints that would cut off parts of a structure.

### Ecruteak towers

Parent `legendarymonuments:traditional_village/ecruteak` is already used by RC4 village music. Bell Tower uses exact templates `legendarymonuments:traditional_village/ecruteak/bell_tower_base`, `bell_tower_middle`, `bell_tower_top`. Burned Tower uses the same prefix with `burned_tower_1` through `burned_tower_4`.

Verified corresponding NBT files and template pools containing `minecraft:single_pool_element` with those exact locations. Use parent AND piece, preferably seven exact rules rather than broad wildcards. A loose `burned_tower.nbt` also exists, but a template filename alone is not a registered structure; do not invent a standalone rule. At priority 41 the tower overrides Ecruteak 30 and weather 40. Check vertical piece transitions and immediate exterior fallback.

### Lake interior/exterior split

Parents: `legendarymonuments:lake_acuity`, `lake_valor`, `lake_verity`. All are native jigsaw structures, fixed start height 55, with center start pools under `legendarymonuments:lake_guardians/lake_<name>/3x3`. Exact pools and template IDs exist.

Read central template NBT: each is **37 x 48 x 37**. Trial spawners occur at local Acuity (16,9,14), Valor (11,10,23), Verity (16,9,27). This establishes substantial central room geometry, not a cave-only boundary. No separately named cave/interior structure or template was located. Scanning lake template palettes for portal/pedestal blocks did not establish an alternate separate interior.

Candidate central pieces are recorded for investigation, not approved matches. Applying cavern music to their full box may include outdoor space or miss adjacent cave tiles. CobbleSafari has no arbitrary Y/height condition in the installed DTO. Recommended default: PLA - Lake throughout the whole parent bounds and **defer the three PLA - Lake Cavern overrides** until a targeted runtime inspection proves a suitable native piece footprint. Explicitly document this temporary inside/outside limitation in RC5 release notes.

If a precise piece set is demonstrated later, place the three interior overrides before exterior rules with deterministic source-key ordering, all at 41. Do not assume piece conditions win ties automatically. Fixed CSMusic Areas could cover measured rooms in a specific world, but do not automatically discover every generated lake; they require a separate approved world-specific scope. Do not create areas now.

### Other large landmarks

Snowpoint is directly `legendarymonuments:snowpoint_temple`, start pool `snowpoint_temple/312`, jigsaw size 7, maximum distance 116. Its complexity is generation and vertical containment, not lack of a parent ID. Spear Pillar and Turnback Cave likewise have native parent IDs. Final Island starts at Y235–285 and should not activate for someone standing on terrain below it. Southern Island and the ocean landmarks need submerged/vertical boundary checks; retain native bounds.

### Terralith and Cobblemon

All six explicit Terralith IDs exist: `mage_complex`, `mage_tower`, `mage_tower_spring`, `mage_tower_summer`, `mage_tower_autumn`, `mage_tower_winter`. Seasonal names are different structures, not calendar/time filters. All share XY - Scary House with mansion and need only one track registration.

Cobblemon current IDs: `cobblemon:shipwreck_coves/lush_shipwreck_cove` and `.../submerged_shipwreck_cove`. Lava Shipwreck Cove is explicitly marked coming in 1.8 (B5) and absent from 1.7.3 structure entries. Defer it without registering a guessed ID; its song is already needed for the two current coves.

### Three unlocated landmarks

Groudon's Desolate Volcano C88, Kyogre's Primordial Sea C92, Sky Pillar C96 are assigned to Legendary Monuments in the workbook but have no matching structure, template or dimension filename in the inspected installed mods/global packs. The complete installed LM structure list lacks them; LM's three dimension files are distortion_world, hall_of_origin_world, reawakening_sanctum, none an evidenced substitute.

Status is **NEEDS_USER_DECISION**, not a fabricated version guarantee. Provider/version may differ from the finalized sheet. Do not silently substitute monuments from another addon, a biome, or downloaded worlds. Recommend defer all three, preserving their exact assignments for a later provider update. No new mod installation is part of RC5.

## Audio inventory

Confirmed current source counts: **407 tracks, 1,306 rules, 16 trigger files**. Manifest and installed RC4 resource ZIP contain **416 events and 416 OGGs**. Root `data/` matches historical mirrored data byte-for-byte for every root file.

All **32** song labels map exactly to `Structures/<label>.ogg` in the source ZIP. Each basename has exactly one match across that ZIP; no spelling substitutions, missing OGGs or alternate-path duplicates were found. All 32 have OggS/Vorbis headers. CSV records exact bytes and CRC32. This is not a full decode or an auditory loop-seam test.

Reuse without modifying ambient tags:

| Song | Track | Sound event |
|---|---|---|
| ORAS - Drought | `dysfam_music:structures_oras_drought` | `dysfam_music:music/structures/oras_drought` |
| XY - Team Flare Secret HQ | `dysfam_music:structures_xy_team_flare_secret_hq` | `dysfam_music:music/structures/xy_team_flare_secret_hq` |

Both keep `dimension_nether_wastes_basalt` and their existing Nether ambient use. A later direct music rule can reference the same track; no ambient pool/tag change is needed. Existing ambient eligibility does not constitute dedicated location coverage, so zero new workbook conditions are fully implemented already.

Full workbook scope would add **30** registrations, **93,665,466 bytes (89.33 MiB)** before compression, giving 437 tracks and 446 events. Single full-file `loop` is the proposed treatment for all new songs; no separate intro/outro assets are present for these labels. Audition seams during implementation, and only add segment handling if audio evidence requires it.

Recommended 40-condition scope uses 28 songs: **27 new + Heatran's reused event**. It excludes Cave of Origin, Sky Pillar and Lake Cavern additions, while Drought remains untouched in ambient. That gives 434 tracks and 443 events/OGGs. If lake interiors become viable, add one shared Lake Cavern registration: 435/444. Full 437/446 remains a future complete-scope figure, not the initial RC5 acceptance count.

## Conflicts and remaining checks

Ambient 10 < villages 30 < weather 40 < structures 41 < future interiors 42 < generic battles 50 < special battles 60. Every new exploration rule uses `battle: "never"`. Weather loses inside mapped structures by design; battles disable exploration matching. Do not alter RC4 Pokemon Tower at priority 30.

Installed CobbleSafari 0.3.4 `CsMusicTriggerFileData$When` exposes dimension, biome, biome_tag, time_range, weather, area, area_tag, battle, species, form, structure and structure_piece. Tracker bytecode reconfirms extraction of actual single-pool template IDs. Prior RC4 bytecode research documents full 3D containment, cached starts, and descending priority then ascending source-key tie resolution. Non-single pool elements may fall back to generic piece types. No proximity padding or automatic specificity ordering is supported by the researched path.

Unknown overlaps at equal priority need explicit regression cases if encountered. Shared-song overlaps (mansion/mage variants) are harmless for selection. Lake parent/interior overlaps are intentional and require ordering if activated. Leave unchanged RC1–RC4 definitions byte-for-byte and use explicit music references for RC5.

No live diagnostics performed. Remaining release gates: tower containment, representative whole-structure bounds, ambient/weather/battle recovery, source audio decode and one actual playback check. Lake geometry and missing providers are scoped deferrals, not reasons to block the verified remainder.
