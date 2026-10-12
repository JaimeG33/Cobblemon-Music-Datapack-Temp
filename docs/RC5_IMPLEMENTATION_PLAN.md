# RC5 implementation plan for approval

Status: approved 2026-10-11. The user explicitly authorized implementation of the recommended 40-condition scope and seven deferrals. Whole-lake fallback is approved; optional lake investigation remains deferred. Implementation and static build validation are complete; gameplay QA is pending. See [build results](RC5_BUILD_RESULTS.md). The proposal below is retained as the approved scope and validation specification. Baseline is `6a974fb509dcd58603cf17e7b7d54df48742dab5`; RC4 testing is accepted. See [research](RC5_STRUCTURES_RESEARCH.md) and [47-row mapping](RC5_STRUCTURES_MAPPING.csv).

## Recommended release scope

Implement 38 category-A conditions and the Bell/Burned Tower piece mappings after representative containment checks: **40 workbook conditions, 28 songs, 27 new registrations and one reused registration**. Retain all existing RC4 tracks and rules.

Defer lava cove (requires future Cobblemon), three unlocated LM-assigned landmarks, and three lake-interior overrides. Lake exteriors use PLA - Lake over native whole bounds; this also plays inside until a valid interior override exists. Do not describe deferred conditions as shipped. Keep all 47 rows in the mapping and record decisions there.

Two approval decisions, with recommended defaults:

1. Approve the 40-condition initial scope and defer the four unavailable locations without installing/upgrading mods.
2. Approve whole-lake music as the temporary fallback; defer cave-specific music unless a small post-approval native-bounds inspection resolves it. Do not use overly broad center-piece matching or world-specific areas by default.

## Proposed files and behavior

Nothing below has been created or modified in production.

| Location | Proposed change |
|---|---|
| `data/dysfam_music/csmusic/structures_<normalized_song>.json` | 27 new full-loop definitions for approved scope; mapping contains proposed IDs. Share one registration across repeated conditions. |
| `data/dysfam_music/csmusic/definition/structures_vanilla.json` | Eight actual vanilla structures. Thalic belongs in LM file despite source column. |
| `.../definition/structures_cobblemon.json` | Lush and submerged cove rules only. |
| `.../definition/structures_legendary_monuments.json` | Verified landmarks, whole-lake rules and seven exact tower-piece rules. No missing-location rules. |
| `.../definition/structures_mega_showdown.json` | Wishing Weald. |
| `.../definition/structures_terralith.json` | Six explicit mage IDs sharing Scary House. |
| `DysFam_CSMusic_Ambient_RC1_Package/datapack/` | Mirror approved root runtime changes and metadata exactly. |
| `.../manifest/csmusic_release_assets.csv` | Append approved new songs with exact archive members, normalized destinations, full_loop, structures layer, RC5 release. Preserve existing rows. |
| `.../tools/build_csmusic_rc5_datapack.ps1` | New dedicated cumulative RC5 builder based on forward-slash-safe RC4 behavior. |
| `.../tools/build_csmusic_rc5_resourcepack.ps1` | New dedicated cumulative audio builder with source ZIP path parameter and RC5 outputs. |
| `.../tools/validate_csmusic_rc5.py` | New approved-scope, baseline-preservation, schema/ID/audio/count validator. |
| `testing/` | Add small RC5 scenario set/configuration after approval, preserving RC4 results and existing safeguards. |
| Root/mirror `pack.mcmeta`, release metadata, README and docs | Update cumulative release label/status, roadmap RC5 structures / RC6 interiors / RC7 special battles. Keep Minecraft 1.21.1 formats. |

Use direct `music` references, priority 41, `battle: "never"`, exact `structure` and expected `dimension`. Towers also require exact `structure_piece`; all seven pieces share two song registrations. Refer directly to existing Heatran track; do not change its tag or copy its audio. Drought stays unchanged and gets no new rule while its landmark is deferred.

Order specific overrides before generic parent rules where relevant, but validate actual ascending source keys rather than assuming array index numerics determine every tie. If lake overrides are approved, isolate them in an explicitly earlier-sorting definition file (for example `structures_legendary_monuments_00_interiors.json`) and verify ordering against the exterior file. All remain priority 41. No arbitrary priority increase, proximity padding or invented condition fields.

## Implementation sequence

1. Recheck branch/status and inputs against handoff; preserve other work. Record scope approval and exact deferrals. Ensure relevant installed content/version has not changed.
2. Before any live automation, recover the existing owned ticket as described below. Perform one tower inspection and, only if desired, one bounded lake inspection. Failure of a lake split leaves its override deferred.
3. Add shared audio registrations/definitions for approved songs, using the authoritative source ZIP at its relocated path. Preserve baseline files and existing registrations byte-for-byte where possible.
4. Add vanilla and Cobblemon rules, then conventional LM landmarks, Mega Showdown and Terralith, then tower piece rules. Keep RC4 Pokemon Tower untouched. Mirror runtime content.
5. Add dedicated RC5 builders and validation; update metadata/docs. Calculate counts from approved rules and assets. Do not overwrite RC4 output paths.
6. Run static validation, build cumulative RC5 releases, inspect ZIP structure and output references, then perform the small representative runtime suite in the copied test world. Install test releases only under the approved implementation/testing scope.
7. Record results, deferred rows, exact build hashes and remaining limits. No commit, push or publication without separate authorization.

## Build and preservation strategy

