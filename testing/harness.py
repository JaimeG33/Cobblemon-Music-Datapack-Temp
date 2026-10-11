"""Windows CSMusic controller. No production pack writes; fresh feedback required."""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
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


def audit(config):
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
    installed = profile / 'saves' / config['source_world'] / 'datapacks' / config['expected_datapack'].removeprefix('file/')
    require(installed.is_file(), 'Expected RC4 datapack is not installed in source save')
    with zipfile.ZipFile(installed) as z:
        source_files = [REPO / 'pack.mcmeta'] + list((REPO / 'data').rglob('*'))
        compared = 0
        for source in source_files:
            if source.is_file():
                name = source.relative_to(REPO).as_posix()
                require(z.read(name) == source.read_bytes(), 'Installed datapack differs from repository: ' + name)
                compared += 1
    resource_options = [line for line in (profile / 'options.txt').read_text(encoding='utf-8').splitlines() if line.startswith('resourcePacks:')]
    return {'profile': str(profile), 'saves': [p.name for p in (profile / 'saves').iterdir() if p.is_dir()],
            'mods': mods, 'metadata_warnings': metadata_warnings, 'source_counts': source_counts, 'builtin_counts': defaults,
            'computed_total': [a+b for a,b in zip(source_counts, defaults)],
            'installed_datapack': {'file': str(installed), 'sha256': digest(installed), 'source_files_matched': compared},
            'resource_pack_options_disk_snapshot': resource_options,
            'windows': windows(), 'java_running': java_running(),
            'previous_log_evidence_only': [line for line in old.splitlines() if '[CSMusic] Loaded' in line or 'Loading Minecraft ' in line],
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
    target = saves / ('CSMusic Automation ' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    require(not target.exists(), 'Copy destination already exists')
    original_hash = digest(source / 'level.dat')
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('session.lock'))
    level = nbtlib.load(target / 'level.dat')
    data = level['Data']
    require(str(data['Version']['Name']) == '1.21.1', 'Save is not Minecraft 1.21.1')
    data['LevelName'] = nbtlib.String(target.name)
    data['GameType'] = nbtlib.Int(1)
    data['allowCommands'] = nbtlib.Byte(1)
    if 'Player' in data:
        data['Player']['playerGameType'] = nbtlib.Int(1)
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
    write_json(HERE / 'prepared.json', receipt)
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
    return re.findall(r'^- \[[^\n]+\] ([#\w:./-]+)(?: \([^\n]*?\))? \(priority (-?\d+)\) <= playing$', text, re.M)


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
    exact = {'datapack list enabled', 'function dysfam_music:check', 'function csmusic_harness:identity',
             'reload', 'cobblesafari csmusic current', 'cobblesafari csmusic structures', 'data get entity @s Pos',
             'gamerule doDaylightCycle', 'gamerule doDaylightCycle true', 'gamerule doDaylightCycle false',
             'execute if entity @s[gamemode=creative] run tellraw @s "CSMUSIC_CREATIVE"'}
    patterns = [r'tellraw @s "CSMUSIC_[a-f0-9]+_(?:BEGIN|END)"',
                r'locate structure [a-z0-9_.-]+:[a-z0-9_/.-]+',
                r'forceload (?:query|add|remove) -?\d+ -?\d+',
                r'function csmusic_harness:probe \{x:-?\d+,z:-?\d+\}',
                r'tp @s -?\d+\.5 -?\d+ -?\d+\.5', r'weather (?:clear|rain|thunder)', r'time set \d+']
    return command in exact or any(re.fullmatch(p, command) for p in patterns)


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
        require(not self.stop_file.exists(), 'Emergency STOP file present')
        require(not self.user.GetAsyncKeyState(0x77) & 0x8000, 'Emergency F8 stop')
        self.gui.failSafeCheck()
        require(self.user.IsWindow(self.hwnd), 'Minecraft window closed')
        require(not self.user.IsHungAppWindow(self.hwnd), 'Minecraft window unresponsive')
        require(self.user.GetForegroundWindow() == self.hwnd, 'Minecraft lost focus; no further input permitted')

    def send(self, command):
        require('\n' not in command and '\r' not in command and command.isascii() and len(command) <= 255, 'Unsafe chat command')
        require(allowed_command(command), 'Command outside harness allowlist')
        self.guard()
        self.gui.press('/')
        time.sleep(.2)
        # Replace any unfinished chat input left by an interrupted run.
        self.guard()
        self.gui.hotkey('ctrl', 'a')
        for char in '/' + command:
            self.guard()
            self.gui.write(char)
        self.guard()
        self.gui.press('enter')

    def screenshot(self, path):
        self.guard()
        rect = wintypes.RECT()
        self.user.GetWindowRect(self.hwnd, ctypes.byref(rect))
        screen = self.gui.screenshot(region=(rect.left, rect.top, rect.right-rect.left, rect.bottom-rect.top))
        if screen.convert('RGB').getbbox() is not None:
            screen.save(path)
            return
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
                    return
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
        self.report = {'id': mode if not case else case['id'], 'description': 'CSMusic ' + mode,
                       'started': stamp(), 'status': 'blocked', 'validation': 'static' if mode in ('audit', 'dry-run') else 'runtime selection',
                       'audible_playback': 'not tested', 'commands': [], 'states': [],
                       'controller_sha256': digest(Path(__file__)),
                       'expected': case or {'counts': config['expected_counts'], 'release': 'RC4'}, 'observed': {}}
        if mode == 'capture':
            self.report['expected'] = {'evidence': 'nonblack screenshot and fresh playing-source response; this mode does not rerun RC4 smoke'}
        self.desktop = self.tail = None
        self.raw = ''

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
            self.desktop.screenshot(self.out / (name + '.png'))

    def command(self, command, timeout=None):
        timeout = timeout or self.config['command_timeout']
        nonce = 'CSMUSIC_' + uuid.uuid4().hex
        item = {'command': '/' + command, 'started': stamp(), 'status': 'input pending', 'timeout': timeout}
        self.report['commands'].append(item)
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
                self.capture('command-' + str(len(self.report['commands'])))
                return result
            time.sleep(.05)
        item['status'] = 'timeout'
        raise Blocked('No complete fresh command response within timeout: ' + command)

    def runtime_ready(self):
        receipt = json.loads((HERE / 'prepared.json').read_bytes())
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
        self.desktop.focus()
        self.tail = LogTail(Path(self.config['profile']) / 'logs/latest.log')
        self.state('READY', 90, 'Fresh copy-specific identity response and creative mode')
        identity = self.command('function csmusic_harness:identity')
        require('CSMUSIC_WORLD_' + receipt['token'] in identity, 'Wrong world, title/menu screen, or copy identity pack not active')
        creative = self.command('execute if entity @s[gamemode=creative] run tellraw @s "CSMUSIC_CREATIVE"')
        require('CSMUSIC_CREATIVE' in creative.splitlines(), 'Copied world must be creative')
        self.report['environment']['test_world'] = str(world)

    def smoke(self):
        self.state('QUERY', 300, 'Enabled RC4 pack, status function, current selection, and fresh loader totals')
        packs = self.command('datapack list enabled')
        require(self.config['expected_datapack'] in packs, 'RC4 datapack not confirmed enabled')
        check = self.command('function dysfam_music:check')
        require('Release: RC4' in check, 'Status function is not RC4')
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
        self.report['observed'].update({'runtime_counts': counts, 'current': current, 'pack_check': check, 'enabled_packs': packs})
        self.state('VERIFY', 1, 'All fresh smoke assertions passed')

    def structure(self, case):
        sid = case['structure']
        require(re.fullmatch(r'[a-z0-9_.-]+:[a-z0-9_/.-]+', sid), 'Invalid structure ID')
        self.state('LOCATE', self.config['locate_timeout'] + 30, 'Fresh exact-ID locate response')
        result = self.command('locate structure ' + sid, self.config['locate_timeout'])
        self.state('PARSE', 1, 'Complete numeric XYZ; never invent missing Y')
        x, y, z = locate_coordinates(result, sid)
        self.report['observed']['locate'] = [x, y, z]
        self.state('TRAVEL', 180, 'Verified destination air/headroom, solid floor, and exact numeric teleport')
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
            probe = self.command(f'function csmusic_harness:probe {{x:{x},z:{z}}}')
            candidates = re.findall(r'^CSMUSIC_GROUND (-?\d+) (-?\d+) (-?\d+)$', probe, re.M)
            valid = [(int(a), int(b), int(c)) for a,b,c in candidates if int(a) == x and int(c) == z and -63 <= int(b) <= 318]
            require(valid, 'Terrain probe found no loaded safe surface; no teleport sent')
            destination = max(valid, key=lambda p: p[1])
            y = destination[1]
            self.report['observed']['verified_ground'] = destination
            travel = self.command(f'tp @s {x + 0.5} {y} {z + 0.5}')
            require('Teleported ' in travel, 'Teleport response unavailable')
            pos = self.command('data get entity @s Pos')
            numbers = re.search(r'\[(-?[\d.]+)d, (-?[\d.]+)d, (-?[\d.]+)d\]', pos)
            require(numbers and all(abs(float(a)-b) < .1 for a,b in zip(numbers.groups(), (x+.5, y, z+.5))), 'Player did not reach verified XYZ')
            weather = case.get('weather', 'clear')
            ticks = case.get('time', 1000)
            require(weather in ('clear', 'rain', 'thunder') and isinstance(ticks, int) and 0 <= ticks < 24000, 'Invalid scenario time/weather')
            require('Set the weather' in self.command('weather ' + weather), 'Weather change not confirmed')
            require('Set the time' in self.command('time set ' + str(ticks)), 'Time change not confirmed')
            self.state('SETTLE', self.config['settle_seconds'] + 1, 'Allow configured structure cache to refresh while focus remains held')
            self.wait(self.config['settle_seconds'])
            self.state('QUERY', 90, 'Structure containment and current playing source captured')
            bounds = self.command('cobblesafari csmusic structures')
            current = self.command('cobblesafari csmusic current')
            self.report['observed'].update({'structures': bounds, 'structure_current': current})
            self.state('VERIFY', 1, 'Exact structure bounds, expected selection and priority')
            require(contains_structure(bounds, sid), 'Located ground is not within structure bounds; needs another tested landing point')
            if case.get('piece'):
                require(contains_structure(bounds, sid, case['piece']), 'Landing point is not inside the exact required piece; calibrated piece waypoint needed')
            expected = case.get('music') or '#' + case['pool']
            selected = playing(current)
            if (expected, str(case['priority'])) not in selected:
                self.report['status'] = 'fail'
                raise AssertionError(f'Expected {expected} at priority {case["priority"]}; observed {selected}. Inspect structures/current for overlapping bounds and equal-priority sources before treating this as a datapack defect.')
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
        cases = json.loads((HERE / 'suite.json').read_bytes())['structures']
        setup = next(c for c in cases if c['id'] == case['setup_id'])
        self.structure(setup)
        self.state('QUERY', 60, 'Read and freeze daylight cycle for exact tick-boundary testing')
        before = self.command('gamerule doDaylightCycle')
        match = re.search(r'doDaylightCycle is currently set to: (true|false)', before)
        require(match, 'Cannot read daylight-cycle rule; no boundary test')
        original = match.group(1)
        self.command('gamerule doDaylightCycle false')
        self.report['observed']['daylight_cycle_restore_pending'] = original
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
                self.state('SETTLE', self.config['settle_seconds'] + 1, 'Wait for changed context arbitration')
                self.wait(self.config['settle_seconds'])
                self.state('QUERY', 45, 'Fresh regression selection and context')
                current = self.command('cobblesafari csmusic current')
                observation = {'expected': step, 'current': current, 'status': 'fail'}
                steps.append(observation)
                expected = step.get('music') or '#' + step['pool']
                context = re.search(r'time: (\d+) \| weather: (\w+)', current)
                require(context, 'Context unavailable')
                if 'context_weather' in step:
                    require(context[2] == step['context_weather'], 'Biome/weather fixture mismatch')
                if 'time' in step:
                    require(int(context[1]) == step['time'], 'Clock not frozen at requested boundary')
                if (expected, str(step['priority'])) not in playing(current):
                    raise AssertionError('Regression selection mismatch: ' + step['id'])
                observation['status'] = 'pass'
        finally:
            self.desktop.guard()
            self.state('CLEANUP', 45, 'Restore copied-world daylight-cycle setting')
            response = self.command('gamerule doDaylightCycle ' + original)
            require('doDaylightCycle' in response and original in response, 'Daylight-cycle restoration not confirmed')
            self.report['observed']['daylight_cycle_restore_pending'] = None

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
        self.report['observed']['recovered_report'] = str(self.recover_report)

    def run(self):
        try:
            self.state('PREFLIGHT', 60, 'Paths, installed versions, counts, and controls checked')
            env = audit(self.config)
            require(time.monotonic() <= self.deadline, 'Preflight exceeded 60 seconds')
            self.report['environment'] = env
            require(env['computed_total'] == self.config['expected_counts'], 'Installed built-ins/source counts differ from expected RC4')
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
                self.runtime_ready()
                if self.recover_report:
                    self.recover()
                if self.mode == 'capture':
                    self.state('QUERY', 90, 'Native framebuffer evidence and fresh selection response')
                    self.capture('native-evidence')
                    current = self.command('cobblesafari csmusic current')
                    require('csmusic sources for ' in current and playing(current), 'No current selection captured')
                    self.report['observed']['current'] = current
                else:
                    self.smoke()
                if self.mode == 'regression':
                    self.regression(self.case)
                elif self.case:
                    self.structure(self.case)
                self.report['status'] = 'pass'
        except (Exception, KeyboardInterrupt) as exc:
            self.report['status'] = 'blocked' if isinstance(exc, (Blocked, KeyboardInterrupt, FileNotFoundError)) or type(exc).__name__ == 'FailSafeException' else 'fail'
            self.report['possible_cause'] = f'{type(exc).__name__}: {exc}'
        finally:
            self.state('RECORD', 5, 'JSON, Markdown, log excerpt persisted')
            # Do not send cleanup input after any abort/focus loss.
            self.state('CLEANUP', 1, 'Close log handle; leave copy and evidence intact; no GUI recovery input')
            if self.tail:
                self.tail.close()
            self.report['duration_seconds'] = round(time.monotonic() - self.start, 3)
            self.report['finished'] = stamp()
            self.report['evidence'] = sorted(p.name for p in self.out.glob('*.png')) + ['commands.log']
            (self.out / 'commands.log').write_text(self.raw, encoding='utf-8')
            write_json(self.out / 'report.json', self.report)
            lines = [f"# {self.report['id']}: {self.report['status']}", '', f"Validation: {self.report['validation']}. Audible playback: not tested.", '',
                     self.report.get('possible_cause', 'All assertions for this mode passed.'), '', f"Duration: {self.report['duration_seconds']} seconds.", '',
                     'Expected: `' + json.dumps(self.report['expected']) + '`', '', 'See [complete structured evidence](report.json) and [fresh log excerpt](commands.log).', '']
            for c in self.report['commands']:
                lines.extend(['## `' + c['command'] + '`', '', c['status'], '', '```text', c.get('response', ''), '```', ''])
            lines.extend(f'![{p.name}]({p.name})' for p in self.out.glob('*.png'))
            (self.out / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
            print(str(self.out / 'report.md'), flush=True)
        return 0 if self.report['status'] == 'pass' else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['audit', 'prepare', 'install-probe', 'dry-run', 'smoke', 'structure', 'regression', 'capture'])
    parser.add_argument('--config', type=Path, default=HERE / 'config.json')
    parser.add_argument('--case', default='pallet_town')
    parser.add_argument('--recover-report', type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_bytes())
    if args.mode == 'prepare':
        print(json.dumps(prepare(config), indent=2))
        return 0
    if args.mode == 'install-probe':
        receipt = json.loads((HERE / 'prepared.json').read_bytes())
        world = Path(receipt['world']).resolve()
        require(world.parent == (Path(config['profile']) / 'saves').resolve(), 'Wrong profile')
        require(json.loads((world / 'csmusic-harness-copy.json').read_bytes()) == receipt, 'Invalid copy receipt')
        install_probe(world)
        print('Installed terrain probe in copied world only; reload needed')
        return 0
    case = None
    if args.mode in ('structure', 'regression'):
        cases = json.loads((HERE / 'suite.json').read_bytes())['structures' if args.mode == 'structure' else 'regressions']
        case = next(c for c in cases if c['id'] == args.case)
    return Controller(config, args.mode, case, args.recover_report).run()


if __name__ == '__main__':
    raise SystemExit(main())
