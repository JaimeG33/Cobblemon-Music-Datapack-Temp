# Testing

## Clean CSMusic QA environment

Keep enabled:

- CobbleSafari 0.3.4
- the normal DysFam modpack
- only the newest DysFam CSMusic datapack/resource pack

Disable while validating CSMusic:

- ReactiveMusic
- CobbleThemes
- old Pokemon Music Pack by ToaRex
- obsolete DysFam CSMusic builds

## Build RC2

```powershell
.\DysFam_CSMusic_Ambient_RC1_Package\tools\build_csmusic_rc2_datapack.ps1
.\DysFam_CSMusic_Ambient_RC1_Package\tools\build_csmusic_rc2_resourcepack.ps1
```

Expected outputs:

- `build_output\DysFam_CSMusic_RC2_Datapack.zip`
- `build_output\DysFam_CSMusic_RC2_ResourcePack.zip`

Both builders must finish with validation passed.

## Known-good RC2 runtime totals

With CobbleSafari 0.3.4:

- 283 music definitions
- 1,267 trigger rules
- 15 trigger files
- 0 skipped definitions
- 0 rejected trigger files

## Diagnostics

```mcfunction
/reload
/datapack list enabled
/function dysfam_music:check
/function dysfam_music:check_audio
/cobblesafari csmusic list
/cobblesafari csmusic current
```

## Generation regression sample

Recommended species:

```mcfunction
/spawnpokemon pikachu
/spawnpokemon hoppip
/spawnpokemon mudkip
/spawnpokemon lucario
/spawnpokemon snivy
/spawnpokemon froakie
/spawnpokemon rowlet
/spawnpokemon wooloo
/spawnpokemon sprigatito
```

Expected tracks:

- Pikachu -> Gen 1 / LGPE
- Hoppip -> Gen 2 / HGSS
- Mudkip -> Gen 3 / ORAS
- Lucario -> Gen 4 / BDSP
- Snivy -> Gen 5 / SVID
- Froakie -> Gen 6 / PLZA
- Rowlet -> Gen 7 / USUM
- Wooloo -> Gen 8 / SWSH
- Sprigatito -> Gen 9 / SV

For each battle verify correct intro/loop, no ambient overlap, correct `battle_genN`, and ambient resume afterward.

## Ambient regression

Verify at least Plains day/night, Desert day/night, one underground pool, Nether, and End.

## Add-on species

A custom/add-on PokÃ©mon not present in `docs/reference/cobblemon_species_1.7.3.csv` is outside RC2 base-species scope.

## Critical ZIP rule

Always build the datapack using:

`DysFam_CSMusic_Ambient_RC1_Package\tools\build_csmusic_rc2_datapack.ps1`

The builder forces `/` ZIP paths. A previous Windows ZIP used backslashes, which Minecraft accepted while CobbleSafari failed to discover the CSMusic files.
