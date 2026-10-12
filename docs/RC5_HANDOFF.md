# RC5 standalone handoff

Planning completed 2026-10-11 with explicit deferrals. **Implementation has NOT begun. Await user approval of `RC5_IMPLEMENTATION_PLAN.md` before production edits or tests.** No commit or push was made.

## Start here

Repository: `D:/Minecraft Stuff/Minecraft Datapacks/DysFam_CSMusic_Ambient_RC1_Datapack`.
Remote: `https://github.com/JaimeG33/Cobblemon-Music-Datapack-Temp`.
Baseline branch `codex/csmusic-test-harness`, commit `6a974fb509dcd58603cf17e7b7d54df48742dab5`. Starting worktree was clean; this session adds five `docs/RC5_*` planning files only. Preserve later user changes.

Read in order:
1. `RC5_IMPLEMENTATION_PLAN.md` for scope and approval choices.
2. `RC5_STRUCTURES_MAPPING.csv` for all 47 original condition rows and exact evidence.
3. `RC5_STRUCTURES_RESEARCH.md` for special-case details, sources, counts and hashes.
4. `RC5_STRUCTURES_PROGRESS.md` for checkpoints and current completion state.

## Inputs already located

- Final assignments: `C:/Users/Jaime/Downloads/CSMusic_Reference_Excel_Files/Music Pack Conditions & Music(2)_2.xlsx`, Structures A/B/C/D/G. E/F are RC6 interiors. 47 conditions, 33 groups, 32 songs.
- Historical companion: same folder, `DysFam_CSMusic_Master_Implementation_Mapping_v3(2)_2.xlsx`; old statuses/IDs do not supersede code or installed archive evidence.
- **Source audio moved:** `D:/Minecraft Stuff/Minecraft Datapacks/CSMusic Sources/DysFam Music OGG Files.zip`. Do not stop at the absent Downloads copy or rebuild without passing this path.
- Profile `D:/Minecraft Stuff/ModrinthApp/profiles/DysFam Cobblemon 2.0 6.0.0`: Minecraft 1.21.1, Cobblemon 1.7.3, Safari 0.3.4, LM 8.1, Mega Showdown 1.9.5, Terralith 2.6.2.
- Source manifest `DysFam_CSMusic_Ambient_RC1_Package/manifest/csmusic_release_assets.csv`.
- Track definitions `data/dysfam_music/csmusic/*.json`; trigger rules **`data/dysfam_music/csmusic/definition/*.json`** (not a csmusic_triggers folder).
- Mirror under `DysFam_CSMusic_Ambient_RC1_Package/datapack/`.

## Findings and recommended decision

38 direct structure conditions have exact archive-verified IDs. Two tower conditions use seven exact Ecruteak pieces. Three lake interior rows have verified parents but only candidate center-piece detection. Four unresolved locations: future lava cove plus Groudon volcano, Kyogre sea and Sky Pillar, whose providers/IDs are unlocated in installed resources.

Recommend first RC5 scope **40 conditions** (38 direct + two towers), defer the four unavailable locations and three lake interiors. Play PLA - Lake across whole lake bounds until a cave-only native footprint is proven. Ask approval for this explicit limitation; do not silently claim the original full sheet is implemented.

All 32 audio files exist with exact matching labels and Ogg/Vorbis headers. Complete scope would add 30 tracks/events and reuse two. Recommended initial scope adds **27**, reuses Heatran's existing XY - Team Flare Secret HQ, and leaves ORAS - Drought's ambient registration untouched. Counts: baseline 407 tracks/1306 rules/16 files/416 events; recommended tracks/events 434/443. Rules/file totals depend on final approved expansion; derive them.

Do not guess IDs for absent landmarks. No proximity padding, compatibility mod, mod update, area creation or biome substitution authorized. Thalic Pyramid is LM in the Overworld; Heatran is Nether; Eternatus and Hoopa are End. Seasonal mage towers are separate structure variants. Bell/Burned Tower need parent plus piece matching; same song shared across segments. Lake `3x3` template boxes are 37x48x37 and are not proven cave-only.

Preserve all existing ambient tags and RC1–RC4 definitions, including Pokemon Tower 30. New structure priority 41, battle never; hierarchy 10/30/40/41/42/50/60. Future roadmap: RC6 specific interiors, RC7 advanced battles.

## Next exact action

Before approval: review the two scope choices in the plan with the user; stop before coding.

After explicit approval: recheck Git and input versions, record approved deferrals, inspect the force-load recovery prerequisite, then follow the plan. Use new RC5 builders; RC4 scripts hardcode their counts and output paths. Do not run the historical RC4 generator against cumulative RC5 files. No commit/push/publish unless separately authorized.

## Live-testing prerequisite and limits

No live testing or cleanup occurred during planning. Final RC4 report records owned force-load block XZ (-3520,4352), copied world `CSMusic Automation 20261010-192614`, no pending daylight restoration. Once approved and that world is ready, use existing recovery command with `testing/results/20261011-175431-061aa5/recovery-target.json`; inspect ownership if this ignored local file is unavailable. Never clear unrelated tickets or touch original saves.

Then use a small suite: vanilla structure, cove, LM landmark, tower nesting, native entry/exit, weather and battle interaction, one actual audio check. Archive IDs and header checks are planning evidence, not gameplay or decoded-audio results. The implementation plan describes exact gates and safe sequencing.
