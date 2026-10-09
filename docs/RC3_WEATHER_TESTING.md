# RC3 Weather — Complete / Working

RC3 contains the completed RC2 ambient and generic wild-battle layers plus weather.
The user confirmed successful gameplay QA, including the follow-up snowfall-at-night check. RC3 is the working cumulative baseline for RC4.

## Source and installed schema

Song assignments come from `C:/Users/Jaime/Downloads/CSMusic_Reference_Excel_Files/Music Pack Conditions & Music(2)_2.xlsx`, Weather!A1:C3.
The implementation workbook is a technical companion, not an override of those assignments.

Inspected with Java 21 `javap -p -c` against the installed
`cobblesafari-fabric-1.21.1-0.3.4.jar`.
SHA256: `B773074B7C66C4A92646B038D366FAFBBEF7750133B8615BCEB462E61EF0F008`.

- `CsMusicTriggerFileData$When.weather` is `List<String>`: use JSON arrays, not scalar strings.
- `CsMusicTriggerDataLoader` uses ordinary Gson and compiles that list into weather states.
- Supported states/aliases: `none`/`clear`, `rain`/`raining`, `snow`/`snowing`, `thunder`/`thunderstorm`/`storm`.
- `CsMusicWeather.current` gives thunder precedence. Otherwise, when the world is raining, it reads biome precipitation at the player's position and returns rain, snow, or none.
- This is biome/position precipitation classification, not an exposure check: it does not test whether the player is under a roof. Seasonal mod interactions still need gameplay QA.
- `CsMusicCondition.matches` ANDs dimension, time, biome, weather and battle conditions.
- `time_range` is a two-integer array. `CsMusicTimeRange.matches` includes the start and excludes the end. `CsMusicEvalContext` normalizes time modulo 24000 (and supports its time override).

The supplied patch was not executed: its scalar `weather` values do not match this DTO, and its `rain` rules would not select local snow. Its ASCII token check could not detect either problem.

## Implemented behavior

| Context in the Overworld, outside battle | Selection |
|---|---|
| Clear weather | Existing ambient |
| Ordinary rain classified as rain | Existing ambient |
| Thunderstorm, including snowy/dry biomes | ORAS - Heavy Rain |
| Local snow, ticks 0–11999 | NPS - Shiver Snowfields (Day) |
| Local snow, ticks 12000–23999 | NPS - Shiver Snowfields (Night) |

All three weather rules have priority 40 and `battle: "never"`.
Generic wild battles retain priority 50 and all 1,016 species rules unchanged.
Snow uses `weather: ["snow"]`; no fixed snowy-biome list is needed or used.
This follows actual local precipitation classification, including modded biomes and altitude effects exposed by the runtime, instead of assuming every ambient snowy category always has snow.

## Counts

| Item | Expected |
|---|---:|
| DysFam track definitions | 280 (268 ambient + 9 battle + 3 weather) |
| Resource events / OGG files | 289 |
| Weather rules | 3 |
| Total definitions with installed CobbleSafari built-ins | 286 |
| Total rules with installed CobbleSafari built-ins | 1,270 |
| Total trigger files with installed CobbleSafari built-ins | 16 |

Root and historical datapack mirror are synchronized. `/function dysfam_music:check` reports expected counts, not a live registry inspection.

## Validation performed

- Both PowerShell builders completed successfully; both ZIPs passed CRC and forward-slash path checks.
- Resource ZIP contains 289 registered events and 289 files with OGG signatures; every track sound reference resolves.
- Weather JSON deserialized using Gson 2.11.0 and the actual installed CobbleSafari trigger DTO. The installed `CsMusicTimeRange` class passed start-inclusive/end-exclusive checks.
- An independent selection matrix passed 96 dimension/battle/weather/time combinations, including the day/night boundary.
- All RC2 music JSON remains unchanged after Git line-ending normalization; all original 286 manifest records are preserved. Root and mirror data files match byte-for-byte.
- Counts were computed from source and the installed JAR: project 280 definitions / 1,266 rules / 13 files, plus built-ins 6 definitions / 4 rules / 3 files.
- User gameplay QA passed: ordinary rain retains ambient; thunder selects Heavy Rain; snow selects the day/night tracks; clear weather restores ambient; battles interrupt weather and weather resumes afterward. The snowfall-at-night follow-up was explicitly confirmed successful.
- Seasonal-mod edge cases were not separately established. Rapid dimension-hopping remains deferred.
- Existing built packs retain their original QA labels; this documentation update does not require reinstalling them.

## Build

From the repository root, in PowerShell:

```powershell
.\DysFam_CSMusic_Ambient_RC1_Package\tools\build_csmusic_rc3_datapack.ps1
.\DysFam_CSMusic_Ambient_RC1_Package\tools\build_csmusic_rc3_resourcepack.ps1
```

Outputs are `DysFam_CSMusic_Ambient_RC1_Package/build_output/DysFam_CSMusic_RC3_Datapack.zip`
and `DysFam_CSMusic_RC3_ResourcePack.zip` in the same directory.
The resource builder defaults to `C:/Users/Jaime/Downloads/DysFam Music OGG Files.zip` (override with `-ZipPath`).
The RC2 builder files are preserved; they read the active cumulative source/manifest, so rebuilding a historical RC2 release requires the RC2 branch.

## Installation and gameplay QA

Use a test world. Install the RC3 datapack into that world's `datapacks/` and the RC3 resource pack into the profile's `resourcepacks/`.
Enable only the RC3 pair; disable older CSMusic datapacks/resource packs. Keep Reactive Music, CobbleThemes and the old ToaRex music pack disabled.
This implementation does not automatically modify the installed world or resource-pack selection.

```mcfunction
/reload
/datapack list enabled
/function dysfam_music:check
/cobblesafari csmusic list
/cobblesafari csmusic current
```

Confirm the log counts above with zero skipped definitions and zero rejected trigger files.

1. In Plains: `/weather clear`, `/time set day`: ambient.
2. `/weather rain`: Plains ambient remains.
3. `/weather thunder`: Heavy Rain, priority 40.
4. Move to a snowy surface biome (e.g. Snowy Plains), then `/weather rain`, `/time set day`: Snow Day.
5. `/time set night`: Snow Night.
6. Test `/time set 11999`, `/time set 12000`, `/time set 23999`, `/time set 0`: clean day/night boundaries.
7. In that snowy biome, `/weather thunder`: Heavy Rain, without competing snow rules.
8. `/weather clear`: ambient resumes.
9. Start a wild battle during active weather: correct generation intro/loop wins; weather resumes after battle while its condition remains active.
10. Verify a normal ambient biome and an ordinary wild battle as RC2 regression checks. Confirm weather does not apply in Nether/End.

Run `/cobblesafari csmusic current` after each context change. Allow the engine's normal arbitration/crossfade time.

Manual resource-only checks (one at a time, `/stopsound @s music` between them):

```mcfunction
/function dysfam_music:check_weather_audio
/playsound dysfam_music:music/weather/nps_shiver_snowfields_day music @s
/playsound dysfam_music:music/weather/nps_shiver_snowfields_night music @s
```

Direct playsound checks do not validate CSMusic selection and may overlap its custom player.
Rapid dimension-hopping overlap remains deferred. RC4 Villages is the next feature after RC3 passes in-game QA.
