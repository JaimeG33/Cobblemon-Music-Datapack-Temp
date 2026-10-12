# RC5 structures build results

Implemented 2026-10-11 after explicit user approval of the handoff's recommended scope. **Built and statically validated; four-location representative selection QA passed. Full transition QA remains pending.** RC4 was accepted as the continuation baseline. No commit, push or publication was performed.

## Approved scope and behavior

40 of the original 47 workbook conditions are implemented: 38 native whole-structure conditions plus Bell/Burned Tower. The towers expand into seven exact parent-and-piece rules, giving 45 new rules across five definition files. New rules specify their dimension, use priority 41 and `battle: "never"`. Existing RC1–RC4 track definitions, trigger rules, ambient tags and manifest records are preserved, including Pokemon Tower at priority 30. Only the existing diagnostic status function and pack metadata change in the baseline runtime layer.

27 new full-loop registrations serve 28 distinct approved songs; Heatran reuses XY - Team Flare Secret HQ. ORAS - Drought remains unchanged in the ambient layer. The lake rules play PLA - Lake throughout native lake bounds, including interiors.

Approved deferrals:

- Lava Shipwreck Cove: unavailable in installed Cobblemon 1.7.3.
- Groudon's Desolate Volcano, Kyogre's Primordial Sea and Sky Pillar: installed providers/IDs remain unlocated.
- Lake Acuity, Valor and Verity interior overrides: cave-only native containment remains unproven. No optional lake investigation was added to this release.

No guessed IDs, proximity padding, compatibility mods, mod updates, world-specific areas or biome substitutions were added. RC6 remains specific interiors; RC7 remains advanced battles.

## Final counts

| Measure | Project RC5 | Installed CobbleSafari defaults | Expected runtime total |
|---|---:|---:|---:|
| Tracks | 434 | 6 | 440 |
| Trigger rules | 1,351 | 4 | 1,355 |
| Definition files | 21 | 3 | 24 |
| Events / OGGs | 443 | — | 443 project resource assets |

## Outputs and hashes

Files are under `DysFam_CSMusic_Ambient_RC1_Package/build_output/` and intentionally ignored by Git. Both packs are cumulative; enable one current DysFam datapack and resource pack together.

| File | SHA256 |
|---|---|
| `DysFam_CSMusic_RC5_Datapack.zip` | `c779374e461f9cd093ecb0e5ab1299757c6490b9231d95448eeddefa2d635980` |
| `DysFam_CSMusic_RC5_ResourcePack.zip` | `4ab14dc5be52f24e3c274d6d412db741a8684ffcf00612c7ec38803a7ea4c405` |

## Verification completed

- Exact mapping of all 40 approved conditions, including songs, dimension and tower-piece expansion; seven deferrals remain inactive.
- 430 baseline data files preserved after normalizing Git checkout line endings; all existing track/trigger content and manifest rows preserved.
- Root/mirror file sets and bytes match exactly, including metadata.
- Installed CobbleSafari 0.3.4 DTO parsed all 21 files / 1,351 rules. All seven tower patterns match their exact ID and reject unrelated IDs.
- Recorded archive paths still exist; tower IDs are referenced by actual single-pool elements and have NBT templates. Completed archive discovery was not repeated.
- 232 simulated eligibility/arbitration checks covering inside/outside context, dimension exclusion, battle exclusion, priorities and tower exterior fallback. These do not establish real 3D containment.
- All 443 source members have unique paths and Ogg/Vorbis headers. All 27 new files passed full FFmpeg decoding; durations, channels and sample rates are retained in [structured results](RC5_BUILD_RESULTS.json).
- Independent ZIP inspection verifies root layout, forward slashes, duplicate/path rejection, CRCs, cumulative file sets, streaming sound mappings and all packaged OGG source sizes/CRCs.
- All 36 harness unit tests passed, covering existing safeguards and the new RC5 fixture references. RC4 configuration and suite remain unchanged.

Local detailed reports: `build_output/RC5_VALIDATION.json` and `build_output/RC5_AUDIO_VALIDATION.json`. A portable evidence summary is saved in [RC5_BUILD_RESULTS.json](RC5_BUILD_RESULTS.json).

## Rebuild

From the repository root:

