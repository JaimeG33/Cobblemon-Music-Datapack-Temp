# RC4 village detection and worldgen review

Research before implementation. No world, mod, pack activation, or profile configuration changes were made.
User clarified that the standalone `O` in Magic Villages Night is a typo; magical villages retain priority 30.

## Completed follow-up audit — 2026-10-09

The new handoff was checked against the current local files, original Villages workbook, audio source ZIP, 263 mod/global/world-pack archives, saved `level.dat` selections and `latest.log`. This follow-up supersedes the earlier activation snapshot below. Only documentation and the research CSV were updated; the profile, worlds, original archives, runtime datapack and release outputs were not changed.

Deliverables:

- [Exact structure-to-music and special-building map](RC4_STRUCTURE_MUSIC_MAP.md): all 13 BCA villages, two Terralith villages, seven CobbleTowns towns, both Legendary Monuments variants, and building-template candidates.
- [Audio inventory and missing registrations](RC4_AUDIO_INVENTORY.md), with [exact per-track CSV](reference/rc4_village_audio_inventory.csv).
- [Activation, archive compatibility and optional-pack audit](RC4_DATAPACK_AUDIT.md): current selections, portable policy proposal, all 49 optional archive declarations and relevant overlapping resources.
- [RC4 implementation proposal and gameplay QA](RC4_IMPLEMENTATION_PLAN.md): expected files, supported schema, tower precedence, cumulative counts and future build commands.

Verified changes since the first handoff:

1. `simple_datapacks.json` is already portable: empty required list and only relative `datapacks` in the optional list. Both obsolete absolute paths have been removed. The history/author of that edit is not inferred.
2. `RC3 ver 1 Weather Test/level.dat` now enables CobbleTowns and RC3. `Update again` still disables CobbleTowns and uses RC2. One copied CobbleTowns ZIP in the RC3 save matches the profile ZIP byte-for-byte.
3. The log independently confirms Pallet Town locate at X -1568, Z 5824, `[bounds: 1, piece: 1]`, and `cobbletowns:pallet_town/rare_structures/lab`; it also confirms two noncontainment observations. Y and the exact movement cannot be reconstructed from those log lines. The user's report supplies the inside/above/outside context.
4. CobbleTowns has an actual additional defect: the Lentimas small chest loot table fails to parse in-game because of `minecraft:grass`. Its malformed metadata remains present. These defects coexist with successful Pallet generation/detection and do not prove that its other structures fail.
5. Terralith `custom_structures` is enabled. The target structure resources have no differing root-file overrides in the scanned archives; only BCA provides the replacement vanilla village structure set.
6. Villages contains 127 unique song labels. With both Twinleaf versions, all 128 candidate source OGGs exist, one Kitakami registration is reusable, and 127 new events/tracks are needed. Source audio additions total about 313.12 MiB before ZIP compression.
7. Installed bytecode resolves equal priorities by ascending source key after descending priority. A piece does not automatically beat a structure. Put tower at rule index 0 and Lavender Town at index 1 in the same new trigger file to preserve priority 30 with deterministic precedence. Runtime Tower detection and entry/exit QA remain outstanding.
8. Root and historical mirrored runtime data currently match exactly. Repository counts are 280 tracks / 1,266 rules / 13 trigger files; CobbleSafari contributes 6 tracks / 4 rules / 3 trigger files, explaining the actual logged totals 286 / 1,270 / 16. The manifest has 289 DysFam events.

**Decision requiring song selection:** workbook I25 has unsuffixed Twinleaf Town, but the library offers separate Day and Night versions. Recommend both with time rules. The nonlegendary traditional village has no workbook assignment; recommend keeping ambient unless the user explicitly extends the mapping. Intended mandatory optional-pack selection cannot be recovered from the historical server handoff; that broader policy does not block QA in the already configured test world.

Runtime versus handoff evidence: the second handoff reports successful BCA categories, both Terralith villages and Ecruteak location tests. Their archive IDs were independently confirmed here. The retained log independently verifies the Pallet test; this review did not launch Minecraft or reproduce every reported test.

## Earlier documentation

`C:/Users/Jaime/Downloads/CSMusic_Ambient_RC1_Testing_Handoff_2026-09-01.md`, sections 8–9 (lines 156–199), explicitly records that the mini-test targeted vanilla `minecraft:village_*` while the world used Terralith/BCA villages. Later diagnostics identified the correct structures. Observed IDs included `terralith:fortified_village`, `#terralith:fortified_villages`, `#bca:villages`, and `bca:default/one_off/pokecenter`.

`CSMusic_Post_Ambient_RC1_Handoff_2026-09-04.md`, lines 205–213, reports working structure diagnostics: Terralith village, BCA bounds, and BCA Pokecenter piece. Ambient kept playing because village/building music rules had not been implemented.

