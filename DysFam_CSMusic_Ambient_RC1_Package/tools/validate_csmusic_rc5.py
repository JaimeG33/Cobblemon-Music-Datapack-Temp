"""Validate approved RC5 scope, preservation, installed IDs, audio and built archives."""
import argparse
from collections import Counter
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
from generate_csmusic_rc5 import BASELINE, DEFAULT_AUDIO, INCLUDED, PACKAGE, REPO, mapping


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def read_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def git_file(path):
    return subprocess.check_output(['git', 'show', f'{BASELINE}:{path}'], cwd=REPO)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio', type=Path, default=DEFAULT_AUDIO)
    parser.add_argument('--ffmpeg', type=Path)
    parser.add_argument('--archives', action='store_true')
    parser.add_argument('--report', type=Path, default=PACKAGE / 'build_output/RC5_VALIDATION.json')
    args = parser.parse_args()
    root = REPO / 'data/dysfam_music/csmusic'
    tracks = {'dysfam_music:' + p.stem: read_json(p.read_bytes()) for p in root.glob('*.json')}
    files = {p.name: read_json(p.read_bytes())['rules'] for p in (root / 'definition').glob('*.json')}
    rules = [r for values in files.values() for r in values]
    manifest_name = 'DysFam_CSMusic_Ambient_RC1_Package/manifest/csmusic_release_assets.csv'
    with (REPO / manifest_name).open(encoding='utf-8-sig', newline='') as f:
        manifest = list(csv.DictReader(f))
    baseline_manifest = list(csv.DictReader(io.StringIO(git_file(manifest_name).decode('utf-8-sig'))))
    require(len(baseline_manifest) == 416 and manifest[:416] == baseline_manifest, 'RC4 manifest preservation')
    baseline_csv = git_file(manifest_name)
    require((REPO / manifest_name).read_bytes().replace(b'\r\n', b'\n').startswith(baseline_csv.replace(b'\r\n', b'\n')), 'Manifest prefix preservation')
    archive = subprocess.check_output(['git', 'archive', BASELINE, 'data'], cwd=REPO)
    preserved = 0
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for entry in tar:
            if not entry.isfile() or entry.name.endswith('/function/check.mcfunction'):
                continue
            before = tar.extractfile(entry).read().replace(b'\r\n', b'\n')
            require((REPO / entry.name).read_bytes().replace(b'\r\n', b'\n') == before, 'Baseline changed: ' + entry.name)
            preserved += 1
    require(sum(r['when'].get('battle') == 'wild' for r in rules) == 1016, 'Generic battle count')
    new_files = {name: values for name, values in files.items() if name.startswith('structures_')}
    new_rules = [r for values in new_files.values() for r in values]
    rows = mapping()
    included = [r for r in rows if r['Recommended_RC5_Scope'] in INCLUDED]
    deferred = [r for r in rows if r not in included]
    require(len(rows) == 47 and len(included) == 40 and len(deferred) == 7, 'Approved condition count')
    require(all(r['Implementation_Status'] == ('IMPLEMENTED_PENDING_GAMEPLAY_QA' if r in included else 'DEFERRED_APPROVED') for r in rows), 'Mapping approval/implementation status')
    expected = Counter()
    for row in included:
        for piece in (row['Proposed_Structure_Piece_ID'].split(';') if row['Proposed_Structure_Piece_ID'] else ['']):
            expected[(row['Existing_Track_ID'] or row['Proposed_Track_ID'], row['Proposed_Structure_ID'], piece, row['Dimension'])] += 1
    actual = Counter()
    for rule in new_rules:
        require(set(rule) == {'music', 'priority', 'when'} and rule['priority'] == 41, 'RC5 rule schema/priority')
        when = rule['when']
        require(when['battle'] == 'never' and set(when) <= {'battle', 'dimension', 'structure', 'structure_piece'}, 'RC5 supported conditions')
        require(rule['music'] in tracks, 'Missing track reference')
        actual[(rule['music'], when['structure'], when.get('structure_piece', ''), when['dimension'])] += 1
    require(expected == actual and sum(actual.values()) == 45, 'Exact approved cells/music/IDs/dimensions/piece expansion')
    for row in deferred:
        if row['Proposed_Structure_Piece_ID']:
            require(not any(r['when'].get('structure_piece') == row['Proposed_Structure_Piece_ID'] for r in new_rules), 'Deferred lake piece activated')
    require((len(tracks), len(rules), len(files), len(manifest)) == (407 + 27, 1306 + sum(expected.values()), 16 + len(new_files), 416 + 27), 'Cumulative counts')
    require(len(new_files) == 5, 'Five RC5 definition files')
    for field in ('Sound_Event_ID', 'Destination_OGG_Path', 'Resource_Path', 'Source_ZIP_Path'):
        require(len({r[field] for r in manifest}) == len(manifest), 'Duplicate manifest ' + field)
    new_tracks = {r['Proposed_Track_ID']: r for r in included if not r['Existing_Track_ID']}
    require({r['CSMusic_Track_ID'] for r in manifest[416:]} == set(new_tracks), 'Approved audio additions')
    for row in manifest[416:]:
        source = new_tracks[row['CSMusic_Track_ID']]
        require(row['Spreadsheet_Song'] == source['Exact_Song_Label'] and row['Source_ZIP_Path'] == source['Source_ZIP_Member'], 'Exact audio provenance')
        require(row['Feature_Layer'] == 'structures' and row['Release_Added'] == 'RC5' and row['Segment_Role'] == 'full_loop' and row['Pool_Tags'] == '', 'New manifest metadata')
        require(tracks[row['CSMusic_Track_ID']] == {'loop': row['Sound_Event_ID']}, 'New full-loop definition')
    events = {r['Sound_Event_ID'] for r in manifest}
    for name, track in tracks.items():
        for segment in ('intro', 'loop', 'outro'):
            if track.get(segment):
                require(track[segment] in events, f'Unresolved {segment}: {name}')
    for row in manifest:
        require(row['Sound_Event_ID'] == 'dysfam_music:' + row['Resource_Path'], 'Event/resource mismatch')
        require(row['Destination_OGG_Path'] == 'assets/dysfam_music/sounds/' + row['Resource_Path'] + '.ogg', 'Destination mismatch')
        require(re.fullmatch(r'music/[a-z0-9_/]+', row['Resource_Path']), 'Unsafe resource path')
    mirror = PACKAGE / 'datapack'
    source_set = {'pack.mcmeta', *[p.relative_to(REPO).as_posix() for p in (REPO / 'data').rglob('*') if p.is_file()]}
    mirror_set = {'pack.mcmeta', *[p.relative_to(mirror).as_posix() for p in (mirror / 'data').rglob('*') if p.is_file()]}
    require(source_set == mirror_set, 'Root/mirror file sets')
    for name in source_set:
        require((REPO / name).read_bytes() == (mirror / name).read_bytes(), 'Root/mirror bytes: ' + name)
    require(read_json((REPO / 'pack.mcmeta').read_bytes())['pack']['pack_format'] == 48, 'Datapack format')
    require(read_json((PACKAGE / 'resourcepack_template/pack.mcmeta').read_bytes())['pack']['pack_format'] == 34, 'Resource pack format')
    # Reuse archive evidence by reading only the exact recorded paths; no discovery scan.
    evidence = {}
    for row in included:
        path, member = row['ID_Evidence'].split('!/', 1)
        member = member.split(';', 1)[0]
        evidence.setdefault(path, set()).add(member)
    for path, members in evidence.items():
        with zipfile.ZipFile(path) as z:
            require(members <= set(z.namelist()), 'Recorded structure evidence changed: ' + path)
    lm = next(Path(p) for p in evidence if 'legendarymonuments-' in p)
    safari = lm.parent / 'cobblesafari-fabric-1.21.1-0.3.4.jar'
    defaults = [0, 0, 0]
    with zipfile.ZipFile(safari) as z:
        require(read_json(z.read('fabric.mod.json'))['version'] == '0.3.4', 'Installed CobbleSafari version')
        for name in z.namelist():
            if re.fullmatch(r'data/[^/]+/csmusic/[^/]+\.json', name):
                defaults[0] += 1
            elif re.fullmatch(r'data/[^/]+/csmusic/definition/[^/]+\.json', name):
                defaults[1] += len(read_json(z.read(name))['rules'])
                defaults[2] += 1
    require(defaults == [6, 4, 3], 'Installed default counts changed')
    with zipfile.ZipFile(lm) as z:
        pool_members = [n for n in z.namelist() if n.startswith('data/legendarymonuments/worldgen/template_pool/traditional_village/ecruteak/') and n.endswith('.json')]
        locations = {e['element'].get('location') for n in pool_members for e in read_json(z.read(n))['elements'] if e['element'].get('element_type') == 'minecraft:single_pool_element'}
        for rule in new_rules:
            piece = rule['when'].get('structure_piece')
            if piece:
                require(piece in locations, 'Tower not referenced by single pool: ' + piece)
                require('data/legendarymonuments/structure/' + piece.split(':')[1] + '.nbt' in z.namelist(), 'Missing tower template')
    # Simulated condition/arbitration checks; gameplay containment is a separate gate.
    simulated = 0
    def matches(rule, structure, piece, dimension, battle):
        when = rule['when']
        return (when['dimension'] == dimension and when['battle'] == 'never' and not battle
                and when['structure'] == structure and ('structure_piece' not in when or when['structure_piece'] == piece))
    for rule in new_rules:
        w = rule['when']
        sid, piece, dim = w['structure'], w.get('structure_piece', ''), w['dimension']
        require(matches(rule, sid, piece, dim, False), 'Inside selection')
        require(not matches(rule, '', '', dim, False), 'Outside selection')
        require(not matches(rule, sid, piece, dim, True), 'Battle exclusion')
        require(not matches(rule, sid, piece, 'minecraft:invalid', False), 'Dimension exclusion')
        require(max([10, 30, 40, rule['priority']]) == 41, 'Weather/village arbitration')
        if piece:
            require(not matches(rule, sid, 'legendarymonuments:unrelated', dim, False), 'Tower exterior fallback')
        simulated += 5 + bool(piece)
    decoded = []
    with zipfile.ZipFile(args.audio) as z:
        members = Counter(z.namelist())
        for row in manifest:
            member = row['Source_ZIP_Path']
            require(members[member] == 1, 'Missing/duplicate source member: ' + member)
            with z.open(member) as f:
                header = f.read(64)
            require(header.startswith(b'OggS') and b'\x01vorbis' in header, 'Invalid Ogg/Vorbis header: ' + member)
        for row in manifest[416:]:
            info = z.getinfo(row['Source_ZIP_Path'])
            source = new_tracks[row['CSMusic_Track_ID']]
            require(info.file_size == int(source['Source_Bytes']) and f'{info.CRC:08x}' == source['Source_CRC32'], 'Source bytes/CRC changed')
            if args.ffmpeg:
                data = z.read(info)
                proc = subprocess.run([str(args.ffmpeg), '-hide_banner', '-v', 'info', '-xerror', '-i', 'pipe:0', '-c:a', 'pcm_s16le', '-f', 's16le', '-'], input=data, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
                text = proc.stderr.decode(errors='replace')
                audio_line = next((line.strip() for line in text.splitlines() if 'Audio: vorbis' in line), '')
                duration = re.findall(r'time=([0-9:.]+)', text)
                require(audio_line and duration, 'Decoded audio metadata unavailable')
                decoded.append({'song': row['Spreadsheet_Song'], 'stream': audio_line, 'decoded_duration': duration[-1], 'status': 'PASS_DECODE'})
    hashes = {}
    if args.archives:
        dp = PACKAGE / 'build_output/DysFam_CSMusic_RC5_Datapack.zip'
        rp = PACKAGE / 'build_output/DysFam_CSMusic_RC5_ResourcePack.zip'
        for path in (dp, rp):
            with zipfile.ZipFile(path) as z:
                names = z.namelist()
                require(len(names) == len(set(names)) and all('\\' not in n and not n.startswith('/') and '..' not in n.split('/') for n in names), 'ZIP paths/duplicates')
                require(z.testzip() is None, 'ZIP CRC')
                require('pack.mcmeta' in names, 'Root pack metadata')
                if path == dp:
                    require(set(names) == source_set, 'Datapack ZIP file set')
                    for name in names:
                        require(z.read(name) == (REPO / name).read_bytes(), 'Packaged datapack bytes: ' + name)
                else:
                    require(z.read('pack.mcmeta') == (PACKAGE / 'resourcepack_template/pack.mcmeta').read_bytes(), 'Resource metadata')
                    sounds = read_json(z.read('assets/dysfam_music/sounds.json'))
                    require(set(sounds) == {r['Resource_Path'] for r in manifest}, 'Packaged sound events')
                    require(set(names) == {'pack.mcmeta', 'assets/dysfam_music/sounds.json', *[r['Destination_OGG_Path'] for r in manifest]}, 'Resource ZIP exact set')
                    with zipfile.ZipFile(args.audio) as source_zip:
                        for row in manifest:
                            require(sounds[row['Resource_Path']] == {'sounds': [{'name': row['Sound_Event_ID'], 'stream': True}]}, 'Streaming event mapping')
                            source_info = source_zip.getinfo(row['Source_ZIP_Path'])
                            target_info = z.getinfo(row['Destination_OGG_Path'])
                            require((source_info.file_size, source_info.CRC) == (target_info.file_size, target_info.CRC), 'Packaged OGG bytes/CRC')
            hashes[path.name] = sha(path)
    report = {'status': 'PASS_STATIC', 'baseline': BASELINE, 'preserved_data_files': preserved,
              'scope': {'included': 40, 'deferred': [r['Original_Condition'] for r in deferred]},
              'counts': {'tracks': len(tracks), 'rules': len(rules), 'definition_files': len(files), 'events': len(manifest)},
              'installed_defaults': defaults, 'expected_runtime_counts': [len(tracks) + defaults[0], len(rules) + defaults[1], len(files) + defaults[2]],
              'simulated_selection_checks': simulated, 'source_headers_checked': len(manifest),
              'decoded_audio': decoded, 'archive_sha256': hashes,
              'gameplay': 'PENDING: native containment, transitions and actual playback',
              'loop_seams': 'PENDING: representative audition; decoding does not establish seamless loops'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'decoded_audio'}, indent=2))
    print(f'Decoded {len(decoded)} new audio files. Report: {args.report}')


if __name__ == '__main__':
    main()
