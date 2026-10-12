"""Windows CSMusic controller. No production pack writes; fresh feedback required."""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import uuid
import zipfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


class Blocked(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise Blocked(message)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def assistance_message(report):
    category = report.get('failure_category', '')
    if category == 'BLOCKED_SCENARIOS':
        blocked = [item for item in report.get('scenarios', []) if item.get('status') == 'BLOCKED']
        if blocked:
            scenario = blocked[0]
            target = scenario.get('expected', {}).get('structure', scenario['id'])
            if 'Terrain probe' in scenario.get('exception', {}).get('message', ''):
                return 'No safe landing at ' + target + '. Confirm readiness to try another verified waypoint.'
            if scenario.get('expected', {}).get('piece'):
                return 'Please stand safely inside Pokemon Tower and confirm readiness before restarting.'
            return 'Test stopped: ' + scenario['id'] + '. Check the report and confirm readiness before restarting.'
    messages = {
        'BLOCKED_CHAT_STATE': 'Please close all menus and chat, unpause the copied world, and confirm readiness before restarting.',
        'BLOCKED_MANUAL_LISTENING': 'Please confirm Lavender music is audible. Reply in Codex, then return to Minecraft.',
        'BLOCKED_MANUAL_TOWER': 'Please stand on a safe floor inside Pokemon Tower, close chat, and confirm readiness in Codex.',
        'BLOCKED_FIXTURE': 'Please move or identify a safe waypoint inside the requested structure/piece, then start a new run.',
        'BLOCKED_LOADING': 'Please wait for the destination to finish loading, confirm Minecraft is responsive, then start a new run.',
        'BLOCKED_FOCUS': 'Please inspect and clear Minecraft chat/menu state, foreground the verified copied world, then explicitly start recovery or a new run.',
        'OVERLAPPING_STRUCTURES_EXPECTED_ARBITRATION': 'This is a verified structure overlap. Choose a Pallet-only waypoint or treat the overlap as its own arbitration regression.'}
    return messages.get(category)


def notify_assistance(config, message):
    options = config.get('assistance', {})
    try:
        if options.get('beep', False):
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass
    if options.get('windows_notification', False) and os.name == 'nt':
        ctypes.windll.user32.MessageBoxW(0, message, 'CSMusic harness needs assistance', 0x40 | 0x1000)


def gamerule_value(response):
    match = re.search(r'doDaylightCycle is currently set to: (true|false)', response)
    require(match is not None, 'Cannot verify current doDaylightCycle value')
    return match.group(1)


def expected_rule_sources(selection, priority):
    """Resolve declared sources for a track/pool at priority without altering runtime ordering."""
    results = []
    for path in sorted((REPO / 'data/dysfam_music/csmusic/definition').glob('*.json')):
        data = json.loads(path.read_bytes())
        for index, rule in enumerate(data.get('rules', [])):
            if int(rule.get('priority', -9999)) != int(priority):
                continue
            selected = rule.get('music') or ('#' + rule['tag'] if rule.get('tag') else None)
            if selected == selection:
                results.append(f'definition:csmusic/definition/{path.name}#{index}')
    return results


def install_probe(world):
    """Read-only terrain queries, installed exclusively in the receipted test copy."""
    pack = world / 'datapacks/csmusic_harness'
    functions = pack / 'data/csmusic_harness/function'
    functions.mkdir(parents=True, exist_ok=True)
    tags = pack / 'data/csmusic_harness/tags/block'
    tags.mkdir(parents=True, exist_ok=True)
    write_json(tags / 'safe_floor.json', {'values': ['minecraft:' + b for b in
               ('stone', 'dirt', 'grass_block', 'sand', 'sandstone', 'cobblestone', 'stone_bricks',
                'deepslate', 'gravel', 'dirt_path', 'podzol', 'snow_block', 'oak_planks', 'spruce_planks', 'birch_planks')]})
    lines = []
    for y in range(318, -64, -1):
        lines.append(f'$execute if loaded $(x) {y} $(z) if block $(x) {y-1} $(z) #csmusic_harness:safe_floor if block $(x) {y} $(z) minecraft:air if block $(x) {y+1} $(z) minecraft:air run tellraw @s "CSMUSIC_GROUND $(x) {y} $(z)"')
    (functions / 'probe.mcfunction').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def windows():
    require(os.name == 'nt', 'Windows desktop required')
    user = ctypes.windll.user32
    found = []
    callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def visit(hwnd, _):
        if user.IsWindowVisible(hwnd):
            title = ctypes.create_unicode_buffer(1024)
            user.GetWindowTextW(hwnd, title, 1024)
            pid = wintypes.DWORD()
            user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if 'minecraft' in title.value.lower():
                found.append({'hwnd': int(hwnd), 'pid': pid.value, 'title': title.value})
        return True
    user.EnumWindows(callback(visit), 0)
    return found


def java_running():
    result = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, text=True, check=True)
    return bool(re.search(r'"javaw?\.exe"', result.stdout, re.I))


def verify_installed_datapack(installed, recovery_only=False):
    require(installed.is_file(), 'Expected datapack is not installed in configured test world')
    with zipfile.ZipFile(installed) as z:
        require(json.loads(z.read('pack.mcmeta'))['pack']['pack_format'] == 48, 'Unexpected datapack format')
        require(z.testzip() is None, 'Installed datapack ZIP failed CRC validation')
        # Cleanup ownership and copy identity do not depend on the latest production
        # definitions. Ordinary gameplay preflight still compares every source byte.
        if recovery_only:
            return 0
        compared = 0
        source_files = [REPO / 'pack.mcmeta'] + list((REPO / 'data').rglob('*'))
        for source in source_files:
            if source.is_file():
                name = source.relative_to(REPO).as_posix()
                require(z.read(name) == source.read_bytes(), 'Installed datapack differs from repository: ' + name)
                compared += 1
        return compared


def audit(config, recovery_only=False):
    profile = Path(config['profile'])
    require(profile.is_dir(), 'Profile missing')
    mods = {}
    metadata_warnings = []
    defaults = [0, 0, 0]
    for jar in (profile / 'mods').glob('*.jar'):
        with zipfile.ZipFile(jar) as z:
            if 'fabric.mod.json' not in z.namelist():
                continue
            try:
                meta = json.loads(z.read('fabric.mod.json'))
            except (ValueError, UnicodeError) as exc:
                metadata_warnings.append({'file': jar.name, 'error': str(exc)})
                continue
            if meta.get('id') in ('cobblesafari', 'cobblemon', 'fabric-api'):
                mods[meta['id']] = {'version': meta['version'], 'file': str(jar), 'sha256': digest(jar)}
            if meta.get('id') == 'cobblesafari':
                for name in z.namelist():
                    if re.fullmatch(r'data/[^/]+/csmusic/[^/]+\.json', name):
                        defaults[0] += 1
                    elif re.fullmatch(r'data/[^/]+/csmusic/definition/[^/]+\.json', name):
                        defaults[1] += len(json.loads(z.read(name))['rules'])
                        defaults[2] += 1
    root = REPO / 'data/dysfam_music/csmusic'
    triggers = list((root / 'definition').glob('*.json'))
    source_counts = [len(list(root.glob('*.json'))), sum(len(json.loads(p.read_bytes())['rules']) for p in triggers), len(triggers)]
    log = profile / 'logs/latest.log'
    old = log.read_text(encoding='utf-8', errors='replace') if log.exists() else ''
    installed_world = config.get('installed_world', config['source_world'])
    if 'installed_world' in config:
        receipt = json.loads((HERE / config.get('receipt', 'prepared.json')).read_bytes())
        world = (profile / 'saves' / installed_world).resolve()
        require(world == Path(receipt['world']).resolve(), 'Configured installation is not the verified copy')
        require(json.loads((world / 'csmusic-harness-copy.json').read_bytes()) == receipt, 'Invalid copy receipt')
    installed = profile / 'saves' / installed_world / 'datapacks' / config['expected_datapack'].removeprefix('file/')
    compared = verify_installed_datapack(installed, recovery_only)
    resource_options = [line for line in (profile / 'options.txt').read_text(encoding='utf-8').splitlines() if line.startswith('resourcePacks:')]
    rp_path = Path(config.get('audio', {}).get('reference_resource_pack', ''))
    audio_inventory = {'reference_pack': str(rp_path), 'available': rp_path.is_file(),
                       'loopback_runtime_events_logged': False, 'instrumentation': 'not detected in ordinary client log'}
    if rp_path.is_file():
        with zipfile.ZipFile(rp_path) as z:
            sound_path = 'assets/dysfam_music/sounds.json'
            audio_inventory['sound_events'] = len(json.loads(z.read(sound_path))) if sound_path in z.namelist() else None
            audio_inventory['ogg_files'] = sum(n.endswith('.ogg') and n.startswith('assets/dysfam_music/sounds/') for n in z.namelist())
    safari_jar = Path(mods['cobblesafari']['file'])
    with zipfile.ZipFile(safari_jar) as z:
        class_names = [n for n in z.namelist() if n.startswith('maxigregrze/cobblesafari/client/audio/') and n.endswith('.class')]
    audio_inventory['cobblesafari_audio_classes'] = class_names
    audio_inventory['cobblesafari_jar_sha256'] = mods['cobblesafari']['sha256']
    audio_inventory['static_bytecode_findings'] = {
        'private_client_state_fields': ['CsMusicPlayer.currentTrackId', 'CsMusicPlayer.currentVoice', 'CsMusicVoice.positionSamples'],
        'fade_constants_ms': {'synced_crossfade': 1000, 'crossfade': 5000, 'fade': 2500},
        'normal_track_start_stop_log_events': False,
        'runtime_instrumentation_added': False}
    log_audio = [line for line in old.splitlines() if re.search(r'\b(csmusic|sound engine|sound event|openal|playing sound)\b', line, re.I)]
    audio_inventory['relevant_log_lines'] = log_audio[-40:]
    audio_inventory['client_instrumentation_found'] = any(re.search(r'playing sound|sound event.*play', line, re.I) for line in log_audio)
    minimap_jars = [p.name for p in (profile / 'mods').glob('*.jar') if re.search(r'minimap|worldmap|xaero', p.name, re.I)]
    minimap_configs = [str(p) for p in (profile / 'config').glob('*xaero*')]
    return {'profile': str(profile), 'saves': [p.name for p in (profile / 'saves').iterdir() if p.is_dir()],
            'mods': mods, 'metadata_warnings': metadata_warnings, 'source_counts': source_counts, 'builtin_counts': defaults,
            'computed_total': [a+b for a,b in zip(source_counts, defaults)],
            'installed_datapack': {'file': str(installed), 'sha256': digest(installed), 'source_files_matched': compared,
                                   'validation': 'readable historical ZIP for ownership recovery only' if recovery_only else 'current source byte comparison'},
            'resource_pack_options_disk_snapshot': resource_options,
            'windows': windows(), 'java_running': java_running(),
            'previous_log_evidence_only': [line for line in old.splitlines() if '[CSMusic] Loaded' in line or 'Loading Minecraft ' in line],
            'audio_investigation': audio_inventory,
            'minimap_investigation': {'mod_jars': minimap_jars, 'configuration_paths': minimap_configs,
                                      'roi': config.get('minimap_roi'),
                                      'authority': 'visual corroboration only; structure bounds and piece diagnostics remain authoritative'},
            'settings': json.loads((profile / 'config/cobblesafari/csmusic_settings.json').read_bytes())}


