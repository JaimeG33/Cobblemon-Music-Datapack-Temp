"""Offline safety/feedback tests; these do not claim Minecraft gameplay passed."""
import hashlib
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import numpy as np

from harness import (Blocked, Controller, Desktop, LogTail, allowed_command, chat_lines,
                     contains_structure, framed_response, locate_coordinates, music_sources,
                     expected_rule_sources, playing, runtime_source, selection_diagnosis)
from audio import _wave_similarity


class FeedbackTests(unittest.TestCase):
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
        with patch('harness.time.sleep'):
            desk.send('time set 12000')
        self.assertEqual(desk.gui.press.call_args_list, [(('/',), {}), (('enter',), {})])
        desk.gui.hotkey.assert_called_once_with('ctrl', 'a')
        self.assertEqual(''.join(call.args[0] for call in desk.gui.write.call_args_list), '/time set 12000')
        self.assertLess(desk.gui.mock_calls.index(__import__('unittest').mock.call.hotkey('ctrl', 'a')),
                        desk.gui.mock_calls.index(__import__('unittest').mock.call.write('/')))

    def test_partial_command_interruption_then_resume_clears_stale_input(self):
        desk = Desktop.__new__(Desktop)
        desk.gui = Mock()
        desk.guard = Mock()
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


if __name__ == '__main__':
    unittest.main()
