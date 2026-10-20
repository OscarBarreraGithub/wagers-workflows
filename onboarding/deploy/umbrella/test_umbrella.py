"""Stdlib assembly/argv tests with tiny FAKE executables; no package execution."""
import copy
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
import assemble
import launcher

ADAPTIVE_PINS = {'numpy': '2.2.6', 'scipy': '1.15.3', 'scikit-learn': '1.6.1',
                 'joblib': '1.4.2', 'threadpoolctl': '3.6.0', 'pip': '25.0.1'}


class UmbrellaContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='umbrella argv only ')
        self.root = Path(self.temp.name).resolve()
        self.cfg = {
            'schema_version': 1, 'module_name': 'wagers-tools/2026.10-env001',
            'python_module': 'python/3.14.7-fasrc01',
            'release_prefix': str(self.root / 'release one'), 'module_root': str(self.root / 'modules one'),
            'host_prefix': str(self.root / 'host runtime'), 'host_python': str(self.root / 'host runtime/bin/python'),
            'myotally': {'prefix': str(self.root / 'myotally fixed')},
            'imagej': {'source': str(self.root / 'imagej source')},
            'cellprofiler': {'source': str(self.root / 'cp source'), 'sif': str(self.root / 'container fixed/cp.sif'),
                             'runtime': str(self.root / 'container executable/singularity')},
            'scanpy': {'source': str(self.root / 'scanpy source'), 'runtime_prefix': str(self.root / 'scanpy env')},
            'adaptive_screen': {'source': str(self.root / 'adaptive source'),
                                'runtime_prefix': str(self.root / 'adaptive env'),
                                'receipt': str(self.root / 'adaptive evidence/receipt.json')},
        }
        self.config = self.root / 'private config.json'
        self.capture = self.root / 'captured argv.json'
        # The host delegates ONLY our umbrella dispatcher to the test interpreter.
        # Anything else is captured, never imported/executed as a tutorial.
        self.put(self.cfg['host_python'], '#!/bin/sh\n'
                 'for arg do\n case "$arg" in */lib/launcher.py) '
                 f'exec {shlex.quote(sys.executable)} "$@" ;; esac\ndone\n'
                 f'exec {shlex.quote(sys.executable)} {shlex.quote(str(self.root / "capture.py"))} "$@"\n', True)
        self.put(self.root / 'capture.py',
                 'import json,os,sys\nfrom pathlib import Path\n'
                 'Path(os.environ["ARGV_CAPTURE"]).write_text(json.dumps({"argv":sys.argv[1:],'
                 '"env":{k:v for k,v in os.environ.items() if k.startswith("PYTHON")}}))\n')
        fake = ('#!/bin/sh\n# FAKE argv recorder only; python -I -B contract shape\n'
                f'exec {shlex.quote(sys.executable)} {shlex.quote(str(self.root / "capture.py"))} "$@"\n')
        myo = Path(self.cfg['myotally']['prefix'])
        self.put(myo / 'bin/wagers-myotally', fake, True)
        for name in ('app/wagers.py', 'app/scripts/tutorial_suite.py', 'app/scripts/validate_one.py',
                     'upstream/source/Myotally_V1.py', 'env/conda-meta/history', 'provenance/build.json'):
            self.put(myo / name, '# FAKE asset, no package code\n')
        self.put(myo / 'env/bin/python', fake, True)
        ij = Path(self.cfg['imagej']['source'])
        for name in ('tutorial.py', 'ImageJMeasure.java', '.runtime/classes/ImageJMeasure.class'):
            self.put(ij / name, 'FAKE asset\n')
        for name in ('ij-1.54p.jar', 'jdk.tar.gz'):
            self.put(ij / '.runtime' / name, 'FAKE archive for guard tests\n')
        artifact = launcher.digest(ij / '.runtime/jdk.tar.gz')
        spec = {'sha256': artifact, 'java_home': 'fake-jdk'}
        self.put(ij / 'runtime-lock.json', json.dumps({'imagej': {'sha256': artifact},
                 'jdk': {launcher.platform.system() + '-' + launcher.platform.machine(): spec}}))
        self.put(ij / '.runtime/fake-jdk/.imagej-complete.json',
                 json.dumps({'archive_sha256': artifact, 'java_home': 'fake-jdk'}))
        for name in ('bin/java', 'bin/javac', 'release', 'lib/modules'):
            self.put(ij / '.runtime/fake-jdk' / name, fake, name.startswith('bin/'))
        self.put(ij / '.runtime/build.json', json.dumps({'source': launcher.digest(ij / 'ImageJMeasure.java'), 'jar': artifact}))
        cp = self.cfg['cellprofiler']
        for name in ('runner.py', 'cp_measure.py'):
            self.put(Path(cp['source']) / name, '# FAKE entrypoint, never executed\n')
        self.put(cp['sif'], 'FAKE SIF bytes\n')
        self.put(cp['sif'] + '.json', json.dumps({'source': 'docker://cellprofiler/cellprofiler@' + launcher.CP_DIGEST,
                 'digest': launcher.CP_DIGEST, 'platform': 'linux/amd64', 'sif_sha256': launcher.digest(cp['sif'])}))
        self.put(cp['runtime'], fake, True)
        for key in ('scanpy', 'adaptive_screen'):
            src, env = Path(self.cfg[key]['source']), Path(self.cfg[key]['runtime_prefix'])
            names = ('tutorial.py', 'workflow.py', 'requirements.lock') if key == 'scanpy' else (
                'tutorial.py', 'contract.py', 'proposer.py', 'simulator.py', 'suite.py', 'requirements.txt')
            for name in names:
                self.put(src / name, '# FAKE --runtime-prefix entrypoint, never executed\n')
            pins = {'fake-package': '1.0'} if key == 'scanpy' else ADAPTIVE_PINS
            self.put(src / names[-1], ''.join(f'{name}=={version}\n' for name, version in pins.items()))
            base = self.root / (key + ' base-python')
            self.put(base / 'bin/python3.12', fake, True)
            self.put(base / 'lib/python3.12/base-marker', 'FAKE base library\n')
            self.put(env / 'pyvenv.cfg', f'home = {base / "bin"}\n'
                     'include-system-site-packages = false\nversion = 3.12.12\n'
                     f'executable = {base / "bin/python3.12"}\ncommand = python -m venv --copies env\n')
            self.put(env / 'bin/python', fake, True)
            for name, version in pins.items():
                self.put(env / f'lib/python3.12/site-packages/{name.replace("-", "_")}-{version}.dist-info/METADATA',
                         f'Name: {name}\nVersion: {version}\n')
            if key == 'scanpy':
                self.put(env / 'install-report.json', json.dumps({'install': [{'metadata': {'name': 'fake-package', 'version': '1.0'}}]}))
        self.put(self.cfg['adaptive_screen']['receipt'], '{"FAKE": "argv tests only"}\n')
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def put(self, path, text, executable=False):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        if executable:
            path.chmod(0o755)

    def save(self):
        self.config.write_text(json.dumps(self.cfg))

    def build(self):
        self.save()
        result = assemble.assemble(str(self.config))
        self.assertEqual(result['status'], 'assembled-not-installed-validated')
        self.assertFalse(self.capture.exists(), 'assembly accidentally executed a runtime')

    def run_fake(self, tool, args, ok=True):
        self.capture.unlink(missing_ok=True)
        result = subprocess.run([str(Path(self.cfg['release_prefix']) / 'bin' / ('wagers-' + tool)), *args],
                                env={**os.environ, 'ARGV_CAPTURE': str(self.capture), 'PYTHONPATH': '/untrusted leak',
                                     'PYTHONHOME': '/untrusted leak'}, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stderr)
        if ok:
            value = json.loads(self.capture.read_text())
            self.assertNotIn('PYTHONPATH', value['env'])
            self.assertNotIn('PYTHONHOME', value['env'])
            self.assertEqual(value['env']['PYTHONDONTWRITEBYTECODE'], '1')
            return value['argv']
        self.assertFalse(self.capture.exists(), 'refusal executed fake runtime')

    def adaptive_conda(self):
        root = Path(self.cfg['adaptive_screen']['runtime_prefix'])
        (root / 'pyvenv.cfg').unlink()
        self.put(root / 'conda-meta/history', '# FAKE Mamba transaction\n')
        record = {'name': 'python', 'version': '3.12.12', 'build': 'h123_0_cpython',
                  'build_number': 0, 'subdir': 'linux-64', 'depends': ['libffi >=3.4'],
                  'timestamp': 1750000000000}
        path = root / 'conda-meta/python-3.12.12-h123_0_cpython.json'
        self.put(path, json.dumps(record))
        self.put(root / 'conda-meta/libffi-3.4.6-h123_1.json',
                 json.dumps({'name': 'libffi', 'version': '3.4.6', 'build': 'h123_1'}))
        return root, path, record

    def test_adaptive_conda_inventory_and_fixed_route_without_inspect_execution(self):
        root, record, _ = self.adaptive_conda()
        before = {str(p): launcher.digest(p) for p in self.root.rglob('*') if p.is_file()}
        with patch.object(subprocess, 'run', side_effect=AssertionError('inspect executed subprocess')), \
                patch.object(os, 'execve', side_effect=AssertionError('inspect executed runtime')):
            inventory = launcher.inspect(self.cfg)
        self.assertEqual(before, {str(p): launcher.digest(p) for p in self.root.rglob('*') if p.is_file()})
        self.assertFalse(self.capture.exists())
        self.assertFalse((root / 'pyvenv.cfg').exists())
        for path in (root / 'conda-meta').iterdir():
            self.assertEqual(inventory['files'][str(path)], launcher.digest(path))
        self.assertIn(str(root), inventory['protected'])
        self.build()
        args = ['suite', '--out', str(self.root / 'private adaptive results')]
        self.assertEqual(self.run_fake('adaptive-screen', args),
                         ['-E', '-s', '-B', str(Path(self.cfg['adaptive_screen']['source']) / 'tutorial.py'), *args])
        self.run_fake('adaptive-screen', ['suite', '--out', str(root / 'results')], ok=False)
        self.run_fake('adaptive-screen', ['suite', '--runtime-prefix=/elsewhere'], ok=False)
        # Valid but changed metadata must still invalidate the saved inventory.
        record.write_text(record.read_text() + '\n')
        self.run_fake('adaptive-screen', args, ok=False)

    def test_adaptive_conda_missing_multiple_wrong_and_ambiguous_records(self):
        root, path, record = self.adaptive_conda()
        original = path.read_text()
        cases = ('missing', 'missing-history', 'multiple', 'wrong-version', 'wrong-name',
                 'wrong-filename', 'mixed-layout')
        for case in cases:
            with self.subTest(case=case):
                path.write_text(original)
                extra = None
                if case == 'missing':
                    path.unlink()
                elif case == 'missing-history':
                    (root / 'conda-meta/history').unlink()
                elif case == 'multiple':
                    extra = root / 'conda-meta/python-3.12.12-other_0.json'
                    self.put(extra, json.dumps({**record, 'build': 'other_0'}))
                elif case == 'wrong-version':
                    path.unlink()
                    extra = root / 'conda-meta/python-3.12.11-h123_0_cpython.json'
                    self.put(extra, json.dumps({**record, 'version': '3.12.11'}))
                elif case == 'wrong-name':
                    path.write_text(json.dumps({**record, 'name': 'pip'}))
                elif case == 'wrong-filename':
                    path.unlink()
                    extra = root / 'conda-meta/renamed.json'
                    self.put(extra, original)
                else:
                    extra = root / 'pyvenv.cfg'
                    self.put(extra, 'version = 3.12.12\n')
                with self.assertRaises(ValueError):
                    assemble.assemble(str(self.config))
                self.assertFalse(Path(self.cfg['release_prefix']).exists())
                self.assertFalse(Path(self.cfg['module_root']).exists())
                self.assertFalse(self.capture.exists())
                if extra:
                    extra.unlink()
                self.put(root / 'conda-meta/history', '# FAKE Mamba transaction\n')

    def test_adaptive_conda_malformed_metadata_fails_closed(self):
        root, path, record = self.adaptive_conda()
        malformed = ('{', '[]', 'null', '{}',
                     json.dumps({**record, 'version': 3.12}),
                     json.dumps({**record, 'build': ''}),
                     json.dumps(record)[:-1] + ', "version": "3.12.12"}',
                     json.dumps(record)[:-1] + ', "extra": {"key": 1, "key": 2}}')
        nonfinite = tuple(json.dumps(record)[:-1] + ', "extra": ' + token + '}'
                          for token in ('NaN', 'Infinity', '-Infinity', '1e999', '-1e999'))
        for value in (*malformed, *nonfinite):
            with self.subTest(value=value):
                path.write_text(value)
                with self.assertRaises(ValueError):
                    launcher.inspect(self.cfg)
        path.write_text(json.dumps(record))
        # Other records cannot hide a Python identity in malformed metadata.
        other = root / 'conda-meta/libffi-3.4.6-h123_1.json'
        other.write_text('{')
        with self.assertRaises(ValueError):
            launcher.inspect(self.cfg)
        self.assertFalse(self.capture.exists())

    def test_adaptive_conda_metadata_drift_inventory(self):
        root, path, _ = self.adaptive_conda()
        self.build()
        for target in (root / 'conda-meta/history', root / 'conda-meta/libffi-3.4.6-h123_1.json'):
            with self.subTest(target=target.name):
                original = target.read_text()
                target.write_text(original + '\n')
                self.run_fake('adaptive-screen', ['suite', '--out', str(self.root / 'private results')], ok=False)
                target.write_text(original)
        added = root / 'conda-meta/other-1.0-h0.json'
        self.put(added, json.dumps({'name': 'other', 'version': '1.0', 'build': 'h0'}))
        self.run_fake('adaptive-screen', ['suite', '--out', str(self.root / 'private results')], ok=False)
        added.unlink()
        path.unlink()
        self.run_fake('adaptive-screen', ['suite', '--out', str(self.root / 'private results')], ok=False)

    def test_adaptive_conda_requires_each_distribution_pin(self):
        root, _, _ = self.adaptive_conda()
        for name, version in ADAPTIVE_PINS.items():
            path = root / f'lib/python3.12/site-packages/{name.replace("-", "_")}-{version}.dist-info/METADATA'
            original = path.read_text()
            for value in (None, f'Name: {name}\nVersion: 0.0\n'):
                with self.subTest(name=name, metadata=value):
                    if value is None:
                        path.unlink()
                    else:
                        path.write_text(value)
                    with self.assertRaisesRegex(ValueError, 'installed distribution metadata'):
                        launcher.inspect(self.cfg)
                    path.write_text(original)

    def test_existing_venv_layout_and_scanpy_conda_refusal(self):
        root = Path(self.cfg['adaptive_screen']['runtime_prefix'])
        original = (root / 'pyvenv.cfg').read_text()
        # A final symlink to the fake base interpreter; never execute it here.
        base = self.root / 'adaptive_screen base-python'
        python = root / 'bin/python'
        python.unlink()
        python.symlink_to(base / 'bin/python3.12')
        inventory = launcher.inspect(self.cfg)
        self.assertIn(str(root / 'pyvenv.cfg'), inventory['files'])
        self.assertIn(str(base), inventory['protected'])
        (root / 'pyvenv.cfg').write_text('version = 3.12.11\n')
        with self.assertRaisesRegex(ValueError, 'wrong venv Python version'):
            launcher.inspect(self.cfg)
        (root / 'pyvenv.cfg').write_text(original)
        scan = Path(self.cfg['scanpy']['runtime_prefix'])
        (scan / 'pyvenv.cfg').unlink()
        self.put(scan / 'conda-meta/history', '# Conda is unsupported for Scanpy\n')
        self.put(scan / 'conda-meta/python-3.12.12-h0.json',
                 json.dumps({'name': 'python', 'version': '3.12.12', 'build': 'h0'}))
        with self.assertRaisesRegex(ValueError, 'pyvenv.cfg'):
            launcher.inspect(self.cfg)
        self.assertFalse(self.capture.exists())

    def check_venv_base_outputs(self, symlink):
        bases = [self.root / (key + ' base-python') for key in ('scanpy', 'adaptive_screen')]
        if symlink:
            for key, base in zip(('scanpy', 'adaptive_screen'), bases):
                python = Path(self.cfg[key]['runtime_prefix']) / 'bin/python'
                python.unlink()
                python.symlink_to(base / 'bin/python3.12')
        before = {str(p): launcher.digest(p) for base in bases for p in base.rglob('*') if p.is_file()}
        with patch.object(subprocess, 'run', side_effect=AssertionError('inspect executed subprocess')), \
                patch.object(os, 'execve', side_effect=AssertionError('inspect executed runtime')):
            inventory = launcher.inspect(self.cfg)
        for base in bases:
            self.assertIn(str(base), inventory['protected'])
            python = base / 'bin/python3.12'
            self.assertEqual(inventory['files'][str(python)], launcher.digest(python))
        # Assembly destinations must also be refused before either is created.
        original = copy.deepcopy(self.cfg)
        for field in ('release_prefix', 'module_root'):
            for base in bases:
                self.cfg = copy.deepcopy(original)
                dest = base / 'lib/new assembly'
                self.cfg[field] = str(dest)
                self.save()
                with self.assertRaisesRegex(ValueError, 'overlap'):
                    assemble.assemble(str(self.config))
                self.assertFalse(dest.exists())
                self.assertFalse(Path(original['release_prefix']).exists())
                self.assertFalse(Path(original['module_root']).exists())
        self.cfg = original
        self.build()
        # All launchers share the inventory, including another tool's base.
        for base in bases:
            for dest in (base / 'results', base / 'bin/results', base / 'lib/python3.12/results'):
                with self.subTest(base=base.name, destination=dest):
                    self.run_fake('scanpy', ['suite', '--output', str(dest)], ok=False)
                    self.run_fake('adaptive-screen', ['suite', '--out=' + str(dest)], ok=False)
                    self.assertFalse(dest.exists())
        self.assertEqual(before, {str(p): launcher.digest(p) for base in bases
                                  for p in base.rglob('*') if p.is_file()})
        outside = str(self.root / 'private results after refusal')
        got = self.run_fake('scanpy', ['suite', '--output', outside])
        self.assertEqual(got[4:], ['--output', outside,
                                  '--runtime-prefix', self.cfg['scanpy']['runtime_prefix']])

    def test_copied_venvs_protect_full_base_before_outputs(self):
        self.check_venv_base_outputs(symlink=False)

    def test_symlinked_venvs_protect_full_base_before_outputs(self):
        self.check_venv_base_outputs(symlink=True)

    def test_venv_missing_ambiguous_and_invalid_home_refused_before_writes(self):
        alias = self.root / 'base alias'
        alias.symlink_to(self.root / 'scanpy base-python', target_is_directory=True)
        for key in ('scanpy', 'adaptive_screen'):
            root = Path(self.cfg[key]['runtime_prefix'])
            marker = root / 'pyvenv.cfg'
            original = marker.read_text()
            base = self.root / (key + ' base-python')
            self.put(base / 'not-a-directory/bin', 'FAKE file instead of home\n')
            homes = ('', 'relative/bin', str(self.root / 'missing/bin'), str(base),
                     str(base / 'not-a-directory/bin'), str(alias / 'bin'), '/bin',
                     str(base / 'bin/../bin'), str(base / 'REQUIRED/bin'))
            malformed = ['version = 3.12.12\n', original + f'home = {base / "bin"}\n',
                         original + f'HOME = {base / "bin"}\n', original + 'home without equals\n']
            malformed += [f'version = 3.12.12\nhome = {home}\n' for home in homes]
            for value in malformed:
                with self.subTest(key=key, metadata=value):
                    marker.write_text(value)
                    with self.assertRaises(ValueError):
                        assemble.assemble(str(self.config))
                    self.assertFalse(Path(self.cfg['release_prefix']).exists())
                    self.assertFalse(Path(self.cfg['module_root']).exists())
                    self.assertFalse(self.capture.exists())
            marker.write_text(original)
        # Corrected metadata permits a fresh assembly without runtime execution.
        self.build()

    def test_venv_home_requires_base_interpreter_and_consistent_symlink(self):
        base = self.root / 'scanpy base-python'
        python = base / 'bin/python3.12'
        original = python.read_bytes()
        outside = self.root / 'outside interpreter/python3.12'
        self.put(outside, '# FAKE outside interpreter\n', True)
        for case in ('missing', 'not-executable', 'outside-base'):
            with self.subTest(case=case):
                if case == 'missing':
                    python.unlink()
                elif case == 'not-executable':
                    python.chmod(0o644)
                else:
                    python.unlink()
                    python.symlink_to(outside)
                with self.assertRaises(ValueError):
                    launcher.inspect(self.cfg)
                python.unlink(missing_ok=True)
                python.write_bytes(original)
                python.chmod(0o755)
        own = Path(self.cfg['scanpy']['runtime_prefix']) / 'bin/python'
        own.unlink()
        own.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'contradicts home'):
            launcher.inspect(self.cfg)
        self.assertFalse(self.capture.exists())

    def test_venv_home_metadata_and_base_interpreter_drift_refused(self):
        self.build()
        for key in ('scanpy', 'adaptive_screen'):
            for target in (Path(self.cfg[key]['runtime_prefix']) / 'pyvenv.cfg',
                           self.root / (key + ' base-python') / 'bin/python3.12'):
                with self.subTest(key=key, target=target.name):
                    original = target.read_text()
                    target.write_text(original + '\n')
                    self.run_fake('scanpy', ['suite', '--output', str(self.root / 'private results')], ok=False)
                    target.write_text(original)

    def test_five_literal_routes_and_injected_defaults(self):
        self.build()
        output = str(self.root / 'private results/literal $value; not shell')
        value = 'input with spaces $(touch NEVER) ; "quote"'
        self.assertEqual(self.run_fake('myotally', ['analyze', '--manifest', value, '--run-dir', output]),
                         ['analyze', '--manifest', value, '--run-dir', output])
        got = self.run_fake('imagej', ['measure', '--input', value, '--out', output])
        self.assertEqual(got, ['-E', '-s', '-B', str(Path(self.cfg['imagej']['source']) / 'tutorial.py'),
                               'measure', '--input', value, '--out', output])
        for mode in ('run', 'suite', 'generate'):
            args = [mode, '--dest', output] if mode != 'run' else [mode, '--originals', value, '--output', output]
            got = self.run_fake('cellprofiler', args)
            extra = ['--sif', self.cfg['cellprofiler']['sif'], '--runtime', self.cfg['cellprofiler']['runtime']] if mode != 'generate' else []
            self.assertEqual(got[4:], args + extra)
        for mode, script in (('suite', 'tutorial.py'), ('run', 'workflow.py')):
            got = self.run_fake('scanpy', [mode, '--output', output])
            self.assertEqual(got, ['-E', '-s', '-B', str(Path(self.cfg['scanpy']['source']) / script),
                                  '--output', output, '--runtime-prefix', self.cfg['scanpy']['runtime_prefix']])
        got = self.run_fake('adaptive-screen', ['propose', '--state', value, '--out', output])
        self.assertEqual(got[4:], ['propose', '--state', value, '--out', output])

    def test_invalid_preflight_corrected_retry_and_no_execution(self):
        marker = Path(self.cfg['imagej']['source']) / '.runtime/fake-jdk/.imagej-complete.json'
        saved = marker.read_bytes()
        marker.unlink()
        with self.assertRaisesRegex(ValueError, 'required file missing'):
            assemble.assemble(str(self.config))
        self.assertFalse(Path(self.cfg['release_prefix']).exists())
        self.assertFalse(Path(self.cfg['module_root']).exists())
        marker.write_bytes(saved)
        self.build()

    def test_reject_placeholder_relative_missing_and_executable(self):
        original = copy.deepcopy(self.cfg)
        for mutation in ('placeholder', 'relative', 'module', 'missing', 'executable'):
            with self.subTest(mutation=mutation):
                self.cfg = copy.deepcopy(original)
                if mutation == 'placeholder':
                    self.cfg['release_prefix'] = '/REQUIRED/fresh'
                elif mutation == 'relative':
                    self.cfg['release_prefix'] = 'relative release'
                elif mutation == 'module':
                    self.cfg['python_module'] = 'python'
                elif mutation == 'missing':
                    self.cfg['cellprofiler']['runtime'] = str(self.root / 'absent')
                else:
                    Path(self.cfg['cellprofiler']['runtime']).chmod(0o644)
                self.save()
                with self.assertRaises(ValueError):
                    assemble.assemble(str(self.config))
                self.assertFalse(Path(original['release_prefix']).exists())
        self.assertFalse(self.capture.exists())

    def test_overlap_and_symlinks_rejected_before_writes(self):
        original = copy.deepcopy(self.cfg)
        cases = [original['module_root'], str(Path(original['imagej']['source']) / 'new release'),
                 str(Path(original['scanpy']['runtime_prefix']) / 'new release'), str(self.root),
                 str(Path(assemble.__file__).parent / 'must not write')]
        link = self.root / 'source alias'
        link.symlink_to(original['imagej']['source'], target_is_directory=True)
        cases.append(str(link / 'new release'))
        for destination in cases:
            with self.subTest(destination=destination):
                self.cfg = copy.deepcopy(original)
                self.cfg['release_prefix'] = destination
                self.save()
                with self.assertRaises(ValueError):
                    assemble.assemble(str(self.config))
                self.assertFalse(Path(original['module_root']).exists())

    def test_overwrite_refusal_and_read_only_doctor_module_inspection(self):
        self.build()
        prefix = Path(self.cfg['release_prefix'])
        before = {str(p): launcher.digest(p) for p in self.root.rglob('*') if p.is_file()}
        with self.assertRaisesRegex(ValueError, 'fresh'):
            assemble.assemble(str(self.config))
        result = subprocess.run([str(prefix / 'bin/wagers-doctor'), '--json'], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('biology NOT validated', json.loads(result.stdout)['scope'])
        self.assertEqual(before, {str(p): launcher.digest(p) for p in self.root.rglob('*') if p.is_file()})
        self.assertEqual((prefix / 'provenance/config.json').read_bytes(), self.config.read_bytes())
        module = Path(self.cfg['module_root']) / (self.cfg['module_name'] + '.lua')
        lines = module.read_text().splitlines()
        self.assertEqual([line.split('(')[0] for line in lines],
                         ['help', 'whatis', 'depends_on', 'prepend_path', 'setenv', 'setenv'])
        for line in lines[1:]:
            # Our Lua uses only function calls with JSON-compatible string arguments.
            json.loads('[' + line.partition('(')[2][:-1] + ']')
        self.assertIn('depends_on("python/3.14.7-fasrc01")', lines)
        for wrapper in (prefix / 'bin').iterdir():
            subprocess.run(['/bin/sh', '-n', str(wrapper)], check=True)

    def test_fixed_runtime_overrides_shared_outputs_and_asset_drift(self):
        self.build()
        for tool, args in (
            ('cellprofiler', ['run', '--sif', '/elsewhere']),
            ('cellprofiler', ['suite', '--runt=/elsewhere']),
            ('scanpy', ['run', '--runtime-prefix=/elsewhere']),
            ('scanpy', ['suite', '--runt', '/elsewhere']),
            ('myotally', ['doctor', '--source', '/elsewhere']),
            ('myotally', ['doctor', '--sou=/elsewhere']),
            ('imagej', ['install']),
            ('cellprofiler', ['install']),
            ('myotally', ['fetch-source']),
            ('imagej', ['seal', '--input', self.cfg['imagej']['source']]),
            ('adaptive-screen', ['suite', '--out', str(Path(self.cfg['release_prefix']) / 'results')]),
            ('scanpy', ['suite', '--output=' + str(Path(self.cfg['cellprofiler']['sif']).parent / 'results')]),
        ):
            with self.subTest(tool=tool, args=args):
                self.run_fake(tool, args, ok=False)
        Path(self.cfg['imagej']['source'], '.runtime/classes/ImageJMeasure.class').unlink()
        self.run_fake('imagej', ['suite', '--out', str(self.root / 'private run')], ok=False)

    def test_failed_construction_retains_log_and_fresh_retry(self):
        original_write = Path.write_bytes

        def fail_dispatch(path, data):
            if path.name == 'launcher.py':
                raise OSError('deliberate construction failure, no package execution')
            return original_write(path, data)

        with patch.object(Path, 'write_bytes', fail_dispatch):
            with self.assertRaisesRegex(OSError, 'deliberate'):
                assemble.assemble(str(self.config))
        evidence = Path(self.cfg['release_prefix']) / 'provenance/build.json'
        saved = evidence.read_bytes()
        self.assertEqual(json.loads(saved)['status'], 'failed')
        self.cfg.update(release_prefix=str(self.root / 'release corrected'), module_root=str(self.root / 'modules corrected'))
        self.build()
        self.assertEqual(evidence.read_bytes(), saved)

    def test_myotally_isolated_bytecode_gap_fails_closed(self):
        path = Path(self.cfg['myotally']['prefix']) / 'app/wagers.py'
        path.write_text('child = ["python", "-I", "shared-script.py"]\n')
        with self.assertRaisesRegex(ValueError, 'isolated child lacks -B'):
            assemble.assemble(str(self.config))
        self.assertFalse(Path(self.cfg['release_prefix']).exists())
        # Corrected fake source shape only: accept the reviewed ordering without
        # importing this source or executing Myotally/control packages.
        for name in ('wagers.py', 'scripts/tutorial_suite.py', 'scripts/validate_one.py'):
            self.put(Path(self.cfg['myotally']['prefix']) / 'app' / name,
                     'import sys\nsys.dont_write_bytecode = True\n'
                     'child = ["python", "-I", "-B", "shared-script.py"]\n')
        self.build()


if __name__ == '__main__':
    unittest.main()
