# RC4 final gameplay session - 2026-10-11

**Session closed: beta candidate; no confirmed RC4 defect.** All completed representative selection checks passed. Jaime manually verified village music -> battle music -> village music after fleeing. Weather and village-boundary behavior remain unverified in this session. This is an assessment, not publication of an RC4 release.

Reviewed baseline: Phase 2 pushed at `4bafbefd3e8e92d11c0e39c531497c48a602172d`. Jaime authorized committing and pushing the final testing changes on 2026-10-11. Changes are scoped to `testing/`; production rules, resources, release artifacts and the source save were not edited. Raw screenshots, WAVs and command logs remain local and excluded from Git; their structured results are included here and in the JSON report.

| Release question | Current evidence |
|---|---|
| 1. Loading correctly? | Yes: fresh 413 definitions, 1,310 rules, 19 files; zero skipped/rejected. |
| 2. Representative village categories? | PASS_SELECTION: BCA basic/magic/cold; Terralith basic/hot, daytime. Basic night/day regression pending. |
| 3. Named settlements? | PASS_SELECTION: Lavender, Cherrygrove, Twinleaf daytime. Ecruteak BLOCKED_FOCUS; other towns unverified. |
| 4. Twinleaf/Tower transitions? | Tower -> Lavender -> Tower passed exact piece/source checks. Twinleaf exact ticks skipped at Jaime's request; daytime passed. |
| 5. Weather/battle overrides? | Rain/snow/thunder regressions NOT_RUN. PASS_MANUAL: Jaime heard village -> battle -> village after fleeing; exact track/priority not independently recorded. |
| 6. Correct audio output? | Three real non-silent, unclipped WAVs rank expected named tracks/valid pool member above Pallet. INCONCLUSIVE_AUDIO until controlled calibration; client start/stop telemetry unavailable. |
| 7. Genuine RC4 defects? | None confirmed; observed interruptions are harness/input/fixture problems. |
| 8. Untested? | Twinleaf exact ticks skipped; generic night, weather, ambient/boundary, weather-plus-battle and outside-village battle unverified; Ecruteak/unsampled towns and transition/SFX/nonmatch audio controls unverified. |
| 9. Release recommendation? | Reasonable beta candidate. Stable-release evidence remains incomplete for shared weather/fallback behavior and calibrated audio. No confirmed RC4 defect blocks beta consideration. |

Selection passes do not imply audible playback. The user tentatively reported Lavender constantly playing; manual track identity/physical output remain unconfirmed.

## Automated run history

- [audit](results/20261011-160439-e9ef36/report.json): **PASS_STATIC**, 12.686 seconds.
- [cobbletowns_lavender_town_1](results/20261011-160519-258098/report.json): **PASS_SELECTION**, 407.917 seconds.
- [capture](results/20261011-161351-6f6ae9/report.json): **CONTROLLER_OR_EVIDENCE_ERROR**, 69.271 seconds.
- [capture](results/20261011-162317-5af6a4/report.json): **BLOCKED_CHAT_STATE**, 74.247 seconds.
- [representative](results/20261011-162827-bba133/report.json): **BLOCKED_SCENARIOS**, 330.48 seconds.
- [representative](results/20261011-164113-d08c27/report.json): **BLOCKED_SCENARIOS**, 1014.391 seconds.
- [representative](results/20261011-170209-346cd8/report.json): **BLOCKED_SCENARIOS**, 2490.513 seconds.

- [final regression retry](results/20261011-175431-061aa5/report.json): **BLOCKED_SCENARIOS**, 382.748 seconds. Fresh loader checks passed and travel to another Twinleaf candidate was verified; focus/abort stopped the run before containment or time-boundary results. Weather scenarios NOT_RUN.

## Manual result and requested testing policy

Jaime reported: "It went from village music, to battle music, then back to village music after I fled." This is **PASS_MANUAL** for audible battle override and return in one unspecified village. Mod, coordinates, generation, exact track and priority were not captured; it is not an automated diagnostic pass.

Future testing should take the minimum time needed for meaningful representative coverage:

