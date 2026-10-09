# DysFam CSMusic Datapack + Resource Pack

Unified music system for the DysFam Cobblemon modpack using CobbleSafari CSMusic.

## Current status

**RC3 Weather: implemented, awaiting in-game QA. RC2 remains the tested baseline.**

RC3 adds thunderstorm and local snowfall day/night music. Build and enable both cumulative RC3 packs; see [RC3 testing](docs/RC3_WEATHER_TESTING.md).

Completed and tested:

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
