# CSMusic Windows testing prototype

This controller uses PyAutoGUI for Windows keyboard input and screenshots, and fresh Minecraft system-chat log responses for evidence. It never treats sending a command, a screenshot, declared pack counts, or old log entries as a runtime pass. Production music files and release ZIPs are not edited.

## Setup and use

Run from the repository root in PowerShell:

```powershell
.\testing\run.ps1 setup
.\testing\run.ps1 audit
.\testing\run.ps1 self-test
.\testing\run.ps1 dry-run
# Close Minecraft before copying a save:
.\testing\run.ps1 prepare
```

`config.json` selects the profile, source save, expected release totals and timeouts. Preparation makes a new timestamped `CSMusic Automation ...` save, preserving the source save and all unrelated packs. It changes only the copy to creative mode with cheats and installs a test-only identity/terrain-probe datapack. `prepared.json` records the copy identity. Never copy its identity pack into another world. The current source is **RC4 Village Test**, not the obsolete RC3 save name in the task brief.

Launch the existing profile through Modrinth, load the named copied save, and leave it unpaused, outside chat or menus. Start a test, then allow the controller to focus Minecraft. Do not type during a run:

```powershell
.\testing\run.ps1 smoke
.\testing\run.ps1 structure -Case pallet_town
```

The structure command repeats the smoke gate before attempting travel. `suite.json` contains the RC4 structure rules, named settlements and generic pools; use the desired entry's `id` for `-Case`.

Two configurable regression sequences are implemented (their execution status is in the session report):

```powershell
.\testing\run.ps1 regression -Case pallet_weather
.\testing\run.ps1 regression -Case twinleaf_exact_boundaries
```

They travel through the structure fixture, apply each weather/time step, allow arbitration, and assert the playing source, priority and observed weather. Boundary tests freeze the copied world's daylight cycle and restore its prior setting on normal completion. A failed fixture, such as rain being classified as snow, blocks rather than misdiagnosing the music. Other regression entries are an explicit fixture backlog, **not implemented gameplay coverage**. Battle creation/completion, calibrated biome transitions, structure edge/vertical transitions and tower piece transitions still need fixtures or additional control work.

## Stop and recovery

- Press **F8**, move the mouse to any primary-screen corner, switch focus away from Minecraft, or create `testing/STOP`.
- Stop checks run before every typed character and during waits. There is a small OS scheduling race between a focus check and an input event; GUI automation cannot make those two operations atomic.
- Focus loss is terminal for that run. The controller never refocuses or sends cleanup keys after an abort. Clear any partially typed chat manually before restarting.
- Delete the STOP file manually when ready to run again. Ctrl+C also aborts.
- The copied world remains where the test stopped, with any test time/weather changes. The original is never restored over, deleted or regenerated.
- Travel temporarily force-loads one destination chunk if it was not already forced. Normal cleanup removes only that new ticket. After an emergency stop, `observed.temporary_forceload` records a ticket that may need manual removal in the copy. No cleanup command is sent while another app has focus.
- To recover that ticket once the copied world is ready, run `.\testing\.venv\Scripts\python.exe .\testing\harness.py capture --recover-report <interrupted-report.json>`. Recovery verifies the copy identity and the interrupted run's ownership evidence. A regression interrupted while daylight is frozen also records `daylight_cycle_restore_pending`; restore that documented value manually in the copy.

## Evidence and validation levels

Every run gets a unique ignored `testing/results/<timestamp>-<id>/` directory with `report.json`, `report.md`, `commands.log` and command screenshots when available. Exit code 0 means that mode passed; code 2 means failure or blocked. A dry-run pass means controls can be imported and queried without input; it is not a gameplay pass.

If desktop capture is completely black, the controller uses the verified F2 binding and copies Minecraft's native screenshot into the run evidence. The original native screenshot is retained in the profile's screenshots directory. If native capture also fails, the run blocks. Earlier prototype runs had black screenshots; their usable evidence is the log, as identified in the session report.

The report distinguishes static validation from runtime selection and always marks audible playback **not tested**. CSMusic's `current` output describes the selected source/pool; it does not prove the individual sound in a random pool is audible. No audio capture is implemented.

Each command is enclosed by unpredictable BEGIN/END `tellraw` markers. Only new `[System] [CHAT]` lines between those markers are parsed. Normal player chat, historical entries, partial lines and rotated/truncated logs cannot satisfy a request. Empty/unknown responses block their assertion. English client messages are required by the current parsers.

Smoke proves the copy identity, creative mode, enabled RC4 pack, RC4 status function, fresh loader counts with zero skips/rejections after `/reload`, and a parseable playing source. The status function's declared counts are never substituted for live loader counts. Reloading happens only in the verified copy.

## Controller states

| State | Success/evidence | Timeout/recovery |
|---|---|---|
| PREFLIGHT | Installed version/hash inventory and computed source + built-in counts | Abort on incompatible/missing inputs |
| READY | Correct process/profile; fresh copy token; creative assertion | Bounded command roundtrips; abort without world edits |
| LOCATE | Exact structure ID and fresh coordinate response | 240 seconds per locate; abort if incomplete/error |
| PARSE | Valid X/Z, retain unknown Y explicitly | Reject malformed/out-of-range results |
| TRAVEL | Probe confirms numeric XYZ, safe floor and headroom; teleport and player-position confirmation | Bounded commands, no guessed landing Y |
| SETTLE | Focus held through cache allowance | 35 seconds by default |
| QUERY | Fresh `structures` and `current` responses | 15 seconds per command |
| VERIFY | Bounds containment plus playing music/pool and priority | Mismatch fails; unavailable evidence blocks |
| RECORD | JSON/Markdown/log/screenshot evidence | Local writes; errors surface to operator |
| CLEANUP | Close handles; remove owned force-load ticket only while focused | No automatic recovery input following abort |

The terrain probe uses a conservative solid-block allowlist and two exact air blocks. It can decline snow-layer surfaces or custom floors. It selects the highest valid landing point, which might be a roof; actual CSMusic bounds must still match. Lack of containment is blocked pending another verified landing point, not a music failure. Piece-specific cases require the exact piece line under the correct containing parent, and block if the landing point misses it. The tower still needs calibrated landing/entry/exit waypoints; its gameplay behavior has not been tested by this harness.

## Feasibility and limitations

The installed 1.21.1 client log contains `csmusic current`, structure bounds, and loader totals. A Fabric logging mod is therefore unnecessary for the initial smoke path. Nonce markers detect missing feedback rather than assuming all chat is logged. A future bridge could expose world identity, chunk height/bounds, structured command callbacks, exact piece containment and sound-engine observations without UI typing; it must remain test-only and must not change selection behavior.

No supported unattended launch interface was verified for the local Modrinth installation. Launching and selecting the copy currently require the user. No launcher account data or tokens are stored in evidence. Minecraft freeze detection combines Windows hung-window checks and response deadlines; a locate timeout does not forcibly terminate the game/server task.

PyAutoGUI's documented fail-safe is retained: [official documentation](https://pyautogui.readthedocs.io/en/latest/index.html#fail-safes). The implementation additionally checks focus and F8 during waits. See `SESSION_RESULTS.md` for what was actually executed during implementation.