```powershell
python ./DysFam_CSMusic_Ambient_RC1_Package/tools/generate_csmusic_rc5.py
./DysFam_CSMusic_Ambient_RC1_Package/tools/build_csmusic_rc5_datapack.ps1
./DysFam_CSMusic_Ambient_RC1_Package/tools/build_csmusic_rc5_resourcepack.ps1
python ./DysFam_CSMusic_Ambient_RC1_Package/tools/validate_csmusic_rc5.py --archives
```

Both builders accept `-ZipPath` and default to the relocated source archive at `D:/Minecraft Stuff/Minecraft Datapacks/CSMusic Sources/DysFam Music OGG Files.zip`. They stream only cumulative manifest members directly into RC5 ZIPs; no bulk extraction or recursive build-directory cleanup is needed. A failed build does not replace the previous final ZIP. Historical RC4 scripts and release outputs are untouched.

To repeat full audio decoding, pass `--ffmpeg '<ffmpeg.exe path>'` to the validator. To repeat installed DTO checks, compile `tools/ValidateRc5Schema.java` with the installed CobbleSafari JAR and Gson JAR on the classpath, then run `ValidateRc5Schema data/dysfam_music/csmusic/definition`.

## Pending gameplay gates

Minecraft is not required for building. The initial build session performed no game input or world changes. A subsequent user-authorized session installed RC5, prepared a fresh disposable world and passed the four-location representative selection sample; see [RC5 gameplay session](../testing/RC5_SESSION_RESULTS.md). Native containment, entry/exit/above-bounds behavior, tower vertical transitions, weather recovery, battle interruption/resumption, actual playback and representative loop-seam audition remain pending.

When gameplay testing is ready:

1. Load only the verified copied world `CSMusic Automation 20261010-192614`, with Minecraft foreground, unpaused, chat/menus closed.
2. Before new automation, run the existing recovery command from the handoff: `./testing/run.ps1 recover -RecoverReport testing/results/20261011-175431-061aa5/recovery-target.json`. It removes only the recorded owned ticket at XZ (-3520,4352); no daylight restoration is pending. This uses the existing RC4 setup before installing RC5. Recovery preflight accepts the readable historical pack without requiring current RC5 source bytes/counts; copy identity, foreground readiness and ticket ownership checks remain mandatory. Gameplay preflight still requires the current source snapshot.
3. Close Minecraft before staging RC5. Put the RC5 datapack in the copied world's datapacks directory and disable its RC4 DysFam ZIP. Put the RC5 resource pack in the profile resourcepacks directory, then enable it instead of RC4 in Minecraft. Preserve original saves and historical ZIPs.
4. Run `./testing/run_rc5.ps1 smoke`, then `./testing/run_rc5.ps1 representative -Audio`. RC5 has a separate configuration and suite; expected runtime totals are 440/1355/24. Fixture positions require fresh containment; a failed locate/piece fixture remains blocked and needs manual assistance.
5. At one representative whole structure, capture entry, exit and above-bounds fallback and weather resumption outside. At Bell/Burned Tower, inspect vertical piece transitions and return to Ecruteak village music outside the tower. Verify one generic wild battle interrupts structure music and the structure track resumes afterward.
6. Capture an actual structure playback sample and audition a representative full-loop seam. The existing audio matcher remains uncalibrated; report its evidence separately from any user audible confirmation.

The representative automated subset selects Desert Pyramid, Lush Cove, Amphitheater and Bell Tower, plus one structure/weather sequence. Burned Tower is available individually. This fixture selection does not claim the manual transition/battle gates have run. See [implementation plan](RC5_IMPLEMENTATION_PLAN.md) for the full release gates.

## Subsequent representative gameplay sample

On 2026-10-11, the user authorized installation and a fresh copied test world. Desert Pyramid, Lush Cove, Amphitheater and Bell Tower selected their intended priority-41 tracks. Cove evidence combines the user's audible change confirmation with a subsequent runtime selected-source snapshot. Amphitheater used a user-assisted position; Bell Tower used a saved native-bounds candidate and exact live piece verification, overriding Ecruteak 30. Full results and remaining limits are in [RC5_SESSION_RESULTS.md](../testing/RC5_SESSION_RESULTS.md). No music-definition fix was required; initial failures were invalid locate-height/piece fixtures or focus stops. Build hashes remain unchanged.
