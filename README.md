# DysFam CSMusic Datapack + Resource Pack

Unified music system for the DysFam Cobblemon modpack using CobbleSafari CSMusic.

## Current status

**RC4 Villages: Built / Awaiting Gameplay QA. RC3 remains Complete / Working.**

RC4 adds basic, magic, cold and hot village day/night pools, seven named CobbleTowns settlements, Ecruteak Village and Lavender Town's Pokémon Tower. Twinleaf uses Day/Night tracks; nonlegendary traditional villages retain ambient music. Install both cumulative RC4 packs; see [RC4 installation and gameplay QA](docs/RC4_VILLAGE_TESTING.md).

RC4 contains 407 DysFam tracks, 1,306 rules, 16 trigger files and 416 resource events/OGGs. With the installed CobbleSafari defaults, expect 413 tracks / 1,310 rules / 19 trigger files. Static verification is documented in the testing guide; in-game RC4 behavior still requires user QA.

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

`C:\Users\Jaime\Downloads\DysFam Music OGG Files.zip`
