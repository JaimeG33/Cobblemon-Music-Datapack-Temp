# Phase 2 session results — 2026-10-11

**Implementation:** offline controller, reporting, audio-feasibility and scheduling work completed locally on `codex/csmusic-test-harness`, based on reviewed commit `34fc8be859a9fb4f729754c431bf4f8a5ffde568`. During Phase 2 validation no commit, push, merge or production change was made. Phase 2 was subsequently committed and pushed at `4bafbefd3e8e92d11c0e39c531497c48a602172d`; this is the reviewed baseline for the final gameplay session.

## What passed

- All 20 offline unit tests passed. They cover source/index identity, shared-pool arbitration, the Pallet/Lavender overlap, stale chat after partial interruption, daylight checkpoints across interruption points, and waveform matching on controlled synthetic signals.
- Python compilation, PowerShell syntax parsing, static audit and dry-run passed.
- WASAPI loopback inventory found the default Realtek output endpoint. The installed RC4 ZIP supplied 416 sound-event mappings and 416 OGG references without extracting the archive.
- Synthetic matcher ranking selected the correct Pallet and Lavender references for their respective volume-scaled samples, returned zero for silence, and did not reliably resolve an overlapping two-track sample. These are reference-derived checks only.
- The prior October 10 evidence was revalidated: all 17 command responses were freshly framed, and the owned force-load ticket was removed. The Pallet point is now correctly described as an overlap arbitration observation.
- The copied-world receipt matches its local copy receipt, and the original `RC4 Village Test/level.dat` hash still matches the stored receipt hash.
- Live Minecraft validation ran against the prepared copy after the user confirmed readiness. The Pallet diagnostic at `(-3664, 68, 720)` loaded, showed both `cobbletowns:lavender_town` and `cobbletowns:pallet_town` with `bounds: 1`, and consistently selected Lavender rule `villages_cobbletowns.json#1` at priority 30. The run was classified `OVERLAPPING_STRUCTURES_EXPECTED_ARBITRATION`, not a wrong-selection failure. See [Pallet report](results/20261011-152306-492b67/report.md).
- A second live diagnostic found a Lavender-only point at `(-3712, 91, 720)`: Lavender had `bounds: 1`, Pallet had `bounds: 0`, and Lavender rule `#1` won. It was `PASS_SELECTION`. See [Lavender report](results/20261011-152808-d4cec2/report.md).
- Both live runs verified world identity and creative mode, captured native screenshots and minimap crops, waited for two stable loaded/bounds/music observations, and removed their temporary force-load tickets. The daylight/weather recovery path completed and was verified.

## What remains unverified

- No live Windows loopback WAV was captured. Audio matching is therefore `INCONCLUSIVE_AUDIO`, no confidence threshold exists, and `FAIL_AUDIO` cannot be emitted.
- A Pallet-only waypoint is still needed before Pallet can pass its intended selection rule independently or before making a Pallet audio claim. The live point is a verified overlap, not a Pallet-only fixture.
- Client playback state is private in the installed CobbleSafari implementation. Logs expose startup/errors, not normal track lifecycle. No test bridge was introduced.
- Battle, tower movement, vertical boundaries, long-distance alternate-instance search, and automated screenshot/minimap interpretation remain untested or blocked on safe fixtures.

The machine-readable details are in [PHASE2_SESSION_RESULTS.json](PHASE2_SESSION_RESULTS.json), and the cumulative layer-by-layer matrix is in [COVERAGE.json](COVERAGE.json). Large local screenshots, logs, synthetic benchmark output, and the copied-world receipt remain under ignored `testing/results/` or `testing/prepared.json` and are not published to GitHub.