- Start with one affected village per mod, not every variant. Add distinct changed behaviors only where the change requires them.
- Check shared weather and day/night conditions at one suitable fixture. If a second fixture also passes, stop repeating equivalent combinations. Rain and snow require suitable biome classifications rather than expecting the same precipitation everywhere.
- Expand coverage when a failure, contradictory evidence, or materially different rule warrants it. Use manual checks when automation costs more time than it saves.
- Shared rules provide indirect confidence for untested variants; record those variants as unsampled, not individually passed.
- Twinleaf exact boundaries were explicitly declined by Jaime and will not be resumed. No further live test is scheduled by this report.

The `representative` preset now selects BCA basic, Terralith hot and Cherrygrove, plus one BCA shared rain/thunder and basic day/night regression. Other fixtures remain individually callable for a specific need. This is a future preset; changing it does not alter the historical executed plan or create new passes.

The elapsed time and repetition were disproportionate to the change: controller repairs, fresh identity/input checks, reloads, loading waits and interrupted retries dominated the session. Those costs are harness findings, not evidence of RC4 defects.

## Verified travel/fixtures

| Case | Verified XYZ | Horizontal / vertical displacement | Loaded stable | Source/music |
|---|---|---|---|---|
| bca_village_default_small_0 | [-877.5, 64.0, -382.5] | 3034.989 / -32.493 | 111.1s, 2 observations | definition:csmusic/definition/villages_generic.json#0 -> #village_basic_day @ 30 |
| terralith_fortified_village_26 | [-2181.5, 70.0, -575.5] | 1318.205 / 6.0 | 108.3s, 2 observations | definition:csmusic/definition/villages_generic.json#26 -> #village_basic_day @ 30 |
| bca_village_dark_small_12 | [-4735.5, 70.0, -4191.5] | 6.391 / -5.256 | 112.3s, 2 observations | definition:csmusic/definition/villages_generic.json#12 -> #village_magic_day @ 30 |
| bca_village_ice_small_20 | [-8943.5, 70.0, -4207.5] | 4208.03 / 0.0 | 110.7s, 2 observations | definition:csmusic/definition/villages_generic.json#20 -> #village_cold_day @ 30 |
| terralith_fortified_desert_village_28 | [-6543.5, 70.0, 272.5] | 5082.362 / 0.0 | 113.3s, 2 observations | definition:csmusic/definition/villages_generic.json#28 -> #village_hot_day @ 30 |
| cobbletowns_cherrygrove_city_3 | [-6831.5, 70.0, -479.5] | 805.263 / 0.0 | 108.9s, 2 observations | definition:csmusic/definition/villages_cobbletowns.json#3 -> dysfam_music:villages_hgss_cherrygrove_city @ 30 |
| cobbletowns_twinleaf_town_5 | [-6847.5, 70.0, -4127.5] | 3648.035 / 0.0 | 107.6s, 2 observations | definition:csmusic/definition/villages_cobbletowns.json#5 -> dysfam_music:villages_bdsp_twinleaf_town_day @ 30 |
| pokemon_tower_enter | [-3686.5, 95.0, 697.5] | 5768.236 / 25.0 | 107.4s, 2 observations | definition:csmusic/definition/villages_cobbletowns.json#0 -> dysfam_music:villages_lgpe_pokemon_tower @ 30 |
| lavender_outside_tower | [-3711.5, 91.0, 720.5] | 33.971 / -4.0 | 106.5s, 2 observations | definition:csmusic/definition/villages_cobbletowns.json#1 -> dysfam_music:villages_lgpe_lavender_town @ 30 |
| pokemon_tower_reenter | [-3686.5, 95.0, 697.5] | 33.971 / 4.0 | 118.5s, 2 observations | definition:csmusic/definition/villages_cobbletowns.json#0 -> dysfam_music:villages_lgpe_pokemon_tower @ 30 |

Lavender initial proof: `(-3711.5,91,720.5)`, movement 125.547 horizontal / -1.352 vertical, safely probed terrain, repeated bounds/source observations. Subsequent tests use user-authorized spectator mode: floor/headroom waived, gamemode/XYZ/loading/containment/source reverified. Cached candidates never substitute for live diagnostics. BCA road images are retained; later per-batch images hit the configured screenshot cap, explicitly recorded rather than treated as visual passes.

