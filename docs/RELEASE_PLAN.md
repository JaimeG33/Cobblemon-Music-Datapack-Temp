# Release Plan

Releases are cumulative. Only the newest DysFam datapack and resource pack should be enabled during normal QA.

| Release | Feature layer | Technical priority | Status |
|---|---|---:|---|
| RC1 | Ambient biomes / dimensions | 10 | Working |
| RC2 | Generic wild battles by generation | 50 | Complete / Working |
| RC3 | Weather | 40 | Complete / Working |
| RC4 | Villages | 30 | Next / Planning |
| RC5 | PokÃ©center / PokÃ©mart / specific buildings | 42 | Planned |
| RC6 | General / special structures | 41 | Planned |
| RC7 | Advanced/special PokÃ©mon battles | 60 | Planned |
| Optional | Trainer battle layer | 55 | Research / possible |

## RC2 completed mapping

- Gen 1 -> LGPE - Battle Wild Pokemon
- Gen 2 -> HGSS - Battle Wild Pokemon
- Gen 3 -> ORAS - Battle Wild Pokemon
- Gen 4 -> BDSP - Battle Wild Pokemon
- Gen 5 -> SVID - Battle Wild Pokemon
- Gen 6 -> PLZA - Battle Wild Pokemon
- Gen 7 -> USUM - Battle Wild Pokemon
- Gen 8 -> SWSH - Battle Wild Pokemon
- Gen 9 -> SV - Battle Wild Pokemon

RC2 contains all nine intro/loop pairs and 1,016 exact base-species rules generated from:

`docs/reference/cobblemon_species_1.7.3.csv`

## Later battle work

Still planned:

- add-on/custom species;
- trainer/NPC/PvP themes;
- special species/forms;
- legendary/mythical/special encounters;
- boss/raid-specific music where appropriate.

These later rules should override the generic priority-50 battle layer rather than replace it.

## Deferred issue

Rapid dimension-hopping overlap is intentionally deferred until final integration QA.

## RC4 next-step scope

RC3 gameplay QA is complete based on the user's weather and battle-transition tests, including explicit confirmation of nighttime snowfall. RC4 builds cumulatively on that baseline.

Source: `C:/Users/Jaime/Downloads/CSMusic_Reference_Excel_Files/Music Pack Conditions & Music(2)_2.xlsx`, Villages sheet.

- Add basic, magic, cold and hot village pools with the source's day/night splits.
- Add the specific CobbleTowns location assignments and Legendary Monuments Ecruteak Village assignment.
- Resolve actual structure IDs/tags and necessary piece IDs from installed BCA, Terralith, CobbleTowns and Legendary Monuments data, then confirm detection with `/cobblesafari csmusic structures`.
- Use village priority 30 and `battle: "never"`: ambient 10 < villages 30 < weather 40 < generic wild battles 50.
- Reuse existing registered sound events where possible; add only missing village audio/events to the cumulative manifest and resource pack.
- Build cumulative RC4 packs and test entry/exit, day/night, named locations, weather overrides and battle return behavior.
- Keep Pokecenter/Pokemart overrides for RC5 and general structures for RC6.

Source clarification: the user confirmed the standalone `O` in Magic Villages Night is a typo; ignore it and retain village priority 30. The Villages sheet separately maps Pokemon Tower inside Lavender Town; installed data identifies it as a building piece, so plan a specific piece rule with deterministic precedence. Preserve the workbook's song intent while matching exact archive filenames.

See [RC4 village research](RC4_VILLAGE_RESEARCH.md) for the historical vanilla-ID mismatch, BCA village replacement, current portable optional-pack configuration, enabled CobbleTowns in the RC3 test save, compatibility findings and structure-boundary behavior. The [implementation proposal](RC4_IMPLEMENTATION_PLAN.md), [exact structure map](RC4_STRUCTURE_MUSIC_MAP.md) and [audio inventory](RC4_AUDIO_INVENTORY.md) are ready for review. RC4 implementation is awaiting that review and the Twinleaf audio decision.