The October master handoff and integration guide repeat these findings and recommend exact IDs/pieces plus CSMusic Areas as a fallback. They do not establish a separate, reproduced failure of proximity detection or identify BCA's precise replacement resource. Those details required installed-file inspection.

## Installed profile evidence

Profile: `D:/Minecraft Stuff/ModrinthApp/profiles/DysFam Cobblemon 2.0 6.0.0`.
Examined root data resources in 262 installed mod/global-pack/world-pack archives, relevant configs, both saved worlds' `level.dat` pack selections, current log, and installed CobbleSafari 0.3.4 bytecode.
Archive presence alone is not evidence a world enabled a datapack. Saved-world observations are disk snapshots, not a live server query.

### BCA replaces the default vanilla village generation set

`mods/cobblemon-additions-4.3.0.jar` provides `data/minecraft/worldgen/structure_set/villages.json`.
Its entries are exclusively these 13 BCA structures:

- `bca:village/default_small`, `default_mid`, `default_large`
- `bca:village/fighting_small`, `fighting_mid`, `fighting_large`
- `bca:village/dark_small`, `dark_mid`
- `bca:village/fairy_small`, `fairy_mid`
- `bca:village/ice_small`, `ice_mid`, `ice_large`

No competing copy of that resource was found among the scanned archives. This explains the absence of normal vanilla village generation in this setup. Vanilla IDs remaining registered would not mean they are still selected for generation. Existing worlds/chunks may retain structures created under an older setup.

For RC4, map the BCA IDs instead of restoring vanilla generation. Restoration, if wanted independently, would require an intentional worldgen compatibility change, not a music fix.

### Historical snapshot: CobbleTowns was disabled in both saved worlds

At the earlier inspection, `datapacks/CobbleTowns 1.1.3 (for 1.6).zip` was explicitly in `DataPacks.Disabled` in both:

- `saves/RC3 ver 1 Weather Test/level.dat`
- `saves/Update again/level.dat`

Both saves have generation enabled and the BCA/Terralith/Legendary Monuments mod datapacks enabled. Numerous other profile-level optional ZIPs are also disabled. Therefore these local worlds do not necessarily reproduce the friend's complete server datapack setup.

The earlier `config/simple_datapacks.json` had a required path `A:\Modrinth\profiles\DysFam Cobblemon 2.0\datapacks`, which does not exist here. Optional paths included the valid relative `datapacks` folder and nonexistent `C:\Users\toare\Downloads`. The log examined then reported failed directory listing for both obsolete absolute paths. The current configuration no longer contains these paths, and the latest log does not report those directory-listing failures.

