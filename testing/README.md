# CSMusic testing harness

The Windows controller tests RC4 using a verified, disposable copy of `RC4 Village Test`. It edits only files under `testing/` in this repository and test-only files in that copied world. It never changes production trigger rules, release ZIPs, or the source save.

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

Runs use bounded `/locate` and travel. They do not generate distant terrain or guess safe alternate coordinates. An ambiguous or inaccessible fixture stops with a BLOCKED category and asks for actionable user help; a later invocation rechecks identity and focus. The known Pallet/Lavender overlap is an arbitration case, not a Pallet-only pass or a proven music defect. The earlier run at approximately `[-3663.5, 68, 720.5]` had both structures in bounds and selected Lavender's priority-30 source.

## Audio capture and references

Setup installs pinned PyAudioWPatch, which exposes the system's WASAPI loopback endpoint. Inspect devices without recording:

```powershell
.\testing\run.ps1 audio-devices
```

This machine currently exposes `Speaker (Realtek(R) Audio) [Loopback]`, 48 kHz stereo, matching the Windows default output. Endpoint capture records the digital output mix and can include other applications; it does not verify physical speaker output or isolate Minecraft. No device or global volume settings are changed.

Capture a local WAV while a known track is playing, or opt in to a gameplay run with `-Audio`:

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

Current matcher evidence is **synthetic only**: reference-derived volume-scaled and background-noise samples separate these two tracks, silence scores zero, and a two-track overlap is ambiguous. A first spectral-only ranking confused the town tracks. No Minecraft loopback recording has been captured or calibrated, so the threshold is unset, every matcher result is `INCONCLUSIVE_AUDIO`, and `FAIL_AUDIO` is never emitted. Audio is not a required gameplay gate until controlled live match/nonmatch/silence and mixed-transition recordings establish useful thresholds.

Static inspection of installed CobbleSafari 0.3.4 found a private client music player with current track/voice state, a private voice sample-position field, and 1-second synchronized, 5-second crossfade, and 2.5-second fade constants. The standard client log records load errors but did not expose normal per-track start/stop events. This harness does not instrument or modify CobbleSafari. A test-only companion/mixin remains optional future work.

## Loading, images and minimap

After teleport, the harness verifies world identity and exact player XYZ, checks destination chunk loading, polls structure bounds and music sources until stable, and captures native screenshots. Defaults are a 35-second minimum settle, 7-second polling, 180-second loading limit, and two stable observations. These are configurable in `config.json`. A valid `/tp` message alone is never considered ready.

The configured top-right minimap region is cropped into adjacent `*-minimap.png` evidence. Pixel statistics and screenshots are retained as visual corroboration only; the harness does not claim automated scene understanding. Structure bounds and exact piece containment remain authoritative. The installed profile has Xaero Minimap and Xaero World Map.

## Stop, assistance and recovery

- Press F8, move the cursor to a primary-screen corner, switch focus, or create `testing/STOP` to halt input.
- The controller never resumes or sends cleanup keys after focus loss. A partially typed command is replaced with Ctrl+A before the next fresh command, but a new run still requires the user to confirm the game is ready and foreground.
- BLOCKED fixture/loading/focus reports include a specific assistance request. The Windows alert does not play a Minecraft sound or refocus the game. Start a new run only after the requested action; there is no automatic resume.
- Owned temporary force-load tickets and pending daylight-cycle restoration are recorded. Once the copied world is loaded and ready, recover an interrupted report with:

```powershell
.\testing\run.ps1 recover -RecoverReport <interrupted-report.json>
```

Recovery verifies the copied-world token and receipt, queries current `doDaylightCycle`, restores only the documented original value if needed, and removes only a force-load ticket proven to be owned by that report. It cannot send input while focus is lost.

## Reports and status

Each run writes `report.json`, `report.md`, `commands.log`, and a bounded set of screenshots under ignored `testing/results/`. Audio WAVs are stored with their local reports and are excluded from Git. Existing failure evidence is never automatically deleted. The report retains exceptions and distinguishes selection failures, fixture/arbitration blocks, loading/focus problems, audio-device/tool issues, inconclusive audio, and untested layers.

The source contains trigger IDs and indices, the runtime parser retains the exact winning source key and index, and reports include competing sources and bounds. Only a verified single-structure fixture with fresh, parseable source evidence can produce `FAIL_SELECTION`. `PASS` means the configured selection-level gates passed; audio remains separately marked `NOT_TESTED` or `INCONCLUSIVE_AUDIO`.

October 10 runtime results remain historical in `SESSION_RESULTS.md` and `SESSION_RESULTS.json`. Phase 2 implementation and this session's new evidence are recorded separately in `PHASE2_IMPLEMENTATION.md`, `PHASE2_SESSION_RESULTS.md`, `PHASE2_SESSION_RESULTS.json`, and `COVERAGE.json`. The live Pallet overlap report is `results/20261011-152306-492b67/report.md`; the Lavender-only selection pass is `results/20261011-152808-d4cec2/report.md`. Ignored screenshots, logs and the copied-world receipt are local evidence and are not in Git.
