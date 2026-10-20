"""Installer contracts only: subprocess doubles do not execute/install packages."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('independent_install', Path(__file__).with_name('install.py'))
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve() / 'literal space ; punctuation'
        self.base.mkdir()
        self.repo = self.base / 'repository'
        self.repo.mkdir()
        self.site = self.base / 'site'
        self.site.mkdir()
        site = {}
        for key in installer.CAPABILITIES:
            exe = self.site / key
            exe.write_text('#!/bin/sh\nexit 99\n')
            exe.chmod(0o755)
            site[key] = {'prefix': str(self.site), 'executable': str(exe),
                         'sha256': installer.sha(exe), 'version': key + ' version exact'}
        self.cfg = {'schema_version': 1, 'source_repository': str(self.repo), 'source_commit': 'a' * 40,
                    'install_root': str(self.base / 'fresh final software'), 'module_root': str(self.base / 'fresh modules'),
                    'module_name': 'wagers-tools/test001', 'python_module': 'python/exact001',
                    'system_path': [str(self.site)], 'site': site}
        self.config = self.base / 'private config.json'
        self.write_config()
        self.files = {'onboarding/deploy/install/' + name: Path(__file__).with_name(name).read_bytes()
                      for name in ('install.py', 'check_runtime.py')}
        self.files['onboarding/tutorials/imagej/tutorial.py'] = b'# package source\n'
        self.executed = []
        self.probes = []

    def write_config(self):
        self.config.write_text(json.dumps(self.cfg))

    def fake_output(self, argv, env, cwd):
        self.probes.append((argv, dict(env), cwd))
        if argv[-1] == '--version':
            return (self.cfg['site'][Path(argv[0]).name]['version'] + '\n').encode()
        if argv[-2:] == ['config', 'list']:
            return b'\n'
        return b'[3, 14, 7]\n'

    def preflight(self):
        with patch.object(installer.platform, 'system', return_value='Linux'), \
             patch.object(installer.platform, 'machine', return_value='x86_64'), \
             patch.object(installer, 'output', side_effect=self.fake_output), \
             patch.object(installer, 'source_files', return_value=self.files):
            return installer.preflight(self.config)

    def fake_run(self, command, **kwargs):
        self.executed.append(command)
        self.assertNotIn('shell', kwargs)
        self.assertEqual(kwargs['cwd'], Path(self.cfg['install_root']))
        if any(str(value).endswith('/deploy/umbrella/assemble.py') for value in command):
            # Simulated assembler artifacts only: no real assembler/runtime execution.
            selected = json.loads(Path(command[-1]).read_text())
            provenance = Path(selected['release_prefix']) / 'provenance'
            provenance.mkdir(parents=True)
            installer.dump(provenance / 'config.json', selected)
            venv = Path(self.cfg['install_root']) / 'runtimes/scanpy-venv'
            venv.mkdir()
            (venv / 'pyvenv.cfg').write_text('home = ' + str(venv.parent / 'scanpy-base/bin') + '\n')
            installer.dump(provenance / 'inventory.json', {
                'files': {str(venv / 'pyvenv.cfg'): 'double'},
                'executables': [selected['host_python']],
                'protected': [selected['release_prefix'], selected['module_root'],
                              str(venv.parent / 'scanpy-base'), selected['imagej']['source']]})
        return subprocess.CompletedProcess(command, 0)

    def build(self, runner=None):
        with patch.object(installer.subprocess, 'run', side_effect=runner or self.fake_run):
            return installer.Build(self.cfg, self.files, {'python': 'fake'}, self.config).build()

    def restore_modes(self):
        root = Path(self.cfg['install_root'])
        if root.exists():
            for path in root.rglob('*'):
                if path.is_dir():
                    path.chmod(0o755)

    def test_fresh_nonexistent_roots_preflight_creates_nothing(self):
        cfg, files, versions = self.preflight()
        self.assertEqual(cfg, self.cfg)
        self.assertEqual(files, self.files)
        self.assertEqual(len(versions), 5)
        self.assertFalse(Path(cfg['install_root']).exists())
        self.assertFalse(Path(cfg['module_root']).exists())

    def test_mamba_config_probe_excludes_poison_inherited_configuration(self):
        poison = {'CONDARC': '/old/config', 'MAMBARC': '/old/mambarc',
                  'MAMBA_RC_FILES': '/old/rc', 'CONDA_RC_FILES': '/old/condarc',
                  'CONDA_PREFIX': '/old/env', 'CONDA_TOKEN': 'private-token',
                  'MAMBA_NO_RC': 'false', 'AWS_SECRET_ACCESS_KEY': 'private-key'}
        with patch.dict(os.environ, poison):
            self.preflight()
            build_env = installer.clean_environment(self.cfg, Path(self.cfg['install_root']))
        configs = [(argv, env, cwd) for argv, env, cwd in self.probes if argv[-2:] == ['config', 'list']]
        self.assertEqual(len(configs), 1)
        argv, env, cwd = configs[0]
        self.assertEqual(argv, [self.cfg['site']['mamba']['executable'], 'config', 'list'])
        self.assertEqual(cwd, Path(self.cfg['source_repository']))
        self.assertEqual(env, installer.clean_environment(self.cfg))
        for actual in (env, build_env):
            self.assertEqual(actual['MAMBA_NO_RC'], 'true')
            for key in set(poison) - {'MAMBA_NO_RC'}:
                self.assertNotIn(key, actual)
        self.assertTrue(all(probe_env == env for _, probe_env, _ in self.probes))

    def test_failing_mamba_config_probe_leaves_both_roots_absent(self):
        def fail_config(argv, env, cwd):
            if argv[-2:] == ['config', 'list']:
                raise subprocess.CalledProcessError(1, argv, output=b'Incompatible configuration')
            return self.fake_output(argv, env, cwd)
        with patch.object(installer.platform, 'system', return_value='Linux'), \
             patch.object(installer.platform, 'machine', return_value='x86_64'), \
             patch.object(installer, 'output', side_effect=fail_config), \
             patch.object(installer, 'source_files') as sources, \
             patch.object(installer.subprocess, 'run') as stages:
            with self.assertRaisesRegex(ValueError, 'Mamba config preflight.*Incompatible configuration'):
                installer.install(self.config)
        sources.assert_not_called()
        stages.assert_not_called()
        self.assertFalse(Path(self.cfg['install_root']).exists())
        self.assertFalse(Path(self.cfg['module_root']).exists())

    def test_existing_release_or_module_refused_without_writes(self):
        for key in ('install_root', 'module_root'):
            with self.subTest(key=key):
                dest = Path(self.cfg[key])
                dest.mkdir()
                with self.assertRaisesRegex(ValueError, 'fresh nonexistent'):
                    self.preflight()
                dest.rmdir()

    def test_overlap_protection(self):
        original = dict(self.cfg)
        cases = [('module_root', self.cfg['install_root'] + '/modules'),
                 ('install_root', str(self.repo / 'child')),
                 ('install_root', str(self.site / 'child')),
                 ('install_root', str(self.base)),
                 ('module_root', str(self.config / 'child'))]
        for key, value in cases:
            with self.subTest(value=value):
                self.cfg = {**original, key: value}
                self.write_config()
                with self.assertRaises(ValueError):
                    self.preflight()
        self.cfg = original
        runtime = self.base / 'old runtime'
        runtime.mkdir()
        (runtime / 'conda-meta').mkdir()
        self.cfg['install_root'] = str(runtime / 'new')
        self.write_config()
        with self.assertRaisesRegex(ValueError, 'existing runtime'):
            self.preflight()

    def test_prerequisites_hash_version_platform_missing_executable(self):
        original = json.loads(json.dumps(self.cfg))
        for mutation, error in ((lambda: self.cfg['site']['mamba'].update(sha256='0' * 64), 'SHA256'),
                                (lambda: self.cfg['site']['python'].update(executable=str(self.site / 'missing')), 'missing executable')):
            self.cfg = json.loads(json.dumps(original))
            mutation()
            self.write_config()
            with self.assertRaisesRegex(ValueError, error):
                self.preflight()
        self.cfg = original
        self.write_config()
        with patch.object(installer.platform, 'system', return_value='Darwin'):
            with self.assertRaisesRegex(ValueError, 'Linux x86_64'):
                installer.preflight(self.config)
        with patch.object(installer.platform, 'system', return_value='Linux'), \
             patch.object(installer.platform, 'machine', return_value='x86_64'), \
             patch.object(installer, 'output', return_value=b'wrong version'):
            with self.assertRaisesRegex(ValueError, 'version mismatch'):
                installer.preflight(self.config)

    def test_canonical_paths_and_symlinks_refused(self):
        for value in (str(self.base / 'a/../b'), str(self.base) + '//b', 'relative', '/REQUIRED/path'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                installer.absolute(value)
        alias = self.base / 'alias'
        alias.symlink_to(self.repo, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            installer.absolute(str(alias / 'new'))

    def test_full_plan_literal_argv_and_isolation(self):
        self.addCleanup(self.restore_modes)
        with patch.dict(os.environ, {'HOME': '/old-account', 'PYTHONPATH': '/old-runtime',
                                    'SINGULARITY_BIND': '/private', 'TOKEN': 'secret'}):
            state = self.build()
        self.assertEqual(state['status'], 'installed-runtime-probed')
        names = [s['name'] for s in state['stages']]
        self.assertEqual(names[-2:], ['assemble', 'inventory'])
        self.assertTrue(all(s['status'] == 'passed' for s in state['stages']))
        commands = {s['name']: s['argv'] for s in state['stages']}
        root = Path(self.cfg['install_root'])
        self.assertEqual(commands['scanpy-base-create'], [str(self.site / 'mamba'), 'create', '--yes', '--prefix',
            str(root / 'runtimes/scanpy-base'), '--channel', 'conda-forge', '--override-channels', 'python=3.12.12', 'pip=25.0.1'])
        self.assertEqual(commands['scanpy-venv-install'], [str(root / 'runtimes/scanpy-base/bin/python'), '-B',
            str(root / 'source/onboarding/tutorials/scanpy/setup_runtime.py'), '--prefix', str(root / 'runtimes/scanpy-venv')])
        self.assertIn(str(root / 'source/onboarding/tutorials/adaptive-screen/requirements.txt'), commands['adaptive-pip'])
        self.assertIn(str(root / 'runtimes/cellprofiler/cellprofiler-4.2.8.sif'), commands['cellprofiler-install'])
        env = installer.clean_environment(self.cfg, root)
        self.assertEqual(env['HOME'], str(root / 'work/home'))
        for key in ('PYTHONPATH', 'TOKEN', 'SINGULARITY_BIND'):
            self.assertNotIn(key, env)
        assembly = json.loads((root / 'provenance/umbrella-config.json').read_text())
        self.assertEqual(assembly['scanpy']['runtime_prefix'], str(root / 'runtimes/scanpy-venv'))
        for tool in ('myotally', 'imagej', 'cellprofiler', 'scanpy', 'adaptive_screen'):
            for key, value in assembly[tool].items():
                if key != 'runtime':
                    self.assertTrue(Path(value).is_relative_to(root), (tool, key, value))
        self.assertEqual(installer.verify_sources(root / 'source', self.files),
                         {k: hashlib.sha256(v).hexdigest() for k, v in self.files.items()})
        audit = json.loads((root / 'provenance/installed-path-audit.json').read_text())
        self.assertEqual(audit['status'], 'installed-path-audit-passed')
        self.assertIn(str(root / 'runtimes/scanpy-base/bin'), audit['checked_paths'])
        self.assertIn('installed_path_audit_sha256', state)

    def test_post_assembly_refuses_external_checkout_and_old_venv_base(self):
        self.addCleanup(self.restore_modes)
        self.build()
        root = Path(self.cfg['install_root'])
        provenance = root / 'umbrella/provenance'
        selected = json.loads((provenance / 'config.json').read_text())
        original = json.loads((provenance / 'inventory.json').read_text())
        for value, diagnostic in ((str(self.base / 'previous validation/bin/python'), 'outside fresh tree'),
                                  (str(self.repo / 'private helper.py'), 'source checkout')):
            with self.subTest(value=value):
                changed = {**original, 'executables': [value]}
                installer.dump(provenance / 'inventory.json', changed)
                with self.assertRaisesRegex(ValueError, diagnostic):
                    installer.audit_installed_paths(self.cfg, selected)
        installer.dump(provenance / 'inventory.json', original)
        venv = root / 'runtimes/scanpy-venv'
        # Even a declared site prefix must not replace the newly built Scanpy base.
        (venv / 'pyvenv.cfg').write_text('home = ' + str(self.site / 'bin') + '\n')
        with self.assertRaisesRegex(ValueError, 'freshly built base Python'):
            installer.audit_installed_paths(self.cfg, selected)
        (venv / 'pyvenv.cfg').write_text('home = ' + str(venv.parent / 'scanpy-base/bin') + '\n')
        base = root / 'runtimes/scanpy-base/bin'
        base.mkdir(parents=True)
        (base / 'python').symlink_to(self.site / 'python')
        with self.assertRaisesRegex(ValueError, 'outside fresh tree'):
            installer.audit_installed_paths(self.cfg, selected)

    def test_failure_preserves_receipt_and_never_assembles_or_retries(self):
        def fail(command, **kwargs):
            if 'create' in command:
                self.executed.append(command)
                raise subprocess.CalledProcessError(7, command)
            return self.fake_run(command, **kwargs)
        with self.assertRaises(subprocess.CalledProcessError):
            self.build(fail)
        state = json.loads((Path(self.cfg['install_root']) / 'provenance/install.json').read_text())
        self.assertEqual(state['status'], 'failed')
        self.assertEqual(state['stages'][-1]['status'], 'failed')
        self.assertEqual(state['stages'][-1]['returncode'], 7)
        self.assertEqual(sum('create' in c for c in self.executed), 1)
        self.assertFalse(any('assemble.py' in ' '.join(c) for c in self.executed))
        self.assertFalse(Path(self.cfg['module_root']).exists())
        self.assertTrue(Path(state['stages'][-1]['log']).is_file())

    def test_changed_source_refuses_before_assembly(self):
        def mutate(command, **kwargs):
            if 'cellprofiler-probe' not in str(command) and '4.2.8 import passed' in ' '.join(command):
                p = Path(self.cfg['install_root']) / 'source/onboarding/tutorials/imagej/tutorial.py'
                p.chmod(0o644)
                p.write_text('# drift\n')
            return self.fake_run(command, **kwargs)
        with self.assertRaisesRegex(ValueError, 'source inventory/bytes'):
            self.build(mutate)
        self.assertFalse(any('assemble.py' in ' '.join(c) for c in self.executed))

    def test_git_object_export_complete_and_selected_installer_bytes(self):
        # Git reads are doubled; assert each tracked blob (including non-Python helper) is retained.
        files = {**self.files, **{'onboarding/' + p: b'content' for p in (
            'scripts/bootstrap.py', 'environment.yml', 'wagers.py', 'tutorials/scanpy/setup_runtime.py',
            'tutorials/scanpy/requirements.lock', 'tutorials/adaptive-screen/requirements.txt',
            'tutorials/imagej/runtime-lock.json', 'tutorials/cellprofiler/runner.py',
            'deploy/umbrella/assemble.py', 'deploy/umbrella/launcher.py', 'tutorials/imagej/ImageJMeasure.java')}}
        blobs = {str(i).encode(): data for i, data in enumerate(files.values())}
        listing = b''.join(b'100644 blob ' + str(i).encode() + b'\t' + name.encode() + b'\0'
                           for i, name in enumerate(files))
        def git(argv, env, cwd):
            self.assertEqual(cwd, self.cfg['source_repository'])
            if 'rev-parse' in argv:
                return (self.cfg['source_commit'] + '\n').encode()
            if 'ls-tree' in argv:
                return listing
            return blobs[argv[-1].encode()]
        with patch.object(installer, 'output', side_effect=git):
            self.assertEqual(installer.source_files(self.cfg, {}), files)
            blobs[b'0'] = b'changed installer'
            with self.assertRaisesRegex(ValueError, 'selected source_commit'):
                installer.source_files(self.cfg, {})


if __name__ == '__main__':
    unittest.main()
