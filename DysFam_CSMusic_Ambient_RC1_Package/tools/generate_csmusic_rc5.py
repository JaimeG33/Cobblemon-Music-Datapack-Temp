"""Generate the explicitly approved 40-condition RC5 layer from the research mapping.

Does not invoke or modify the historical RC4 generator. Existing runtime definitions
and manifest records are preserved; reruns require identical generated RC5 content.
"""
import csv
import io
import json
from pathlib import Path
import shutil

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / 'DysFam_CSMusic_Ambient_RC1_Package'
BASELINE = '6a974fb509dcd58603cf17e7b7d54df48742dab5'
DEFAULT_AUDIO = Path('D:/Minecraft Stuff/Minecraft Datapacks/CSMusic Sources/DysFam Music OGG Files.zip')
INCLUDED = {'INCLUDE_AFTER_APPROVAL', 'INCLUDE_SUBJECT_TO_PIECE_CONTAINMENT_CHECK'}
FILES = {'Minecraft': 'vanilla', 'Cobblemon': 'cobblemon',
         'Legendary Monuments': 'legendary_monuments', 'Mega Showdown': 'mega_showdown',
         'Terralith': 'terralith'}


def mapping():
    with (REPO / 'docs/RC5_STRUCTURES_MAPPING.csv').open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def approved_rules(rows):
    result = {f'structures_{name}.json': [] for name in FILES.values()}
    for row in rows:
        if row['Recommended_RC5_Scope'] not in INCLUDED:
            continue
        track = row['Existing_Track_ID'] or row['Proposed_Track_ID']
        pieces = row['Proposed_Structure_Piece_ID'].split(';') if row['Proposed_Structure_Piece_ID'] else ['']
        for piece in pieces:
            when = {'dimension': row['Dimension'], 'battle': 'never', 'structure': row['Proposed_Structure_ID']}
            if piece:
                when['structure_piece'] = piece
            result[f"structures_{FILES[row['Source_Mod']]}.json"].append({'music': track, 'priority': 41, 'when': when})
    return result


def write_new_json(path, value):
    if path.exists() and json.loads(path.read_bytes()) != value:
        raise ValueError(f'Refusing to replace differing existing content: {path}')
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def main():
    rows = mapping()
    included = [r for r in rows if r['Recommended_RC5_Scope'] in INCLUDED]
    assert len(rows) == 47 and len(included) == 40
    root = REPO / 'data/dysfam_music/csmusic'
    manifest_path = PACKAGE / 'manifest/csmusic_release_assets.csv'
    with manifest_path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        manifest = list(reader)
    new = {r['Proposed_Track_ID']: r for r in included if not r['Existing_Track_ID']}
    assert len(new) == 27
    for track, row in new.items():
        slug = track.split(':')[1].removeprefix('structures_')
        resource = f'music/structures/{slug}'
        event = 'dysfam_music:' + resource
        write_new_json(root / (track.split(':')[1] + '.json'), {'loop': event})
        record = {'Spreadsheet_Song': row['Exact_Song_Label'], 'Source_ZIP_Path': row['Source_ZIP_Member'],
                  'Original_OGG_Filename': row['Source_ZIP_Member'].split('/')[-1],
                  'Size_MB': f"{int(row['Source_Bytes']) / 1048576:.2f}", 'Resource_Path': resource,
                  'Sound_Event_ID': event, 'CSMusic_Track_ID': track, 'Pool_Tags': '',
                  'Destination_OGG_Path': f'assets/dysfam_music/sounds/{resource}.ogg',
                  'Segment_Role': 'full_loop', 'Feature_Layer': 'structures', 'Release_Added': 'RC5'}
        existing = [r for r in manifest if r['CSMusic_Track_ID'] == track]
        if existing:
            assert existing == [record], f'Differing registration: {track}'
        else:
            manifest.append(record)
    assert len(manifest) == 443
    # Retain the existing CSV prefix verbatim, including its newline convention.
    before = manifest_path.read_bytes()
    with manifest_path.open(encoding='utf-8-sig', newline='') as f:
        original = list(csv.DictReader(f))
    if len(original) < len(manifest):
        tail = io.StringIO(newline='')
        writer = csv.DictWriter(tail, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator='\r\n')
        writer.writerows(manifest[len(original):])
        assert before.endswith(b'\n')
        manifest_path.write_bytes(before + tail.getvalue().encode('utf-8'))
    rules = approved_rules(rows)
    assert sum(map(len, rules.values())) == 45
    for name, values in rules.items():
        write_new_json(root / 'definition' / name, {'rules': values})
    description = 'DysFam CSMusic RC5 - Ambient + Battles + Weather + Villages + Structures'
    for path, fmt in [(REPO / 'pack.mcmeta', 48), (PACKAGE / 'resourcepack_template/pack.mcmeta', 34)]:
        path.write_text(json.dumps({'pack': {'pack_format': fmt, 'description': description}}, indent=2) + '\n', encoding='utf-8')
    check = REPO / 'data/dysfam_music/function/check.mcfunction'
    lines = [
        ('=== ToaRex Music Pack Status ===', 'gold'),
        ('Datapack: ONLINE', 'green'),
        ('Release: RC5 - Ambient + Battles + Weather + Villages + Structures (Gameplay QA pending)', 'aqua'),
        ('DysFam CSMusic tracks declared: 434', 'white'),
        ('Resource sound events expected: 443 (client pack cannot be queried by vanilla commands)', 'white'),
        ('Generic wild species rules: 1016 (base Cobblemon 1.7.3)', 'white'),
        ('Expected CobbleSafari runtime: 440 music definitions / 1355 trigger rules / 24 trigger files', 'white'),
        ('Structures: 40 conditions / 45 rules at priority 41; seven conditions deferred', 'aqua'),
        ('Lake music currently covers whole native bounds, including interiors', 'aqua'),
        ('Detection: /cobblesafari csmusic structures; audio: /function dysfam_music:check_audio', 'aqua'),
    ]
    check.write_text(''.join('tellraw @s ' + json.dumps({'text': text, 'color': color}) + '\n' for text, color in lines), encoding='utf-8')
    mirror = PACKAGE / 'datapack'
    for path in [REPO / 'pack.mcmeta', *[p for p in (REPO / 'data').rglob('*') if p.is_file()]]:
        dest = mirror / path.relative_to(REPO)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
    print('Generated RC5: 40 conditions, 45 rules, 27 new tracks; cumulative 434/1351/21 and 443 events.')


if __name__ == '__main__':
    main()
