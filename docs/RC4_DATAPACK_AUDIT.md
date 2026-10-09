# RC4 datapack activation and compatibility audit

Disk inspection on 2026-10-09: 263 root mod/global/world-pack archives, including 49 profile-level optional ZIPs. Root resource paths and metadata were inspected; this is not a complete runtime compatibility certification of every unrelated pack or overlay.

## Current activation and portable policy

`config/simple_datapacks.json` now has `requiredDatapacksPaths: []` and `optionalDatapacksPaths: ["datapacks"]`. The obsolete A-drive and other-user Downloads paths from the earlier handoff are absent. `copyDatapacks` and `shouldApplyRequiredPacksToExistingWorld` remain true. No optional ZIP is currently made required by this configuration. Historical server intent remains unknown.

| Saved world | CSMusic selection | CobbleTowns selection |
|---|---|---|
| RC3 ver 1 Weather Test | RC3 enabled | Enabled |
| Update again | RC2 enabled | Disabled |

These selections came from decompressed `level.dat` NBT, not a live command. The one saved-world CobbleTowns ZIP is byte-identical to the profile copy. The source file is not modified or replaced. Mod datapacks for BCA, Terralith and Legendary Monuments are enabled in both saved snapshots; `config/terralith.json` has `custom_structures: true`.