## Audio calibration

| Live sample | Leading waveform score | Negative / next score | Result |
|---|---|---|---|
| Lavender | 0.669720 | Pallet 0.158248; margin 0.511472 | INCONCLUSIVE_AUDIO |
| BCA magic | Valid pool member ORAS Lilycove 0.437449 | Fortree 0.284367; Pallet 0.129991 | INCONCLUSIVE_AUDIO |
| Cherrygrove | Expected 0.396846 | Pallet 0.101388; margin 0.295458 | INCONCLUSIVE_AUDIO |

Each WAV is 30.016 seconds, stereo 48 kHz, captured from the automatically verified default Realtek WASAPI loopback. RMS: Lavender 503.596; magic 283.327; Cherrygrove 232.102. All unclipped. Magic compared every valid pool member plus Pallet. Post-capture identity/position/selection checks passed for magic and Cherrygrove. Scores are correlation/ranking evidence, not confidence percentages. Endpoint mix may contain other applications. Reference ZIP was read in place; OGGs use FFmpeg; our PCM16 WAVs decode natively and use linear resampling, an explicit calibration limitation. No PASS_AUDIO or FAIL_AUDIO threshold exists.

## Harness/input/fixture findings

- The first BCA lookup `(-4608,~,192)` found no safe surface: no teleport, owned ticket removed. Spectator testing then validated the saved road candidate.
- Xaero waypoint manager screenshot is bound to U. Command entry previously assumed slash opened chat after 0.2 seconds; leaked letters/numbers into gameplay/creative inventory are the leading explanation for the menu and reported spruce items. Exact item acquisition was not captured; user discarded them and later inventory data was empty.
- Fresh selected-slash copy is now required before command text; fresh exact command copy before Enter. Transient clipboard locks have bounded guarded retries. Copies consume controller text on the clipboard; unrelated contents are never logged. Focus/stop aborts stay latched.
- Suite constructor now accepts plans without individual case IDs; unvisited cases are explicitly NOT_RUN. Short spectral-reference anchors are clamped. WAV decoder repaired because bundled FFmpeg lacks WAV demuxing.
- Spawn announcements in framed responses previously reset raw-text stability. Semantic structure/loaded comparisons ignore unrelated broadcasts while full logs remain intact. Original magic attempt remains BLOCKED, not retroactively counted as a pass; corrected retry passed.
- In-game tellraw/playsound were verified for diagnostics and assistance with recording stopped. Notifications are rate-limited; Windows dialog/beep disabled. Focus loss during Ecruteak prevented in-game notification; only terminal/report fallback was used.

## Preservation/checks

33 offline tests passed. Python compilation, PowerShell parsing, JSON and diff checks passed during the session; final verification results are also retained in the structured report. Copy receipt matched and original source level.dat matched its stored hash. Source save, production definitions/resources/release ZIPs and unrelated mod/generation configs were not edited. Owned force-load tickets were cleaned up in completed scenarios. The final interrupted Twinleaf attempt retains one owned ticket at block XZ `(-3520,4352)`; it stopped before freezing daylight, so no daylight-cycle restoration is pending. No game input was resumed during reporting. A derived local recovery report exposes this scenario to the existing recovery command while preserving the original report: with the copied world foreground and chat closed, run `./testing/run.ps1 recover -RecoverReport testing/results/20261011-175431-061aa5/recovery-target.json`. This small recovery target is local ignored evidence, not uploaded; its original scenario and ownership are retained in the consolidated JSON.

See [structured evidence](FINAL_GAMEPLAY_SESSION_RESULTS.json), [coverage matrix](COVERAGE.json), [menu incident](results/input-leak-incident-20261011/incident.json), [Lavender WAV](results/20261011-160519-258098/audio-loopback.wav), and both audio WAVs linked by the second representative report. Large WAVs, screenshots and command logs remain ignored local evidence.
