# Testing

## Clean CSMusic test environment

Keep enabled:

- CobbleSafari 0.3.4
- the normal DysFam modpack
- only the newest DysFam CSMusic datapack/resource pack under test

Disable while validating battle music:

- ReactiveMusic
- CobbleThemes
- old Pokemon Music Pack by ToaRex
- obsolete CSMusic resource-pack builds

If Chat Patches duplicate-message counting makes diagnostics hard to read, disable its duplicate counter during testing.

## Build RC2 resource pack

From the repository root:

```powershell
.\DysFam_CSMusic_Ambient_RC1_Package\tools\build_csmusic_rc2_resourcepack.ps1
```

The default source archive is:

`C:\Users\Jaime\Downloads\DysFam Music OGG Files.zip`

Expected output:

`DysFam_CSMusic_Ambient_RC1_Package\build_output\DysFam_CSMusic_RC2_ResourcePack.zip`

The builder must finish with ZIP validation passed.

## Datapack diagnostics

Useful in-game commands:

```mcfunction
/reload
/datapack list enabled
/cobblesafari csmusic list
/cobblesafari csmusic current
/cobblesafari csmusic structures
```

RC1 baseline before RC2 was approximately:

- 274 total loaded music definitions including CobbleSafari built-ins
- 251 trigger rules from 6 files
- zero skipped/rejected

RC2 prototype should add:

- 9 DysFam music definitions
- 3 trigger rules
- 1 trigger-definition file

Exact totals can vary if CobbleSafari's built-ins change, so zero skipped/rejected matters more than matching a hardcoded total.

## RC2 prototype battle tests

Spawn/fight one of each test species:

```mcfunction
/spawnpokemon pikachu
/spawnpokemon lucario
/spawnpokemon sprigatito
```

Expected mapping:

- Pikachu -> `dysfam_music:battle_gen1` -> LGPE
- Lucario -> `dysfam_music:battle_gen4` -> BDSP
- Sprigatito -> `dysfam_music:battle_gen9` -> SV

For each test verify:

1. Ambient music is audible before battle.
2. Battle start causes ambient to yield.
3. Correct battle intro plays once.
4. Correct loop continues after the intro.
5. Cobblemon/CobbleThemes music does not overlap.
6. `/cobblesafari csmusic current` shows the expected battle track.
7. Ending/fleeing the battle stops battle music.
8. Ambient music resumes afterward.

Do not generate the full 1,016-species rule table until all three prototype generations pass.

## Regression checks

After battle testing, briefly verify:

- Plains day/night ambient
- Desert day/night ambient
- one underground pool
- Nether
- End

This catches accidental RC1 regressions before expanding RC2.

## RC2 full candidate

Expected runtime with CobbleSafari 0.3.4:

- 283 music definitions
- 1,267 trigger rules
- 15 trigger files
- 0 skipped definitions
- 0 rejected trigger files

Useful checks:

`mcfunction
/function dysfam_music:check
/function dysfam_music:check_audio
`

Generation smoke-test species:
Pikachu, Hoppip, Mudkip, Lucario, Snivy, Froakie, Rowlet, Wooloo, Sprigatito.

## Datapack ZIP rule

The datapack ZIP must contain forward-slash paths (data/dysfam_music/...). The earlier Windows backslash ZIP caused Minecraft to enable the pack while CobbleSafari could not discover its CSMusic resources. Always use 	ools/build_csmusic_rc2_datapack.ps1.