"""Focused host-only regression for the suite's directory-symlink fixture."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import tutorial as t


class DirectorySymlinkFixtureTests(unittest.TestCase):
    def test_construction_preserves_inputs_and_guard_refuses_before_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            original = t.fixtures(root / 'original')
            # A nested directory with the same name must still be copied.
            nested = original / 'extra' / 'masks'
            nested.mkdir(parents=True)
            (nested / 'keep.bin').write_bytes(b'\x00nested masks\xff')
            before = {p.relative_to(original): p.read_bytes()
                      for p in original.rglob('*') if p.is_file()}
            destination = root / 'input-symlink_directory'
            with patch.object(t.shutil, 'rmtree', side_effect=AssertionError('fixture must not delete')) as removed, \
                    patch.object(t.shutil, 'copyfile', wraps=t.shutil.copyfile) as copied:
                t.directory_symlink_fixture(original, destination)
            removed.assert_not_called()
            self.assertTrue((destination / 'masks').is_symlink())
            self.assertEqual((destination / 'masks').readlink(), original / 'masks')
            expected_copies = {original / name for name in before if name.parts[0] != 'masks'}
            self.assertEqual({Path(call.args[0]) for call in copied.call_args_list}, expected_copies)
            retained = {p.relative_to(destination): p.read_bytes()
                        for p in destination.rglob('*')
                        if p.is_file() and p.relative_to(destination).parts[0] != 'masks'}
            self.assertEqual(retained, {name: data for name, data in before.items()
                                        if name.parts[0] != 'masks'})

            output = root / 'rejected-symlink_directory'
            with patch.object(t, 'sha', side_effect=AssertionError('must refuse before hashing')) as hashed, \
                    patch.object(t, 'prepare', side_effect=AssertionError('must refuse before JDK')) as prepared:
                with self.assertRaisesRegex(ValueError, 'input symlinks rejected before hashing'):
                    t.measure(destination, output)
            hashed.assert_not_called()
            prepared.assert_not_called()
            self.assertFalse(output.exists())
            self.assertEqual({p.relative_to(original): p.read_bytes()
                              for p in original.rglob('*') if p.is_file()}, before)


if __name__ == '__main__':
    unittest.main()