def prepare(config):
    import nbtlib
    require(not java_running(), 'Close Minecraft before copying a save; live copies are not safe')
    saves = Path(config['profile']) / 'saves'
    source = (saves / config['source_world']).resolve()
    require(source.parent == saves.resolve() and source.is_dir(), 'Invalid source save')
    require(not source.is_symlink(), 'Linked save not supported')
    for p in source.rglob('*'):
        require(not p.is_symlink() and not p.is_junction(), 'Linked save contents not supported')
    token = uuid.uuid4().hex
    prefix = config.get('world_name_prefix', 'CSMusic Automation ')
    require(re.fullmatch(r'[A-Za-z0-9 _-]{1,48}', prefix), 'Invalid copied-world name prefix')
    target = saves / (prefix + datetime.now().strftime('%Y%m%d-%H%M%S'))
    require(not target.exists(), 'Copy destination already exists')
    original_hash = digest(source / 'level.dat')
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('session.lock'))
    level = nbtlib.load(target / 'level.dat')
    data = level['Data']
    require(str(data['Version']['Name']) == '1.21.1', 'Save is not Minecraft 1.21.1')
    data['LevelName'] = nbtlib.String(target.name)
    prepare_mode = config.get('prepare_gamemode', 'creative')
    require(prepare_mode in ('creative', 'spectator'), 'Invalid preparation gamemode')
    game_type = 3 if prepare_mode == 'spectator' else 1
    data['GameType'] = nbtlib.Int(game_type)
    data['allowCommands'] = nbtlib.Byte(1)
    if 'Player' in data:
        data['Player']['playerGameType'] = nbtlib.Int(game_type)
        abilities = data['Player']['abilities']
        for key in ('mayfly', 'instabuild', 'invulnerable'):
            abilities[key] = nbtlib.Byte(1)
    pack = target / 'datapacks/csmusic_harness'
    functions = pack / 'data/csmusic_harness/function'
    functions.mkdir(parents=True)
    write_json(pack / 'pack.mcmeta', {'pack': {'pack_format': 48, 'description': 'Isolated CSMusic test-world identity'}})
    # Token exists only in this copy. A fresh command roundtrip proves world identity.
    (functions / 'identity.mcfunction').write_text('tellraw @s ' + json.dumps('CSMUSIC_WORLD_' + token) + '\n', encoding='utf-8')
    install_probe(target)
    enabled = data['DataPacks']['Enabled']
    enabled.append(nbtlib.String('file/csmusic_harness'))
    level.save()
    require(digest(source / 'level.dat') == original_hash, 'Original level.dat changed during copy')
    receipt = {'world': str(target.resolve()), 'token': token, 'source': str(source),
               'source_level_sha256': original_hash, 'created': stamp(), 'profile': config['profile']}
    write_json(target / 'csmusic-harness-copy.json', receipt)
    write_json(HERE / config.get('receipt', 'prepared.json'), receipt)
    return receipt


def chat_lines(text):
    # Player chat is deliberately excluded. Never use bare user-supplied messages as feedback.
    return [re.sub(r'§.', '', s.split('[System] [CHAT] ', 1)[1])
            for s in text.splitlines() if '[System] [CHAT] ' in s]


def framed_response(text, nonce):
    lines = chat_lines(text)
    if nonce + '_BEGIN' not in lines or nonce + '_END' not in lines:
        return None
    first, last = lines.index(nonce + '_BEGIN'), lines.index(nonce + '_END')
    require(last > first, 'Out-of-order command markers')
    return '\n'.join(lines[first+1:last])


def playing(text):
    return [item for item in music_sources(text) if item['playing']]


def music_sources(text):
    """Parse source identity, rule index, selected track/pool, priority and winner flag."""
    result = []
    pattern = re.compile(
        r'^- \[(?P<source>[^\]]+)#(?P<index>\d+)\] '
        r'(?P<selection>[#\w:./-]+)(?: \([^\n]*?\))? '
        r'\(priority (?P<priority>-?\d+)\)(?P<playing> <= playing)?$', re.M)
    for match in pattern.finditer(text):
        rule_index = int(match['index'])
        result.append({'source': match['source'], 'rule_index': rule_index,
                       'source_key': match['source'] + '#' + str(rule_index),
                       'selection': match['selection'], 'priority': int(match['priority']),
                       'playing': bool(match['playing'])})
    return result


def runtime_source(source):
    """Translate a suite source path to CobbleSafari's displayed source-key format."""
    normalized = source.replace('\\', '/')
    marker = '/csmusic/'
    require(marker in normalized and re.fullmatch(r'.+\.json#\d+', normalized),
            'Invalid suite source identifier: ' + source)
    relative = normalized.split(marker, 1)[1]
    return 'definition:csmusic/' + relative


def selection_diagnosis(case, bounds, current, all_cases):
    """Classify mismatch only when runtime source and containment evidence are complete."""
    matches = music_sources(current)
    winners = [entry for entry in matches if entry['playing']]
    expected_source = runtime_source(case['source'])
    expected = case.get('music') or '#' + case['pool']
    expected_matches = [entry for entry in matches
                        if entry['source_key'] == expected_source and entry['selection'] == expected
                        and entry['priority'] == int(case['priority'])]
    structures = re.findall(r'^- ([\w:./-]+)\s+\[bounds: 1,', bounds, re.M)
    source_cases = {runtime_source(item['source']): item for item in all_cases}
    if not bounds.startswith('Structures at '):
        return {'category': 'INCOMPLETE_DIAGNOSTIC_EVIDENCE', 'expected_source': expected_source,
                'matching_structures': structures, 'sources': matches}
    if not contains_structure(bounds, case['structure'], case.get('piece')):
        return {'category': 'INVALID_OR_AMBIGUOUS_FIXTURE', 'expected_source': expected_source,
                'matching_structures': structures, 'sources': matches}
    if not winners or not matches:
        return {'category': 'INCOMPLETE_DIAGNOSTIC_EVIDENCE', 'expected_source': expected_source,
                'matching_structures': structures, 'sources': matches}
    competing = [entry for entry in winners if entry['source_key'] != expected_source
                 and entry['source_key'] in source_cases
                 and contains_structure(bounds, source_cases[entry['source_key']]['structure'],
                                        source_cases[entry['source_key']].get('piece'))]
    higher_priority = [entry for entry in winners if entry['priority'] > int(case['priority'])]
    if higher_priority:
        return {'category': 'EXPECTED_PRIORITY_ARBITRATION', 'expected_source': expected_source,
                'matching_structures': structures, 'sources': matches,
                'winning_competitor': higher_priority[0]}
    if competing:
        category = ('OVERLAPPING_STRUCTURES_EXPECTED_ARBITRATION'
                    if competing[0]['priority'] == int(case['priority']) else 'EXPECTED_PRIORITY_ARBITRATION')
        return {'category': category, 'expected_source': expected_source,
                'matching_structures': structures, 'sources': matches,
                'winning_competitor': competing[0]}
    unmapped = [entry for entry in winners if entry['priority'] == int(case['priority'])
                and entry['source_key'] != expected_source and entry['source_key'] not in source_cases]
    if unmapped:
        return {'category': 'INCOMPLETE_DIAGNOSTIC_EVIDENCE', 'expected_source': expected_source,
                'matching_structures': structures, 'sources': matches,
                'unmapped_winner': unmapped[0]}
    if expected_matches and any(entry['playing'] for entry in expected_matches):
        return {'category': 'PASS_SELECTION', 'expected_source': expected_source,
                'matching_structures': structures, 'sources': matches}
    if not expected_matches:
        return {'category': 'INCOMPLETE_DIAGNOSTIC_EVIDENCE', 'expected_source': expected_source,
                'matching_structures': structures, 'sources': matches}
    return {'category': 'VALID_FIXTURE_WRONG_SELECTION', 'expected_source': expected_source,
            'matching_structures': structures, 'sources': matches}


def contains_structure(text, structure, piece=None):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not re.match(r'^- ' + re.escape(structure) + r'\s', line):
            continue
        if '[bounds: 1, piece:' not in line:
            return False
        if not piece:
            return True
        if '[bounds: 1, piece: 1]' not in line:
            return False
        for detail in lines[i+1:]:
            if detail.startswith('- '):
                break
            if detail.strip() == 'piece: ' + piece:
                return True
        return False
    return False


def locate_coordinates(text, structure):
    match = re.search(r'The nearest ' + re.escape(structure) + r' is at \[(-?\d+), (~|-?\d+), (-?\d+)\]', text)
    require(match is not None, 'Locate response missing exact structure ID and coordinates')
    x, y, z = match.groups()
    xyz = (int(x), None if y == '~' else int(y), int(z))
    require(abs(xyz[0]) < 29999984 and abs(xyz[2]) < 29999984, 'Locate coordinates outside world bounds')
    return xyz


def allowed_command(command):
    if command.startswith('tellraw @s {'):
        try:
            payload = json.loads(command[len('tellraw @s '):])
            return (isinstance(payload, dict) and set(payload) == {'text', 'color'}
                    and payload['color'] == 'gold' and isinstance(payload['text'], str)
                    and payload['text'].startswith('[CSMusic Tester] ')
                    and len(payload['text']) <= 160 and payload['text'].isascii()
                    and not any(ord(c) < 32 for c in payload['text']))
        except (ValueError, TypeError):
            return False
    exact = {'datapack list enabled', 'function dysfam_music:check', 'function csmusic_harness:identity',
             'reload', 'cobblesafari csmusic current', 'cobblesafari csmusic structures', 'data get entity @s Pos',
             'data get entity @s Inventory',
             'gamerule doDaylightCycle', 'gamerule doDaylightCycle true', 'gamerule doDaylightCycle false',
             'execute if entity @s[gamemode=spectator] run tellraw @s "CSMUSIC_SPECTATOR"',
             'execute if entity @s[gamemode=creative] run tellraw @s "CSMUSIC_CREATIVE"'}
    patterns = [r'tellraw @s "CSMUSIC_[a-f0-9]+_(?:BEGIN|END)"',
                r'execute if loaded -?\d+ -?\d+ -?\d+ run tellraw @s "CSMUSIC_LOADED"',
                r'locate structure [a-z0-9_.-]+:[a-z0-9_/.-]+',
                r'forceload (?:query|add|remove) -?\d+ -?\d+',
                r'function csmusic_harness:probe \{x:-?\d+,z:-?\d+\}',
                r'tp @s -?\d+\.5 -?\d+ -?\d+\.5', r'weather (?:clear|rain|thunder)', r'time set \d+',
                r'playsound minecraft:[a-z0-9_./]+ master @s ~ ~ ~ (?:0\.[1-9]\d?|1) (?:0\.[5-9]|1(?:\.[0-9])?|2)']
    return command in exact or any(re.fullmatch(p, command) for p in patterns)


