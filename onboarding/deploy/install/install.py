#!/usr/bin/env python3
"""Build five isolated runtimes at fresh final paths, then assemble one module."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

sys.dont_write_bytecode = True
SCHEMA = {'schema_version', 'source_repository', 'source_commit', 'install_root',
          'module_root', 'module_name', 'python_module', 'site', 'system_path'}
CAPABILITIES = {'python', 'mamba', 'singularity', 'git', 'curl'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def absolute(value, executable=False):
    require(isinstance(value, str) and value and value.isascii()
            and all(32 <= ord(c) < 127 for c in value), 'paths must be printable ASCII')
    require(not re.search(r'REQUIRED|PLACEHOLDER|CHANGE_ME|[<>${}~]', value, re.I),
            'fill concrete absolute paths; unresolved placeholder')
    p = Path(value)
    require(p.is_absolute() and '..' not in p.parts, 'absolute path without parent traversal required')
    require(not any(x.is_symlink() for x in (p.parents if executable else (p, *p.parents))),
            'symlink directories are forbidden; use physical canonical paths')
    require(str(p) == value, 'use canonical path spelling')
    return p


def overlap(a, b):
    return a == b or a in b.parents or b in a.parents


def clean_environment(cfg, root=None):
    # Do not inherit account credentials, Python/Conda configuration, old installs,
    # container bind variables, or user caches. Site capabilities must work here.
    dirs = [str(Path(cfg['site'][key]['executable']).parent) for key in ('mamba', 'python', 'singularity', 'git', 'curl')]
    env = {'PATH': os.pathsep.join(dict.fromkeys(dirs + cfg['system_path'])),
           'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'HOME': '/nonexistent',
           'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1',
           'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'NUMBA_NUM_THREADS': '1',
           'MPLBACKEND': 'Agg', 'MAMBA_NO_RC': 'true'}
    if root is not None:
        for key, relative in {
            'HOME': 'work/home', 'TMPDIR': 'work/tmp', 'XDG_CACHE_HOME': 'work/cache',
            'CONDA_PKGS_DIRS': 'work/conda-pkgs', 'MAMBA_ROOT_PREFIX': 'work/mamba',
            'PIP_CACHE_DIR': 'work/pip', 'MPLCONFIGDIR': 'work/matplotlib',
            'NUMBA_CACHE_DIR': 'work/numba', 'SINGULARITY_CACHEDIR': 'work/sif-cache',
            'SINGULARITY_TMPDIR': 'work/sif-tmp', 'APPTAINER_CACHEDIR': 'work/sif-cache',
            'APPTAINER_TMPDIR': 'work/sif-tmp',
        }.items():
            env[key] = str(root / relative)
    return env


def output(command, env, cwd):
    return subprocess.check_output([str(x) for x in command], env=env, cwd=cwd,
                                   stderr=subprocess.STDOUT)


def source_files(cfg, env):
    """Read Git objects, never a partial package/worktree or an installed runtime."""
    git = cfg['site']['git']['executable']
    repo = cfg['source_repository']
    commit = cfg['source_commit']
    resolved = output([git, 'rev-parse', '--verify', commit + '^{commit}'], env, repo).decode().strip()
    require(resolved == commit, 'source_commit must be a full exact commit ID')
    listing = output([git, 'ls-tree', '-r', '-z', commit, '--', 'onboarding/'], env, repo)
    files = {}
    for entry in listing.split(b'\0'):
        if not entry:
            continue
        meta, name = entry.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        relative = name.decode('utf-8')
        parts = PurePosixPath(relative).parts
        require(parts[0] == 'onboarding' and '..' not in parts
                and not any(p in ('.runtime', 'runs', '__pycache__', '.git') for p in parts),
                'source commit contains runtime/cache or invalid path: ' + relative)
        require(mode in ('100644', '100755') and kind == 'blob',
                'source must contain regular tracked files, not links/submodules: ' + relative)
        files[relative] = output([git, 'cat-file', 'blob', oid], env, repo)
    required = ('scripts/bootstrap.py', 'environment.yml', 'wagers.py',
                'tutorials/scanpy/setup_runtime.py', 'tutorials/scanpy/requirements.lock',
                'tutorials/adaptive-screen/requirements.txt', 'tutorials/imagej/runtime-lock.json',
                'tutorials/cellprofiler/runner.py', 'deploy/umbrella/assemble.py',
                'deploy/umbrella/launcher.py', 'deploy/install/check_runtime.py')
    require(all('onboarding/' + p in files for p in required), 'source commit lacks complete installer/package tree')
    # The invoked installer and probes must be the selected reviewed bytes too.
    for name in ('install.py', 'check_runtime.py'):
        key = 'onboarding/deploy/install/' + name
        require(key in files and files[key] == Path(__file__).with_name(name).read_bytes(),
                'run installer/probe bytes from the selected source_commit')
    return files


def preflight(config_path):
    config = absolute(str(config_path))
    cfg = json.loads(config.read_text())
    require(isinstance(cfg, dict) and set(cfg) == SCHEMA and cfg['schema_version'] == 1,
            'unknown/missing config fields or schema')
    require(platform.system() == 'Linux' and platform.machine() == 'x86_64',
            'installation requires Linux x86_64 compute; no scheduler is submitted')
    require(re.fullmatch(r'[a-f0-9]{40}', cfg['source_commit']) is not None, 'full source_commit required')
    for key in ('module_name', 'python_module'):
        require(isinstance(cfg[key], str) and re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9][A-Za-z0-9_.+-]*', cfg[key])
                and not re.search('REQUIRED|PLACEHOLDER|CHANGE_ME', cfg[key], re.I),
                key + ' requires an explicit name/version')
    require(cfg['module_name'].split('/')[0] != cfg['python_module'].split('/')[0], 'module names collide')
    paths = {k: absolute(cfg[k]) for k in ('source_repository', 'install_root', 'module_root')}
    require(paths['source_repository'].is_dir(), 'source_repository missing')
    require(not config.is_relative_to(paths['source_repository'])
            and not config.is_relative_to(Path(__file__).resolve().parents[3]),
            'keep private config outside the source repositories')
    require(isinstance(cfg['site'], dict) and set(cfg['site']) == CAPABILITIES, 'five exact site capabilities required')
    protected = [config, paths['source_repository'], Path(__file__).resolve().parents[3]]
    for key, tool in cfg['site'].items():
        require(isinstance(tool, dict) and set(tool) == {'prefix', 'executable', 'sha256', 'version'},
                'site capability requires prefix/executable/sha256/version: ' + key)
        prefix, exe = absolute(tool['prefix']), absolute(tool['executable'], True)
        require(prefix.is_dir() and exe.is_file() and os.access(exe, os.X_OK), 'missing executable: ' + str(exe))
        require(exe.is_relative_to(prefix) and exe.resolve().is_relative_to(prefix), 'executable outside declared prefix')
        require(isinstance(tool['sha256'], str) and re.fullmatch('[a-f0-9]{64}', tool['sha256'])
                and sha(exe) == tool['sha256'], 'site executable SHA256 mismatch: ' + key)
        require(isinstance(tool['version'], str) and tool['version'].strip(), 'exact version output required: ' + key)
        protected.extend((prefix, exe.resolve()))
    require(Path(cfg['site']['mamba']['executable']).name == 'mamba', 'Myotally bootstrap requires executable named mamba')
    require(isinstance(cfg['system_path'], list) and cfg['system_path'], 'explicit system_path directories required')
    for value in cfg['system_path']:
        p = absolute(value)
        require(p.is_dir(), 'system_path directory missing: ' + value)
        protected.append(p)
    roots = [paths[k] for k in ('install_root', 'module_root')]
    require(not overlap(*roots), 'install/module overlap')
    for dest in roots:
        require(not dest.exists(), 'fresh nonexistent install_root AND module_root required; never overwrite')
        require(not any(overlap(dest, p) for p in protected), 'destination overlaps source/config/site software')
        require(not any((p / 'conda-meta').exists() or (p / 'pyvenv.cfg').exists() for p in dest.parents),
                'destination is inside an existing runtime')
    env = clean_environment(cfg)
    require(shutil.which('mamba', path=env['PATH']) == cfg['site']['mamba']['executable'], 'ambiguous mamba PATH selection')
    require(shutil.which('curl', path=env['PATH']) == cfg['site']['curl']['executable'], 'ambiguous curl PATH selection')
    versions = {}
    for key, tool in cfg['site'].items():
        versions[key] = output([tool['executable'], '--version'], env, paths['source_repository']).decode().strip()
        require(versions[key] == tool['version'], 'site version mismatch: ' + key)
    # --version does not load Mamba's configuration. Check the same sanitized
    # environment used for builds; no_rc must not be paired with CONDARC.
    try:
        output([cfg['site']['mamba']['executable'], 'config', 'list'], env, paths['source_repository'])
    except subprocess.CalledProcessError as exc:
        detail = (exc.output or b'').decode(errors='replace').strip()
        raise ValueError('Mamba config preflight failed before destination creation: ' + detail) from exc
    python = cfg['site']['python']['executable']
    probe = json.loads(output([python, '-I', '-B', '-c',
        'import json,sys,ssl,venv,tarfile; print(json.dumps(list(sys.version_info[:3])))'],
        env, paths['source_repository']))
    require(tuple(probe) >= (3, 12, 0), 'host Python 3.12+ with ssl/venv/tarfile required')
    files = source_files(cfg, env)
    return cfg, files, versions


def verify_sources(snapshot, files):
    expected = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    actual = {}
    for path in snapshot.rglob('*'):
        relative = path.relative_to(snapshot).as_posix()
        # The one reviewed package intentionally installs its runtime beside its sources.
        if relative.startswith('onboarding/tutorials/imagej/.runtime/') or relative == 'onboarding/tutorials/imagej/.runtime':
            continue
        require(not path.is_symlink(), 'unexpected source symlink: ' + relative)
        if path.is_file():
            actual[relative] = sha(path)
    require(actual == expected, 'source inventory/bytes changed; refuse module assembly')
    return expected


def audit_installed_paths(cfg, expected):
    """Check the assembled selections/inventory, including the venv's actual base."""
    root = Path(cfg['install_root'])
    provenance = root / 'umbrella/provenance'
    installed = json.loads((provenance / 'config.json').read_text())
    require(installed == expected, 'assembled runtime selections differ from installer config')
    inventory = json.loads((provenance / 'inventory.json').read_text())
    site = [Path(tool['prefix']) for tool in cfg['site'].values()]
    modules = Path(cfg['module_root'])
    repository = Path(cfg['source_repository'])

    def check(value, allowed):
        path = absolute(value, executable=True)
        for selected in (path, path.resolve()):
            require(not selected.is_relative_to(repository),
                    'installed path depends on source checkout: ' + value)
            require(any(selected.is_relative_to(base) for base in allowed),
                    'installed path outside fresh tree/declared prerequisites: ' + value)

    # Package sources, runtimes, receipts and venv base must be freshly built,
    # even when an existing installation happens to sit below a site prefix.
    internal = [installed['release_prefix']]
    for tool in ('myotally', 'imagej', 'cellprofiler', 'scanpy', 'adaptive_screen'):
        internal.extend(value for key, value in installed[tool].items()
                        if not (tool == 'cellprofiler' and key == 'runtime'))
    for value in internal:
        check(value, [root])
    for value in (root / 'runtimes/myotally/env/bin/python',
                  root / 'runtimes/adaptive/bin/python', root / 'runtimes/scanpy-base/bin/python'):
        check(str(value), [root])
    venv = root / 'runtimes/scanpy-venv'
    homes = [line.partition('=')[2].strip() for line in (venv / 'pyvenv.cfg').read_text().splitlines()
             if line.partition('=')[0].strip().lower() == 'home']
    require(homes == [str(root / 'runtimes/scanpy-base/bin')],
            'Scanpy venv must use the freshly built base Python')
    check(homes[0], [root])
    check(str(venv / 'bin/python'), [root])
    paths = set(inventory['files']) | set(inventory['executables']) | set(inventory['protected'])
    paths.update(tool['executable'] for tool in cfg['site'].values())
    for value in sorted(paths):
        check(value, [root, modules, *site])
    receipt = {'status': 'installed-path-audit-passed', 'checked_paths': sorted(paths | set(internal) | set(homes)),
               'allowed_roots': sorted({str(root), str(modules), *map(str, site)}),
               'assembled_config_sha256': sha(provenance / 'config.json'),
               'inventory_sha256': sha(provenance / 'inventory.json'),
               'scope': 'Selected source/runtime/base and inventoried paths; not dynamic-library dependency closure'}
    dump(root / 'provenance/installed-path-audit.json', receipt)
    return receipt


