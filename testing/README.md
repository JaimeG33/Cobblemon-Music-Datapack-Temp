# CSMusic testing harness

The Windows controller tests RC4 using a verified, disposable copy of `RC4 Village Test`. It edits only files under `testing/` in this repository and test-only files in that copied world. It never changes production trigger rules, release ZIPs, or the source save.

Phase 2 was pushed at `4bafbefd3e8e92d11c0e39c531497c48a602172d`. Final gameplay session changes stay local under `testing/`.

## Setup and run modes

From the repository root in PowerShell:

```powershell
.\testing\run.ps1 setup
.\testing\run.ps1 self-test
.\testing\run.ps1 audit
.\testing\run.ps1 dry-run
```

When Minecraft is closed, `prepare` makes a timestamped `CSMusic Automation ...` copy and writes an identity receipt. The local October 10 copy is described by ignored `testing/prepared.json`; only use it after the controller verifies its receipt and fresh in-game identity. The source save remains `RC4 Village Test`.

Launch the existing Modrinth profile, load the copied world, leave the game unpaused and at a safe state, close chat/menus, and keep Minecraft in the foreground. The controller will not steal focus. Supported play modes are:

```powershell
.\testing\run.ps1 smoke
.\testing\run.ps1 quick
.\testing\run.ps1 representative
.\testing\run.ps1 diagnostic
.\testing\run.ps1 exhaustive
.\testing\run.ps1 structure -Case pallet_town
.\testing\run.ps1 regression -Case twinleaf_exact_boundaries
```

`quick` runs smoke plus Pallet Town selection. The default `representative` plan covers BCA basic/magic/cold, Terralith basic/hot, Pallet, Twinleaf day, Lavender Town and Pokémon Tower, and Ecruteak, followed by the Pallet weather and Twinleaf boundary sequences. `diagnostic` expands to more variants; `exhaustive` visits every configured structure and then the supported representative sequences. Static coverage and live scenario results remain separate. These plans do not claim unvisited structures passed.

Runs use bounded `/locate` and travel. They do not generate distant terrain or guess safe alternate coordinates. An ambiguous or inaccessible fixture stops with a BLOCKED category and asks for actionable user help; a later invocation rechecks identity and focus. The known Pallet/Lavender overlap is an arbitration case, not a Pallet-only pass or a proven music defect. Travel records include initial/final XYZ, locate/probe coordinates, exact teleport command/response and horizontal/vertical displacement. Safe floor and headroom do not establish whether a surface is a rooftop: inspect retained images when that distinction matters. The Lavender candidate waypoint uses its previously verified height only after a fresh safe-surface probe.

The earlier run at approximately `[-3663.5, 68, 720.5]` had both structures in bounds and selected Lavender's priority-30 source.

## Audio capture and references

Setup installs pinned PyAudioWPatch, which exposes the system's WASAPI loopback endpoint. Inspect devices without recording:

```powershell
.\testing\run.ps1 audio-devices
```

This machine currently exposes `Speaker (Realtek(R) Audio) [Loopback]`, 48 kHz stereo, matching the Windows default output. Endpoint capture records the digital output mix and can include other applications; it does not verify physical speaker output or isolate Minecraft. No device or global volume settings are changed.

Opt in to a verified gameplay run with `-Audio`; this capture checks focus and stop controls at each buffer and preserves a partial WAV on interruption. Standalone `audio-capture` does not associate its recording with a verified game fixture. Gameplay matching includes Pallet as a negative reference by default. `audio.case_ids` limits opt-in capture to BCA magic and Cherrygrove in the representative plan; clear that list for capture at every selection-pass fixture. The bundled profile FFmpeg has no WAV demuxer: loopback PCM16 WAVs are decoded with Python and linearly resampled; OGG references use FFmpeg. This resampling method remains part of the calibration uncertainty. Capture a local WAV while a known track is playing, or opt in to a gameplay run with `-Audio`:

```powershell
.\testing\run.ps1 audio-capture -Duration 30
.\testing\run.ps1 quick -Audio
```

The installed RC4 resource-pack ZIP is used directly as the reference source. `audio-identify` resolves named tracks or every track in a pool, ranks waveform subsequence and spectral candidates, and can compare two selections:

```powershell
.\testing\run.ps1 audio-identify -Recording <recording.wav> `
  -Selection dysfam_music:villages_lgpe_pallet_town `
  -NegativeSelection dysfam_music:villages_lgpe_lavender_town
.\testing\run.ps1 audio-benchmark `
  -Selection dysfam_music:villages_lgpe_pallet_town `
  -NegativeSelection dysfam_music:villages_lgpe_lavender_town
```

Current matcher evidence includes three real Minecraft WASAPI captures: Lavender, Cherrygrove and a BCA magic-pool member ranked above negative references. All were non-silent and unclipped. Controlled nonmatch, sound-effects and transition calibration remains incomplete; the threshold is unset and results remain `INCONCLUSIVE_AUDIO`. See [final gameplay results](FINAL_GAMEPLAY_SESSION_RESULTS.md) for scores, manual battle verification and the release assessment.

Static inspection of installed CobbleSafari 0.3.4 found a private client music player with current track/voice state, a private voice sample-position field, and 1-second synchronized, 5-second crossfade, and 2.5-second fade constants. The standard client log records load errors but did not expose normal per-track start/stop events. This harness does not instrument or modify CobbleSafari. A test-only companion/mixin remains optional future work.

