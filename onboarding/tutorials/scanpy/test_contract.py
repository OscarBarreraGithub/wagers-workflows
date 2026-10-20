"""Small stdlib-only checks for runtime selection and filesystem contracts."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
import setup_runtime
import tutorial
import workflow as w


class Contracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.package = self.root / 'source'
        self.package.mkdir()
        self.runtime = self.root / 'shared runtime'
        self.runtime.mkdir()
        self.patch = patch.object(w, 'PACKAGE', self.package)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.source = self.package / 'fixture.json'
        self.source.write_text('{}')

    def refuse(self, out, message, source=None):
        with self.assertRaisesRegex(ValueError, message):
            w.reserve_output(out, source, self.runtime)
        self.assertFalse(out.exists())

    def test_external_fixture_and_legacy_runs(self):
        external = self.root / 'private output with spaces'
        self.assertEqual(w.reserve_output(external, self.source, self.runtime), external)
        self.assertEqual(external.stat().st_mode & 0o777, 0o700)
        with self.assertRaisesRegex(ValueError, 'output reuse'):
            w.reserve_output(external, self.source, self.runtime)
        legacy = self.package / 'runs' / 'fresh'
        self.assertEqual(w.reserve_output(legacy, runtime_prefix=self.runtime), legacy)
        self.assertEqual(w.selected_runtime(), self.package / '.runtime')

    def test_source_runtime_and_ancestor_guards(self):
        self.refuse(self.package / 'new', 'under source')
        self.refuse(self.package / 'runs', 'under source')
        self.refuse(self.runtime / 'new', 'runtime overlap')
        with patch.object(sys, 'prefix', str(self.root / 'active')):
            self.refuse(self.root / 'active' / 'new', 'runtime overlap')
        with patch.object(sys, 'base_prefix', str(self.root / 'base')):
            self.refuse(self.root / 'base' / 'new', 'runtime overlap')
        other = self.root / 'other environment'
        other.mkdir()
        (other / 'pyvenv.cfg').write_text('home = unrelated')
        self.refuse(other / 'new', 'existing environment ancestor')
        with self.assertRaisesRegex(ValueError, 'under source|runtime overlap'):
            w.reserve_output(self.root, runtime_prefix=self.runtime)
        for marker in ['report.json', 'suite-report.json', 'readout.h5ad', 'pseudobulk.h5ad']:
            result = self.root / marker.replace('.', '-')
            result.mkdir()
            (result / marker).write_text('evidence')
            self.refuse(result / 'new', 'results/snapshot')

    def test_input_overlap_and_symlinks(self):
        inputs = self.root / 'inputs'
        inputs.mkdir()
        source = inputs / 'source.json'
        source.write_text('{}')
        self.refuse(inputs / 'new', 'input/output overlap', source)
        with self.assertRaisesRegex(ValueError, 'input/output overlap'):
            w.reserve_output(inputs, source, self.runtime)
        linked = self.root / 'link'
        linked.symlink_to(inputs, target_is_directory=True)
        self.refuse(linked / 'new', 'symlink paths')
        symin = inputs / 'link.json'
        symin.symlink_to(source)
        self.refuse(self.root / 'new', 'symlink paths', symin)

    def test_setup_reservation_is_exclusive_and_external(self):
        with patch.object(setup_runtime, 'PACKAGE', self.package):
            default = self.package / '.runtime'
            self.assertEqual(setup_runtime.reserve_prefix(default), default)
            fresh = self.root / 'fresh environment'
            self.assertEqual(setup_runtime.reserve_prefix(fresh), fresh)
            with self.assertRaisesRegex(ValueError, 'already exists'):
                setup_runtime.reserve_prefix(fresh)
            with self.assertRaisesRegex(ValueError, 'under source'):
                setup_runtime.reserve_prefix(self.package / 'bad')
            with self.assertRaisesRegex(ValueError, 'runtime overlap'):
                setup_runtime.reserve_prefix(Path(sys.prefix).resolve() / 'bad')
        self.assertEqual(list(fresh.iterdir()), [])  # No venv/install/network used by this test.

    def test_runtime_identity_and_receipt_contract(self):
        (self.package / 'requirements.lock').write_text('Thing_Name==1.0\n')
        receipt = self.runtime / 'install-report.json'
        receipt.write_text(json.dumps({'install': [{'metadata': {'name': 'thing-name', 'version': '1.0'}}]}))
        with patch.object(sys, 'prefix', str(self.runtime)), patch.object(sys, 'version_info', (3, 12)), \
                patch.object(w.importlib.metadata, 'version', return_value='1.0'):
            identity = w.runtime_identity(self.runtime)
            self.assertEqual(identity['versions'], {'Thing_Name': '1.0'})
            with self.assertRaisesRegex(ValueError, 'runtime mismatch'):
                w.runtime_identity()
            with patch.object(sys, 'version_info', (3, 11)):
                with self.assertRaisesRegex(ValueError, 'runtime requires Python 3.12'):
                    w.runtime_identity(self.runtime)
            with patch.object(w.importlib.metadata, 'version', return_value='2.0'):
                with self.assertRaisesRegex(ValueError, 'runtime version mismatch'):
                    w.runtime_identity(self.runtime)
            receipt.write_text('{"install": []}')
            with self.assertRaisesRegex(ValueError, 'runtime install receipt disagrees'):
                w.runtime_identity(self.runtime)
            report = {'status': 'PASS', 'runtime': identity}
            w.verify_runtime_unchanged(report, self.runtime)
            self.assertEqual(report['status'], 'FAIL')
            self.assertFalse(report['runtime_unchanged'])
            receipt.unlink()
            with self.assertRaisesRegex(ValueError, 'runtime install receipt is missing'):
                w.runtime_identity(self.runtime)

    def test_runtime_failure_does_not_blame_input(self):
        out = self.root / 'runtime failure'
        with patch.object(w, 'validate', return_value={}), \
                patch.object(w, 'runtime_identity', side_effect=ValueError('runtime mismatch')):
            self.assertEqual(w.run(self.source, out, self.runtime), 1)
        report = json.loads((out / 'report.json').read_text())
        self.assertEqual(report['runtime_check'], 'FAIL')
        self.assertEqual(report['failed_stage'], 'runtime')
        self.assertEqual(report['stages'], {s: 'PASS' if s == 'validate' else 'NOT_RUN' for s in w.STAGES})
        self.assertNotIn('runtime', report)

    def test_child_runtime_and_no_bytecode_propagation(self):
        log = self.root / 'child.log'
        with patch.object(tutorial.subprocess, 'run') as run:
            run.return_value.returncode = 0
            self.assertEqual(tutorial.invoke(self.source, self.root / 'out', log, self.runtime), 0)
            args, kwargs = run.call_args
            self.assertIn('-B', args[0])
            self.assertEqual(args[0][-2:], ['--runtime-prefix', str(self.runtime)])
            self.assertEqual(kwargs['env']['PYTHONDONTWRITEBYTECODE'], '1')


if __name__ == '__main__':
    unittest.main()