The [Simple Datapacks author](https://modrinth.com/mod/simple-datapacks) documents relative folders, required automatic application, optional selection and distinct dedicated-server behavior. Therefore server versus local differences may arise from the documented server policy as well as the stale historical path; the full historical cause is not proven. The old path alone is insufficient to reconstruct it.

Recommend retaining the current portable optional folder for QA. If mandatory content is later agreed, use a curated relative `datapacks_required` directory and separate `datapacks` optional directory; put only agreed packs in the required directory. Do not list one directory in both categories. Copying to a save can retain older versions when profile originals change, so compare copies and enabled IDs during upgrades. This is a proposal, not a configuration change.

## World-generation and collision findings

- CobbleTowns, Aether Expansion, `PaleGardenBiomeTag` and the end-raids addon contain worldgen resources and are optional locally. Their availability in Modrinth does not prove selection in a world. The last two primarily extend eligibility tags; they are not alternate town generators.
- Only BCA supplies root `data/minecraft/worldgen/structure_set/villages.json` among scanned archives. No differing duplicate was found for the target BCA/Terralith/CobbleTowns/Legendary Monuments structure, structure-set or template-pool resources.
- Exclusion zones against `minecraft:villages` connect Terralith and CobbleTowns placement to BCA because BCA replaces the set. Ecruteak variants share a rarer placement and require the dyna-plains biome. Rarity and eligibility are separate from music matching.
- 589 root resource paths have differing bytes across mod/global archives. Many are additive tags and intended overrides, so this count is not a count of broken conflicts. Optional-pack collisions include cooking recipes, species spawn pools and head/shulker loot; inspect intended winners before making all optional packs required.
- `ATM x MSD` overlaps Mega Showdown and five `DysFamMissingMons` spawn-pool paths (beautifly, cascoon, dustox, silcoon, wurmple). `Uncommon Starters` changes 81 paths also supplied elsewhere. These are gameplay override candidates, not evidence of village detection failure.
- `double shulker shells` and `more mob heads` both change `minecraft:loot_table/entities/shulker`; player-head loot overlaps mini blocks/more mob heads/player head drops. Cooking conversion/cheaper cooking and other recipe packs also overlap. Enabled order and intended behavior matter.
- No archive deletion, pack activation, world regeneration or mod removal is justified by the overlap scan alone. Nested JAR packs, overlay selection, tag merge semantics and Java-registered data require runtime context; the scan reports root file evidence.

## CobbleTowns: demonstrated versus pending

The actual `pack.mcmeta` declares format 34, supported formats [18,26], and has a trailing `z`, which fails strict JSON parsing. Minecraft accepted enough metadata to log the inconsistent-format warning and load the pack. Minecraft 1.21 uses datapack version 48 ([official release notes](https://feedback.minecraft.net/hc/en-us/articles/27547857163917-Minecraft-Java-Edition-1-21-Tricky-Trials)); metadata alone does not prove worldgen failure.

A demonstrated content defect is `data/cobbletowns/loot_table/lentimas_town/chest_small.json`: its `minecraft:grass` item is rejected in `latest.log` at lines 3363, 3884 and 4822. Only this CobbleTowns JSON references that obsolete item. All its `.json` files parse strictly; its nested Cobblemon loot-table reference paths exist in the archive set. Parsing is not proof that every item or function is valid.

Log evidence: enabling at line 3255; unsuccessful locate before restart at line 4524; successful Pallet locate after restart at 7328–7330; lab detection at 7475–7476; outside/above noncontainment at 7466 and 7481. The located position is X -1568, Z 5824. The log does not preserve Y for those diagnostics. This demonstrates registration, generation and jigsaw-template detection in Minecraft 1.21.1/Cobblemon 1.7.3 for Pallet Town. Other towns, NPC behavior, all loot and special buildings remain gameplay QA targets.

If requested later, review a separate compatibility copy or narrowly targeted override for metadata and the failed loot table, keeping the original ZIP intact. Merely changing format to 48 is not a full migration. Neither the filename `(for 1.6)` nor the loot error establishes that CSMusic cannot match the town.

## Optional archive inventory

All 49 are offered through the current optional folder. Formats are declarations, not validated guarantees. Old main formats without a supported range covering 48 deserve a separate review; modern multi-version packs commonly declare ranges covering 48.

| Archive | Main format | Supported range | Worldgen entries | Metadata |
|---|---:|---|---:|---|
| 1.6 Should Effects Remounted v2.zip | 48 | not declared | 0 | valid JSON |
| Aether Expansion v1.0.zip | 34 | not declared | 15 | valid JSON |
| age lock v1.0.0 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| amethyst blocks to shards.zip | 48 | not declared | 0 | valid JSON |
| armor statues v2.8.21 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| ATM x MSD [v3.6.1].zip | 48 | {"min_inclusive": 34, "max_inclusive": 48} | 0 | valid JSON |
| cauldron concrete v3.0.10 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| cauldron mud v1.0.8 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| CobbleCuisine_campfire_conversion.zip | 48 | not declared | 0 | valid JSON |
| CobbledGacha Template Datapack.zip | 34 | not declared | 0 | valid JSON |
| Cobbled_Variants_1.4.6.zip | 34 | not declared | 0 | valid JSON |
| CobblemonCheaperCooking.zip | 48 | not declared | 0 | valid JSON |
| cobblemoncuisinexcobbleworkers.zip | 48 | not declared | 0 | valid JSON |
| CobblemonRaidDenDesigns-0.5_RELEASE.zip | 48 | not declared | 0 | valid JSON |
| cobblemonraiddens-dynamax.zip | 48 | not declared | 0 | valid JSON |
| cobblemonraiddens-end_raids.zip | 48 | not declared | 3 | valid JSON |
| cobblemonraiddens-legendaries.zip | 48 | not declared | 0 | valid JSON |
| cobblemonraiddens-mega.zip | 48 | not declared | 0 | valid JSON |
| cobblemonraiddens-natdex.zip | 48 | not declared | 0 | valid JSON |
| cobblemonraiddens-tera.zip | 48 | not declared | 0 | valid JSON |
| cobblemonraiddens-ub+paradox.zip | 48 | not declared | 0 | valid JSON |
| cobblemonworkers_tweaks.zip | 48 | not declared | 0 | valid JSON |
| CobbleTowns 1.1.3 (for 1.6).zip | 34 | [18, 26] | 112 | trailing data |
| craftable spawner block.zip | 48 | not declared | 0 | valid JSON |
| CraftSpawnEggs-[1.21]-v.2.1.5.zip | 48 | not declared | 0 | valid JSON |
| custom nether portals v2.3.18 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| diamond incubator recipe change.zip | 48 | not declared | 0 | valid JSON |
| double shulker shells v1.3.15 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| dragon drops v1.3.15 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| DysFamMissingMons.zip | 15 | [15, 99] | 0 | valid JSON |
| ender chest always drops v1.0.7 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| fast-smelt-v1.0.8d-1.21.zip | 48 | {"min_inclusive": 48, "max_inclusive": 81} | 0 | valid JSON |
| glass always drops v1.0.7 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| mini blocks v1.1.5 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| more effective tools v1.0.9 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| more mob heads v2.18.3 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| MoreApples [v1.2.0].zip | 48 | not declared | 0 | valid JSON |
| multiplayer sleep v2.6.15 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| name colors v1.0.13 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| Nether Gold Ore Drops Raw Gold v1.3 (1.20-1.21.11).zip | 15 | {"min_inclusive": 15, "max_inclusive": 95} | 0 | valid JSON |
| PaleGardenBiomeTag.zip | 48 | not declared | 10 | valid JSON |
| player head drops v1.1.15 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| Raw-Ore-Processing_v1.6_1.20.3-1.21.1.zip | 9 | not declared | 0 | valid JSON |
| silence mobs v1.2.9 (MC 1.21-1.21.11).zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| silk touch budding amethyst v1.0.6 (MC 1.21-1.21.9).zip | 48 | {"min_inclusive": 48, "max_inclusive": 88} | 0 | valid JSON |
| Uncommon Starters.zip | 48 | not declared | 0 | valid JSON |
| unlock all recipes v2.0.14 (MC 1.21-1.21.8).zip | 48 | {"min_inclusive": 48, "max_inclusive": 81} | 0 | valid JSON |
| VanillaTweaks_c535023_MC1.21-1.21.11.zip | 48 | {"min_inclusive": 48, "max_inclusive": 94} | 0 | valid JSON |
| Vivillon Pride Patterns v2.0.zip | 48 | {"min_inclusive": 34, "max_inclusive": 48} | 0 | valid JSON |

Declared format warnings beyond CobbleTowns include Aether Expansion, CobbledGacha Template, Cobbled Variants (34 without a supported range) and Raw Ore Processing (9 without a supported range). These are candidates for compatibility review, not established failures from this inspection. Broad supported ranges on DysFamMissingMons and Nether Gold Ore include 48 despite their older main format.
