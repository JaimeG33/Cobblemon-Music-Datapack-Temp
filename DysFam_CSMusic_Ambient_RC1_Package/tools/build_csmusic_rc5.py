"""Build cumulative RC5 ZIPs without extracting the source music library."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

sys.dont_write_bytecode = True
from generate_csmusic_rc5 import DEFAULT_AUDIO, PACKAGE, REPO


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['datapack', 'resourcepack'])
    parser.add_argument('--audio', type=Path, default=DEFAULT_AUDIO)
    args = parser.parse_args()
    # Fail before replacing an existing build if source/scope/preservation is invalid.
    subprocess.run([sys.executable, str(PACKAGE / 'tools/validate_csmusic_rc5.py'), '--audio', str(args.audio)], check=True)
    out = PACKAGE / 'build_output'
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"DysFam_CSMusic_RC5_{'Datapack' if args.kind == 'datapack' else 'ResourcePack'}.zip"
    temp = target.with_suffix('.zip.tmp')
    try:
        with zipfile.ZipFile(temp, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            if args.kind == 'datapack':
                for path in [REPO / 'pack.mcmeta', *sorted(p for p in (REPO / 'data').rglob('*') if p.is_file())]:
                    z.write(path, path.relative_to(REPO).as_posix())
            else:
                z.write(PACKAGE / 'resourcepack_template/pack.mcmeta', 'pack.mcmeta')
                with (PACKAGE / 'manifest/csmusic_release_assets.csv').open(encoding='utf-8-sig', newline='') as f:
                    rows = list(csv.DictReader(f))
                sounds = {}
                with zipfile.ZipFile(args.audio) as source:
                    counts = Counter(source.namelist())
                    for row in rows:
                        member = row['Source_ZIP_Path']
                        if counts[member] != 1:
                            raise ValueError('Missing/duplicate source member: ' + member)
                        with source.open(member) as src, z.open(row['Destination_OGG_Path'], 'w', force_zip64=True) as dst:
                            shutil.copyfileobj(src, dst)
                        sounds[row['Resource_Path']] = {'sounds': [{'name': row['Sound_Event_ID'], 'stream': True}]}
                z.writestr('assets/dysfam_music/sounds.json', json.dumps(sounds, indent=2) + '\n')
        with zipfile.ZipFile(temp) as z:
            names = z.namelist()
            if z.testzip() or len(names) != len(set(names)) or any('\\' in n for n in names):
                raise ValueError('Built ZIP failed CRC/path/duplicate checks')
        temp.replace(target)
    finally:
        if temp.exists():
            temp.unlink()
    with target.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    print(f'SUCCESS: {target}\nSHA256: {digest}')


if __name__ == '__main__':
    main()
