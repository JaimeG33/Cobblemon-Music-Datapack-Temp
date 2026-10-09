# Release Plan

Releases are cumulative. Only the newest DysFam datapack and resource pack should be enabled during normal QA.

| Release | Feature layer | Technical priority | Status |
|---|---|---:|---|
| RC1 | Ambient biomes / dimensions | 10 | Working |
| RC2 | Generic wild battles by generation | 50 | Complete / Working |
| RC3 | Weather | 40 | Prototype / QA |
| RC4 | Villages | 30 | Planned |
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