def structure_signature(response):
    """Compare diagnostic records, ignoring unrelated fresh chat broadcasts and ordering."""
    return tuple(sorted(line.strip() for line in response.splitlines()
                        if re.match(r'^Structures at ', line)
                        or re.match(r'^- [\w:./-]+\s+.*\[bounds: [01], piece: [01]\]', line)
                        or re.match(r'^\s+piece:', line)))


class LogTail:
    def __init__(self, path):
        self.path = path
        self.stream = path.open('rb')
        self.stream.seek(0, 2)
        self.pending = b''
        self.identity = (path.stat().st_dev, path.stat().st_ino)

    def read(self):
        stat = self.path.stat()
        require((stat.st_dev, stat.st_ino) == self.identity and stat.st_size >= self.stream.tell(), 'Log rotated/truncated; abort')
        data = self.pending + self.stream.read()
        complete, _, self.pending = data.rpartition(b'\n')
        if b'\n' not in data:
            self.pending = data
            return ''
        return complete.decode('utf-8', errors='replace') + '\n'

    def close(self):
        self.stream.close()


class Desktop:
    def __init__(self, hwnd, stop_file, profile=None):
        import pyautogui
        self.gui = pyautogui
        self.gui.FAILSAFE = True
        self.gui.PAUSE = 0.025
        self.user = ctypes.windll.user32
        self.user.GetForegroundWindow.restype = wintypes.HWND
        self.hwnd = hwnd
        self.stop_file = stop_file
        self.profile = profile

    def focus(self):
        self.user.ShowWindow(self.hwnd, 9)
        self.user.SetForegroundWindow(self.hwnd)
        time.sleep(.3)
        self.guard()

    def guard(self):
        require(not getattr(self, 'aborted', False), 'Desktop input aborted; explicit new invocation required')
        try:
            require(not self.stop_file.exists(), 'Emergency STOP file present')
            require(not self.user.GetAsyncKeyState(0x77) & 0x8000, 'Emergency F8 stop')
            self.gui.failSafeCheck()
            require(self.user.IsWindow(self.hwnd), 'Minecraft window closed')
            require(not self.user.IsHungAppWindow(self.hwnd), 'Minecraft window unresponsive')
            require(self.user.GetForegroundWindow() == self.hwnd, 'Minecraft lost focus; no further input permitted')
        except BaseException:
            self.aborted = True
            raise

    def send(self, command):
        require('\n' not in command and '\r' not in command and command.isascii() and len(command) <= 255, 'Unsafe chat command')
        require(allowed_command(command), 'Command outside harness allowlist')
        self.guard()
        self.gui.press('/')
        time.sleep(1.0)
        # Prove that the slash reached a text field before typing command keys.
        # A focused Minecraft window alone does not imply that chat is open.
        self.guard()
        self.gui.hotkey('ctrl', 'a')
        try:
            require(self.copy_selected_text() == '/',
                    'Chat input not verified; no command text sent. Close menus/chat and restart.')
        except BaseException:
            self.aborted = True
            raise
        for char in '/' + command:
            self.guard()
            self.gui.write(char)
        self.guard()
        self.gui.hotkey('ctrl', 'a')
        try:
            require(self.copy_selected_text() == '/' + command,
                    'Chat command text changed; Enter not sent. Close menus/chat and restart.')
        except BaseException:
            self.aborted = True
            raise
        self.guard()
        self.gui.press('enter')

    def copy_selected_text(self):
        """Require a fresh copy, without logging or examining unrelated clipboard contents."""
        sequence = self.user.GetClipboardSequenceNumber()
        self.guard()
        self.gui.hotkey('ctrl', 'c')
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            self.guard()
            if self.user.GetClipboardSequenceNumber() != sequence:
                self.user.GetClipboardData.restype = wintypes.HANDLE
                kernel = ctypes.windll.kernel32
                kernel.GlobalLock.argtypes = [wintypes.HGLOBAL]
                kernel.GlobalLock.restype = ctypes.c_void_p
                kernel.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
                if not self.user.OpenClipboard(None):
                    # Clipboard history/tools may briefly hold the lock after Ctrl+C.
                    # Retry only while the same focus and stop guards still pass.
                    time.sleep(.05)
                    continue
                try:
                    handle = self.user.GetClipboardData(13)  # CF_UNICODETEXT
                    require(handle, 'Clipboard copy did not provide text; command entry stopped')
                    pointer = kernel.GlobalLock(handle)
                    require(pointer, 'Clipboard text unavailable; command entry stopped')
                    try:
                        return ctypes.wstring_at(pointer)
                    finally:
                        kernel.GlobalUnlock(handle)
                finally:
                    self.user.CloseClipboard()
            time.sleep(.05)
        raise Blocked('Chat copy did not complete; no text field verified')

    def screenshot(self, path):
        self.guard()
        rect = wintypes.RECT()
        self.user.GetWindowRect(self.hwnd, ctypes.byref(rect))
        screen = self.gui.screenshot(region=(rect.left, rect.top, rect.right-rect.left, rect.bottom-rect.top))
        if screen.convert('RGB').getbbox() is not None:
            screen.save(path)
            return path
        # Some OpenGL/fullscreen sessions return an all-black desktop capture. F2 captures
        # the actual game framebuffer and avoids claiming a black image as useful evidence.
        require(self.profile is not None, 'Black desktop screenshot; native capture profile unavailable')
        screenshots = Path(self.profile) / 'screenshots'
        before = {p.name for p in screenshots.glob('*.png')}
        options = (Path(self.profile) / 'options.txt').read_text(encoding='utf-8')
        require('key_key.screenshot:key.keyboard.f2' in options, 'Native screenshot key is not F2')
        self.guard()
        self.gui.press('f2')
        until = time.monotonic() + 10
        while time.monotonic() < until:
            self.guard()
            fresh = [p for p in screenshots.glob('*.png') if p.name not in before]
            if len(fresh) == 1:
                try:
                    from PIL import Image
                    with Image.open(fresh[0]) as captured:
                        captured.load()
                        require(captured.convert('RGB').getbbox() is not None, 'Native screenshot also black')
                    shutil.copy2(fresh[0], path)
                    return path
                except (OSError, PermissionError):
                    pass  # Screenshot may still be being written.
            time.sleep(.1)
        raise Blocked('No complete native screenshot received within 10 seconds')


