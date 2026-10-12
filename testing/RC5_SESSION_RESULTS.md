# RC5 installation and gameplay session

2026-10-11. The user authorized installing RC5, preparing a new test world and testing the four representative locations.

Installed the cumulative RC5 resource pack and selected it in the existing Modrinth profile; retained RC4's resource ZIP. Profile options were backed up under `results/rc5-install-20261011-195337/options-before.txt`. Installed hashes match the build results.

Created **CSMusic RC5 Test 20261011-195339**, a fresh disposable copy of the original RC4 test seed, with RC5 enabled, RC4's copied datapack renamed to `.zip.disabled`, and the inherited companion datapack preserved. Commands and spectator mode are enabled. The original `level.dat` hash is unchanged. The new receipt is `prepared_rc5.json`; the older `prepared.json` and its world/recovery evidence remain intact.

Dry run passed with computed totals **440 tracks / 1355 rules / 24 files**. All 36 offline harness tests passed after adding separate receipt support. No live game commands have been sent yet. Desert Pyramid, Lush Cove, Amphitheater and Bell Tower are pending world readiness. The bounded saved-chunk scout located no existing instances of those targets; live `/locate` and containment checks are necessary.

The user must load the new world, leave Minecraft foreground/unpaused with chat and menus closed, and confirm readiness. Then run the separate RC5 representative suite with audio capture. Do not apply the old RC4 force-load recovery report to this new world; it belongs to the previous copied world.

Installation evidence: `results/rc5-install-20261011-195337/installation.json`. Dry-run evidence: `results/20261011-195426-53d300/report.json`. Current compact status: [RC5_SESSION_RESULTS.json](RC5_SESSION_RESULTS.json).

## First live attempt

Copied-world identity, spectator mode and fresh runtime counts **440/1355/24** passed; zero definitions skipped and zero files rejected. The first Desert Pyramid `/locate` returned (-176, ~, -1984). The unknown height fell back to the current player height, Y86; live diagnostics consistently showed bounds 0 / piece 0 and ambient music, so this was an invalid fixture rather than a music-selection failure. The owned force-load ticket was removed successfully. Other structures and the weather regression were not run after the suite stop.

Saved generated chunk data subsequently provided exact temple bounds [-176,61,-1984,-156,75,-1964]. The candidate is corrected to [-166,68,-1974], pending a fresh live containment check. Renewed foreground/readiness confirmation was requested before restarting, following the harness's blocked-fixture procedure. Report: `results/20261011-200206-98985a/report.json`.

## User-assisted continuation

The corrected pyramid run passed exact native containment and selection. A 30-second WASAPI capture was non-silent and unclipped; BW - Relic Castle ranked above the Pallet negative reference (waveform scores 0.5699 vs 0.0699). The matcher remains uncalibrated, so its formal audio classification is inconclusive.

The cove run stopped on focus loss after travel. The user descended to the actual ship and heard the music change. The next runtime snapshot independently showed LGPE - The Final Road selected from `structures_cobblemon.json#0` at priority 41 at that manually adjusted position. The interrupted owned cove ticket was recovered. No repeat of the passed pyramid was needed.

Amphitheater travel inherited the ship's Y=-15 and stopped on focus loss while the user moved to the landmark. Saved piece bounds were [4934,65,4691,4976,72,4720]. After the user confirmed standing inside at Y68, a compact current-fixture check recovered the ticket and passed exact native containment and SV - Meloettas Relic Song selection at priority 41. Evidence: `results/20261011-203045-f76277/report.json`.

The Bell Tower locate found Ecruteak at [26800,~,55264]. At the village arrival point, live diagnostics showed Ecruteak bounds 1 / piece 0, with Ecruteak City selected at priority 30. The test correctly blocked as an invalid tower fixture and removed its owned ticket. Saved Bell Tower base bounds are [26703,64,55323,26748,109,55369], with middle/top pieces at Y110-157 and Y158-205. The corrected base candidate is [26725,86,55346], pending renewed foreground readiness and a compact loaded-terrain capture check. Village-point evidence: `results/20261011-203215-f132ec/report.json`.

Full weather, battle, entry/exit and vertical-piece transition scenarios remain pending; current work is the user's four-location smoke check. Failed locate-height fixtures and focus stops are recorded as controller/fixture limits, not RC5 music-selection failures.

## Final four-location sample — passed

| Location | Result | Evidence |
|---|---|---|
| Desert Pyramid | Automated exact native containment and BW - Relic Castle selection at 41; audio captured separately | `results/20261011-201121-1ad5fa/report.json`, pyramid scenario |
| Lush Cove | User stood on the actual ship and heard music change; subsequent runtime snapshot selected LGPE - The Final Road at 41 | User confirmation plus `results/20261011-202423-aaf05a/report.json`, root playing source |
| Amphitheater | User-assisted position; exact native containment and SV - Meloettas Relic Song selected at 41 | `results/20261011-203045-f76277/report.json` |
| Bell Tower | Saved native-bounds candidate, already-loaded destination and spectator travel verified; exact Bell Tower base piece detected; HGSS - Bell Tower 41 overrides Ecruteak City 30 and ambient 10 | `results/20261011-204234-cb896e/report.json` |

The final Bell position is [26725.5,86,55346.5]. The earlier outside-tower village snapshot selected Ecruteak City at 30 with no matching piece; the inside snapshot proves exact parent-and-piece override. This is two positional observations, not a continuously observed exit/return transition.

No outstanding force-load tickets are owned by these RC5 runs: successful tests removed their tickets, interrupted cove/amphitheater tickets were recovered, and the final compact Bell check added none. The older RC4 copied world's ticket remains separate and untouched.

These results give representative selection confidence across vanilla, Cobblemon and Legendary Monuments plus the nested-piece override. Full weather/battle/entry-exit/above-bounds regression, Bell middle/top and Burned Tower visits, and loop-seam audition remain pending. Audio capture ranked the expected pyramid track above its negative reference but remains formally uncalibrated. No production rule changes were needed to achieve these passes; fixture coordinates and controller capture support were corrected. No commit or push was performed.
