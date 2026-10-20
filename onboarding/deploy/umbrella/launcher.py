"""Read-only guards and argv routing; copied into each umbrella release.

Never imports a tutorial or invokes an installer. Filesystem inspection is not
package execution, version verification of an interpreter, or biological validation.
"""
import ast
from email.parser import Parser
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import sys

CP_DIGEST = 'sha256:fec440caa2b44edf80f9bd440a3d8c6b214d72437332ad2586a32d79e2eae2a4'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def overlap(a, b):
    return a == b or a in b.parents or b in a.parents


def conda_json(text):
    """Reject ambiguous keys and nonfinite numbers, including exponent overflow."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate Conda metadata key')
            result[key] = value
        return result

    def finite(value):
        number = float(value)
        require(math.isfinite(number), 'nonfinite Conda metadata number')
        return number

    return json.loads(text, object_pairs_hook=unique, parse_float=finite, parse_constant=finite)


def absolute(value, executable=False):
    require(isinstance(value, str) and value and value.isascii()
            and all(32 <= ord(c) < 127 for c in value), 'paths must be printable ASCII')
    require(not re.search(r'REQUIRED|PLACEHOLDER|CHANGE_ME|[<>${}~]', value, re.I),
            'unresolved placeholder in path')
    path = Path(value)
    require(path.is_absolute(), 'absolute concrete path required')
    # Venv Python is commonly a final symlink. Its resolved base is protected too.
    links = path.parents if executable else [path, *path.parents]
    require(not any(p.is_symlink() for p in links), 'symlink directory/path forbidden')
    require('..' not in path.parts, 'parent traversal forbidden')
    return path


def inspect(cfg):
    """Check installed assets without running any configured executable."""
    files = set()
    executables = set()
    protected = [absolute(cfg[k]) for k in ('release_prefix', 'module_root', 'host_prefix')]

    def file(path, executable=False):
        path = absolute(str(path), executable=executable)
        require(path.is_file(), f'required file missing: {path}')
        if executable:
            require(os.access(path, os.X_OK), f'executable required: {path}')
            executables.add(str(path))
            protected.append(path.resolve().parent)
        files.add(str(path))
        return path

    def source(key, names):
        root = absolute(cfg[key]['source'])
        require(root.is_dir(), f'source directory missing: {root}')
        protected.append(root)
        for name in names:
            file(root / name)
        # Record all sibling Python sources, including helpers imported by CLI.
        for path in root.glob('*.py'):
            file(path)
        return root

    def venv(key, version):
        root = absolute(cfg[key]['runtime_prefix'])
        protected.append(root)
        text = file(root / 'pyvenv.cfg').read_text()
        found = re.search(r'^version\s*=\s*(\S+)', text, re.M)
        require(found and (found[1] == version if version.count('.') == 2
                          else found[1].startswith(version + '.')), f'{key}: wrong venv Python version')
        values = {}
        for line in text.splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            name, equal, value = line.partition('=')
            name = name.strip().lower()
            require(equal and name and name not in values, f'{key}: malformed/ambiguous venv metadata')
            values[name] = value.strip()
        require('home' in values, f'{key}: missing venv home')
        home = absolute(values['home'])
        require(home.name == 'bin' and home.is_dir() and home.parent != Path(home.anchor),
                f'{key}: invalid venv home (existing base bin directory required)')
        # Copies do not reveal their base through bin/python.resolve(). Protect
        # the entire prefix declared by home, including its libraries, instead.
        base = home.resolve().parent
        base_python = file(home / ('python' + '.'.join(version.split('.')[:2])), True)
        require(base_python.resolve().is_relative_to(base), f'{key}: venv home interpreter outside base prefix')
        protected.append(base)
        python = file(root / 'bin/python', True)
        require(not python.is_symlink() or python.resolve().is_relative_to(base),
                f'{key}: venv Python symlink contradicts home')
        return root

    def adaptive_runtime():
        root = absolute(cfg['adaptive_screen']['runtime_prefix'])
        meta = root / 'conda-meta'
        if not (meta.exists() or meta.is_symlink()):
            return venv('adaptive_screen', '3.12.12')
        # Do not guess which layout wins or accept history alone as a Python pin.
        marker = root / 'pyvenv.cfg'
        require(not (marker.exists() or marker.is_symlink()), 'ambiguous adaptive venv/Conda layout')
        meta = absolute(str(meta))
        require(meta.is_dir(), 'adaptive Conda metadata directory missing')
        protected.append(root)
        file(meta / 'history')
        versions = []
        for path in sorted(meta.glob('*.json')):
            data = conda_json(file(path).read_text())
            require(isinstance(data, dict) and all(isinstance(data.get(k), str) and data[k]
                    for k in ('name', 'version', 'build')), 'malformed Conda package identity')
            require(path.name == f"{data['name']}-{data['version']}-{data['build']}.json",
                    'contradictory Conda filename/package identity')
            if data['name'] == 'python':
                versions.append(data['version'])
        require(len(versions) == 1, 'adaptive Conda requires exactly one Python record')
        require(versions[0] == '3.12.12', 'adaptive Conda requires Python 3.12.12')
        file(root / 'bin/python', True)
        return root

    def metadata(root, requirements):
        found = {}
        for path in (root / 'lib/python3.12/site-packages').glob('*.dist-info/METADATA'):
            data = Parser().parsestr(file(path).read_text())
            found[re.sub(r'[-_.]+', '-', data['Name']).lower()] = data['Version']
        for line in requirements.read_text().splitlines():
            if line and not line.startswith('#'):
                name, version = line.split('==')
                require(found.get(re.sub(r'[-_.]+', '-', name).lower()) == version,
                        f'missing/mismatched installed distribution metadata: {name}')

    host = file(absolute(cfg['host_python'], executable=True), True)
    require(host.is_relative_to(Path(cfg['host_prefix'])), 'host Python outside host_prefix')
    myo = absolute(cfg['myotally']['prefix'])
    protected.append(myo)
    installed = file(myo / 'bin/wagers-myotally', True)
    # A conservative static gate: -I ignores the bytecode environment variable.
    # Do not silently turn a known unsafe installed launcher into a new runtime.
    require(re.search(r'python\s+(?:-I\s+-B|-B\s+-I)\s', installed.read_text()),
            'Myotally installed launcher must explicitly use python -I -B')
    file(myo / 'provenance/build.json')
    for name in ('wagers.py', 'scripts/tutorial_suite.py', 'scripts/validate_one.py'):
        path = file(myo / 'app' / name)
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.List, ast.Tuple)):
                values = [n.value for n in node.elts if isinstance(n, ast.Constant)]
                require('-I' not in values or '-B' in values,
                        f'Myotally isolated child lacks -B: {path}')
    upstream = myo / 'upstream/source'
    require(upstream.is_dir() and any(upstream.glob('*.py')), 'Myotally upstream source missing')
    for path in upstream.glob('*.py'):
        file(path)
    file(myo / 'env/bin/python', True)
    file(myo / 'env/conda-meta/history')

    ij = source('imagej', ('tutorial.py', 'runtime-lock.json', 'ImageJMeasure.java'))
    lock = json.loads((ij / 'runtime-lock.json').read_text())
    key = platform.system() + '-' + platform.machine()
    spec = lock['jdk'][key]
    runtime = ij / '.runtime'
    require(not (runtime / '.jdk-extracting').exists(), 'ImageJ interrupted JDK extraction')
    jar = file(runtime / 'ij-1.54p.jar')
    archive = file(runtime / 'jdk.tar.gz')
    require(digest(jar) == lock['imagej']['sha256'] and digest(archive) == spec['sha256'],
            'ImageJ archive/JAR pin mismatch')
    home = runtime / spec['java_home']
    require(home.is_relative_to(runtime) and '..' not in home.parts, 'invalid ImageJ java_home')
    marker = file(runtime / Path(spec['java_home']).parts[0] / '.imagej-complete.json')
    require(json.loads(marker.read_text()) == {'archive_sha256': spec['sha256'], 'java_home': spec['java_home']},
            'ImageJ incomplete JDK marker')
    for name in ('bin/java', 'bin/javac', 'release', 'lib/modules'):
        file(home / name, name.startswith('bin/'))
    stamp = file(runtime / 'build.json')
    require(json.loads(stamp.read_text()) == {'source': digest(ij / 'ImageJMeasure.java'), 'jar': digest(jar)},
            'ImageJ stale class stamp (automatic compilation forbidden)')
    file(runtime / 'classes/ImageJMeasure.class')

    source('cellprofiler', ('runner.py', 'cp_measure.py'))
    cp = cfg['cellprofiler']
    sif = file(absolute(cp['sif']))
    protected.append(sif.parent)
    receipt = file(Path(str(sif) + '.json'))
    data = json.loads(receipt.read_text())
    require(data.get('digest') == CP_DIGEST
            and data.get('source') == 'docker://cellprofiler/cellprofiler@' + CP_DIGEST
            and data.get('platform') == 'linux/amd64' and data.get('sif_sha256') == digest(sif),
            'CellProfiler pinned SIF receipt/hash mismatch')
    file(absolute(cp['runtime'], executable=True), True)

    scan = source('scanpy', ('tutorial.py', 'workflow.py', 'requirements.lock'))
    require(all('--runtime-prefix' in (scan / name).read_text() for name in ('tutorial.py', 'workflow.py')),
            'Scanpy requires reviewed explicit --runtime-prefix contract')
    env = venv('scanpy', '3.12')
    metadata(env, scan / 'requirements.lock')
    receipt = file(env / 'install-report.json')
    data = json.loads(receipt.read_text())
    recorded = {re.sub(r'[-_.]+', '-', item['metadata']['name']).lower(): item['metadata']['version']
                for item in data['install']}
    for line in (scan / 'requirements.lock').read_text().splitlines():
        if line and not line.startswith('#'):
            name, version = line.split('==')
            require(recorded.get(re.sub(r'[-_.]+', '-', name).lower()) == version,
                    'Scanpy install receipt disagrees with lock')
    adaptive = source('adaptive_screen', ('tutorial.py', 'contract.py', 'proposer.py', 'simulator.py', 'suite.py', 'requirements.txt'))
    env = adaptive_runtime()
    metadata(env, adaptive / 'requirements.txt')
    file(absolute(cfg['adaptive_screen']['receipt']))
    return {'files': {p: digest(p) for p in sorted(files)}, 'executables': sorted(executables),
            'protected': sorted(set(map(str, protected))),
            'scope': 'Filesystem assets and hashes only; interpreter/package execution, installed pins, Lmod, user access and biology NOT validated.'}


# Exact option names prevent argparse abbreviations from replacing fixed runtimes.
OPTIONS = {
    'myotally': {'--manifest', '--inspect-images', '--quality', '--min-area', '--max-area', '--run-dir',
                '--review', '--output', '--evidence-dir', '--version', '--help'},
    'imagej': {'--input', '--out', '--help'},
    'cellprofiler': {'--dest', '--originals', '--output', '--help'},
    'scanpy': {'--input', '--output', '--help'},
    'adaptive-screen': {'--out', '--seed', '--count', '--candidates', '--outcomes', '--state', '--batch',
                        '--strategy', '--truth', '--adaptive', '--random', '--help'},
}
COMMANDS = {
    'myotally': {'doctor', 'analyze', 'validate-manifest', 'export-review', 'validate-one', 'tutorial-suite'},
    'imagej': {'seal', 'fixtures', 'measure', 'suite'},
    'cellprofiler': {'generate', 'run', 'suite'},
    'scanpy': {'suite', 'run'},
    'adaptive-screen': {'generate', 'init', 'propose', 'import', 'simulate', 'evaluate', 'suite'},
}
OUTPUTS = {'--out', '--output', '--dest', '--run-dir', '--evidence-dir'}


def command(cfg, inventory, tool, args):
    require(tool in COMMANDS, 'unknown launcher')
    require(args and (args[0] in COMMANDS[tool] or args[0] in ('--help', '--version')),
            'choose a documented command; install/fetch/internal commands are unavailable')
    flags = OPTIONS[tool]
    for i, arg in enumerate(args):
        if arg.startswith('--'):
            flag, equal, value = arg.partition('=')
            require(flag in flags, f'unsupported option: {flag} (runtime selection is fixed)')
            if flag in OUTPUTS or (tool == 'imagej' and args[0] == 'seal' and flag == '--input'):
                require(equal or i + 1 < len(args), f'missing value: {flag}')
                out = Path(value if equal else args[i + 1]).expanduser().resolve()
                require(not any(overlap(out, Path(p)) for p in inventory['protected']),
                        'output overlaps shared software/module/runtime')
    python = [cfg['host_python'], '-E', '-s', '-B']
    if tool == 'myotally':
        return [str(Path(cfg['myotally']['prefix']) / 'bin/wagers-myotally'), *args]
    if tool == 'scanpy':
        require(args[0] in ('run', 'suite'), 'Scanpy usage: suite|run --help')
        entry = 'tutorial.py' if args[0] == 'suite' else 'workflow.py'
        return [str(Path(cfg['scanpy']['runtime_prefix']) / 'bin/python'), '-E', '-s', '-B',
                str(Path(cfg['scanpy']['source']) / entry), *args[1:],
                '--runtime-prefix', cfg['scanpy']['runtime_prefix']]
    if tool == 'adaptive-screen':
        return [str(Path(cfg['adaptive_screen']['runtime_prefix']) / 'bin/python'), '-E', '-s', '-B',
                str(Path(cfg['adaptive_screen']['source']) / 'tutorial.py'), *args]
    if tool == 'cellprofiler':
        cp = cfg['cellprofiler']
        extra = ['--sif', cp['sif'], '--runtime', cp['runtime']] if args[0] in ('run', 'suite') else []
        return [*python, str(Path(cp['source']) / 'runner.py'), *args, *extra]
    return [*python, str(Path(cfg['imagej']['source']) / 'tutorial.py'), *args]


def main():
    require(sys.version_info >= (3, 12), 'umbrella host Python requires 3.12+')
    release = Path(__file__).resolve().parents[1]
    cfg = json.loads((release / 'provenance/config.json').read_text())
    saved = json.loads((release / 'provenance/inventory.json').read_text())
    current = inspect(cfg)
    require(current == saved, 'referenced assets changed; use a reviewed new release')
    tool, *args = sys.argv[1:]
    if tool == 'doctor':
        require(args in ([], ['--json']), 'doctor accepts only --json')
        print(json.dumps(current, indent=2))
        return
    argv = command(cfg, current, tool, args)
    env = {k: v for k, v in os.environ.items() if not k.startswith('PYTHON')}
    env.update(PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    os.execve(argv[0], argv, env)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, SyntaxError) as exc:
        print(f'UMBRELLA REFUSED: {exc}', file=sys.stderr)
        sys.exit(2)