class Controller:
    def __init__(self, config, mode, case=None, recover_report=None):
        self.config, self.mode, self.case = config, mode, case
        self.recover_report = recover_report
        self.start = time.monotonic()
        self.out = HERE / 'results' / (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6])
        self.out.mkdir(parents=True)
        run_id = mode if not case else (case.get('id', mode) if isinstance(case, dict) else mode)
        self.report = {'id': run_id, 'description': 'CSMusic ' + mode,
                       'started': stamp(), 'status': 'blocked', 'validation': 'static' if mode in ('audit', 'dry-run') else 'runtime selection',
                       'test_level': 'selection-only; audio is not a required gate unless calibrated and explicitly configured',
                       'verification_layers': {'music_selection': 'NOT_RUN', 'client_sound_event': 'NOT_AVAILABLE',
                                               'windows_loopback_audio': 'NOT_TESTED'},
                       'audible_playback': 'not tested', 'commands': [], 'states': [],
                       'controller_sha256': digest(Path(__file__)),
                       'expected': case if isinstance(case, (dict, list)) else {'counts': config['expected_counts'], 'release': config.get('release', 'RC4')}, 'observed': {}}
        if mode == 'capture':
            self.report['expected'] = {'evidence': 'nonblack screenshot and fresh playing-source response; this mode does not rerun RC4 smoke'}
        self.desktop = self.tail = None
        self.raw = ''
        self.world_verified = False
        self.command_state_safe = False
        self.audio_recording = False

    def request_assistance(self, message):
        """Stop this invocation; confirmation and fresh checks belong to the next invocation."""
        request = {'requested': True, 'message': message,
                   'confirmation': 'not received; no automatic resume',
                   'resume_requires': 'explicit user confirmation, then fresh world/focus/position/fixture checks',
                   'notification': 'terminal/report', 'audio_recording_stopped': not self.audio_recording}
        self.report['assistance'] = request
        options = self.config.get('assistance', {})
        if (self.audio_recording or not self.world_verified or not self.command_state_safe
                or not self.desktop or not self.tail or not options.get('minecraft_sound_alert', True)):
            return request
        try:
            self.desktop.guard()
            marker = HERE / 'results' / 'last-assistance-notification.json'
            previous = json.loads(marker.read_bytes()) if marker.exists() else {}
            if time.time() - float(previous.get('unix_time', 0)) < options.get('minimum_alert_interval_seconds', 60):
                request['notification'] = 'rate limited; terminal/report'
                return request
            self.state('ASSISTANCE', 60, 'Guarded in-game notification; run remains stopped')
            identity = self.command('function csmusic_harness:identity', screenshot=False)
            require('CSMUSIC_WORLD_' + self.receipt['token'] in identity, 'Identity changed before assistance')
            text = '[CSMusic Tester] ' + message
            # Keep the complete command within Minecraft chat's controller limit.
            text = text[:160]
            payload = json.dumps({'text': text, 'color': 'gold'}, separators=(',', ':'))
            self.command('tellraw @s ' + payload, screenshot=False)
            sound = options.get('sound_command', 'playsound minecraft:entity.ender_dragon.death master @s ~ ~ ~ 1 1')
            require(allowed_command(sound) and sound.startswith('playsound '), 'Invalid assistance sound command')
            self.command(sound, screenshot=False)
            write_json(marker, {'unix_time': time.time(), 'report': str(self.out)})
            request['notification'] = 'Minecraft tellraw and playsound'
        except Exception as exc:
            request['notification_error'] = {'type': type(exc).__name__, 'message': str(exc)}
        return request

    def state(self, name, timeout, success):
        self.deadline = time.monotonic() + timeout
        self.report['states'].append({'state': name, 'time': stamp(), 'timeout_seconds': timeout, 'success_condition': success})
        print(name, flush=True)

    def guard(self):
        require(time.monotonic() <= self.deadline, 'State deadline exceeded')
        self.desktop.guard()

    def wait(self, seconds):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            self.guard()
            time.sleep(.05)

    def capture(self, name):
        if self.desktop:
            max_images = int(self.config.get('max_screenshots_per_run', 20))
            existing = [p for p in self.out.glob('*.png') if not p.stem.endswith('-minimap')]
            if len(existing) >= max_images:
                self.report.setdefault('observed', {}).setdefault('visual_capture_skipped', []).append(
                    {'name': name, 'reason': 'configured per-run screenshot limit reached'})
                return None
            path = self.desktop.screenshot(self.out / (name + '.png'))
            try:
                from PIL import Image, ImageStat
                with Image.open(path) as image:
                    image.load()
                    width, height = image.size
                    roi = self.config.get('minimap_roi', [0.70, 0.0, 0.30, 0.32])
                    x0, y0 = int(width*roi[0]), int(height*roi[1])
                    x1, y1 = min(width, int(width*(roi[0]+roi[2]))), min(height, int(height*(roi[1]+roi[3])))
                    crop = image.crop((x0, y0, x1, y1))
                    crop.save(path.with_name(path.stem + '-minimap.png'))
                    stats = ImageStat.Stat(crop.convert('RGB'))
                    self.report.setdefault('observed', {}).setdefault('visual_samples', []).append({
                        'image': path.name, 'minimap_crop': path.stem + '-minimap.png',
                        'dimensions': [width, height], 'roi_pixels': [x0, y0, x1, y1],
                        'roi_rgb_mean': [round(v, 2) for v in stats.mean],
                        'roi_rgb_stddev': [round(v, 2) for v in stats.stddev],
                        'interpretation': 'visual evidence only; no automated structure or loading conclusion'})
            except Exception as exc:
                self.report.setdefault('observed', {}).setdefault('visual_analysis_errors', []).append(
                    {'image': path.name, 'type': type(exc).__name__, 'message': str(exc)})
            return path
        return None

    def command(self, command, timeout=None, screenshot=True):
        timeout = timeout or self.config['command_timeout']
        nonce = 'CSMUSIC_' + uuid.uuid4().hex
        item = {'command': '/' + command, 'started': stamp(), 'status': 'input pending', 'timeout': timeout}
        self.report['commands'].append(item)
        self.command_state_safe = False
        # Fresh tail + unpredictable exact system-chat markers; one outstanding request only.
        self.tail.read()
        self.guard()
        self.desktop.send('tellraw @s ' + json.dumps(nonce + '_BEGIN'))
        self.guard()
        self.desktop.send(command)
        item['status'] = 'submitted; awaiting verified response'
        self.guard()
        self.desktop.send('tellraw @s ' + json.dumps(nonce + '_END'))
        until = time.monotonic() + timeout
        response = ''
        while time.monotonic() < until:
            self.guard()
            chunk = self.tail.read()
            response += chunk
            self.raw += chunk
            result = framed_response(response, nonce)
            if result is not None:
                item.update({'status': 'response captured', 'response': result, 'finished': stamp()})
                require(not re.search(r'Unknown or incomplete command|Incorrect argument|Unknown function|You do not have permission|No entity was found', result), 'Command rejected: ' + result)
                self.command_state_safe = True
                if screenshot:
                    self.capture('command-' + str(len(self.report['commands'])))
                return result
            time.sleep(.05)
        item['status'] = 'timeout'
        raise Blocked('No complete fresh command response within timeout: ' + command)

    def runtime_ready(self):
        receipt = json.loads((HERE / self.config.get('receipt', 'prepared.json')).read_bytes())
        self.receipt = receipt
        world = Path(receipt['world']).resolve()
        require(world.parent == (Path(self.config['profile']) / 'saves').resolve(), 'Copy belongs to another profile')
        require(json.loads((world / 'csmusic-harness-copy.json').read_bytes()) == receipt, 'Copy receipt mismatch')
        wins = windows()
        require(len(wins) == 1, 'Expected exactly one Minecraft window; launch profile and load copied save')
        # Verify process command line against profile without retaining credentials in the report.
        script = f"(Get-CimInstance Win32_Process -Filter 'ProcessId = {wins[0]['pid']}').CommandLine"
        proc = subprocess.run(['powershell', '-NoProfile', '-Command', script], capture_output=True, text=True, check=True)
        require(str(Path(self.config['profile'])).lower() in proc.stdout.replace('/', '\\').lower(), 'Window process is not the configured profile')
        self.desktop = Desktop(wins[0]['hwnd'], HERE / 'STOP', self.config['profile'])
        # Do not take focus away from the user's active application. The operator must leave
        # Minecraft foreground before a run; any later focus loss is terminal.
        self.desktop.guard()
        if self.config.pop('initial_chat_open', False):
            # Used only with explicit operator confirmation of the initial empty chat.
            self.desktop.gui.press('esc')
            time.sleep(1.0)
            self.desktop.guard()
            self.report['observed']['initial_chat_closed'] = 'Escape, explicitly requested by user'
        self.tail = LogTail(Path(self.config['profile']) / 'logs/latest.log')
        mode = self.config.get('test_gamemode', 'creative')
        require(mode in ('creative', 'spectator'), 'Test mode must be creative or explicitly authorized spectator')
        self.state('READY', 90, 'Fresh copy-specific identity response and verified test gamemode')
        identity = self.command('function csmusic_harness:identity')
        require('CSMUSIC_WORLD_' + receipt['token'] in identity, 'Wrong world, title/menu screen, or copy identity pack not active')
        marker = 'CSMUSIC_' + mode.upper()
        verified_mode = self.command(f'execute if entity @s[gamemode={mode}] run tellraw @s "{marker}"')
        require(marker in verified_mode.splitlines(), 'Copied world must be in configured ' + mode + ' mode')
        self.report['environment']['player_mode'] = mode
        self.report['environment']['test_world'] = str(world)
        self.world_verified = True

    def player_position(self):
        response = self.command('data get entity @s Pos', screenshot=False)
        numbers = re.search(r'\[(-?[\d.]+)d, (-?[\d.]+)d, (-?[\d.]+)d\]', response)
        require(numbers, 'Player XYZ response unavailable')
        return [float(v) for v in numbers.groups()]

    def await_readiness(self, case, x, y, z):
        loading = self.config.get('loading', {})
        minimum = int(loading.get('minimum_settle_seconds', self.config['settle_seconds']))
        interval = int(loading.get('poll_seconds', 7))
        timeout = int(loading.get('timeout_seconds', 180))
        required = int(loading.get('stable_observations', 2))
        self.state('WAIT_LOAD', timeout, 'Loaded destination, stable bounds and stable CSMusic winner with screenshots retained')
        started = time.monotonic()
        self.wait(minimum)
        observations = self.report['observed'].setdefault('readiness_observations', [])
        previous = None
        stable = 0
        while time.monotonic() - started < timeout:
            self.guard()
            loaded = self.command(f'execute if loaded {x} {y} {z} run tellraw @s "CSMUSIC_LOADED"', screenshot=False)
            identity = self.command('function csmusic_harness:identity', screenshot=False)
            require('CSMUSIC_WORLD_' + self.receipt['token'] in identity,
                    'Copied-world identity changed during teleport readiness polling')
            bounds = self.command('cobblesafari csmusic structures', screenshot=False)
            current = self.command('cobblesafari csmusic current', screenshot=False)
            image = self.capture('readiness-' + str(len(observations) + 1))
            winners = playing(current)
            signature = ('CSMUSIC_LOADED' in loaded.splitlines(), structure_signature(bounds),
                         tuple((e['source_key'], e['selection'], e['priority']) for e in winners))
            item = {'elapsed_seconds': round(time.monotonic() - started, 1),
                    'destination_loaded': 'CSMUSIC_LOADED' in loaded,
                    'bounds_contain_expected': contains_structure(bounds, case['structure'], case.get('piece')),
                    'playing_sources': winners, 'screenshot': image.name if image else None,
                    'render_loading_indicator_automated': False}
            observations.append(item)
            if item['destination_loaded'] and winners and signature == previous:
                stable += 1
            else:
                stable = 1 if item['destination_loaded'] and winners else 0
            previous = signature
            if stable >= required and time.monotonic() - started >= minimum:
                if not item['bounds_contain_expected']:
                    self.report['failure_category'] = 'BLOCKED_FIXTURE'
                    raise Blocked('Loaded diagnostic point does not meet requested structure or exact piece containment')
                self.report['observed']['loading_readiness'] = {
                    'status': 'ready', 'elapsed_seconds': round(time.monotonic() - started, 1),
                    'stable_observations': stable, 'destination_loaded': True,
                    'bounds_and_music_stable': True}
                return
            self.wait(interval)
        self.report['failure_category'] = 'BLOCKED_LOADING'
        self.report['observed']['loading_readiness'] = {
            'status': 'timeout', 'elapsed_seconds': round(time.monotonic() - started, 1),
            'stable_observations': stable, 'maximum_seconds': timeout}
        raise Blocked('Destination loading and stable CSMusic observations were not established')

    def await_music_stability(self, label):
        loading = self.config.get('loading', {})
        minimum = int(loading.get('minimum_settle_seconds', self.config['settle_seconds']))
        interval = int(loading.get('poll_seconds', 7))
        timeout = int(loading.get('timeout_seconds', 180))
        required = int(loading.get('stable_observations', 2))
        self.state('WAIT_MUSIC', timeout, 'Post-context music selection is stable across repeated fresh responses')
        started = time.monotonic()
        self.wait(minimum)
        previous, stable = None, 0
        observations = self.report['observed'].setdefault('music_stability_observations', [])
        while time.monotonic() - started < timeout:
            current = self.command('cobblesafari csmusic current', screenshot=False)
            winners = playing(current)
            context = re.search(r'time: (\d+) \| weather: (\w+)', current)
            signature = (context.groups() if context else None,
                         tuple((e['source_key'], e['selection'], e['priority']) for e in winners))
            observations.append({'label': label, 'elapsed_seconds': round(time.monotonic()-started, 1),
                                 'context': context.groups() if context else None, 'playing_sources': winners})
            stable = stable + 1 if current and signature == previous and winners and context else (1 if winners and context else 0)
            previous = signature
            if stable >= required:
                return current
            self.wait(interval)
        self.report['failure_category'] = 'BLOCKED_LOADING'
        raise Blocked('Music selection did not stabilize after the context change: ' + label)

    def capture_audio(self, selection, compare_selection=None):
        audio_config = self.config.get('audio', {})
        if not audio_config.get('enabled', False):
            return {'status': 'NOT_TESTED', 'classification': 'NOT_TESTED',
                    'reason': 'Audio capture is disabled in testing/config.json'}
        from audio import AudioUnavailable, capture_loopback, identify
        seconds = min(int(audio_config.get('capture_seconds', 30)), int(audio_config.get('maximum_seconds', 90)))
        self.state('AUDIO_CAPTURE', seconds + 20, 'WASAPI endpoint capture with validated recording and candidate ranking')
        path = self.out / ('audio-loopback-' + uuid.uuid4().hex[:8] + '.wav')
        try:
            self.audio_recording = True
            try:
                evidence = capture_loopback(path, seconds, audio_config.get('device_index'), guard=self.guard)
            finally:
                self.audio_recording = False
            limit = int(audio_config.get('maximum_recording_megabytes', 180)) * 1024 * 1024
            require(path.stat().st_size <= limit, 'Audio recording exceeds configured evidence size limit')
            if evidence['rms_int16'] < float(audio_config.get('minimum_capture_rms_int16', 100)):
                evidence.update({'status': 'BLOCKED_AUDIO_DEVICE', 'classification': 'BLOCKED_AUDIO_DEVICE',
                                 'reason': 'Loopback recording was near silent; no selection conclusion'})
            else:
                negative = compare_selection or audio_config.get('negative_selection', 'dysfam_music:villages_lgpe_pallet_town')
                result = identify(path, selection, Path(audio_config['reference_resource_pack']), audio_config.get('ffmpeg'), negative)
                evidence.update({'status': 'INCONCLUSIVE_AUDIO', 'classification': result['classification'],
                                 'match': result})
                limit = float(audio_config.get('clipping_fraction_limit', 0.01))
                if evidence['clipped_fraction'] > limit:
                    evidence['classification'] = 'INCONCLUSIVE_AUDIO'
                    evidence['clipping_warning'] = f"{evidence['clipped_fraction']:.4%} of samples meet the clipping threshold {limit:.2%}"
            return evidence
        except AudioUnavailable as exc:
            result = evidence if 'evidence' in locals() else {}
            result.update({'status': exc.category, 'classification': exc.category,
                           'exception': {'type': type(exc).__name__, 'message': str(exc)}})
            return result

    def smoke(self):
        release = self.config.get('release', 'RC4')
        self.state('QUERY', 300, 'Enabled pack, status function, current selection, and fresh loader totals')
        packs = self.command('datapack list enabled')
        require(self.config['expected_datapack'] in packs, release + ' datapack not confirmed enabled')
        check = self.command('function dysfam_music:check')
        require('Release: ' + release in check, 'Status function is not ' + release)
        # Declared check counts are NOT runtime evidence. Reload only after copy identity verified.
        self.command('reload', 120)
        until = time.monotonic() + 60
        definitions, rules = [], []
        while time.monotonic() < until:
            self.guard()
            self.raw += self.tail.read()
            definitions = re.findall(r'\[CSMusic\] Loaded (\d+) music definition\(s\), (\d+) skipped', self.raw)
            rules = re.findall(r'\[CSMusic\] Loaded (\d+) trigger rule\(s\) from (\d+) file\(s\), (\d+) file\(s\) rejected', self.raw)
            if definitions and rules:
                break
            time.sleep(.05)
        require(definitions and rules, 'Fresh CSMusic reload counts unavailable')
        d, r = definitions[-1], rules[-1]
        counts = [int(d[0]), int(r[0]), int(r[1])]
        require(counts == self.config['expected_counts'] and d[1] == r[2] == '0', 'Runtime load counts/rejections differ')
        current = self.command('cobblesafari csmusic current')
        require('csmusic sources for ' in current and playing(current), 'No parseable playing selection')
        self.report['observed'].update({'runtime_counts': counts, 'current': current,
                                        'music_sources': music_sources(current),
                                        'playing_source': playing(current),
                                        'pack_check': check, 'enabled_packs': packs})
        self.report['verification_layers']['music_selection'] = 'SMOKE_SELECTION_RESPONSE_CAPTURED'
        self.state('VERIFY', 1, 'All fresh smoke assertions passed')

    def structure(self, case):
        sid = case['structure']
        require(re.fullmatch(r'[a-z0-9_.-]+:[a-z0-9_/.-]+', sid), 'Invalid structure ID')
        self.state('LOCATE', self.config['locate_timeout'] + 30, 'Fresh exact-ID locate response')
        initial_xyz = self.player_position()
        self.report['observed']['initial_xyz'] = initial_xyz
        if case.get('at_current_position'):
            case = dict(case, waypoint=[math.floor(v) for v in initial_xyz])
            if self.config.get('test_gamemode') == 'spectator':
                case['spectator_waypoint'] = case['waypoint']
            self.report['observed']['human_intervention'] = 'User-confirmed current fixture; floor/headroom and containment rechecked'
        result = self.command('locate structure ' + sid, self.config['locate_timeout'])
        self.state('PARSE', 1, 'Complete numeric XYZ; never invent missing Y')
        x, y, z = locate_coordinates(result, sid)
        self.report['observed']['locate'] = [x, y, z]
        spectator_point = case.get('spectator_waypoint') if self.config.get('test_gamemode') == 'spectator' else None
        if spectator_point:
            require(len(spectator_point) == 3 and all(isinstance(v, int) for v in spectator_point), 'Invalid spectator waypoint')
            x, y, z = spectator_point
            require(-63 <= y <= 318 and abs(x) < 29999984 and abs(z) < 29999984, 'Spectator waypoint outside world bounds')
            self.report['observed']['spectator_candidate_xyz'] = spectator_point
        if case.get('candidate_xz'):
            candidate = case['candidate_xz']
            require(len(candidate) == 2 and all(isinstance(v, int) for v in candidate), 'Invalid saved candidate XZ')
            x, z = candidate
            require(abs(x) < 29999984 and abs(z) < 29999984, 'Candidate outside world bounds')
            self.report['observed']['saved_candidate_xz'] = candidate
        if case.get('waypoint'):
            waypoint = case['waypoint']
            require(len(waypoint) == 3 and all(isinstance(v, int) for v in waypoint), 'Invalid candidate waypoint')
            x, _, z = waypoint
            require(abs(x) < 29999984 and abs(z) < 29999984, 'Waypoint outside world bounds')
            self.report['observed']['candidate_waypoint'] = waypoint
        if self.config.get('test_gamemode') == 'spectator' and not spectator_point:
            height = case['waypoint'][1] if case.get('waypoint') else (y if y is not None else math.floor(initial_xyz[1]))
            spectator_point = [x, height, z]
            y = height
            self.report['observed']['spectator_candidate_xyz'] = spectator_point
            self.report['observed']['spectator_height_source'] = ('configured candidate' if case.get('waypoint')
                                                                else 'locate height or current verified player height; containment not assumed')
        require(math.hypot(x + .5 - initial_xyz[0], z + .5 - initial_xyz[2]) <=
                self.config.get('escalation', {}).get('max_travel_distance', 100000), 'Destination exceeds travel limit')
        self.state('TRAVEL', 180, 'Verified destination air/headroom, solid floor, and exact numeric teleport')
        if spectator_point:
            mode = self.command('execute if entity @s[gamemode=spectator] run tellraw @s "CSMUSIC_SPECTATOR"', screenshot=False)
            require('CSMUSIC_SPECTATOR' in mode.splitlines(), 'Spectator mode changed; floor waiver revoked')
        # Force-load only the destination chunk in the disposable copy, and preserve pre-existing tickets.
        ticket = self.command(f'forceload query {x} {z}')
        owned = 'is not marked for force loading' in ticket
        require(owned or 'is marked for force loading' in ticket, 'Unrecognized force-load query; no travel')
        if owned:
            added = self.command(f'forceload add {x} {z}')
            require('Marked chunk' in added or 'Marked chunks' in added, 'Destination chunk not confirmed force-loaded')
            self.report['observed']['temporary_forceload'] = [x, z]
        try:
            self.wait(3)
            loaded_attempts = self.report['observed']['pre_probe_loading'] = []
            for attempt in range(4):
                loaded = self.command(f'execute if loaded {x} 64 {z} run tellraw @s "CSMUSIC_LOADED"', screenshot=False)
                loaded_attempts.append({'attempt': attempt+1, 'loaded': 'CSMUSIC_LOADED' in loaded, 'time': stamp()})
                if 'CSMUSIC_LOADED' in loaded:
                    break
                self.wait(5)
            require(loaded_attempts[-1]['loaded'], 'Destination chunk did not load before terrain probing; no teleport sent')
            if spectator_point:
                valid = []
                destination = (x, y, z)
                self.report['observed']['landing_verification'] = 'Floor/headroom not required: explicitly authorized, runtime-verified spectator mode'
            else:
                probe = self.command(f'function csmusic_harness:probe {{x:{x},z:{z}}}')
                candidates = re.findall(r'^CSMUSIC_GROUND (-?\d+) (-?\d+) (-?\d+)$', probe, re.M)
                valid = [(int(a), int(b), int(c)) for a,b,c in candidates if int(a) == x and int(c) == z and -63 <= int(b) <= 318]
                require(valid, 'Terrain probe found no loaded safe surface; no teleport sent')
                destination = max(valid, key=lambda p: p[1])
            if case.get('waypoint') and not spectator_point:
                preferred = case['waypoint'][1]
                require(any(p[1] == preferred for p in valid), 'Candidate waypoint lacks verified safe floor/headroom')
                destination = next(p for p in valid if p[1] == preferred)
            y = destination[1]
            self.report['observed']['verified_destination'] = destination
            if not spectator_point:
                self.report['observed']['verified_ground'] = destination
            travel = self.command(f'tp @s {x + 0.5} {y} {z + 0.5}')
            require('Teleported ' in travel, 'Teleport response unavailable')
            pos = self.command('data get entity @s Pos')
            numbers = re.search(r'\[(-?[\d.]+)d, (-?[\d.]+)d, (-?[\d.]+)d\]', pos)
            require(numbers and all(abs(float(a)-b) < .1 for a,b in zip(numbers.groups(), (x+.5, y, z+.5))), 'Player did not reach verified XYZ')
            self.report['observed']['player_xyz'] = [float(v) for v in numbers.groups()]
            final_xyz = self.report['observed']['player_xyz']
            self.report['observed']['travel'] = {
                'initial_xyz': initial_xyz, 'locate_xyz': self.report['observed']['locate'],
                'probe_candidates': valid, 'selected_probe_xyz': destination,
                'teleport_destination': [x+.5, y, z+.5],
                'command': f'/tp @s {x+.5} {y} {z+.5}', 'response': travel,
                'verified_final_xyz': final_xyz, 'teleport_verified': True,
                'horizontal_displacement': round(math.hypot(final_xyz[0]-initial_xyz[0], final_xyz[2]-initial_xyz[2]), 3),
                'vertical_displacement': round(final_xyz[1]-initial_xyz[1], 3),
                'already_near_player': math.hypot(x+.5-initial_xyz[0], z+.5-initial_xyz[2]) <= 64,
                'surface_assessment': ('spectator position; floor/headroom checks waived by user, live containment required' if spectator_point
                                       else 'safe floor/headroom verified; ground/roof/interior requires visual review')}
            print('Travel: ' + json.dumps(self.report['observed']['travel']), flush=True)
            weather = case.get('weather', 'clear')
            ticks = case.get('time', 1000)
            require(weather in ('clear', 'rain', 'thunder') and isinstance(ticks, int) and 0 <= ticks < 24000, 'Invalid scenario time/weather')
            require('Set the weather' in self.command('weather ' + weather), 'Weather change not confirmed')
            require('Set the time' in self.command('time set ' + str(ticks)), 'Time change not confirmed')
            self.await_readiness(case, x, y, z)
            self.state('QUERY', 90, 'Structure containment and current playing source captured')
            bounds = self.command('cobblesafari csmusic structures')
            current = self.command('cobblesafari csmusic current')
            self.report['observed'].update({'structures': bounds, 'structure_current': current})
            self.state('VERIFY', 1, 'Exact structure bounds, expected selection and priority')
            expected = case.get('music') or '#' + case['pool']
            all_cases = json.loads((HERE / self.config.get('suite', 'suite.json')).read_bytes())['structures']
            diagnosis = selection_diagnosis(case, bounds, current, all_cases)
            self.report['observed']['selection_diagnosis'] = diagnosis
            self.report['observed']['expected_selection'] = {
                'source': diagnosis['expected_source'], 'selection': expected,
                'priority': int(case['priority'])}
            if diagnosis['category'] == 'PASS_SELECTION':
                self.report['observed']['music_selection_status'] = 'PASS'
                self.report['verification_layers']['music_selection'] = 'PASS'
                audio_cases = self.config.get('audio', {}).get('case_ids', [])
                if self.config.get('audio', {}).get('enabled', False) and (not audio_cases or case['id'] in audio_cases):
                    settle = int(self.config.get('audio', {}).get('post_transition_settle_seconds', 15))
                    self.state('AUDIO_SETTLE', settle + 2, 'Wait for fade/crossfade before loopback sampling')
                    self.wait(settle)
                    self.report['observed']['audio'] = self.capture_audio(expected)
                    self.report['verification_layers']['windows_loopback_audio'] = self.report['observed']['audio']['classification']
                    self.state('AUDIO_RECHECK', 90, 'Verify position, identity and selection after capture/matching')
                    identity = self.command('function csmusic_harness:identity', screenshot=False)
                    require('CSMUSIC_WORLD_' + self.receipt['token'] in identity, 'World changed during audio evidence collection')
                    position_after_audio = self.player_position()
                    require(all(abs(a-b) < .1 for a,b in zip(position_after_audio, final_xyz)), 'Player moved during audio evidence collection')
                    bounds_after_audio = self.command('cobblesafari csmusic structures', screenshot=False)
                    current_after_audio = self.command('cobblesafari csmusic current', screenshot=False)
                    audio_recheck = selection_diagnosis(case, bounds_after_audio, current_after_audio, all_cases)
                    self.report['observed']['audio_context_recheck'] = {
                        'player_xyz': position_after_audio, 'structures': bounds_after_audio,
                        'current': current_after_audio, 'selection_diagnosis': audio_recheck}
                    require(audio_recheck['category'] == 'PASS_SELECTION', 'Selection changed during audio evidence collection')
                    if self.config.get('audio', {}).get('required_for_selection_pass', False) and \
                            self.report['observed']['audio']['classification'] != 'PASS_AUDIO':
                        self.report['failure_category'] = 'INCONCLUSIVE_AUDIO'
                        self.report['status'] = 'blocked'
                        raise Blocked('Audio is required by configuration, but no calibrated PASS_AUDIO evidence is available')
                else:
                    self.report['observed']['audio'] = {'status': 'NOT_TESTED', 'classification': 'NOT_TESTED'}
                return
            if diagnosis['category'] == 'OVERLAPPING_STRUCTURES_EXPECTED_ARBITRATION':
                self.report['status'] = 'blocked'
                self.report['failure_category'] = diagnosis['category']
                raise Blocked('Expected source is eligible, but overlapping structures select another equal-priority rule')
            if diagnosis['category'] == 'EXPECTED_PRIORITY_ARBITRATION':
                self.report['status'] = 'blocked'
                self.report['failure_category'] = diagnosis['category']
                raise Blocked('A higher-priority matching source currently supersedes the requested structure rule')
            if diagnosis['category'] == 'INVALID_OR_AMBIGUOUS_FIXTURE':
                self.report['status'] = 'blocked'
                self.report['failure_category'] = diagnosis['category']
                raise Blocked('Located point is outside the requested structure or required piece')
            if diagnosis['category'] == 'INCOMPLETE_DIAGNOSTIC_EVIDENCE':
                self.report['status'] = 'blocked'
                self.report['failure_category'] = diagnosis['category']
                raise Blocked('Current output did not expose enough source evidence to diagnose the mismatch')
            self.report['status'] = 'fail'
            self.report['failure_category'] = 'FAIL_SELECTION'
            raise AssertionError(f'Verified fixture selects an incorrect rule: expected {diagnosis["expected_source"]} -> {expected} at priority {case["priority"]}; observed {diagnosis["sources"]}')
        finally:
            if owned:
                # Guard first: never resume input or steal focus during recovery.
                self.desktop.guard()
                self.state('CLEANUP', 45, 'Remove destination force-load ticket owned by this run')
                removed = self.command(f'forceload remove {x} {z}')
                require('Unmarked chunk' in removed or 'Unmarked chunks' in removed, 'Temporary force-load cleanup not confirmed')
                self.report['observed']['temporary_forceload'] = None

    def regression(self, case):
        require(case.get('steps') and case.get('setup_id'), case.get('requires', 'Regression fixture is not configured'))
        cases = json.loads((HERE / self.config.get('suite', 'suite.json')).read_bytes())['structures']
        setup = next(c for c in cases if c['id'] == case['setup_id'])
        self.structure(setup)
        self.state('QUERY', 60, 'Read and freeze daylight cycle for exact tick-boundary testing')
        before = self.command('gamerule doDaylightCycle')
        original = gamerule_value(before)
        checkpoint = self.out / 'recovery.json'
        recovery = self.set_daylight_with_checkpoint(original, checkpoint)
        steps = self.report['observed']['regression_steps'] = []
        try:
            for step in case['steps']:
                self.state('QUERY', 90, 'Apply regression time/weather and capture confirmation')
                if 'time' in step:
                    require(isinstance(step['time'], int) and 0 <= step['time'] < 24000, 'Invalid time fixture')
                    require('Set the time' in self.command('time set ' + str(step['time'])), 'Time command not confirmed')
                if 'weather' in step:
                    require(step['weather'] in ('clear', 'rain', 'thunder'), 'Invalid weather fixture')
                    require('Set the weather' in self.command('weather ' + step['weather']), 'Weather command not confirmed')
                current = self.await_music_stability(step['id'])
                observation = {'expected': step, 'current': current, 'status': 'fail'}
                steps.append(observation)
                expected = step.get('music') or '#' + step['pool']
                context = re.search(r'time: (\d+) \| weather: (\w+)', current)
                require(context, 'Context unavailable')
                if 'context_weather' in step:
                    require(context[2] == step['context_weather'], 'Biome/weather fixture mismatch')
                if 'time' in step:
                    require(int(context[1]) == step['time'], 'Clock not frozen at requested boundary')
                winning = playing(current)
                possible_sources = ([runtime_source(step['source'])] if step.get('source')
                                    else expected_rule_sources(expected, step['priority']))
                observation['expected_sources'] = possible_sources
                observation['winning_sources'] = winning
                if not possible_sources:
                    observation['status'] = 'blocked'
                    observation['category'] = 'INCOMPLETE_DIAGNOSTIC_EVIDENCE'
                    raise Blocked('No statically declared trigger rule matches the regression expectation')
                all_rows = music_sources(current)
                if 'csmusic sources for ' not in current or not all_rows:
                    observation['status'] = 'blocked'
                    observation['category'] = 'INCOMPLETE_DIAGNOSTIC_EVIDENCE'
                    raise Blocked('Fresh CSMusic response did not contain parseable source rows')
                actual = [item for item in winning if item['selection'] == expected
                          and item['priority'] == int(step['priority'])
                          and item['source_key'] in possible_sources]
                observation['actual_expected_rule'] = actual
                if not actual:
                    eligible = [item for item in all_rows if item['source_key'] in possible_sources
                                and item['selection'] == expected and item['priority'] == int(step['priority'])]
                    if not eligible:
                        observation['status'] = 'blocked'
                        observation['category'] = 'INCOMPLETE_DIAGNOSTIC_EVIDENCE'
                        raise Blocked('Expected regression source was not exposed among matching rules')
                    observation['category'] = 'FAIL_SELECTION'
                    self.report['failure_category'] = 'FAIL_SELECTION'
                    raise AssertionError('Regression selection mismatch: ' + step['id'])
                observation['status'] = 'pass'
                if step.get('record_audio'):
                    observation['audio'] = self.capture_audio(expected, step.get('negative_selection'))
                    self.report['verification_layers']['windows_loopback_audio'] = observation['audio']['classification']
                    self.state('AUDIO_RECHECK', 90, 'Verify regression clock, position and exact source after capture')
                    after = self.command('cobblesafari csmusic current', screenshot=False)
                    position = self.player_position()
                    observation['audio_context_recheck'] = {'current': after, 'player_xyz': position}
                    require(all(abs(a-b) < .1 for a,b in zip(position, self.report['observed']['player_xyz'])), 'Player moved during regression audio capture')
                    require(any(e['source_key'] in possible_sources and e['selection'] == expected and e['priority'] == int(step['priority'])
                                for e in playing(after)), 'Regression source changed during audio capture')
                    after_context = re.search(r'time: (\d+) \| weather: (\w+)', after)
                    require(after_context and (not 'time' in step or int(after_context[1]) == step['time'])
                            and (not 'context_weather' in step or after_context[2] == step['context_weather']), 'Regression context changed during audio capture')
        finally:
            self.desktop.guard()
            self.state('CLEANUP', 45, 'Restore copied-world daylight-cycle setting')
            self.restore_daylight(checkpoint, recovery)
            self.report['observed']['daylight_cycle_restore_pending'] = None

    def set_daylight_with_checkpoint(self, original, checkpoint):
        world = Path(self.report['environment']['test_world']).resolve()
        recovery = {'world': str(world), 'world_receipt_sha256': digest(world / 'csmusic-harness-copy.json'),
                    'original': original, 'desired': 'false', 'phase': 'intent_persisted', 'updated': stamp()}
        # Persist the original value and intended mutation before sending any mutating command.
        write_json(checkpoint, recovery)
        self.report['observed']['daylight_cycle_restore_pending'] = original
        self.report['observed']['recovery_checkpoint'] = str(checkpoint)
        changed = self.command('gamerule doDaylightCycle false')
        require('doDaylightCycle' in changed and 'false' in changed, 'Daylight freeze not confirmed')
        recovery.update({'phase': 'change_confirmed', 'updated': stamp()})
        write_json(checkpoint, recovery)
        return recovery

    def restore_daylight(self, checkpoint, recovery):
        world = Path(self.report['environment']['test_world']).resolve()
        require(recovery.get('world') == str(world), 'Daylight checkpoint belongs to another copied world')
        require(recovery.get('world_receipt_sha256') == digest(world / 'csmusic-harness-copy.json'),
                'Copied-world identity receipt changed since checkpoint')
        observed = gamerule_value(self.command('gamerule doDaylightCycle'))
        if observed != recovery['original']:
            response = self.command('gamerule doDaylightCycle ' + recovery['original'])
            require('doDaylightCycle' in response and recovery['original'] in response,
                    'Daylight-cycle restoration not confirmed')
            observed = gamerule_value(self.command('gamerule doDaylightCycle'))
            require(observed == recovery['original'], 'Daylight-cycle value did not persist after restoration')
        recovery.update({'phase': 'restored', 'updated': stamp()})
        write_json(checkpoint, recovery)
        return observed

    def recover(self):
        old = json.loads(self.recover_report.read_bytes())
        require(old['environment']['test_world'] == self.report['environment']['test_world'], 'Recovery belongs to another world')
        self.state('CLEANUP', 60, 'Recover only the interrupted run\'s recorded temporary ticket')
        ticket = old['observed'].get('temporary_forceload')
        if ticket:
            require(len(ticket) == 2 and all(type(n) is int and abs(n) < 29999984 for n in ticket), 'Invalid recovery coordinates')
            x, z = ticket
            require(any(c['command'] == f'/forceload add {x} {z}' and 'Marked chunk' in c.get('response', '') for c in old['commands']), 'No evidence this run owned the ticket')
            result = self.command(f'forceload remove {x} {z}')
            require('Unmarked chunk' in result or 'No chunks were removed' in result, 'Recovery cleanup not confirmed')
        recovery_path = Path(old['observed'].get('recovery_checkpoint', ''))
        if recovery_path.is_file():
            pending = json.loads(recovery_path.read_bytes())
            self.restore_daylight(recovery_path, pending)
            pending['recovered_by'] = str(self.out)
            write_json(recovery_path, pending)
            self.report['observed']['daylight_cycle_recovered'] = pending['original']
        elif old['observed'].get('daylight_cycle_restore_pending') in ('true', 'false'):
            # Older interrupted reports recorded the original value but had no durable checkpoint.
            world = Path(self.report['environment']['test_world']).resolve()
            recovery_path = Path(old.get('report_directory', self.recover_report.parent)) / 'recovery.json'
            pending = {'world': str(world),
                       'world_receipt_sha256': digest(world / 'csmusic-harness-copy.json'),
                       'original': old['observed']['daylight_cycle_restore_pending'],
                       'desired': 'false', 'phase': 'legacy_report_recovery', 'updated': stamp()}
            self.restore_daylight(recovery_path, pending)
            self.report['observed']['daylight_cycle_recovered'] = pending['original']
        self.report['observed']['recovered_report'] = str(self.recover_report)

    def scheduled_suite(self, plan):
        self.runtime_ready()
        self.smoke()
        results = []
        root_observed = self.report['observed']
        for case in plan.get('structures', []):
            scenario = {'id': case['id'], 'expected': case, 'status': 'BLOCKED',
                        'category': None, 'observed': {}}
            self.report['observed'] = scenario['observed']
            self.report.pop('failure_category', None)
            try:
                self.structure(case)
                scenario['status'] = 'PASS'
                scenario['category'] = 'PASS_SELECTION'
            except Exception as exc:
                category = self.report.get('failure_category')
                if not category:
                    message = str(exc).lower()
                    if 'chat' in message or 'clipboard' in message:
                        category = 'BLOCKED_CHAT_STATE'
                    elif 'focus' in message or 'input aborted' in message:
                        category = 'BLOCKED_FOCUS'
                    elif 'loaded' in message or 'chunk' in message or 'readiness' in message:
                        category = 'BLOCKED_LOADING'
                    else:
                        category = 'BLOCKED_CONTROLLER_OR_FIXTURE'
                scenario.update({'status': 'FAIL' if category == 'FAIL_SELECTION' else 'BLOCKED',
                                 'category': category,
                                 'exception': {'type': type(exc).__name__, 'message': str(exc)}})
                if category == 'FAIL_SELECTION':
                    scenario['status'] = 'FAIL'
                if scenario['status'] == 'BLOCKED':
                    results.append(scenario)
                    break
            results.append(scenario)
        if not any(item['status'] == 'BLOCKED' for item in results):
            regression_cases = json.loads((HERE / self.config.get('suite', 'suite.json')).read_bytes())['regressions']
            for regression_id in plan.get('regressions', []):
                case = next(c for c in regression_cases if c['id'] == regression_id)
                scenario = {'id': case['id'], 'expected': case, 'status': 'BLOCKED',
                            'category': None, 'observed': {}}
                self.report['observed'] = scenario['observed']
                self.report.pop('failure_category', None)
                try:
                    self.regression(case)
                    scenario['status'] = 'PASS'
                    scenario['category'] = 'PASS_SELECTION'
                except Exception as exc:
                    category = self.report.get('failure_category', 'BLOCKED_CONTROLLER_OR_FIXTURE')
                    scenario.update({'status': 'FAIL' if category == 'FAIL_SELECTION' else 'BLOCKED',
                                     'category': category,
                                     'exception': {'type': type(exc).__name__, 'message': str(exc)}})
                    if scenario['status'] == 'BLOCKED':
                        results.append(scenario)
                        break
                results.append(scenario)
        self.report['observed'] = root_observed
        executed = {item['id'] for item in results}
        for planned in plan.get('structures', []):
            if planned['id'] not in executed:
                results.append({'id': planned['id'], 'expected': planned, 'status': 'NOT_RUN',
                                'category': 'NOT_EXECUTED_AFTER_SUITE_STOP', 'observed': {}})
        for planned_id in plan.get('regressions', []):
            if planned_id not in executed:
                results.append({'id': planned_id, 'status': 'NOT_RUN',
                                'category': 'NOT_EXECUTED_AFTER_SUITE_STOP', 'observed': {}})
        self.report['scenarios'] = results
        if any(item['status'] == 'FAIL' for item in results):
            self.report['status'] = 'fail'
            self.report['failure_category'] = 'FAIL_SELECTION'
            self.report['possible_cause'] = 'One or more verified fixture scenarios produced a genuine selection mismatch; blocked scenarios remain listed separately.'
        elif any(item['status'] == 'BLOCKED' for item in results):
            self.report['status'] = 'blocked'
            self.report['failure_category'] = 'BLOCKED_SCENARIOS'
            self.report['verification_layers']['music_selection'] = 'PARTIAL_OR_BLOCKED'
            details = ', '.join(item['id'] + ' (' + str(item['category']) + ')' for item in results if item['status'] == 'BLOCKED')
            self.report['possible_cause'] = 'Scenarios blocked before a complete selection-level conclusion: ' + details
        else:
            self.report['status'] = 'pass'
            self.report['failure_category'] = 'PASS_SELECTION'
            self.report['possible_cause'] = 'All configured selection-level scenarios passed; see verification_layers for audio and client sound-event status.'

    def run(self):
        try:
            self.state('PREFLIGHT', 60, 'Paths, installed versions, counts, and controls checked')
            env = audit(self.config, recovery_only=bool(self.recover_report))
            require(time.monotonic() <= self.deadline, 'Preflight exceeded 60 seconds')
            self.report['environment'] = env
            if not self.recover_report:
                require(env['computed_total'] == self.config['expected_counts'], 'Installed built-ins/source counts differ from expected release')
            require(env['mods']['cobblesafari']['version'] == '0.3.4', 'Unsupported CobbleSafari version')
            require(env['mods']['cobblemon']['version'].startswith('1.7.3'), 'Unsupported Cobblemon version')
            require(env['settings']['enabled'], 'CSMusic disabled in installed settings')
            require(env['settings']['structureCacheTtlTicks'] <= self.config['settle_seconds'] * 20, 'Settling allowance shorter than configured structure cache')
            if self.mode == 'audit':
                self.report['status'] = 'pass'
            elif self.mode == 'dry-run':
                import pyautogui
                # No input, focus changes, or screenshots of unrelated applications.
                self.report['observed']['controls'] = {'screen': list(pyautogui.size()), 'failsafe': pyautogui.FAILSAFE, 'input_sent': False}
                self.report['status'] = 'pass'
            else:
                if self.mode in ('quick', 'representative', 'diagnostic', 'exhaustive'):
                    self.scheduled_suite(self.case)
                else:
                    self.runtime_ready()
                if self.recover_report:
                    self.recover()
                if self.mode == 'capture' and (not self.recover_report or self.config.get('capture_fixture')):
                    if self.config.get('capture_waypoint'):
                        point = self.config['capture_waypoint']
                        require(self.config.get('test_gamemode') == 'spectator', 'Captured waypoint requires authorized spectator mode')
                        require(len(point) == 3 and all(type(n) is int for n in point), 'Invalid captured waypoint')
                        x, y, z = point
                        require(-63 <= y <= 318 and abs(x) < 29999984 and abs(z) < 29999984, 'Captured waypoint outside world bounds')
                        self.state('TRAVEL', 180, 'Saved native-bounds candidate in already-loaded terrain; no force-load or generation')
                        mode = self.command('execute if entity @s[gamemode=spectator] run tellraw @s "CSMUSIC_SPECTATOR"', screenshot=False)
                        require('CSMUSIC_SPECTATOR' in mode.splitlines(), 'Spectator mode changed; waypoint travel disabled')
                        loaded = self.command(f'execute if loaded {x} {y} {z} run tellraw @s "CSMUSIC_LOADED"', screenshot=False)
                        require('CSMUSIC_LOADED' in loaded, 'Captured waypoint chunk is not loaded; no teleport sent')
                        response = self.command(f'tp @s {x + .5} {y} {z + .5}')
                        require('Teleported ' in response, 'Captured waypoint teleport unconfirmed')
                        actual = self.player_position()
                        require(all(abs(a-b) < .1 for a,b in zip(actual, [x+.5, y, z+.5])), 'Captured waypoint XYZ not verified')
                        self.report['observed']['candidate_waypoint'] = point
                        settle = int(self.config['settle_seconds'])
                        self.state('WAIT_LOAD', settle + 10, 'Settle structure cache after verified waypoint travel')
                        self.wait(settle)
                    self.state('QUERY', 90, 'Native framebuffer evidence and fresh selection response')
                    self.capture('native-evidence')
                    current = self.command('cobblesafari csmusic current')
                    require('csmusic sources for ' in current and playing(current), 'No current selection captured')
                    self.report['observed']['current'] = current
                    if self.config.get('capture_fixture'):
                        fixture = self.config['capture_fixture']
                        position = self.player_position()
                        bounds = self.command('cobblesafari csmusic structures')
                        diagnosis = selection_diagnosis(fixture, bounds, current, [fixture])
                        self.report['observed'].update({'fixture': fixture, 'player_xyz': position,
                                                       'structures': bounds, 'selection_diagnosis': diagnosis})
                        require(diagnosis['category'] == 'PASS_SELECTION', 'Current fixture selection/containment not verified: ' + diagnosis['category'])
                        self.report['verification_layers']['music_selection'] = ('PASS_SAVED_BOUNDS_FIXTURE'
                            if self.config.get('capture_waypoint') else 'PASS_USER_ASSISTED_FIXTURE')
                elif not self.recover_report and self.mode not in ('quick', 'representative', 'diagnostic', 'exhaustive'):
                    self.smoke()
                if self.mode == 'regression':
                    self.regression(self.case)
                elif self.case and self.mode not in ('quick', 'representative', 'diagnostic', 'exhaustive'):
                    self.structure(self.case)
                if self.mode not in ('quick', 'representative', 'diagnostic', 'exhaustive'):
                    self.report['status'] = 'pass'
        except (Exception, KeyboardInterrupt) as exc:
            if self.report.get('failure_category') == 'FAIL_SELECTION':
                self.report['status'] = 'fail'
            else:
                self.report['status'] = 'blocked'
                if not self.report.get('failure_category'):
                    message = str(exc).lower()
                    if 'chat' in message or 'clipboard' in message:
                        category = 'BLOCKED_CHAT_STATE'
                    elif 'focus' in message or 'input aborted' in message:
                        category = 'BLOCKED_FOCUS'
                    elif isinstance(exc, (FileNotFoundError, ImportError, ModuleNotFoundError)):
                        category = 'BLOCKED_DEPENDENCY'
                    elif isinstance(exc, AssertionError):
                        category = 'BLOCKED_EVIDENCE_OR_FIXTURE'
                    else:
                        category = 'CONTROLLER_OR_EVIDENCE_ERROR'
                    self.report['failure_category'] = category
            self.report['exception'] = {'type': type(exc).__name__, 'message': str(exc)}
            self.report['possible_cause'] = f'{type(exc).__name__}: {exc}'
        finally:
            help_text = assistance_message(self.report)
            if help_text:
                self.request_assistance(help_text)
            self.state('RECORD', 5, 'JSON, Markdown, log excerpt persisted')
            # Do not send cleanup input after any abort/focus loss.
            self.state('CLEANUP', 1, 'Close log handle; leave copy and evidence intact; no GUI recovery input')
            if self.tail:
                self.tail.close()
            self.report['duration_seconds'] = round(time.monotonic() - self.start, 3)
            self.report['finished'] = stamp()
            if 'outcome' not in self.report:
                if self.report.get('failure_category'):
                    self.report['outcome'] = self.report.get('failure_category')
                elif self.report['status'] == 'pass':
                    self.report['outcome'] = {'audit': 'PASS_STATIC', 'dry-run': 'PASS_DRY_RUN'}.get(self.mode, 'PASS_SELECTION')
                else:
                    self.report['outcome'] = 'BLOCKED_CONTROLLER_OR_EVIDENCE'
            self.report['evidence'] = sorted(p.name for pattern in ('*.png', '*.wav') for p in self.out.glob(pattern)) + ['commands.log']
            if (self.out / 'recovery.json').is_file():
                self.report['evidence'].append('recovery.json')
            if help_text:
                write_json(self.out / 'assistance.json', self.report['assistance'])
            (self.out / 'commands.log').write_text(self.raw, encoding='utf-8')
            write_json(self.out / 'report.json', self.report)
            lines = [f"# {self.report['id']}: {self.report['status']}", '',
                     f"Outcome: {self.report['outcome']}. Validation: {self.report['validation']}. Audible playback: not physically verified.", '',
                     self.report.get('possible_cause', 'All assertions for this mode passed.'), '', f"Duration: {self.report['duration_seconds']} seconds.", '',
                     'Expected: `' + json.dumps(self.report['expected']) + '`', '', 'See [complete structured evidence](report.json) and [fresh log excerpt](commands.log).', '']
            if self.report.get('scenarios'):
                lines.extend(['## Scenario outcomes', ''])
                for scenario in self.report['scenarios']:
                    lines.append(f"- `{scenario['id']}`: **{scenario['status']}** — {scenario.get('category', 'unknown')}.")
                lines.append('')
            for c in self.report['commands']:
                lines.extend(['## `' + c['command'] + '`', '', c['status'], '', '```text', c.get('response', ''), '```', ''])
            lines.extend(f'![{p.name}]({p.name})' for p in self.out.glob('*.png'))
            (self.out / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
            if help_text:
                notify_assistance(self.config, help_text)
            print(str(self.out / 'report.md'), flush=True)
        return 0 if self.report['status'] == 'pass' else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['audit', 'prepare', 'install-probe', 'dry-run', 'smoke', 'structure', 'regression', 'capture',
                                        'quick', 'representative', 'diagnostic', 'exhaustive', 'audio-devices',
                                        'audio-capture', 'audio-identify', 'audio-benchmark'])
    parser.add_argument('--config', type=Path, default=HERE / 'config.json')
    parser.add_argument('--case', default='pallet_town')
    parser.add_argument('--recover-report', type=Path)
    parser.add_argument('--recording', type=Path)
    parser.add_argument('--selection', default='dysfam_music:villages_lgpe_pallet_town')
    parser.add_argument('--negative-selection', default='dysfam_music:villages_lgpe_lavender_town')
    parser.add_argument('--audio', action='store_true', help='Capture loopback audio during supported gameplay modes')
    parser.add_argument('--at-current-position', action='store_true', help='Reprobe the user-confirmed current fixture rather than locate landing')
    parser.add_argument('--initial-chat-open', action='store_true', help='Close the initial empty chat only after explicit operator confirmation')
    parser.add_argument('--duration', type=int)
    parser.add_argument('--device-index', type=int)
    args = parser.parse_args()
    config = json.loads(args.config.read_bytes())
    if args.initial_chat_open:
        config['initial_chat_open'] = True
    if args.audio:
        config.setdefault('audio', {})['enabled'] = True
    if args.mode.startswith('audio-'):
        from audio import AudioUnavailable, capture_loopback, identify, list_devices, synthetic_benchmark
        audio_config = config.get('audio', {})
        try:
            if args.mode == 'audio-devices':
                result = list_devices()
            elif args.mode == 'audio-capture':
                duration = args.duration or int(audio_config.get('capture_seconds', 30))
                require(duration <= int(audio_config.get('maximum_seconds', 90)), 'Duration exceeds configured maximum')
                output = HERE / 'results' / ('audio-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
                output.mkdir(parents=True, exist_ok=True)
                evidence = capture_loopback(output / 'loopback.wav', duration,
                                           args.device_index if args.device_index is not None else audio_config.get('device_index'))
                if evidence['rms_int16'] < float(audio_config.get('minimum_capture_rms_int16', 100)):
                    evidence['classification'] = 'BLOCKED_AUDIO_DEVICE'
                    evidence['signal_warning'] = 'Loopback recording was near silent; no audio identity conclusion.'
                else:
                    evidence['classification'] = 'INCONCLUSIVE_AUDIO'
                if evidence['clipped_fraction'] > float(audio_config.get('clipping_fraction_limit', 0.01)):
                    evidence['clipping_warning'] = 'Recorded waveform contains substantial clipped samples.'
                evidence['calibrated'] = False
                result = evidence
                write_json(output / 'report.json', result)
                (output / 'report.md').write_text(
                    '# Audio loopback capture\n\nClassification: `INCONCLUSIVE_AUDIO` (recording only; no calibrated track assertion).\n\n'
                    + '```json\n' + json.dumps(result, indent=2, ensure_ascii=False) + '\n```\n', encoding='utf-8')
            elif args.mode == 'audio-identify':
                require(args.recording is not None and args.recording.is_file(), '--recording must name a local WAV recording')
                result = identify(args.recording, args.selection, Path(audio_config['reference_resource_pack']),
                                  audio_config.get('ffmpeg'), args.negative_selection)
            else:
                result = synthetic_benchmark(args.selection, args.negative_selection,
                                             Path(audio_config['reference_resource_pack']), audio_config.get('ffmpeg'))
            print(json.dumps(result, indent=2, ensure_ascii=False))
            if args.mode != 'audio-capture':
                output = HERE / 'results' / ('audio-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
                output.mkdir(parents=True, exist_ok=True)
                write_json(output / 'report.json', result)
                (output / 'report.md').write_text(
                    '# ' + args.mode + '\n\nClassification: `' + str(result.get('classification', result.get('calibration_status', 'device inventory'))) + '`\n\n'
                    + '```json\n' + json.dumps(result, indent=2, ensure_ascii=False) + '\n```\n', encoding='utf-8')
                print('Evidence report: ' + str(output / 'report.json'))
            return 0
        except AudioUnavailable as exc:
            print(json.dumps({'status': exc.category, 'classification': exc.category,
                              'exception': {'type': type(exc).__name__, 'message': str(exc)}}, indent=2))
            return 2
        except Exception as exc:
            print(json.dumps({'status': 'BLOCKED_AUDIO_TOOL', 'classification': 'BLOCKED_AUDIO_TOOL',
                              'exception': {'type': type(exc).__name__, 'message': str(exc)}}, indent=2))
            return 2
    if args.mode == 'prepare':
        print(json.dumps(prepare(config), indent=2))
        return 0
    if args.mode == 'install-probe':
        receipt = json.loads((HERE / config.get('receipt', 'prepared.json')).read_bytes())
        world = Path(receipt['world']).resolve()
        require(world.parent == (Path(config['profile']) / 'saves').resolve(), 'Wrong profile')
        require(json.loads((world / 'csmusic-harness-copy.json').read_bytes()) == receipt, 'Invalid copy receipt')
        install_probe(world)
        print('Installed terrain probe in copied world only; reload needed')
        return 0
    case = None
    suites = json.loads((HERE / config.get('suite', 'suite.json')).read_bytes())
    if args.mode in ('structure', 'regression'):
        cases = suites['structures' if args.mode == 'structure' else 'regressions']
        case = next(c for c in cases if c['id'] == args.case)
        if args.at_current_position:
            require(args.mode == 'structure', '--at-current-position requires structure mode')
            case = dict(case, at_current_position=True)
    elif args.mode in ('quick', 'representative', 'diagnostic', 'exhaustive'):
        ids = suites['modes'].get(args.mode, [])
        structures = suites['structures'] if args.mode == 'exhaustive' else [
            next(c for c in suites['structures'] if c['id'] == case_id) for case_id in ids]
        case = {'structures': structures, 'regressions': suites.get('mode_regressions', {}).get(args.mode, [])}
    return Controller(config, args.mode, case, args.recover_report).run()


if __name__ == '__main__':
    raise SystemExit(main())
