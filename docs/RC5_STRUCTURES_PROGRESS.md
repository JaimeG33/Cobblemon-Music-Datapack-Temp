# RC5 structures planning progress

## Initial checkpoint — 2026-10-11
- Repository confirmed: JaimeG33/Cobblemon-Music-Datapack-Temp.
- Branch: `codex/csmusic-test-harness`; HEAD: `6a974fb509dcd58603cf17e7b7d54df48742dab5`.
- Initial Git working tree clean. No applicable ancestor AGENTS.md found.
- Task: research, workbook mapping, audio inventory, feasibility and implementation plan only. User accepts RC4 as sufficient to proceed with planning.
- Do not change production data/assets/manifests/builders/configuration/worlds; no builds, gameplay, commits, pushes or publishing. Implementation requires explicit approval.
- Roadmap: RC5 general structures; RC6 interiors; RC7 advanced battles. Preserve priorities 10/30/40/41/42/50/60, battle never for structures, native bounds, no proximity padding.
- Brief: `C:/Users/Jaime/.codex/attachments/d86970e7-8e8f-49d7-a3df-504d74ce26e9/Pasted text.txt`.
- Pending: locate authoritative workbooks; audit worksheet; inspect installed archives; inventory audio; resolve detection; write mapping/research/plan/handoff; verify documentation-only diff.
- Initial expected counts (not yet verified): 47 conditions, 33 groups, 32 songs, 2 reusable and 30 new registrations.
- Next exact action: read spreadsheet skill and project research/build documentation; locate Downloads workbooks and installed relevant archives.

## Workbook and initial archive checkpoint
- Both exact finalized workbooks located under `C:/Users/Jaime/Downloads/CSMusic_Reference_Excel_Files/` and read through OOXML, preserving addresses.
- Source audio ZIP found at `D:/Minecraft Stuff/Minecraft Datapacks/CSMusic Sources/DysFam Music OGG Files.zip`; old Downloads path is absent. No source replacement needed.
- General scope uses Structures columns A/B/C/D/G; E/F reserved for RC6. Exact labels include `Ampitheater`, `Dragon Spiral Tower`, `Thalic Pyramid`.
- All 32 expected song filenames appear in ZIP Structures directory. Detailed registration/header audit pending.
- Installed archives: Cobblemon 1.7.3, CobbleSafari 0.3.4, Legendary Monuments 8.1 Love_for_All, Mega Showdown 1.9.5, Terralith 2.6.2.
- Thalic Pyramid is Legendary Monuments, despite workbook's Vanilla column. Both current cove IDs exist; lava cove absent from Cobblemon structure entries.
- Bell/Burned Tower are Ecruteak template pieces, not registered standalone structures. Lake exterior registry IDs exist; interiors unresolved. Groudon/Kyogre/Sky Pillar absent from primary LM structure list; targeted installed archive scan running.
- CobbleSafari When DTO confirms dimension, biome, biome_tag, time_range, weather, area, area_tag, battle, species, form, structure, structure_piece. No arbitrary height field.
- Reusable definitions are `structures_oras_drought` and `structures_xy_team_flare_secret_hq`, both tagged `dimension_nether_wastes_basalt`; preserve existing use.
- Next exact action: finish archive scan; inspect lake template NBT and tower pool links; produce row mapping and definitive audio audit.

## Mapping and audio checkpoint
- Saved `docs/RC5_STRUCTURES_MAPPING.csv`: 47 condition rows, original condition/music cells, 33 assignment groups, 32 distinct songs.
- Categories: 38 A (whole-structure), 5 B (two tower piece mappings plus three lake interior candidates), 0 C, 4 D (lava future-version plus three unlocated landmarks).
- 39 distinct parent/whole structure IDs verified in installed archives, covering 43 condition rows. This is archive evidence, not runtime confirmation.
- Audio inventory: all 32 exact labels match unique ZIP basenames and Ogg/Vorbis headers. Two reusable manifest registrations; 30 new tracks, 93,665,466 bytes (~89.33 MiB). No spelling substitutions or split intro/loop/outro files needed by inventory; seam quality not auditioned.
- Confirmed baseline: 407 tracks / 1306 rules / 16 definition files; installed RC4 resource ZIP 416 events and 416 OGGs. Root and mirrored data bytes match.
- Dimensions: Heatran Nether; Eternatus and Hoopa End; Thalic Overworld (confirmed Lithostitched injector). No custom dimension substitution for missing landmarks.
- Lake center candidates `legendarymonuments:lake_guardians/lake_{acuity,valor,verity}/3x3` have 37x48x37 NBT bounds and trial-spawner rooms. No precise cave-only semantic boundary proven. Recommend deferring interiors pending bounded runtime inspection after approval.
- Recommended initial implementation scope forming: 38 direct conditions plus Bell/Burned Tower (40 conditions); defer lava and three absent landmarks, and initially defer three lake interiors. This would require 27 new registrations + 1 reused Heatran event; retain Drought unchanged in ambient.
- Next exact action: write research/implementation/handoff documents; cross-check override and mirror scope; verify only five planning files changed.

