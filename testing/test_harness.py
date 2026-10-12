"""Offline safety/feedback tests; these do not claim Minecraft gameplay passed."""
import hashlib
import ctypes
import json
import tempfile
import types
import wave
import zipfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import numpy as np

from harness import (Blocked, Controller, Desktop, LogTail, allowed_command, chat_lines,
                     contains_structure, framed_response, locate_coordinates, music_sources,
                     expected_rule_sources, playing, runtime_source, selection_diagnosis, structure_signature,
                     verify_installed_datapack)
from audio import _wave_similarity, capture_loopback, identify


class FeedbackTests(unittest.TestCase):
    def test_structure_stability_ignores_spawn_chat_but_detects_bounds_changes(self):
        response = ('Structures at -4736 70 -4192 (2):\n'
                    '- minecraft:mineshaft #minecraft:mineshaft [bounds: 0, piece: 0]\n'
                    '- bca:village/dark_small #bca:villages [bounds: 1, piece: 0]')
        announced = 'A wild Common Hidden Ability Ledyba has appeared!\n' + response
        self.assertEqual(structure_signature(response), structure_signature(announced))
        self.assertNotEqual(structure_signature(response), structure_signature(response.replace('bounds: 1', 'bounds: 0')))

    def test_floor_waiver_requires_spectator_and_still_verifies_exact_selection(self):
        case = {'id': 'spectator_test', 'structure': 'bca:village/default_small', 'priority': 30,
                'pool': 'village_basic_day', 'source': r'data\dysfam_music\csmusic\definition\villages_generic.json#0',
                'spectator_waypoint': [10, 64, 20]}
        for mode in ('spectator', 'creative'):
            controller = Controller.__new__(Controller)
            controller.config = {'test_gamemode': mode, 'locate_timeout': 10, 'audio': {'enabled': False}}
            controller.report = {'observed': {}, 'verification_layers': {}}
            controller.desktop = Mock()
            controller.state = controller.wait = controller.await_readiness = Mock()
            queries = []
            positions = iter(['[0.5d, 64.0d, 0.5d]', '[10.5d, 64.0d, 20.5d]'])
            def response(command, *args, **kwargs):
                queries.append(command)
                if command == 'data get entity @s Pos': return next(positions)
                if command.startswith('locate '): return 'The nearest bca:village/default_small is at [10, ~, 20]'
                if command.startswith('execute if entity'): return 'CSMUSIC_SPECTATOR'
                if command.startswith('forceload query'): return 'Chunk is marked for force loading'
                if command.startswith('execute if loaded'): return 'CSMUSIC_LOADED'
                if command.startswith('function csmusic_harness:probe'): return ''
                if command.startswith('tp @s'): return 'Teleported player'
                if command.startswith('weather '): return 'Set the weather'
                if command.startswith('time set '): return 'Set the time'
                if command.endswith('structures'): return 'Structures at 10 64 20 (1):\n- bca:village/default_small [bounds: 1, piece: 0]'
                if command.endswith('current'): return 'csmusic sources for player\n- [definition:csmusic/definition/villages_generic.json#0] #village_basic_day (priority 30) <= playing'
                raise AssertionError(command)
            controller.command = response
            if mode == 'spectator':
                controller.structure(case)
                self.assertFalse(any('probe' in q for q in queries))
                self.assertTrue(controller.report['observed']['travel']['teleport_verified'])
                self.assertEqual(controller.report['observed']['selection_diagnosis']['category'], 'PASS_SELECTION')
            else:
                with self.assertRaisesRegex(Blocked, 'no loaded safe surface'):
                    controller.structure(case)
                self.assertFalse(any(q.startswith('tp @s') for q in queries))

    def test_suite_plan_without_case_id_constructs_and_preserves_unrun_cases(self):
        with tempfile.TemporaryDirectory() as folder, patch('harness.HERE', Path(folder)):
            plan = {'structures': [{'id': 'first'}, {'id': 'second'}], 'regressions': ['third']}
            controller = Controller({'expected_counts': [413, 1310, 19]}, 'representative', plan)
            controller.runtime_ready = Mock()
            controller.smoke = Mock()
            controller.structure = Mock(side_effect=Blocked('invalid fixture'))
            controller.scheduled_suite(plan)
            self.assertEqual(controller.report['id'], 'representative')
            controller.structure.assert_called_once_with({'id': 'first'})
            self.assertEqual([s['status'] for s in controller.report['scenarios']], ['BLOCKED', 'NOT_RUN', 'NOT_RUN'])

    def test_fresh_text_copy_retries_transient_clipboard_lock(self):
        desk = Desktop.__new__(Desktop)
        desk.gui = Mock()
        desk.guard = Mock()
        desk.user = Mock()
        desk.user.GetClipboardSequenceNumber.side_effect = [1, 2, 2]
        desk.user.OpenClipboard.side_effect = [False, True]
        desk.user.GetClipboardData.return_value = 123
        copied = ctypes.create_unicode_buffer('/')
        kernel = Mock()
        kernel.GlobalLock.return_value = ctypes.addressof(copied)
        with patch('harness.ctypes.windll.kernel32', kernel), patch('harness.time.sleep'):
            self.assertEqual(desk.copy_selected_text(), '/')
        self.assertEqual(desk.user.OpenClipboard.call_count, 2)
        desk.user.CloseClipboard.assert_called_once()
        kernel.GlobalUnlock.assert_called_once_with(123)

    def test_failed_chat_opening_never_types_command_or_presses_enter(self):
        desk = Desktop.__new__(Desktop)
        desk.gui = Mock()
        desk.guard = Mock()
        desk.copy_selected_text = Mock(return_value='')
        with patch('harness.time.sleep'), self.assertRaisesRegex(Blocked, 'Chat input not verified'):
            desk.send('function csmusic_harness:identity')
        desk.gui.write.assert_not_called()
        self.assertEqual(desk.gui.press.call_args_list, [(('/',), {})])
        self.assertTrue(desk.aborted)

    def test_changed_chat_text_is_never_submitted(self):
        desk = Desktop.__new__(Desktop)
        desk.gui = Mock()
        desk.guard = Mock()
        desk.copy_selected_text = Mock(side_effect=['/', 'wrong text'])
        with patch('harness.time.sleep'), self.assertRaisesRegex(Blocked, 'Enter not sent'):
            desk.send('reload')
        self.assertEqual(desk.gui.press.call_args_list, [(('/',), {})])
        self.assertTrue(desk.aborted)

    def test_focus_loss_is_latched_even_after_focus_returns(self):
        desk = Desktop.__new__(Desktop)
        desk.hwnd = 42
        desk.stop_file = Mock()
        desk.stop_file.exists.return_value = False
        desk.gui = Mock()
        desk.user = Mock()
        desk.user.GetAsyncKeyState.return_value = 0
        desk.user.IsWindow.return_value = True
        desk.user.IsHungAppWindow.return_value = False
        desk.user.GetForegroundWindow.return_value = 0
        with self.assertRaisesRegex(Blocked, 'lost focus'):
            desk.guard()
        desk.user.GetForegroundWindow.return_value = 42
        with self.assertRaisesRegex(Blocked, 'aborted'):
            desk.send('reload')
        desk.gui.press.assert_not_called()

    def test_pcm_wav_decode_does_not_require_ffmpeg_wav_demuxer(self):
        samples = np.random.default_rng(7).integers(-2000, 2000, 22050*3, dtype=np.int16)
        stereo = np.column_stack((samples, samples)).astype('<i2')
        with tempfile.TemporaryDirectory() as folder:
            recording = Path(folder) / 'loopback.wav'
            with wave.open(str(recording), 'wb') as output:
                output.setnchannels(2)
                output.setsampwidth(2)
                output.setframerate(22050)
                output.writeframes(stereo.tobytes())
            refs = [{'track': 'test:known', 'event': 'test:known', 'archive_entry': 'test.ogg', 'bytes': b'ogg'}]
            with patch('audio._ffmpeg', return_value='test-ogg-only'), patch('audio.resolve_reference', return_value=refs), \
                    patch('audio._decode_bytes', return_value=samples.astype(np.float32)/32768) as decoder:
                result = identify(recording, 'test:known', Path(folder)/'references.zip')
            decoder.assert_called_once_with(b'ogg', 'test-ogg-only', 'test.ogg')
            self.assertGreater(result['best']['score'], .99)
            self.assertEqual(result['classification'], 'INCONCLUSIVE_AUDIO')

    def assistance_controller(self, folder):
        controller = Controller.__new__(Controller)
        controller.config = {'assistance': {'minimum_alert_interval_seconds': 60}}
        controller.report = {}
        controller.out = Path(folder)
        controller.world_verified = controller.command_state_safe = True
        controller.audio_recording = False
        controller.desktop = Mock()
        controller.tail = Mock()
        controller.receipt = {'token': 'testtoken'}
        controller.state = Mock()
        controller.command = Mock(return_value='CSMUSIC_WORLD_testtoken')
        return controller

    def test_assistance_allowlist_excludes_actions_and_nonself_targets(self):
        self.assertTrue(allowed_command('playsound minecraft:entity.ender_dragon.death master @s ~ ~ ~ 1 1'))
        self.assertTrue(allowed_command('tellraw @s {"text":"[CSMusic Tester] Please enter the tower.","color":"gold"}'))
        for command in ('playsound minecraft:test master @a ~ ~ ~ 1 1',
                        'playsound minecraft:test master @s ~ ~ ~ 10 1',
                        'tellraw @s {"text":"[CSMusic Tester] Help","color":"gold","clickEvent":{"action":"run_command","value":"/kill"}}',
                        'tellraw @a {"text":"[CSMusic Tester] Help","color":"gold"}'):
            self.assertFalse(allowed_command(command))

    def test_assistance_never_sends_during_audio_or_unsafe_command_state(self):
        with tempfile.TemporaryDirectory() as folder:
            for attribute, value in (('audio_recording', True), ('command_state_safe', False), ('world_verified', False)):
                controller = self.assistance_controller(folder)
                setattr(controller, attribute, value)
                controller.request_assistance('Please enter the tower.')
                controller.command.assert_not_called()

    def test_assistance_focus_loss_prevents_all_notifications(self):
        with tempfile.TemporaryDirectory() as folder:
            controller = self.assistance_controller(folder)
            controller.desktop.guard.side_effect = Blocked('focus lost')
            controller.request_assistance('Please return to Minecraft.')
            controller.command.assert_not_called()
            self.assertIn('notification_error', controller.report['assistance'])

    def test_assistance_rechecks_identity_and_rate_limits_across_invocations(self):
        with tempfile.TemporaryDirectory() as folder, patch('harness.HERE', Path(folder)):
            (Path(folder) / 'results').mkdir()
            controller = self.assistance_controller(folder)
            request = controller.request_assistance('Please enter the tower.')
            self.assertEqual(controller.command.call_count, 3)
            self.assertEqual(controller.command.call_args_list[0].args[0], 'function csmusic_harness:identity')
            self.assertEqual(request['notification'], 'Minecraft tellraw and playsound')
            controller.command.reset_mock()
            controller.request_assistance('Please enter the tower.')
            controller.command.assert_not_called()

    def test_loopback_interruption_closes_stream_and_preserves_partial_wav(self):
        stream = Mock()
        stream.read.return_value = b'\x01\x00' * 2048
        endpoint = {'name': 'Test [Loopback]', 'index': 2, 'maxInputChannels': 2, 'defaultSampleRate': 48000}
        audio = Mock()
        audio.get_host_api_info_by_type.return_value = {'defaultOutputDevice': 1}
        audio.get_device_info_by_index.return_value = {'name': 'Test'}
        audio.get_loopback_device_info_generator.return_value = iter([endpoint])
        audio.open.return_value = stream
        context = Mock()
        context.__enter__ = Mock(return_value=audio)
        context.__exit__ = Mock(return_value=False)
        module = types.SimpleNamespace(PyAudio=lambda: context, paWASAPI=1, paInt16=8)
        with tempfile.TemporaryDirectory() as folder, patch.dict('sys.modules', {'pyaudiowpatch': module}):
            output = Path(folder) / 'partial.wav'
            with self.assertRaisesRegex(Blocked, 'Emergency stop'):
                capture_loopback(output, 1, guard=Mock(side_effect=[None, Blocked('Emergency stop')]))
            stream.stop_stream.assert_called_once()
            stream.close.assert_called_once()
            with wave.open(str(output)) as recording:
                self.assertEqual(recording.getnframes(), 1024)

    def test_destructive_and_unrelated_commands_are_denied(self):
        for command in ('kill @e', 'fill 0 0 0 1 1 1 air', 'datapack disable "vanilla"', 'op user', 'execute run stop'):
            self.assertFalse(allowed_command(command), command)
        self.assertTrue(allowed_command('tp @s -122.5 73 -9.5'))
        self.assertTrue(allowed_command('function csmusic_harness:probe {x:-123,z:-10}'))
    def test_player_chat_cannot_spoof_system_feedback(self):
        self.assertEqual(chat_lines('[CHAT] <player> CSMUSIC_END\n[System] [CHAT] real'), ['real'])

    def test_framing_requires_both_fresh_markers_and_preserves_async_messages(self):
        lines = ['old_BEGIN', 'historical success', 'old_END', 'new_BEGIN', 'CSMUSIC_CREATIVE', 'A wild Pokemon appeared!', 'new_END']
        text = '\n'.join('[System] [CHAT] ' + s for s in lines)
        response = framed_response(text, 'new')
        self.assertIn('CSMUSIC_CREATIVE', response.splitlines())
        self.assertNotIn('historical success', response)
        self.assertIsNone(framed_response(text, 'different'))
        self.assertIsNone(framed_response('[System] [CHAT] new_END', 'new'))
        with self.assertRaises(Blocked):
            framed_response('[System] [CHAT] new_END\n[System] [CHAT] new_BEGIN', 'new')

    def test_selection_only_accepts_playing_source(self):
        text = '- [definition:csmusic/definition/villages_generic.json#1] #village_basic_night (29 tracks, repeat 2) (priority 30) <= playing\n- [definition:ambient#1] #ambient (priority 10)'
        self.assertEqual(playing(text), [{'source': 'definition:csmusic/definition/villages_generic.json', 'rule_index': 1,
                                         'source_key': 'definition:csmusic/definition/villages_generic.json#1',
                                         'selection': '#village_basic_night', 'priority': 30, 'playing': True}])
        self.assertEqual(playing('- [definition:test#0] dysfam_music:battle_gen5 (priority 50) <= playing')[0]['source_key'], 'definition:test#0')
        self.assertEqual(playing('- [definition:ambient#1] #ambient (priority 10)'), [])

    def test_source_mapping_and_same_pool_rules_keep_distinct_identity(self):
        self.assertEqual(runtime_source(r'data\dysfam_music\csmusic\definition\villages_generic.json#1'),
                         'definition:csmusic/definition/villages_generic.json#1')
        text = ('- [definition:csmusic/definition/villages_generic.json#1] #village_basic_day (priority 30)\n'
                '- [definition:csmusic/definition/villages_generic.json#10] #village_basic_day (priority 30) <= playing\n'
                '- [definition:csmusic/definition/villages_cobbletowns.json#2] dysfam_music:pallet (priority 30)')
        parsed = music_sources(text)
        self.assertEqual([x['source_key'] for x in parsed], [
            'definition:csmusic/definition/villages_generic.json#1',
            'definition:csmusic/definition/villages_generic.json#10',
            'definition:csmusic/definition/villages_cobbletowns.json#2'])
        self.assertEqual(len(playing(text)), 1)
        self.assertEqual(playing(text)[0]['rule_index'], 10)
        self.assertEqual(expected_rule_sources('dysfam_music:weather_oras_heavy_rain', 40),
                         ['definition:csmusic/definition/weather.json#0'])

    def test_pallet_lavender_overlap_is_not_misreported_as_music_failure(self):
        cases = [
            {'structure': 'cobbletowns:lavender_town', 'source': r'data\dysfam_music\csmusic\definition\villages_cobbletowns.json#1', 'music': 'dysfam_music:lavender', 'priority': 30},
            {'structure': 'cobbletowns:pallet_town', 'source': r'data\dysfam_music\csmusic\definition\villages_cobbletowns.json#2', 'music': 'dysfam_music:pallet', 'priority': 30},
        ]
        case = dict(cases[1], id='pallet', piece=None)
        bounds = ('Structures at -3664 68 720 (2):\n'
                  '- cobbletowns:lavender_town  [bounds: 1, piece: 0]\n'
                  '- cobbletowns:pallet_town  [bounds: 1, piece: 0]')
        current = ('- [definition:csmusic/definition/villages_cobbletowns.json#1] dysfam_music:lavender (priority 30) <= playing\n'
                   '- [definition:csmusic/definition/villages_cobbletowns.json#2] dysfam_music:pallet (priority 30)')
        diag = selection_diagnosis(case, bounds, current, cases)
        self.assertEqual(diag['category'], 'OVERLAPPING_STRUCTURES_EXPECTED_ARBITRATION')
        self.assertEqual(diag['winning_competitor']['source_key'], 'definition:csmusic/definition/villages_cobbletowns.json#1')

    def test_valid_single_fixture_with_wrong_winner_is_selection_failure(self):
        cases = [{'structure': 'cobbletowns:pallet_town', 'source': r'data\dysfam_music\csmusic\definition\villages_cobbletowns.json#2',
                  'music': 'dysfam_music:pallet', 'priority': 30},
                 {'structure': 'minecraft:village_plains', 'source': r'data\dysfam_music\csmusic\definition\villages_generic.json#1',
                  'music': '#village_basic_day', 'priority': 30}]
        diag = selection_diagnosis(cases[0], 'Structures at -1 64 1 (1):\n- cobbletowns:pallet_town  [bounds: 1, piece: 0]',
                                   '- [definition:csmusic/definition/villages_generic.json#1] #village_basic_day (priority 30) <= playing\n'
                                   '- [definition:csmusic/definition/villages_cobbletowns.json#2] dysfam_music:pallet (priority 30)', cases)
        self.assertEqual(diag['category'], 'VALID_FIXTURE_WRONG_SELECTION')

    def test_piece_must_belong_to_exact_containing_parent(self):
        text = '- cobbletowns:pallet_town  [bounds: 1, piece: 0]\n- other:structure [bounds: 1, piece: 1]\n    piece: other:building'
        self.assertTrue(contains_structure(text, 'cobbletowns:pallet_town'))
        self.assertFalse(contains_structure(text, 'cobbletowns:pallet_town', 'other:building'))
        self.assertTrue(contains_structure(text, 'other:structure', 'other:building'))
        self.assertFalse(contains_structure(text.replace('bounds: 1', 'bounds: 0'), 'other:structure'))

    def test_locate_preserves_unknown_y_and_exact_structure(self):
        self.assertEqual(locate_coordinates('The nearest cobbletowns:pallet_town is at [-123, ~, 456] (500 blocks away)', 'cobbletowns:pallet_town'), (-123, None, 456))
        for invalid in ('The nearest other:town is at [1, 2, 3]', 'The nearest cobbletowns:pallet_town is at [1, 3]', 'The nearest cobbletowns:pallet_town is at [30000000, 2, 3]'):
            with self.assertRaises(Blocked):
                locate_coordinates(invalid, 'cobbletowns:pallet_town')

    def test_tail_ignores_history_preserves_partial_lines_and_blocks_truncation(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path = Path(folder) / 'latest.log'
            path.write_bytes(b'historical pass\n')
            tail = LogTail(path)
            try:
                self.assertEqual(tail.read(), '')
                with path.open('ab') as stream:
                    stream.write(b'fresh par')
                self.assertEqual(tail.read(), '')
                with path.open('ab') as stream:
                    stream.write(b'tial\nnext\n')
                self.assertEqual(tail.read(), 'fresh partial\nnext\n')
                path.write_bytes(b'')
                with self.assertRaises(Blocked):
                    tail.read()
            finally:
                tail.close()

    def test_focus_loss_prevents_all_keyboard_input(self):
        desk = Desktop.__new__(Desktop)
        desk.gui = Mock()
        desk.guard = Mock(side_effect=Blocked('focus lost'))
        with self.assertRaises(Blocked):
            desk.send('datapack list enabled')
        desk.gui.press.assert_not_called()
        desk.gui.write.assert_not_called()

    def test_focus_loss_mid_command_never_submits(self):
        desk = Desktop.__new__(Desktop)
        desk.gui = Mock()
        desk.guard = Mock(side_effect=[None, None, Blocked('focus lost')])
        desk.copy_selected_text = Mock(return_value='/')
        with patch('harness.time.sleep'), self.assertRaises(Blocked):
            desk.send('reload')
        self.assertEqual(desk.gui.press.call_args_list, [(('/',), {})])

    def test_multiline_command_is_rejected_before_input(self):
        desk = Desktop.__new__(Desktop)
        desk.gui = Mock()
        with self.assertRaises(Blocked):
            desk.send('say safe\nkill @e')
        desk.gui.press.assert_not_called()

    def test_resumed_command_replaces_stale_chat_line(self):
        desk = Desktop.__new__(Desktop)
        desk.gui = Mock()
        desk.guard = Mock()
        desk.copy_selected_text = Mock(side_effect=['/', '/time set 12000'])
        with patch('harness.time.sleep'):
            desk.send('time set 12000')
        self.assertEqual(desk.gui.press.call_args_list, [(('/',), {}), (('enter',), {})])
        self.assertEqual(desk.gui.hotkey.call_args_list, [(('ctrl', 'a'), {}), (('ctrl', 'a'), {})])
        self.assertEqual(''.join(call.args[0] for call in desk.gui.write.call_args_list), '/time set 12000')
        self.assertLess(desk.gui.mock_calls.index(__import__('unittest').mock.call.hotkey('ctrl', 'a')),
                        desk.gui.mock_calls.index(__import__('unittest').mock.call.write('/')))

    def test_partial_command_interruption_then_resume_clears_stale_input(self):
        desk = Desktop.__new__(Desktop)
        desk.gui = Mock()
        desk.guard = Mock()
        desk.copy_selected_text = Mock(side_effect=['/', '/', '/time set 12000'])
        writes = []
        def interrupt_after_prefix(char):
            writes.append(char)
            if len(writes) == 6:
                raise Blocked('simulated focus interruption')
        desk.gui.write.side_effect = interrupt_after_prefix
        with patch('harness.time.sleep'), self.assertRaises(Blocked):
            desk.send('time set 1000')
        self.assertEqual(''.join(writes), '/time ')
        self.assertNotIn(__import__('unittest').mock.call.press('enter'), desk.gui.mock_calls)
        desk.gui.reset_mock()
        desk.gui.write.side_effect = None
        desk.guard.reset_mock()
        with patch('harness.time.sleep'):
            desk.send('time set 12000')
        self.assertEqual(''.join(call.args[0] for call in desk.gui.write.call_args_list), '/time set 12000')
        self.assertEqual(desk.gui.mock_calls[1], __import__('unittest').mock.call.hotkey('ctrl', 'a'))

    def test_daylight_recovery_is_idempotent_and_verifies_world_first(self):
        controller = Controller.__new__(Controller)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            world = Path(folder) / 'world'
            world.mkdir()
            receipt = world / 'csmusic-harness-copy.json'
            receipt.write_text('{}', encoding='utf-8')
            controller.report = {'environment': {'test_world': str(world)}}
            state = {'world': str(world), 'world_receipt_sha256': __import__('hashlib').sha256(b'{}').hexdigest(),
                     'original': 'true', 'desired': 'false'}
            checkpoint = Path(folder) / 'recovery.json'
            controller.command = Mock(return_value='doDaylightCycle is currently set to: true')
            self.assertEqual(controller.restore_daylight(checkpoint, state), 'true')
            controller.command.assert_called_once_with('gamerule doDaylightCycle')
            self.assertEqual(state['phase'], 'restored')
            state['world_receipt_sha256'] = 'wrong'
            controller.command.reset_mock()
            with self.assertRaises(Blocked):
                controller.restore_daylight(checkpoint, state)
            controller.command.assert_not_called()

    def test_daylight_recovery_restores_after_unconfirmed_submission(self):
        controller = Controller.__new__(Controller)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            world = Path(folder) / 'world'
            world.mkdir()
            receipt = world / 'csmusic-harness-copy.json'
            receipt.write_text('{}', encoding='utf-8')
            controller.report = {'environment': {'test_world': str(world)}}
            state = {'world': str(world), 'world_receipt_sha256': __import__('hashlib').sha256(b'{}').hexdigest(),
                     'original': 'true', 'desired': 'false'}
            checkpoint = Path(folder) / 'recovery.json'
            controller.command = Mock(side_effect=[
                'doDaylightCycle is currently set to: false',
                'Game rule doDaylightCycle has been updated to true',
                'doDaylightCycle is currently set to: true'])
            self.assertEqual(controller.restore_daylight(checkpoint, state), 'true')
            self.assertEqual(controller.command.call_count, 3)

    def test_daylight_intent_is_durable_before_change_submission(self):
        controller = Controller.__new__(Controller)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            world = Path(folder) / 'world'
            world.mkdir()
            (world / 'csmusic-harness-copy.json').write_text('{}', encoding='utf-8')
            controller.report = {'environment': {'test_world': str(world)}, 'observed': {}}
            checkpoint = Path(folder) / 'recovery.json'
            def fail_after_intent(command):
                state = json.loads(checkpoint.read_text(encoding='utf-8'))
                self.assertEqual(state['original'], 'true')
                self.assertEqual(state['desired'], 'false')
                self.assertEqual(state['phase'], 'intent_persisted')
                raise Blocked('simulated interruption before command submission')
            controller.command = Mock(side_effect=fail_after_intent)
            with self.assertRaises(Blocked):
                controller.set_daylight_with_checkpoint('true', checkpoint)
            self.assertEqual(json.loads(checkpoint.read_text(encoding='utf-8'))['phase'], 'intent_persisted')
            controller.command.assert_called_once_with('gamerule doDaylightCycle false')

    def test_interrupted_daylight_restoration_keeps_recovery_checkpoint_pending(self):
        controller = Controller.__new__(Controller)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            world = Path(folder) / 'world'
            world.mkdir()
            (world / 'csmusic-harness-copy.json').write_text('{}', encoding='utf-8')
            controller.report = {'environment': {'test_world': str(world)}}
            state = {'world': str(world), 'world_receipt_sha256': hashlib.sha256(b'{}').hexdigest(),
                     'original': 'true', 'desired': 'false', 'phase': 'change_confirmed'}
            checkpoint = Path(folder) / 'recovery.json'
            checkpoint.write_text(json.dumps(state), encoding='utf-8')
            controller.command = Mock(side_effect=['doDaylightCycle is currently set to: false',
                                                   Blocked('simulated focus loss during restore')])
            with self.assertRaises(Blocked):
                controller.restore_daylight(checkpoint, state)
            self.assertEqual(json.loads(checkpoint.read_text(encoding='utf-8'))['phase'], 'change_confirmed')
            controller.command = Mock(side_effect=['doDaylightCycle is currently set to: false',
                                                   'Game rule doDaylightCycle has been updated to true',
                                                   'doDaylightCycle is currently set to: true'])
            self.assertEqual(controller.restore_daylight(checkpoint, state), 'true')

    def test_wave_matcher_handles_offset_volume_and_silence(self):
        rng = np.random.default_rng(17)
        reference = rng.normal(0, .2, 22050 * 14).astype(np.float32)
        crop = reference[22050 * 4:22050 * 14] * .31
        wrong = np.random.default_rng(19).normal(0, .2, len(crop)).astype(np.float32)
        self.assertGreater(_wave_similarity(crop, reference), .9)
        self.assertLess(_wave_similarity(wrong, reference), .1)
        self.assertEqual(_wave_similarity(np.zeros_like(crop), reference), 0.0)


class Rc5FixtureTests(unittest.TestCase):
    def test_recovery_can_use_historical_pack_but_gameplay_rejects_it(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder) / 'repo'
            repo.mkdir()
            (repo / 'pack.mcmeta').write_text(json.dumps({'pack': {'pack_format': 48, 'description': 'RC5'}}))
            installed = Path(folder) / 'historical.zip'
            with zipfile.ZipFile(installed, 'w') as z:
                z.writestr('pack.mcmeta', json.dumps({'pack': {'pack_format': 48, 'description': 'RC4'}}))
            with patch('harness.REPO', repo):
                self.assertEqual(verify_installed_datapack(installed, recovery_only=True), 0)
                with self.assertRaises(Blocked):
                    verify_installed_datapack(installed)

    def test_recovery_rejects_invalid_pack_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            installed = Path(folder) / 'invalid.zip'
            with zipfile.ZipFile(installed, 'w') as z:
                z.writestr('pack.mcmeta', json.dumps({'pack': {'pack_format': 99}}))
            with self.assertRaises(Blocked):
                verify_installed_datapack(installed, recovery_only=True)

    def test_rc5_config_fixtures_and_regressions_reference_actual_rules(self):
        here = Path(__file__).resolve().parent
        config = json.loads((here / 'config_rc5.json').read_bytes())
        suite = json.loads((here / config['suite']).read_bytes())
        self.assertEqual(config['release'], 'RC5')
        self.assertNotEqual(config['installed_world'], config['source_world'])
        cases = {c['id']: c for c in suite['structures']}
        for case in cases.values():
            source, index = case['source'].split('#')
            rules = json.loads((here.parent / source.replace('\\', '/')).read_bytes())['rules']
            rule = rules[int(index)]
            self.assertEqual(rule['music'], case['music'])
            self.assertEqual(rule['priority'], case['priority'])
            self.assertEqual(rule['when']['structure'], case['structure'])
            self.assertEqual(rule['when'].get('structure_piece'), case.get('piece'))
        for regression in suite['regressions']:
            setup = cases[regression['setup_id']]
            for step in regression['steps']:
                self.assertEqual(step['music'], setup['music'])
                self.assertEqual(step['source'], setup['source'])
                self.assertEqual(step['priority'], 41)
        self.assertTrue(set(suite['modes']['representative']) <= cases.keys())


if __name__ == '__main__':
    unittest.main()
