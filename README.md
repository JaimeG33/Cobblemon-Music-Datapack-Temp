# DysFam CSMusic Datapack + Resource Pack

Unified music system for the DysFam Cobblemon modpack using CobbleSafari CSMusic.

## Current status

**RC5 Structures: Built / Gameplay QA pending. RC4 is accepted as the baseline.**

RC5 adds 40 approved structure conditions through 45 exact rules, including Bell/Burned Tower pieces. It adds 27 music registrations and reuses Heatran's existing track. Four unavailable locations and three lake-interior overrides are explicitly deferred; PLA - Lake currently plays across whole native lake bounds, including interiors. See [RC5 builds, deferrals and validation](docs/RC5_BUILD_RESULTS.md).

The cumulative RC5 packs contain 434 DysFam tracks, 1,351 rules, 21 definition files and 443 events/OGGs. With installed CobbleSafari defaults, expect 440 tracks / 1,355 rules / 24 files. RC1–RC4 tracks, triggers and ambient tags are preserved. Static/schema/archive checks and decoding of all 27 new songs passed; native gameplay containment, transitions and actual playback remain pending.

Completed and tested:

- RC3 weather passed user gameplay QA, including snowfall at night and battle interruption/resumption.

- RC1 ambient biome/dimension music remains the environmental baseline.
- RC2 adds nine generic wild battle themes, one per PokÃ©mon generation.
- All 1,016 base species present in Cobblemon 1.7.3 are mapped to their generation theme.
- Battle testing confirmed correct track selection and ambient -> battle -> ambient transitions.
- `/function dysfam_music:check` reports expected pack status/counts.
- `/function dysfam_music:check_audio` manually verifies a battle sound event.
- Players receive a short "ToaRex music pack is online" message once per world/server load or `/reload`.

Not part of RC2:

- addon/custom species outside base Cobblemon 1.7.3;
- trainer/NPC/PvP themes;
- special legendary/species/form overrides;
- rapid dimension-hopping overlap investigation.

The rapid dimension-hopping issue is intentionally deferred until all planned music layers are complete.

## Repository layout

- `data/` + `pack.mcmeta` - active datapack
- `DysFam_CSMusic_Ambient_RC1_Package/manifest/` - cumulative manifests
- `DysFam_CSMusic_Ambient_RC1_Package/tools/` - datapack/resource-pack builders
- `DysFam_CSMusic_Ambient_RC1_Package/resourcepack_template/` - resource-pack metadata template
- `docs/` - architecture, release plan, testing, build notes, and references
- `build_output/` - generated locally and intentionally ignored by Git

## Player diagnostics

```mcfunction
/function dysfam_music:check
/function dysfam_music:check_audio
/cobblesafari csmusic current
```

## External music source

The finalized source OGG archive is intentionally not stored in Git:

`D:/Minecraft Stuff/Minecraft Datapacks/CSMusic Sources/DysFam Music OGG Files.zip`