class Build:
    def __init__(self, cfg, files, versions, config_path):
        self.cfg, self.files = cfg, files
        self.root = Path(cfg['install_root'])
        self.env = clean_environment(cfg, self.root)
        self.state = {'status': 'building', 'source_commit': cfg['source_commit'], 'site_versions': versions,
                      'stages': [], 'scope': 'installation/import probes only; full suites, Lmod and user access pending'}
        self.config_path = config_path

    def save(self):
        dump(self.root / 'provenance/install.json', self.state)

    def run(self, name, command):
        command = [str(x) for x in command]
        log = self.root / 'provenance' / (name + '.log')
        stage = {'name': name, 'argv': command, 'status': 'running', 'log': str(log)}
        self.state['stages'].append(stage)
        self.save()
        try:
            with log.open('x') as stream:
                stream.write('argv=' + json.dumps(command) + '\n')
                stream.flush()
                result = subprocess.run(command, cwd=self.root, env=self.env, stdout=stream,
                                        stderr=subprocess.STDOUT, check=True)
            stage.update(status='passed', returncode=result.returncode, log_sha256=sha(log))
        except Exception as exc:
            stage.update(status='failed', error=str(exc), returncode=getattr(exc, 'returncode', None))
            raise
        finally:
            self.save()

    def build(self):
        cfg, root = self.cfg, self.root
        root.mkdir(parents=True, mode=0o700)
        (root / 'provenance').mkdir()
        self.save()
        try:
            dump(root / 'provenance/config.json', cfg)
            self.state['config_sha256'] = sha(self.config_path)
            for value in set(self.env.values()):
                if value.startswith(str(root) + '/work/'):
                    Path(value).mkdir(parents=True, exist_ok=True, mode=0o700)
            snapshot = root / 'source'
            for name, data in self.files.items():
                target = snapshot / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as stream:
                    stream.write(data)
                target.chmod(0o444)
            manifest = verify_sources(snapshot, self.files)
            dump(root / 'provenance/source-sha256.json', manifest)
            source = snapshot / 'onboarding'
            host = cfg['site']['python']['executable']
            mamba = cfg['site']['mamba']['executable']
            singularity = cfg['site']['singularity']['executable']
            probe = source / 'deploy/install/check_runtime.py'
            runtimes = root / 'runtimes'
            runtimes.mkdir()
            def py(exe, *args):
                return [exe, '-B', *args]
            def conda(name, prefix):
                self.run(name, [mamba, 'create', '--yes', '--prefix', prefix, '--channel', 'conda-forge',
                                '--override-channels', 'python=3.12.12', 'pip=25.0.1'])
            def records(name, prefix):
                self.run(name + '-explicit', [mamba, 'list', '--prefix', prefix, '--explicit'])
                self.run(name + '-resolved', [mamba, 'env', 'export', '--prefix', prefix])
            myo = runtimes / 'myotally'
            bootstrap_config = root / 'provenance/myotally-config.json'
            dump(bootstrap_config, {'release_prefix': str(myo), 'module_root': str(root / 'internal-modules'),
                                    'module_name': 'wagers-myotally/1.0.2-env001', 'python_module': 'python'})
            self.run('myotally-bootstrap', py(host, source / 'scripts/bootstrap.py', '--config', bootstrap_config))
            self.run('myotally-probe', py(myo / 'env/bin/python', probe, 'myotally'))
            base, scan = runtimes / 'scanpy-base', runtimes / 'scanpy-venv'
            conda('scanpy-base-create', base)
            self.run('scanpy-base-probe', py(base / 'bin/python', probe, 'base'))
            records('scanpy-base', base)
            self.run('scanpy-venv-install', py(base / 'bin/python', source / 'tutorials/scanpy/setup_runtime.py', '--prefix', scan))
            self.run('scanpy-probe', py(scan / 'bin/python', probe, 'scanpy', source / 'tutorials/scanpy/requirements.lock'))
            adaptive = runtimes / 'adaptive'
            conda('adaptive-create', adaptive)
            recipe = source / 'tutorials/adaptive-screen/requirements.txt'
            receipt = root / 'provenance/adaptive-install-report.json'
            self.run('adaptive-pip', py(adaptive / 'bin/python', '-m', 'pip', '--isolated', 'install',
                '--disable-pip-version-check', '--no-cache-dir', '--index-url', 'https://pypi.org/simple',
                '--only-binary=:all:', '--report', receipt, '-r', recipe))
            self.run('adaptive-pip-check', py(adaptive / 'bin/python', '-m', 'pip', '--isolated', 'check'))
            self.run('adaptive-probe', py(adaptive / 'bin/python', probe, 'adaptive', recipe))
            records('adaptive', adaptive)
            imagej = source / 'tutorials/imagej'
            self.run('imagej-install', py(host, imagej / 'tutorial.py', 'install'))
            java = imagej / '.runtime/jdk-21.0.8+9/bin/java'
            self.run('imagej-probe', [java, '-version'])
            cp = source / 'tutorials/cellprofiler'
            sif = runtimes / 'cellprofiler/cellprofiler-4.2.8.sif'
            self.run('cellprofiler-install', py(host, cp / 'runner.py', 'install', '--runtime', singularity, '--sif', sif))
            self.run('cellprofiler-probe', [singularity, 'exec', '--cleanenv', '--containall', '--no-home',
                sif, '/opt/venv/bin/python', '-B', '-c',
                "import importlib.metadata as m; import cellprofiler.modules.identifyprimaryobjects; "
                "assert m.version('cellprofiler') == m.version('cellprofiler-core') == '4.2.8'; print('4.2.8 import passed')"])
            verify_sources(snapshot, self.files)
            for path in sorted(snapshot.rglob('*'), reverse=True):
                if path.is_dir() and '.runtime' not in path.relative_to(snapshot).parts:
                    path.chmod(0o555)
            snapshot.chmod(0o555)
            umbrella = {'schema_version': 1, 'release_prefix': str(root / 'umbrella'),
                'module_root': cfg['module_root'], 'module_name': cfg['module_name'],
                'python_module': cfg['python_module'], 'host_prefix': cfg['site']['python']['prefix'], 'host_python': host,
                'myotally': {'prefix': str(myo)}, 'imagej': {'source': str(imagej)},
                'cellprofiler': {'source': str(cp), 'sif': str(sif), 'runtime': singularity},
                'scanpy': {'source': str(source / 'tutorials/scanpy'), 'runtime_prefix': str(scan)},
                'adaptive_screen': {'source': str(source / 'tutorials/adaptive-screen'),
                                    'runtime_prefix': str(adaptive), 'receipt': str(receipt)}}
            assembly_config = root / 'provenance/umbrella-config.json'
            dump(assembly_config, umbrella)
            self.run('assemble', py(host, source / 'deploy/umbrella/assemble.py', '--config', assembly_config))
            self.run('inventory', [root / 'umbrella/bin/wagers-doctor', '--json'])
            audit_installed_paths(cfg, umbrella)
            self.state['installed_path_audit_sha256'] = sha(root / 'provenance/installed-path-audit.json')
            verify_sources(snapshot, self.files)
            self.state.update(status='installed-runtime-probed', module_root=cfg['module_root'], module_name=cfg['module_name'])
        except BaseException as exc:
            self.state.update(status='failed', error=str(exc), failed_type=type(exc).__name__)
            raise
        finally:
            self.state['finished_utc'] = datetime.now(timezone.utc).isoformat()
            self.save()
        return self.state


def install(config_path):
    cfg, files, versions = preflight(config_path)
    return Build(cfg, files, versions, config_path).build()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.config), indent=2))
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print('INSTALL FAILED (preserve started destinations; choose fresh paths): ' + str(exc), file=sys.stderr)
        sys.exit(2)