RC4 builders hardcode 407/1306/16 and 416. Leave those scripts and existing RC4 artifacts intact. Prefer separate RC5 builders; do not invoke the RC4 generator on RC5 cumulative sources because it assumes its historical manifest baseline and refuses unexpected layers.

Use the explicit source ZIP path `D:/Minecraft Stuff/Minecraft Datapacks/CSMusic Sources/DysFam Music OGG Files.zip`; old Downloads default is stale. Selectively copy required manifest members, never bulk-extract the library. Generate `assets/dysfam_music/sounds.json` from the cumulative manifest with streaming music entries and retain existing event paths. Reject missing/duplicate source members, duplicate track/event/destination IDs, invalid OGG headers, unresolved loops and mismatched counts.

Outputs should be `DysFam_CSMusic_Ambient_RC1_Package/build_output/DysFam_CSMusic_RC5_Datapack.zip` and `.../DysFam_CSMusic_RC5_ResourcePack.zip`, plus validation reports and hashes. Resource pack is cumulative, not an RC5-only delta. Keep pack.mcmeta and data/assets at archive roots, normalize every ZIP separator to `/`, reject backslashes, duplicate entries and parent-path wrapping.

Expected approved-scope counts: 434 project track definitions and 443 events/OGGs. A five-file design with 38 whole-structure rules plus seven exact tower-piece rules would add 45 rules: **illustrative 1,351 rules and 21 definition files**. These are derived estimates, not hardcoded acceptance constants until scope/piece expansion is final. Compute source and output counts independently and reconcile them with baseline plus the approved mapping. Existing CobbleSafari defaults add 6 tracks / 4 rules / 3 files in the RC4 environment; confirm that separately from project counts.

If only the 38 A conditions ship, 25 new registrations give 432 tracks/441 events. If towers join (recommended), 434/443. If precise lake interiors also join, 435/444. All 30 possible additions would give 437/446, requiring resolution of absent landmark providers. Lava uses an already-needed song, so its future rule adds no audio.

## Static validation gates

- Every approved worksheet condition has a rule or documented piece expansion, and every deferred condition remains absent from production triggers. Compare exact cell/song provenance to CSV, not reconstructed display names.
- Compare all existing track definitions, 1,306 rules and manifest rows against baseline commit; detect accidental changes, removals and duplicates. Preserve all 1,016 generic species battle rules and priority 50.
- Verify root/mirror file sets and byte equality, including metadata.
- Parse all JSON; validate actual CobbleSafari 0.3.4 DTO semantics using the existing Java schema helper approach. Structure IDs belong to worldgen/structure, piece IDs to referenced single-pool templates; never treat a pool ID alone as registration proof.
- Validate 41/never/dimensions and table-driven selection: ambient outside, structure inside, weather loses inside, exploration disabled in battle, tower beats Ecruteak. Test equal-priority ordering only for actual overlaps.
- Verify existing 416 event mappings preserved; all new full loops resolve; reuse creates no duplicate OGGs. Decode new files, inspect duration/channel/sample metadata, and audition representative seams. Header verification in planning is not full audio validation.
- Inspect built ZIPs independently for counts, paths, event/asset references, correct metadata and unchanged cumulative layers. Save hashes.

## Small runtime regression suite (not run during planning)

Reuse the existing harness's copied-world, focus, clipboard, stop-latch, ownership and audio-fingerprint controls. Add only needed RC5 cases; no exhaustive structure hunt.

| Case | Evidence to capture |
|---|---|
| Vanilla Desert Pyramid or Stronghold | Exact registered structure at player XYZ; entry, inside, outside and above native bounds; intended song. |
| Cobblemon Lush/Submerged Cove | Conventional modded parent match with water/vertical bounds. |
| LM Snowpoint Temple or Amphitheater | Native landmark containment; one exit to ambient. |
| Bell Tower within Ecruteak | Exact piece ID; transitions through vertical pieces; tower 41 to village 30 on exit. |
| One mapped structure in active weather | Structure 41 beats weather 40; weather resumes on exit where applicable. |
| Existing generic battle regression | Exploration never matches in battle; priority-50 track remains eligible and structure resumes afterward. |
| One real structure audio check | Selected track plus captured playback fingerprint/audible confirmation; selection alone is insufficient. |

If lake interiors are investigated, capture inside cave, center island outdoors, adjoining tiles and full XYZ/bounds; enable overrides only if native piece geometry satisfies the intended split. Do not manufacture a gameplay pass from archive existence. Record pending cases honestly.

### Mandatory recovery before future live automation

`testing/FINAL_GAMEPLAY_SESSION_RESULTS.md` records one owned force-load ticket at block XZ **(-3520,4352)** in copied world `CSMusic Automation 20261010-192614`. It stopped before freezing daylight, so no daylight-cycle restoration is pending.

After approval and only with that copied world loaded, foreground and ready, inspect the local recovery target and use the established command:

`./testing/run.ps1 recover -RecoverReport testing/results/20261011-175431-061aa5/recovery-target.json`

The recovery target is ignored local evidence and may not exist in a fresh checkout. If absent, recover its ownership context from the consolidated final report before any action. Remove only the recorded owned ticket; never broad-clear all force-loads. Do not run cleanup in this planning phase. Prior live automation approval should not be inferred to waive the harness readiness checks.

## Approval boundary

The original planning phase authorized only five RC5 documents. The user explicitly approved implementation on 2026-10-11, covering the recommended 40-condition scope and seven deferrals, dedicated builders, cumulative packages and documented validation. Implementation/build validation is complete; gameplay is pending copied-world readiness. No commit/push/publication is included.
