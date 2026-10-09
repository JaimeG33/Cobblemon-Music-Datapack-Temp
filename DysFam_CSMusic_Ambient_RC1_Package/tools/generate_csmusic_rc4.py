"""Generate RC4 village source from the approved inventory and original workbook.

Python standard library only. Run from any directory; no profile/world writes.
"""
import argparse
import csv
import io
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import zipfile

BASELINE = "dc15892"
DEFAULT_WORKBOOK = Path(r"C:\Users\Jaime\Downloads\CSMusic_Reference_Excel_Files\Music Pack Conditions & Music(2)_2.xlsx")
DEFAULT_AUDIO = Path(r"C:\Users\Jaime\Downloads\DysFam Music OGG Files.zip")
PACKAGE = "DysFam_CSMusic_Ambient_RC1_Package"
POOL_RANGES = {
    "basic_day": ("A", 11, 45), "basic_night": ("B", 11, 39),
    "magic_day": ("C", 8, 22), "magic_night": ("D", 8, 23),
    "cold_day": ("E", 7, 18), "cold_night": ("F", 7, 13),
    "hot_day": ("G", 5, 13), "hot_night": ("H", 5, 12),
}
TOWN_CELLS = {
    "pallet_town": "I5", "lavender_town": "I9", "cherrygrove_city": "I17",
    "pacifidlog_town": "I21", "twinleaf_town": "I25",
    "floaroma_town": "I29", "lentimas_town": "I33",
}


def workbook_cells(path):
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as z:
        strings = ["".join(t.itertext()) for t in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("s:si", ns)]
        rels = {r.attrib["Id"]: r.attrib["Target"] for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        sheet = next(s for s in ET.fromstring(z.read("xl/workbook.xml")).findall("s:sheets/s:sheet", ns) if s.attrib["name"] == "Villages")
        target = rels[sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]]
        target = target.lstrip("/") if target.startswith("/") else "xl/" + target
        cells = {}
        for c in ET.fromstring(z.read(target)).findall("s:sheetData/s:row/s:c", ns):
            v = c.find("s:v", ns)
            value = v.text if v is not None else "".join(c.itertext())
            if c.attrib.get("t") == "s":
                value = strings[int(value)]
            if value:
                cells[c.attrib["r"]] = value
        return cells