## Loading, images and minimap

After teleport, the harness verifies world identity and exact player XYZ, checks destination chunk loading, polls structure bounds and music sources until stable, and captures native screenshots. Defaults are a 35-second minimum settle, 7-second polling, 180-second loading limit, and two stable observations. These are configurable in `config.json`. A valid `/tp` message alone is never considered ready.

The configured top-right minimap region is cropped into adjacent `*-minimap.png` evidence. Pixel statistics and screenshots are retained as visual corroboration only; the harness does not claim automated scene understanding. Structure bounds and exact piece containment remain authoritative. The installed profile has Xaero Minimap and Xaero World Map.

## Stop, assistance and recovery

- Press F8, move the cursor to a primary-screen corner, switch focus, or create `testing/STOP` to halt input.
- The controller never resumes or sends cleanup keys after focus loss. Before typing command text, Ctrl+A/Ctrl+C must provide a fresh selected slash; before Enter, a fresh copy must equal the complete pending command. This consumes clipboard text but never logs unrelated clipboard contents. A failed check stops and latches input. Close partial chat manually before restarting; an explicitly user-confirmed empty chat may be closed with Escape first. Focus loss or an emergency stop remains latched even if the window later regains focus.
- BLOCKED reports stop the suite and record an assistance request. In a verified, responsive copied world with safe chat state and Minecraft focus, the default alert uses a self-targeted gold `/tellraw` and a rate-limited `/playsound`. Recording stops before notification; focus loss or an emergency stop prevents all game input. Modal Windows alerts and Windows beeps are disabled by default. Explicitly confirm the requested action before a new invocation; there is no automatic resume. The next invocation rechecks identity, position, loading, containment and source selection.
- Owned temporary force-load tickets and pending daylight-cycle restoration are recorded. Once the copied world is loaded and ready, recover an interrupted report with:

```powershell
.\testing\run.ps1 recover -RecoverReport <interrupted-report.json>
```

Recovery verifies the copied-world token and receipt, queries current `doDaylightCycle`, restores only the documented original value if needed, and removes only a force-load ticket proven to be owned by that report. It cannot send input while focus is lost.

## Reports and status

Each run writes `report.json`, `report.md`, `commands.log`, and a bounded set of screenshots under ignored `testing/results/`. Audio WAVs are stored with their local reports and are excluded from Git. Existing failure evidence is never automatically deleted. The report retains exceptions and distinguishes selection failures, fixture/arbitration blocks, loading/focus problems, audio-device/tool issues, inconclusive audio, and untested layers.

The source contains trigger IDs and indices, the runtime parser retains the exact winning source key and index, and reports include competing sources and bounds. Only a verified single-structure fixture with fresh, parseable source evidence can produce `FAIL_SELECTION`. `PASS` means the configured selection-level gates passed; audio remains separately marked `NOT_TESTED` or `INCONCLUSIVE_AUDIO`.

October 10 runtime results remain historical in `SESSION_RESULTS.md` and `SESSION_RESULTS.json`. Phase 2 implementation and this session's new evidence are recorded separately in `PHASE2_IMPLEMENTATION.md`, `PHASE2_SESSION_RESULTS.md`, `PHASE2_SESSION_RESULTS.json`, and `COVERAGE.json`. The live Pallet overlap report is `results/20261011-152306-492b67/report.md`; the Lavender-only selection pass is `results/20261011-152808-d4cec2/report.md`. Ignored screenshots, logs and the copied-world receipt are local evidence and are not in Git.

User-assisted piece fixture: after explicitly confirming that the player is standing on a safe floor inside the requested piece, use `structure -Case <id> -AtCurrentPosition`. The controller reprobes that position, centers within the block, and rechecks exact containment; it does not assume a manual waypoint is valid.

During the final gameplay session, Jaime explicitly authorized spectator mode and waived landing-floor/headroom checks. `test_gamemode` is now `spectator`; the controller checks that mode both at readiness and immediately before any floor waiver. Saved `spectator_waypoint` coordinates are candidates until fresh XYZ/loading/structure/piece and source checks pass. Without a saved height, a trial uses the reported locate height or current verified player height and cannot pass unless live 3D containment holds. Creative-mode runs retain floor/headroom probes. Existing `candidate_xz` road positions come from saved structures and preserve the original locate output separately.

## Minimum representative testing

Jaime requested the smallest meaningful sample, with expansion only when failures or materially different changed rules justify it. Start with one village from each affected mod and check shared weather/day/night behavior at one suitable fixture, rather than testing every variant against every condition. A second successful shared-condition fixture is sufficient corroboration when needed; then stop. Distinguish indirect shared-rule coverage from direct passes, and use manual assistance when automation is slow or unreliable.

The reduced `representative` preset samples BCA basic, Terralith hot and Cherrygrove; its shared-condition regression uses only BCA basic. The other configured fixtures remain available individually. Snow needs a separate suitable biome if snow behavior changes or evidence calls for it. Twinleaf exact-tick testing was explicitly skipped by the user this session. Full results and limitations are in [FINAL_GAMEPLAY_SESSION_RESULTS.md](FINAL_GAMEPLAY_SESSION_RESULTS.md) and [COVERAGE.json](COVERAGE.json).
