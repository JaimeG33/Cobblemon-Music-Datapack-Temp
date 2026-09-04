# Release Plan

The releases are cumulative. Only the newest datapack and newest resource pack should be enabled during normal testing.

| Release | Feature layer | Technical priority | Status |
|---|---|---:|---|
| RC1 | Ambient biomes / dimensions | 10 | Working |
| RC2 | Generic wild battles by generation | 50 | Prototype |
| RC3 | Weather | 40 | Planned |
| RC4 | Villages | 30 | Planned |
| RC5 | Pokecenter / Pokemart / specific buildings | 42 | Planned |
| RC6 | General / special structures | 41 | Planned |
| RC7 | Advanced/special Pokemon battles | 60 | Planned |
| Optional | Trainer battle layer | 55 | Research/possible |

## RC2 prototype

Generic wild battle mapping:

- Gen 1 -> LGPE - Battle Wild Pokemon
- Gen 2 -> HGSS - Battle Wild Pokemon
- Gen 3 -> ORAS - Battle Wild Pokemon
- Gen 4 -> BDSP - Battle Wild Pokemon
- Gen 5 -> SVID - Battle Wild Pokemon
- Gen 6 -> PLZA - Battle Wild Pokemon
- Gen 7 -> USUM - Battle Wild Pokemon
- Gen 8 -> SWSH - Battle Wild Pokemon
- Gen 9 -> SV - Battle Wild Pokemon

All nine intro/loop pairs are included in the RC2 resource manifest and all nine track definitions are added to the datapack.

The first trigger file intentionally contains only:

- Pikachu -> Gen 1
- Lucario -> Gen 4
- Sprigatito -> Gen 9

After these pass, generate all species rules using `docs/reference/cobblemon_species_1.7.3.csv`.

## Deferred issue

Rapid dimension hopping previously produced a possible multi-track overlap during a heavily lagged test sequence. Because this is unlikely in ordinary survival play and may be an engine/client cleanup issue rather than a datapack mapping issue, it is deferred while higher-impact gameplay layers are implemented.
