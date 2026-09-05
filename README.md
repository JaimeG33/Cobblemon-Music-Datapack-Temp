# DysFam CSMusic Datapack + Resource Pack

Unified music system for the DysFam Cobblemon modpack using CobbleSafari CSMusic.

## Current status

**RC2 full generic wild-battle candidate**

- RC1 ambient biome/dimension music is already working.
- RC2 adds the nine generic Gen 1-9 wild battle themes.
- Prototype tests passed for Pikachu (Gen 1), Lucario (Gen 4), and Sprigatito (Gen 9).`r`n- RC2 now maps all 1,016 base Cobblemon 1.7.3 species to their generation battle theme.`r`n- Add-on/custom species outside the base Cobblemon table remain unmapped for now.`r`n- The rapid dimension-hopping overlap issue is currently deferred because it is a low-priority edge case.

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

## Player diagnostics

- /function dysfam_music:check
- /function dysfam_music:check_audio

The pack also displays **"ToaRex music pack is online"** once per world/server load or /reload.