def git_bytes(repo, path):
    return subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=repo)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    ap.add_argument("--audio", type=Path, default=DEFAULT_AUDIO)
    args = ap.parse_args()
    repo = args.repo.resolve()
    inventory = list(csv.DictReader((repo / "docs/reference/rc4_village_audio_inventory.csv").open(encoding="utf-8-sig")))
    cells = workbook_cells(args.workbook)
    assert len(inventory) == 128, "Expected the approved 128 candidate audio files"
    for row in inventory:
        for cell in row["Cells"].split(";"):
            assert cells[cell] == row["Workbook_Song"], (cell, row["Workbook_Song"], cells[cell])
    by_song = {}
    for row in inventory:
        by_song.setdefault(row["Workbook_Song"], []).append(row)

    expected_memberships = {}
    for pool, (col, start, end) in POOL_RANGES.items():
        for i in range(start, end + 1):
            expected_memberships.setdefault(cells[f"{col}{i}"], set()).add(pool)
    for row in inventory:
        actual = set(row["Pools_or_Towns"].split(";")) & set(POOL_RANGES)
        assert actual == expected_memberships.get(row["Workbook_Song"], set())

    root = repo / "data/dysfam_music/csmusic"
    mirror = repo / PACKAGE / "datapack"
    manifest = repo / PACKAGE / "manifest/csmusic_release_assets.csv"
    baseline_bytes = git_bytes(repo, f"{PACKAGE}/manifest/csmusic_release_assets.csv")
    baseline_rows = list(csv.DictReader(io.StringIO(baseline_bytes.decode("utf-8-sig"))))
    current_rows = list(csv.DictReader(manifest.open(encoding="utf-8-sig")))
    assert current_rows[:289] == baseline_rows and all(r["Release_Added"] == "RC4" for r in current_rows[289:]), "Unexpected manifest changes; refusing to overwrite other work"
    fields = list(baseline_rows[0])
    additions = []
    with zipfile.ZipFile(args.audio) as audio:
        for row in inventory:
            source = row["Source_ZIP_Path"]
            info = audio.getinfo(source)
            assert info.file_size == int(row["Bytes"]), source
            with audio.open(info) as stream:
                assert stream.read(4) == b"OggS", source
            track = row["Proposed_Track_ID"]
            event = row["Proposed_Sound_Event"]
            tags = sorted("village_" + p for p in row["Pools_or_Towns"].split(";") if p in POOL_RANGES)
            track_path = root / (track.split(":", 1)[1] + ".json")
            if row["Status"] == "reuse":
                definition = json.loads(git_bytes(repo, track_path.relative_to(repo).as_posix()))
                definition["tags"] = list(dict.fromkeys(definition.get("tags", []) + tags))
            else:
                definition = {"loop": event, "tags": tags}
                resource = event.split(":", 1)[1]
                additions.append(dict(zip(fields, [
                    row["Workbook_Song"], source, Path(source).name,
                    f"{info.file_size / (1024 * 1024):.2f}", resource, event, track,
                    ";".join(tags), "assets/dysfam_music/sounds/" + resource + ".ogg",
                    "full_loop", "villages", "RC4",
                ])))
            write_json(track_path, definition)
            write_json(mirror / track_path.relative_to(repo), definition)
    assert len(additions) == 127
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerows(additions)
    manifest.write_bytes(baseline_bytes.rstrip(b"\r\n") + b"\n" + buffer.getvalue().encode("utf-8"))

    def rule(structure, *, tag=None, music=None, window=None, piece=None):
        when = {"dimension": "minecraft:overworld", "battle": "never", "structure": structure}
        if window is not None:
            when["time_range"] = window
        if piece is not None:
            when["structure_piece"] = piece
        return {"tag" if tag else "music": tag or music, "priority": 30, "when": when}

    generic = []
    for theme, sizes, pool in [
        ("default", ("small", "mid", "large"), "basic"),
        ("fighting", ("small", "mid", "large"), "basic"),
        ("dark", ("small", "mid"), "magic"), ("fairy", ("small", "mid"), "magic"),
        ("ice", ("small", "mid", "large"), "cold"),
    ]:
        for size in sizes:
            for period, window in [("day", [0, 12000]), ("night", [12000, 24000])]:
                generic.append(rule(f"bca:village/{theme}_{size}", tag=f"village_{pool}_{period}", window=window))
    for structure, pool in [("terralith:fortified_village", "basic"), ("terralith:fortified_desert_village", "hot")]:
        for period, window in [("day", [0, 12000]), ("night", [12000, 24000])]:
            generic.append(rule(structure, tag=f"village_{pool}_{period}", window=window))

    def track_at(cell):
        rows = by_song[cells[cell]]
        assert len(rows) == 1
        return rows[0]["Proposed_Track_ID"]

    # Equal priority uses source-key ordering in CobbleSafari 0.3.4.
    # Keep tower at index 0 and Lavender Town at index 1 in this same file.
    towns = [rule("cobbletowns:lavender_town", music=track_at("I13"), piece="cobbletowns:lavender_town/buildings/pokemon_tower"),
             rule("cobbletowns:lavender_town", music=track_at("I9"))]
    for town, cell in TOWN_CELLS.items():
        if town == "lavender_town":
            continue
        if town == "twinleaf_town":
            for period, window in [("Day", [0, 12000]), ("Night", [12000, 24000])]:
                candidate = next(r for r in by_song[cells[cell]] if r["Source_ZIP_Path"].endswith(f"({period}).ogg"))
                towns.append(rule("cobbletowns:" + town, music=candidate["Proposed_Track_ID"], window=window))
        else:
            towns.append(rule("cobbletowns:" + town, music=track_at(cell)))
    triggers = {"villages_generic": generic, "villages_cobbletowns": towns,
                "villages_legendary_monuments": [rule("legendarymonuments:traditional_village/ecruteak", music=track_at("J5"))]}
    assert [len(v) for v in triggers.values()] == [30, 9, 1]
    for filename, rules in triggers.items():
        path = root / "definition" / (filename + ".json")
        write_json(path, {"rules": rules})
        write_json(mirror / path.relative_to(repo), {"rules": rules})
    for path in [repo / "pack.mcmeta", mirror / "pack.mcmeta", repo / PACKAGE / "resourcepack_template/pack.mcmeta"]:
        meta = json.loads(path.read_text(encoding="utf-8"))
        meta["pack"]["description"] = "DysFam CSMusic RC4 QA - Ambient + Battles + Weather + Villages"
        write_json(path, meta)
    print("Generated 127 tracks, 40 village rules, 127 manifest additions; Kitakami tag reused; root/mirror synchronized.")


if __name__ == "__main__":
    main()
