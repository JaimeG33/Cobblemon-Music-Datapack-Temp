"""Offline safety/feedback tests; these do not claim Minecraft gameplay passed."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from harness import Blocked, Desktop, LogTail, allowed_command, chat_lines, contains_structure, framed_response, locate_coordinates, playing


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
        self.assertEqual(playing(text), [('#village_basic_night', '30')])
        self.assertEqual(playing('- [definition:test#0] dysfam_music:battle_gen5 (priority 50) <= playing'), [('dysfam_music:battle_gen5', '50')])
        self.assertEqual(playing('- [definition:ambient#1] #ambient (priority 10)'), [])

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


if __name__ == '__main__':
    unittest.main()
