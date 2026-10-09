"""Read-only RC4 validation against workbook, RC3 commit, installed data and ZIPs."""
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import zipfile

sys.dont_write_bytecode = True
from generate_csmusic_rc4 import BASELINE, DEFAULT_AUDIO, DEFAULT_WORKBOOK, PACKAGE, workbook_cells

DEFAULT_PROFILE = Path(r"D:\Minecraft Stuff\ModrinthApp\profiles\DysFam Cobblemon 2.0 6.0.0")
POOLS = {"basic_day": ("A", 11, 45), "basic_night": ("B", 11, 39),
         "magic_day": ("C", 8, 22), "magic_night": ("D", 8, 23),
         "cold_day": ("E", 7, 18), "cold_night": ("F", 7, 13),
         "hot_day": ("G", 5, 13), "hot_night": ("H", 5, 12)}
TOWNS = {"pallet_town": "I5", "lavender_town": "I9", "cherrygrove_city": "I17",
         "pacifidlog_town": "I21", "twinleaf_town": "I25", "floaroma_town": "I29", "lentimas_town": "I33"}


def require(value, message):
    if not value:
        raise AssertionError(message)


def read_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest().upper()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    ap.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    ap.add_argument("--audio", type=Path, default=DEFAULT_AUDIO)
    ap.add_argument("--ffmpeg", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    repo = args.repo.resolve()
    root = repo / "data/dysfam_music/csmusic"
    out = repo / PACKAGE / "build_output"
    tracks = {"dysfam_music:" + f.stem: read_json(f.read_bytes()) for f in root.glob("*.json")}
    triggers = {f.name: read_json(f.read_bytes())["rules"] for f in (root / "definition").glob("*.json")}
    all_rules = [r for rules in triggers.values() for r in rules]
    manifest_path = f"{PACKAGE}/manifest/csmusic_release_assets.csv"
    manifest = list(csv.DictReader((repo / manifest_path).open(encoding="utf-8-sig")))
    require((len(tracks), len(all_rules), len(triggers), len(manifest)) == (407, 1306, 16, 416), "computed RC4 counts")
    require(sum(r["when"].get("battle") == "wild" for r in all_rules) == 1016, "generic wild species count")
    battle_species = [r["when"]["species"] for f, rules in triggers.items() if f.startswith("battle_default_gen") for r in rules]
    require(len(battle_species) == len(set(battle_species)) == 1016, "battle uniqueness")

    baseline_archive = subprocess.check_output(["git", "archive", BASELINE, "data"], cwd=repo)
    with tarfile.open(fileobj=io.BytesIO(baseline_archive)) as archive:
        baseline_data = {m.name: archive.extractfile(m).read() for m in archive if m.isfile()}
    preserved = 0
    for name, before in baseline_data.items():
        after = (repo / name).read_bytes()
        if name.endswith("villages_sv_kitakami.json"):
            expected = read_json(before)
            expected["tags"].append("village_magic_night")
            require(read_json(after) == expected, "Kitakami must only add its village tag")
        elif name.endswith("function/check.mcfunction"):
            require("413 music definitions / 1310 trigger rules / 19 trigger files" in after.decode(), "status counts")
        else:
            require(before.replace(b"\r\n", b"\n") == after.replace(b"\r\n", b"\n"), "RC3 regression: " + name)
            preserved += 1
    baseline_manifest = list(csv.DictReader(io.StringIO(subprocess.check_output(["git", "show", f"{BASELINE}:{manifest_path}"], cwd=repo).decode("utf-8-sig"))))
    require(manifest[:289] == baseline_manifest, "all RC3 manifest records retained")
    require(len(manifest[289:]) == 127 and all(r["Release_Added"] == "RC4" for r in manifest[289:]), "127 RC4 additions")
    mirror = repo / PACKAGE / "datapack"
    root_names = {f.relative_to(repo).as_posix() for f in (repo / "data").rglob("*") if f.is_file()} | {"pack.mcmeta"}
    mirror_names = {f.relative_to(mirror).as_posix() for f in mirror.rglob("*") if f.is_file()}
    require(root_names == mirror_names, "mirror file set")
    for name in root_names:
        require((repo / name).read_bytes() == (mirror / name).read_bytes(), "mirror bytes: " + name)

    cells = workbook_cells(args.workbook)
    inventory = list(csv.DictReader((repo / "docs/reference/rc4_village_audio_inventory.csv").open(encoding="utf-8-sig")))
    inv = collections.defaultdict(list)
    for row in inventory:
        inv[row["Workbook_Song"]].append(row)
        for cell in row["Cells"].split(";"):
            require(cells[cell] == row["Workbook_Song"], "inventory source cell: " + cell)
    pool_members = {"village_" + pool: {inv[cells[f"{col}{i}"]][0]["Proposed_Track_ID"] for i in range(start, end + 1)} for pool, (col, start, end) in POOLS.items()}
    for tag, expected in pool_members.items():
        actual = {tid for tid, track in tracks.items() if tag in track.get("tags", [])}
        require(actual == expected, "workbook pool differs: " + tag)
    expected_structures = {}
    for theme, sizes, category in [("default", ["small", "mid", "large"], "basic"), ("fighting", ["small", "mid", "large"], "basic"), ("dark", ["small", "mid"], "magic"), ("fairy", ["small", "mid"], "magic"), ("ice", ["small", "mid", "large"], "cold")]:
        for size in sizes:
            expected_structures[f"bca:village/{theme}_{size}"] = category
    expected_structures.update({"terralith:fortified_village": "basic", "terralith:fortified_desert_village": "hot"})
    generic = triggers["villages_generic.json"]
    require(len(generic) == 30 and {r["when"]["structure"] for r in generic} == set(expected_structures), "exact generic structure coverage")
    for structure, category in expected_structures.items():
        actual = {(r.get("tag"), tuple(r["when"]["time_range"])) for r in generic if r["when"]["structure"] == structure}
        require(actual == {(f"village_{category}_day", (0, 12000)), (f"village_{category}_night", (12000, 24000))}, "generic day/night coverage: " + structure)
    town_rules = triggers["villages_cobbletowns.json"]
    require(len(town_rules) == 9, "town rule count")
    tower_piece = "cobbletowns:lavender_town/buildings/pokemon_tower"
    require(town_rules[0]["when"].get("structure_piece") == tower_piece and town_rules[0]["music"] == inv[cells["I13"]][0]["Proposed_Track_ID"], "tower index 0")
    require(town_rules[1]["when"]["structure"] == "cobbletowns:lavender_town" and "structure_piece" not in town_rules[1]["when"], "Lavender index 1")
    for town, cell in TOWNS.items():
        rules = [r for r in town_rules if r["when"]["structure"] == "cobbletowns:" + town and "structure_piece" not in r["when"]]
        if town == "twinleaf_town":
            require(len(rules) == 2, "Twinleaf split")
            for period, window in [("Day", [0, 12000]), ("Night", [12000, 24000])]:
                track = next(r["Proposed_Track_ID"] for r in inv[cells[cell]] if r["Source_ZIP_Path"].endswith(f"({period}).ogg"))
                require(any(r["music"] == track and r["when"].get("time_range") == window for r in rules), "Twinleaf " + period)
        else:
            require(len(rules) == 1 and rules[0]["music"] == inv[cells[cell]][0]["Proposed_Track_ID"] and "time_range" not in rules[0]["when"], "town workbook assignment: " + town)
    lm = triggers["villages_legendary_monuments.json"]
    require(len(lm) == 1 and lm[0]["when"]["structure"] == "legendarymonuments:traditional_village/ecruteak" and lm[0]["music"] == inv[cells["J5"]][0]["Proposed_Track_ID"], "Ecruteak mapping")
    village_rules = generic + town_rules + lm
    for rule in village_rules:
        require(set(rule) <= {"tag", "music", "priority", "when"}, "unsupported rule field")
        require(set(rule["when"]) <= {"dimension", "battle", "structure", "structure_piece", "time_range"}, "unsupported village condition")
        require(rule["priority"] == 30 and rule["when"]["battle"] == "never" and rule["when"]["dimension"] == "minecraft:overworld", "village context")
        require(isinstance(rule["when"]["structure"], str) and not rule["when"]["structure"].startswith("#"), "exact scalar structure")
    for rule in all_rules:
        require(("music" in rule) != ("tag" in rule), "music/tag exclusive")
        require(rule["music"] in tracks if "music" in rule else any(rule["tag"] in t.get("tags", []) for t in tracks.values()), "unresolved track/pool")

    installed = {}
    jars = [args.profile / "mods/cobblemon-additions-4.3.0.jar", args.profile / "mods/Terralith_1.21.x_v2.6.2.jar",
            args.profile / "mods/legendarymonuments-fabric-1.21.1-8.1-Love_for_All.jar", args.profile / "datapacks/CobbleTowns 1.1.3 (for 1.6).zip"]
    for jar in jars:
        with zipfile.ZipFile(jar) as z:
            for n in z.namelist():
                if n.startswith("data/"):
                    installed[n] = z.read(n) if n.endswith(".json") else b""
    for rule in village_rules:
        ns, path = rule["when"]["structure"].split(":")
        require(f"data/{ns}/worldgen/structure/{path}.json" in installed, "structure missing from installed archives")
    ns, path = tower_piece.split(":")
    require(f"data/{ns}/structure/{path}.nbt" in installed, "tower template missing")
    pool = read_json(installed["data/cobbletowns/worldgen/template_pool/lavender_town/pokemon_tower.json"])
    require(any(e["element"].get("location") == tower_piece and e["element"]["element_type"] == "minecraft:single_pool_element" for e in pool["elements"]), "tower single-pool template")
    safari = args.profile / "mods/cobblesafari-fabric-1.21.1-0.3.4.jar"
    with zipfile.ZipFile(safari) as z:
        built_tracks = [n for n in z.namelist() if n.startswith("data/cobblesafari/csmusic/") and n.endswith(".json") and "/definition/" not in n]
        built_triggers = [n for n in z.namelist() if n.startswith("data/cobblesafari/csmusic/definition/") and n.endswith(".json")]
        built_rules = sum(len(read_json(z.read(n))["rules"]) for n in built_triggers)
    loader = subprocess.check_output(["javap", "-p", "-v", "-classpath", str(safari), "maxigregrze.cobblesafari.csmusic.CsMusicTriggerDataLoader"], text=True)
    manager = subprocess.check_output(["javap", "-p", "-v", "-classpath", str(safari), "maxigregrze.cobblesafari.csmusic.DimensionalMusicManager"], text=True)
    require("definition:\\u0001#\\u0001" in loader, "actual loader source-key recipe changed")
    require("MusicSource.priority:()I" in manager and "Comparator.reversed" in manager and "MusicSource.key:()Ljava/lang/String;" in manager and "Comparator.thenComparing" in manager, "actual comparator changed")
    keys = [f"definition:csmusic/definition/villages_cobbletowns.json#{i}" for i in (0, 1)]
    require(sorted(keys)[0] == keys[0], "tower source-key precedence")
    selection_cases = 0
    for dimension in ["minecraft:overworld", "minecraft:the_nether"]:
        for battle in [False, True]:
            for weather in ["clear", "rain", "snow", "thunder"]:
                for tick in [0, 11999, 12000, 23999]:
                    for structure, piece in [("bca:village/default_small", None), ("bca:village/ice_mid", None), ("terralith:fortified_desert_village", None), ("cobbletowns:twinleaf_town", None), ("cobbletowns:lavender_town", None), ("cobbletowns:lavender_town", tower_piece), ("legendarymonuments:traditional_village/nonlegendary", None)]:
                        candidates = [(10, "ambient", "ambient")]
                        if dimension == "minecraft:overworld" and not battle:
                            for filename, rules in triggers.items():
                                if filename.startswith("villages_"):
                                    for i, r in enumerate(rules):
                                        w = r["when"]
                                        if w["structure"] != structure or (w.get("structure_piece") and w["structure_piece"] != piece):
                                            continue
                                        if "time_range" in w and not w["time_range"][0] <= tick < w["time_range"][1]:
                                            continue
                                        candidates.append((30, f"definition:csmusic/definition/{filename}#{i}", r.get("music", r.get("tag"))))
                            for i, r in enumerate(triggers["weather.json"]):
                                w = r["when"]
                                if weather not in w["weather"] or ("time_range" in w and not w["time_range"][0] <= tick < w["time_range"][1]):
                                    continue
                                candidates.append((40, f"definition:csmusic/definition/weather.json#{i}", r["music"]))
                        if battle:
                            candidates.append((50, "battle", "battle"))
                        selected = sorted(candidates, key=lambda x: (-x[0], x[1]))[0]
                        expected = 50 if battle else 10 if dimension != "minecraft:overworld" else 40 if weather in ["snow", "thunder"] else 10 if structure.endswith("/nonlegendary") else 30
                        require(selected[0] == expected, "selection matrix priority")
                        if expected == 30 and piece == tower_piece:
                            require(selected[2] == town_rules[0]["music"], "tower beats town in selection matrix")
                        if expected == 30 and structure == "cobbletowns:twinleaf_town":
                            require(selected[2].endswith("_day" if tick < 12000 else "_night"), "Twinleaf selection boundary")
                        selection_cases += 1

    dat_zip = out / "DysFam_CSMusic_RC4_Datapack.zip"
    res_zip = out / "DysFam_CSMusic_RC4_ResourcePack.zip"
    print("PASS: RC3 preservation, workbook pools, installed structure IDs, schema fields, source-key ordering and 448 selection cases. Checking ZIP CRCs/audio...", flush=True)
    with zipfile.ZipFile(dat_zip) as z:
        require(z.testzip() is None and set(z.namelist()) == root_names, "datapack CRC/file set")
        require(len(z.namelist()) == len(set(z.namelist())) and not any("\\" in n for n in z.namelist()), "datapack duplicate/path")
        for n in root_names:
            require(z.read(n) == (repo / n).read_bytes(), "datapack archived content: " + n)
        require(read_json(z.read("pack.mcmeta"))["pack"]["pack_format"] == 48, "datapack format")
    decoded = []
    with zipfile.ZipFile(args.audio) as source, zipfile.ZipFile(res_zip) as z:
        require(z.testzip() is None, "resource ZIP CRC")
        names = z.namelist()
        expected_names = {"pack.mcmeta", "assets/dysfam_music/sounds.json"} | {r["Destination_OGG_Path"] for r in manifest}
        require(len(names) == len(set(names)) and set(names) == expected_names and not any("\\" in n for n in names), "resource file set/paths")
        require(read_json(z.read("pack.mcmeta"))["pack"]["pack_format"] == 34, "resource format")
        events = read_json(z.read("assets/dysfam_music/sounds.json"))
        require(len(events) == 416 and len({r["Sound_Event_ID"] for r in manifest}) == 416, "unique events")
        samples = {inv[cells[cell]][0]["Source_ZIP_Path"] for cell in ["A11", "B11", "C8", "D8", "E7", "F7", "G5", "H5", "I5", "I9", "I13", "I17", "I21", "I29", "I33", "J5"]} | {r["Source_ZIP_Path"] for r in inv[cells["I25"]]}
        for row in manifest:
            source_bytes = source.read(row["Source_ZIP_Path"])
            data = z.read(row["Destination_OGG_Path"])
            require(data == source_bytes and data.startswith(b"OggS") and b"\x01vorbis" in data[:128], "audio source/header: " + row["Source_ZIP_Path"])
            ns, key = row["Sound_Event_ID"].split(":")
            require(ns == "dysfam_music" and row["Resource_Path"] == key and events[key] == {"sounds": [{"name": row["Sound_Event_ID"], "stream": True}]}, "event/manifest relationship")
            if args.ffmpeg and row["Source_ZIP_Path"] in samples:
                # The bundled minimal FFmpeg lacks the null muxer but supports PCM.
                subprocess.run([str(args.ffmpeg), "-v", "error", "-xerror", "-i", "pipe:0", "-c:a", "pcm_s16le", "-f", "s16le", "-"], input=data, check=True, stdout=subprocess.DEVNULL)
                decoded.append(row["Source_ZIP_Path"])
        for tid, track in tracks.items():
            for key in ("intro", "loop", "outro"):
                if key in track:
                    ns, event = track[key].split(":")
                    require(ns == "dysfam_music" and event in events, "unresolved sound: " + tid)
    report = {
        "status": "PASS — Built / Awaiting Gameplay QA", "baseline_commit": BASELINE,
        "project": {"tracks": len(tracks), "rules": len(all_rules), "trigger_files": len(triggers), "events": len(manifest), "ogg_files": len(manifest)},
        "runtime_with_installed_builtins": {"tracks": len(tracks) + len(built_tracks), "rules": len(all_rules) + built_rules, "trigger_files": len(triggers) + len(built_triggers)},
        "preserved_baseline_data_files": preserved, "preserved_manifest_rows": len(baseline_manifest),
        "village_rules": len(village_rules), "wild_species_rules": len(battle_species),
        "workbook_pool_counts": {k: len(v) for k, v in pool_members.items()}, "selection_matrix_cases": selection_cases,
        "decoded_full_audio_samples": decoded, "safari_sha256": digest(safari),
        "artifacts": [{"path": str(p), "bytes": p.stat().st_size, "sha256": digest(p)} for p in [dat_zip, res_zip]],
        "warnings": ["Static tests do not establish in-game success.", "Original CobbleTowns metadata and Lentimas loot defects are unchanged.", "Three-dimensional structure bounds and the existing 600-tick cache require gameplay QA."]
    }
    if args.report:
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
