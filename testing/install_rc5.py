"""Install RC5 and prepare a new isolated test copy while Minecraft is closed."""
import json
from pathlib import Path
import re
import shutil
import sys
import nbtlib

sys.dont_write_bytecode = True
from harness import HERE, REPO, digest, java_running, prepare, require, stamp, write_json


def main():
    require(not java_running(), 'Close Minecraft before installing RC5 or preparing the test copy')
    config_path = HERE / 'config_rc5.json'
    config = json.loads(config_path.read_bytes())
    package = REPO / 'DysFam_CSMusic_Ambient_RC1_Package'
    evidence = json.loads((REPO / 'docs/RC5_BUILD_RESULTS.json').read_bytes())
    artifacts = {kind: package / f'build_output/DysFam_CSMusic_RC5_{kind}.zip' for kind in ('Datapack', 'ResourcePack')}
    for path in artifacts.values():
        require(digest(path).lower() == evidence['archive_sha256'][path.name], 'RC5 build hash mismatch: ' + path.name)
    config.update(receipt='prepared_rc5.json', world_name_prefix='CSMusic RC5 Test ', prepare_gamemode='spectator')
    setup = HERE / 'results' / ('rc5-install-' + __import__('datetime').datetime.now().strftime('%Y%m%d-%H%M%S'))
    setup.mkdir(parents=True, exist_ok=False)
    options = Path(config['profile']) / 'options.txt'
    backup_options = options.read_bytes()
    (setup / 'options-before.txt').write_bytes(backup_options)
    (setup / 'config-before.json').write_bytes(config_path.read_bytes())
    old_receipt_path = HERE / config['receipt']
    if old_receipt_path.exists():
        (setup / 'previous-rc5-receipt.json').write_bytes(old_receipt_path.read_bytes())
    # prepare checks source containment, links, source hash, and the running-game guard.
    receipt = prepare(config)
    world = Path(receipt['world']).resolve()
    saves = (Path(config['profile']) / 'saves').resolve()
    require(world.parent == saves and world != (saves / config['source_world']).resolve(), 'Invalid fresh-copy target')
    require(json.loads((world / 'csmusic-harness-copy.json').read_bytes()) == receipt, 'Fresh copy receipt mismatch')
    packs = world / 'datapacks'
    dp = packs / artifacts['Datapack'].name
    shutil.copyfile(artifacts['Datapack'], dp)
    disabled = []
    for old in packs.glob('DysFam_CSMusic*.zip'):
        if old == dp:
            continue
        require(old.resolve().parent == packs.resolve(), 'Unexpected old-pack target')
        backup = old.with_suffix('.zip.disabled')
        require(not backup.exists(), 'Disabled-pack backup already exists')
        old.rename(backup)
        disabled.append(old.name)
    level = nbtlib.load(world / 'level.dat')
    data = level['Data']
    enabled = [str(value) for value in data['DataPacks']['Enabled'] if not str(value).startswith('file/DysFam_CSMusic')]
    enabled.append('file/' + dp.name)
    data['DataPacks']['Enabled'] = nbtlib.List[nbtlib.String]([nbtlib.String(value) for value in dict.fromkeys(enabled)])
    data['DataPacks']['Disabled'] = nbtlib.List[nbtlib.String]([value for value in data['DataPacks']['Disabled'] if str(value) != 'file/' + dp.name])
    level.save()
    require(not java_running(), 'Minecraft started during preparation; close it before profile installation')
    rp = Path(config['profile']) / 'resourcepacks' / artifacts['ResourcePack'].name
    rp.parent.mkdir(parents=True, exist_ok=True)
    if rp.exists() and digest(rp).lower() != evidence['archive_sha256'][rp.name]:
        shutil.copyfile(rp, setup / ('previous-' + rp.name))
    if not rp.exists() or digest(rp).lower() != evidence['archive_sha256'][rp.name]:
        temp = rp.with_suffix('.zip.installing')
        shutil.copyfile(artifacts['ResourcePack'], temp)
        require(digest(temp).lower() == evidence['archive_sha256'][rp.name], 'Copied resource pack hash mismatch')
        temp.replace(rp)
    text = backup_options.decode('utf-8')
    pattern = re.compile(r'^resourcePacks:(.*)$', re.MULTILINE)
    match = pattern.search(text)
    require(match is not None, 'Resource pack options line missing')
    previous = json.loads(match[1])
    selected = []
    inserted = False
    for entry in previous:
        if entry.startswith('file/DysFam_CSMusic'):
            if not inserted:
                selected.append('file/' + rp.name)
                inserted = True
        else:
            selected.append(entry)
    if not inserted:
        selected.append('file/' + rp.name)
    replacement = 'resourcePacks:' + json.dumps(selected, separators=(',', ':'))
    updated = pattern.sub(lambda _: replacement, text, count=1)
    require(options.read_bytes() == backup_options, 'Options changed during preparation; refusing overwrite')
    options.write_bytes(updated.encode('utf-8'))
    config['installed_world'] = world.name
    config['audio']['reference_resource_pack'] = rp.as_posix()
    write_json(config_path, config)
    require(digest(dp).lower() == evidence['archive_sha256'][dp.name], 'Installed datapack hash mismatch')
    require(digest(Path(receipt['source']) / 'level.dat') == receipt['source_level_sha256'], 'Original world changed')
    report = {'status': 'INSTALLED_PENDING_GAMEPLAY', 'created': stamp(), 'world': str(world), 'receipt': receipt,
              'datapack': {'path': str(dp), 'sha256': digest(dp)},
              'resourcepack': {'path': str(rp), 'sha256': digest(rp)},
              'previous_resourcepacks': previous, 'selected_resourcepacks': selected,
              'disabled_in_copy': disabled, 'options_backup': str(setup / 'options-before.txt'),
              'original_world_preserved': True, 'older_rc4_receipt_preserved': True}
    write_json(setup / 'installation.json', report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