## Final checkpoint — research complete with scoped unresolved cases

All five requested documentation deliverables are present:
- `RC5_STRUCTURES_PROGRESS.md`: session checkpoints and continuation status.
- `RC5_STRUCTURES_MAPPING.csv`: 47 rows, original labels/cells, 33 groups, 32 songs, exact evidence and recommended inclusion/defer flags.
- `RC5_STRUCTURES_RESEARCH.md`: archive/audio findings, dimensions, detection limits and deferred cases.
- `RC5_IMPLEMENTATION_PLAN.md`: approval choices, concrete future files, cumulative builds, preservation checks and representative regression plan.
- `RC5_HANDOFF.md`: standalone continuation guide.

Completed research tasks:
- [x] Confirm repo/branch/commit and preserve clean baseline.
- [x] Locate/read exact final workbook and historical companion.
- [x] Resolve installed structure IDs and distinguish pools/templates from registry IDs.
- [x] Verify 39 unique whole/parent IDs supporting 43 rows; classify 38 A, 5 B, 0 C, 4 D.
- [x] Inventory 32 songs; 2 reusable and 30 full-scope additions; verify all Ogg/Vorbis headers, exact unique basenames and source bytes/CRC.
- [x] Confirm both reused packaged OGG CRCs match authoritative source ZIP members and existing definitions/events resolve.
- [x] Audit whole/piece/dimension feasibility, priorities, nesting and source audio reuse.
- [x] Check 264 installed mod/global/saved-world archives for competing root structure definitions: none found for mapped resources.
- [x] Record build/test strategy and outstanding force-load recovery prerequisite; no live action performed.
- [x] Write five deliverables and reconcile recommended scope: 40 included conditions, 7 explicitly deferred, 27 new registrations + 1 reused event in that scope.
- [x] Verify 47 unique condition cells / 33 music cells / 32 labels, 30 full-scope proposed new track IDs without baseline collisions, exact root/mirror file sets and bytes.
- [x] Git audit: only five untracked docs/RC5_* files; no tracked changes, no production changes. `git diff --check` passed (untracked planning files separately parsed/read).

Unresolved by design, not hidden:
- Three lake interiors need proof of precise native cave containment; retain whole-lake fallback unless approved evidence resolves them.
- Three LM-assigned landmarks lack a located installed provider/ID: Groudon volcano, Kyogre sea, Sky Pillar. Recommend defer, not install alternate mods.
- Lava cove unavailable in current Cobblemon 1.7.3; explicit future-version deferral.
- Two tower mappings need routine runtime piece-containment confirmation after approval.
- Full audio decoding and actual playback/seam checks belong to implementation validation; only header/path/CRC checks occurred here.

No user approval of development has been received. No RC5 definitions, manifests, builders or release ZIPs created; no world/mod/config changes; no game launch, automation, cleanup, commit, push or publishing.

Next exact action for a fresh session: read RC5_HANDOFF.md and RC5_IMPLEMENTATION_PLAN.md, obtain explicit approval of the recommended 40-condition scope and seven deferrals. Only after approval recheck Git/input versions, record approved scope, handle the owned-ticket recovery prerequisite before live automation, and follow the phased implementation plan. Do not repeat completed workbook or archive research unless inputs changed.

## Approved implementation checkpoint — 2026-10-11

- User explicitly approved implementation of the recommended 40-condition scope and seven deferrals. Whole-lake fallback retained; no optional lake investigation added.
- Worktree was clean at `a32e94903fcd644505be1542994ce2ad1c429f33` (planning documents had been committed since the recorded baseline). Workbook and relevant mod hashes matched the research.
- Added 27 full-loop definitions and 45 exact rules in five files; Heatran reuses its existing track. Root/mirror runtime and metadata match. Existing RC1–RC4 tracks/rules/tags/manifest records are preserved.
- Built cumulative RC5 datapack/resource-pack ZIPs through dedicated builders; historical RC4 scripts and artifacts remain untouched.
- Passed approved-scope/preservation/schema/archive/source-audio checks and fully decoded all 27 new OGGs. All 36 harness unit tests pass. Counts: 434/1351/21 and 443 events; expected installed runtime 440/1355/24.
- Added separate RC5 harness configuration and representative fixtures. No live test, world edit, installation, cleanup, commit, push or publication occurred.
- User asked why Minecraft needed to be open; clarified that it is needed only for the pending gameplay checks. Building/static work proceeded with it closed.
- Exact hashes, decode metadata and completed/pending gates are in `RC5_BUILD_RESULTS.md` and `RC5_BUILD_RESULTS.json`.
- Next action: when the copied world is explicitly ready, recover the recorded owned force-load using the original RC4 recovery command, stage RC5 in the copied world, and run the small gameplay suite. Native containment/transitions, actual playback and seam audition remain pending. Do not repeat completed research.