The [Simple Datapacks author's documentation](https://modrinth.com/mod/simple-datapacks) distinguishes automatic required packs from optional packs offered for selection. The stale required path plausibly explains why intended mandatory global packs became optional locally. Historical intent cannot be determined from this configuration alone.

Before full RC4 QA, explicitly select the intended content packs in a fresh test world's creation settings and verify `/datapack list enabled`. Correcting the required folder configuration is an option after deciding which packs should be mandatory; do not automatically enable every optional ZIP. Newly enabled worldgen will not populate existing explored chunks retroactively.

CobbleTowns metadata also needs attention: `pack_format` is 34, `supported_formats` is [18,26], and `pack.mcmeta` has a trailing `z`. The log warns about inconsistent formats. This is a separate metadata defect, not proof that it caused the disabled state. Its worldgen directory layout includes 1.21-style structure paths; the `(for 1.6)` filename is not by itself evidence of incompatibility with Minecraft 1.21.1.

### Exact IDs and tags matter

- BCA's structure tag `#bca:villages` includes `bca:village/witch_hut` as well as the 13 villages. Do not use it indiscriminately for town music.
- BCA also has a biome tag called `#bca:villages`; biome and structure tags are separate registries. Selecting a biome tag would apply outside towns.
- Terralith 2.6.2 has `terralith:fortified_village` and `terralith:fortified_desert_village`. Its broad fortified-villages structure tag includes both, but the workbook assigns basic versus hot music. Separate them.
- BCA default and themed village biome eligibility overlaps. Match the generated structure ID, not the player's biome alone, to distinguish village type.
- No scanned mod/global pack adds BCA to the vanilla `minecraft:village` structure tag.

### Rarity and exclusion zones are intentional

Terralith's `data/terralith/worldgen/structure_set/rare_village.json` excludes placements near `minecraft:villages` with `chunk_count: 8`. CobbleTowns' town sets also exclude that set with `chunk_count: 8`. Because BCA replaces the contents of that set, these exclusions now interact with BCA villages. They can make other towns harder to find; this alone is not a music detection failure.

Legendary Monuments 8.1 defines `legendarymonuments:traditional_village/ecruteak` and a separate `.../nonlegendary` variant. Both require `legendarymonuments:dyna_plains`; the shared placement has spacing 150, separation 75, a seven-chunk village exclusion, and weights 2 versus 6. These are placement parameters, not a guaranteed distance or overall spawn probability.
The workbook names Ecruteak; do not silently assign its song to the nonlegendary variant.

### CobbleTowns location and building distinctions

The archive defines seven named towns: `cherrygrove_city`, `floaroma_town`, `lavender_town`, `lentimas_town`, `pacifidlog_town`, `pallet_town`, `twinleaf_town`, all in namespace `cobbletowns`.
Source labels such as "Lavander" and "Pacificlog" must be translated to exact registry spellings.

Pokemon Tower is a template piece `cobbletowns:lavender_town/buildings/pokemon_tower` inside Lavender Town, not a separate top-level tower structure. Its template pool uses a single pool element, which CSMusic can extract by template ID. In-game piece confirmation and deterministic town-versus-tower precedence are still needed.
Named towns have their own center/mart pieces, such as `cobbletowns:lavender_town/buildings/center` and `.../mart`; matching only standalone `cobbletowns:pokecenter/pokecenter` or `cobbletowns:pokemart/pokemart` would miss those later RC5 targets.

## How installed CSMusic detects structures

Inspected `CsMusicStructureTracker`, `CsMusicStructureFilter`, `CsMusicPiecePattern` in `cobblesafari-fabric-1.21.1-0.3.4.jar` using `javap -p -c`.

- A `structure` condition checks the player's block position inside the complete structure's bounding box, then matches the ID/tag. This is three-dimensional containment, not distance to a village, villagers, beds, a POI, or a name on a map.
- A `structure_piece` condition checks the corresponding piece bounding box and piece ID. `structure` may additionally restrict which parent structures are considered.
- Exact IDs, `#tags`, and `*`/`any` are accepted as structure filters. General ID-prefix globbing is not provided there; piece patterns separately support wildcards.
- A whole structure box can include gaps between buildings. Flying above its vertical limit, walking beyond its edge, or standing in a handmade extension can fail containment despite the village being visually nearby.
- The tracker reads structure references for the player's chunk and requests their start chunks. It skips null/unavailable starts. This is a potential issue immediately after travel or around very large structures, not a reproduced failure in this session.
- Cached structure information expires after the configured 600 ticks (about 30 seconds at 20 TPS). An incomplete cached result may persist until refresh. The player's containment is rechecked against cached boxes, so this does not mean every entry/exit waits 30 seconds.
- The diagnostics path `describeAt` inspects structures independently of the normal cache. Its reported `in bounds` and `in piece` fields should be read separately; merely listing a structure does not prove the rule matches the player's position.
- Jigsaw single-pool elements can return their actual template ID. Other piece types may fall back to a generic piece-type ID, requiring runtime inspection before relying on template matching.

Mappings were cross-checked against Fabric's [BlockBox.contains documentation](https://maven.fabricmc.net/docs/yarn-1.21.1%2Bbuild.3/net/minecraft/util/math/BlockBox.html#contains(net.minecraft.util.math.Vec3i)) and [ServerChunkManager.getWorldChunk](https://maven.fabricmc.net/docs/yarn-1.21.1%2Bbuild.3/net/minecraft/server/world/ServerChunkManager.html#getWorldChunk(int,int)).

Tectonic and Terralith affect terrain and placement; a vertical bounds mismatch is possible. No evidence from this inspection establishes Tectonic, C2ME, Lithium, or the disabled experimental CobbleSafari addon as the cause of the historical failure. Do not remove unrelated mods based on speculation.

## Proposed RC4 approach and useful old-chat material

1. Confirm intended content-pack enablement, especially CobbleTowns, before testing its rules.
2. Match exact BCA variants, the two Terralith villages, and Ecruteak. Use narrowly defined structure tags only when they preserve the workbook's categories.
3. Test a naturally generated village at ground level using `/cobblesafari csmusic structures` and `/cobblesafari csmusic current`, including center, edge, outside, and above the village. Record coordinates including Y.
4. If detection changes after waiting or moving toward the center, investigate start-chunk availability/cache behavior before changing rules or global settings.
5. If music must start outside the generated bounds, define that desired distance first. CSMusic Areas can cover selected fixed locations; automatic expanded bounds for every generated village would require additional integration beyond the current JSON structure filter.

Useful old-chat excerpts: exact failed `/locate` and CSMusic commands/results; screenshots including `in bounds`/`in piece`; structure IDs, world/dimension/XYZ, and whether the structure generated naturally or was pasted/placed; server versus local pack lists and prior config edits; any agreed definition of "near"; decisions about nonlegendary Ecruteak-style settlements and Pokemon Tower precedence. Full chat histories are not necessary.
