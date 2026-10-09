# RC4 village audio inventory

Source: `C:/Users/Jaime/Downloads/CSMusic_Reference_Excel_Files/Music Pack Conditions & Music(2)_2.xlsx`, Villages sheet. Compared with `C:/Users/Jaime/Downloads/DysFam Music OGG Files.zip` and the cumulative `csmusic_release_assets.csv`.

**127 unique workbook song labels; 128 candidate OGGs if Twinleaf uses both Day and Night.** All candidates exist in the source ZIP. One event/track already exists (`SV - Kitakami`); the other 127 candidates need new manifest rows, sound events and track definitions. Choosing only one Twinleaf version reduces additions to 126. New uncompressed source audio totals 313.12 MiB with both Twinleaf versions; final ZIP size will depend on compression.

[Exact per-track inventory, including workbook cells, pools/towns, source ZIP paths, byte sizes and proposed IDs](reference/rc4_village_audio_inventory.csv). This CSV is a research artifact, not the release manifest.

| Pool | Workbook cells | Songs |
|---|---|---|
| `village_basic_day` | A11:A45 | 35 |
| `village_basic_night` | B11:B39 | 29 |
| `village_magic_day` | C8:C22 | 15 |
| `village_magic_night` | D8:D23 | 16 |
| `village_cold_day` | E7:E18 | 12 |
| `village_cold_night` | F7:F13 | 7 |
| `village_hot_day` | G5:G13 | 9 |
| `village_hot_night` | H5:H12 | 8 |

Tracks appearing in more than one pool should share one definition with multiple tags. Add `village_magic_night` to the existing `villages_sv_kitakami` definition while preserving its current `underground_lush` tag and event. Named town assignments other than Twinleaf have one track without a time split.

## Workbook-to-audio differences

| Workbook label | Exact archive basename | Treatment |
|---|---|---|
| BDSP - Sunnyshore City (Day/Night) | BDSP - Sunyshore City (Day/Night) | Resolve spelling; preserve intended city |
| LGPE - Lavander Town | LGPE - Lavender Town | Resolve spelling; registry is `lavender_town` |
| USUM - Trainers' School | USUM - Trainers School | Resolve punctuation |
| BDSP - Twinleaf Town | BDSP - Twinleaf Town (Day), BDSP - Twinleaf Town (Night) | User decision; recommend day/night rules |

The source archive itself spells `SV - Cascaraffa` and `ORAS - Pacificlog Town` this way; do not silently rename source paths. The town registry is `cobbletowns:pacifidlog_town`. Ignore Villages D32 (`O`) as already instructed.

## Missing assets

No missing source OGG was found after the explicit spelling translations and Twinleaf expansion. Missing release registrations comprise the 127 new candidate rows identified in the CSV (126 if only one Twinleaf file is selected). Confirm OGG headers and all output sound-event references during implementation; this pass inventories source paths and sizes, and does not audition or decode all music.
