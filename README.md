# DysFam CSMusic Datapack + Resource Pack

Unified music system for the DysFam Cobblemon modpack using CobbleSafari CSMusic.

## Current status

**RC2 prototype in development**

- RC1 ambient biome/dimension music is already working.
- RC2 adds the nine generic Gen 1-9 wild battle themes.
- The current prototype intentionally maps only three test species:
  - Gen 1: Pikachu
  - Gen 4: Lucario
  - Gen 9: Sprigatito
- Full species generation rules will be generated only after the prototype passes in-game testing.
- The rapid dimension-hopping overlap issue is currently deferred because it is a low-priority edge case.

## Repository layout

- `data/` + `pack.mcmeta` - active datapack
- `DysFam_CSMusic_Ambient_RC1_Package/manifest/` - resource and rule manifests
- `DysFam_CSMusic_Ambient_RC1_Package/tools/` - resource-pack builders
- `DysFam_CSMusic_Ambient_RC1_Package/resourcepack_template/` - resource-pack metadata template
- `docs/` - architecture, roadmap, testing, and generated references
- `build_output/` - generated locally and intentionally ignored by Git

The package directory keeps its historical RC1 name to avoid unnecessary path churn; it is now the cumulative CSMusic build workspace.

## Important external source

The large finalized music archive is intentionally not stored in Git:

`C:\Users\Jaime\Downloads\DysFam Music OGG Files.zip`

See `docs/README.md` for the full project guide.
