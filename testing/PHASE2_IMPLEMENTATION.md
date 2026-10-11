# CSMusic Phase 2 implementation and validation

Date: 2026-10-11. Branch: `codex/csmusic-test-harness`. Reviewed base: `34fc8be859a9fb4f729754c431bf4f8a5ffde568`. All edits in this phase are confined to `testing/`; they are local and uncommitted.

## Audit and preservation

The local branch matched the reviewed GitHub baseline before edits. The October 10 ignored evidence and `prepared.json` were present and preserved. The existing copied-world receipt is used only after a fresh runtime token check; no receipt was reconstructed. The source world remains `RC4 Village Test`. No production definitions, mirrored files, package assets, release ZIPs, profiles, or source saves were edited by this implementation.

The October 10 Pallet report was rechecked independently: all 17 reported commands have one complete, ordered fresh BEGIN/END marker pair in `commands.log`, and each recorded response matches a framed response. The temporary force-load ticket was confirmed removed. Fresh parsing classifies the point as `OVERLAPPING_STRUCTURES_EXPECTED_ARBITRATION`: Lavender Town and Pallet Town both have bounds containment; Lavender source `definition:csmusic/definition/villages_cobbletowns.json#1` wins at priority 30 over Pallet source `...#2`. This is valid observed arbitration, not evidence of a Pallet-only fixture or music-engine defect.

## Audio feasibility

The testing environment now pins PyAudioWPatch and NumPy. WASAPI enumeration succeeded and selected `Speaker (Realtek(R) Audio) [Loopback]`, 48 kHz, stereo, matching the default Windows output. This is endpoint loopback and can include audio from other applications; it says nothing about physical speaker output. No capture was made while the desktop was outside a controlled Minecraft test, and no live Minecraft audio sample has been recorded.

The installed RC4 resource-pack ZIP was used in place. Its `sounds.json` contains 416 DysFam events and its archive contains 416 referenced OGG files. The matcher resolves named tracks or every track in a pool without extracting the complete archive. It compares normalized waveform subsequences at several offsets and records a spectral score as a secondary candidate signal.

The actual Pallet and Lavender OGGs were used for synthetic benchmark samples. The waveform rank selected the correct reference for volume-scaled Pallet and Lavender samples, selected no track for silence, and ranked Lavender first for a synthetic two-track overlap. The first spectral-only rank confused the known matching tracks. These tests demonstrate useful candidate-ranking behavior but do not model real Minecraft decoding, fades, crossfades, endpoint resampling, sound effects, or unrelated desktop audio. No threshold is enabled; audio outcomes remain `INCONCLUSIVE_AUDIO` until controlled live calibration supplies false-match evidence.

Installed CobbleSafari 0.3.4 bytecode contains `CsMusicPlayer` and `CsMusicVoice`. Static `javap` inspection found private current-track/current-voice fields, a private voice sample-position field, and constants for 1,000 ms synchronized crossfade, 5,000 ms crossfade, and 2,500 ms fade. Ordinary logs expose OpenAL device initialization and sound-engine startup plus decode/resource errors, but no normal track start/stop telemetry. No production mod was changed; an optional test-only bridge remains future work.

## Controller and suite changes

- Music parsing retains runtime source key, rule index, selected track or pool, priority, and winning status. Suite paths map to runtime `definition:csmusic/...json#N` keys. Smoke and scenario reports preserve the exact winner.
- Fixture diagnosis separates a valid single fixture with a wrong winner, expected arbitration at an overlapping structure, an invalid fixture, and missing diagnostics. A music failure requires the exact expected source to be visible and the verified fixture to be unambiguous.
- Daylight-cycle changes now persist the original and intended values before command submission. Recovery verifies the copied-world receipt and current gamerule, restores idempotently, and rechecks the result. Interrupted commands retain recovery state. Cleanup commands still require Minecraft focus.
- A resumed command opens chat, selects the entire existing line with Ctrl+A, then types the new command. Mock tests simulate a partially typed command interrupted before Enter and verify the replacement. No live interruption was induced.
- Controller, parser, screenshot, dependency, and evidence exceptions remain blocked/inconclusive with original exception details; they do not become `FAIL_SELECTION` or `FAIL_AUDIO`.
- Teleport readiness checks world identity, exact XYZ, loaded destination, structure bounds, repeated stable source selection, and screenshots within configurable limits. It waits at least 35 seconds, polls every 7 seconds, and times out at 180 seconds by default. Screenshots include a configurable top-right minimap crop; pixels are retained as corroboration, never treated as authoritative structure evidence.
- The default representative plan adds BCA, Terralith, CobbleTowns, Legendary Monuments, Pallet weather and Twinleaf boundaries. Quick, diagnostic, and exhaustive plans are invokable through PowerShell. Audio, device inventory, identification, synthetic benchmarking, and verified recovery also have PowerShell modes.
- Blocked fixture/loading/focus reports can issue a Windows alert and actionable assistance note. The run stops; it does not refocus Minecraft or resume automatically. The user must make the requested change and start a fresh invocation.

## Validation and gameplay status

The offline unit suite passes 20 tests, including parser identity, equal-pool source separation, the Pallet/Lavender overlap regression, wrong-selection classification, gamerule interruption/recovery, stale-chat cleanup, and synthetic waveform matching. Python compile, PowerShell parse, `audit`, `dry-run`, and WASAPI device enumeration succeeded. The synthetic audio benchmark is saved under ignored `testing/results/`.

Two live selection diagnostics were then run in the receipted copied world with the user-confirmed Minecraft foreground. The Pallet lookup at `(-3664, 68, 720)` returned both Pallet and Lavender with `bounds: 1`; both were eligible at priority 30 and Lavender source `#1` won over Pallet source `#2`. The harness recorded `OVERLAPPING_STRUCTURES_EXPECTED_ARBITRATION`, retained screenshots, verified stable loaded state, and cleaned up its force-load ticket. The complementary Lavender case at `(-3712, 91, 720)` returned Lavender `bounds: 1` and Pallet `bounds: 0`; Lavender source `#1` won and the result was `PASS_SELECTION`. Detailed reports are [here](results/20261011-152306-492b67/report.md) and [here](results/20261011-152808-d4cec2/report.md).

These results confirm live selection behavior at those two points, not audible playback. A Pallet-only waypoint, real loopback capture, audio calibration, battle fixtures, tower entry/exit, and the rest of representative live coverage remain unverified. Historical October 10 smoke remains a separate pass. No production file or source save was changed.

Long-range alternate-instance search and automated visual scene classification are intentionally not claimed: there is no independently verified safe search origin, and screenshots do not establish semantic structure identity. Those cases stop for assistance instead of guessing. No audio threshold or failure category is inferred from synthetic signals.

## Next validation

The immediate follow-up for a Pallet-specific pass is to identify and verify a Pallet-only waypoint, then run that case independently. Capture live audio only during a controlled known-track run; compare it against both town tracks, record uncertainty, and keep audio non-gating until calibration is repeatable. The remaining representative suite should be run and reported scenario by scenario.
