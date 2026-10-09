# Build Notes

## Critical datapack ZIP rule

Use `tools/build_csmusic_rc2_datapack.ps1`.

A previous Windows ZIP had entries like:

`data\dysfam_music\csmusic\...`

Minecraft recognized `pack.mcmeta`, but CobbleSafari could not discover the CSMusic files. The permanent builder explicitly converts every entry to `/` paths and validates that zero backslashes remain.

## Current RC2 counts

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
