#!/usr/bin/env python3
"""Reviewed-mask ImageJ tutorial. Python orchestrates; ImageJ measures every object."""
import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
import zlib

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / '.runtime'
LOCK = json.loads((ROOT / 'runtime-lock.json').read_text())
IDS = ['study', 'animal', 'muscle', 'section', 'field']
COLUMNS = IDS + ['fiber', 'endpoint', 'mask', 'reviewed', 'regeneration_sample']
SOURCES = ['.gitignore', 'runtime-lock.json', 'ImageJMeasure.java', 'tutorial.py', 'README.md', 'AGENT_PROMPT.md']


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def tree(path):
    return {str(p.relative_to(path)): sha(p) for p in sorted(path.rglob('*')) if p.is_file()}


def write_csv(path, columns, rows):
    with Path(path).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def read_csv(path):
    with Path(path).open(newline='') as f:
        return list(csv.DictReader(f))


def input_directory(path):
    # Refuse symlinks before opening/hashing any input, including root and directory links.
    path = Path(path).absolute()
    require(not any(p.is_symlink() for p in [path, *path.parents]), 'input symlinks rejected before hashing')
    require(path.is_dir(), 'input must be a directory')
    for directory, dirs, files in os.walk(path, followlinks=False):
        require(not any((Path(directory) / n).is_symlink() for n in dirs + files),
                'input symlinks rejected before hashing')
    return path.resolve()


def new_output(input_dir, output):
    inp, out = input_directory(input_dir), Path(output).resolve()
    require(inp != out and inp not in out.parents and out not in inp.parents, 'output/input overlap rejected')
    require(not out.exists(), 'output reuse rejected; choose a new directory')
    out.mkdir(parents=True, exist_ok=False)
    return inp, out


def run(command, log, **kwargs):
    result = subprocess.run([str(x) for x in command], text=True, capture_output=True,
                            timeout=kwargs.pop('timeout', 60), **kwargs)
    with Path(log).open('a') as f:
        f.write(json.dumps([str(x) for x in command]) + '\n' + result.stdout + result.stderr)
    require(result.returncode == 0, f'command failed ({result.returncode}); see {Path(log).name}')
    return result.stdout


def clean_java_env():
    return {k: v for k, v in os.environ.items()
            if k not in ('JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS', 'JDK_JAVA_OPTIONS', 'CLASSPATH')}


def install():
    key = platform.system() + '-' + platform.machine()
    require(key in LOCK['jdk'], 'supported pins: Darwin-arm64 and Linux-x86_64 only')
    spec = LOCK['jdk'][key]
    RUNTIME.mkdir(exist_ok=True)
    log = RUNTIME / 'install.log'
    for path, artifact in [(RUNTIME / 'ij-1.54p.jar', LOCK['imagej']), (RUNTIME / 'jdk.tar.gz', spec)]:
        if not path.exists():
            tmp = path.with_suffix('.download')
            require(not tmp.exists(), 'unfinished download exists; inspect/remove it before retry')
            run(['curl', '-fL', '--retry', '2', '--output', tmp, artifact['url']], log, timeout=300)
            require(sha(tmp) == artifact['sha256'], 'download SHA256 mismatch')
            tmp.rename(path)
        require(sha(path) == artifact['sha256'], f'artifact SHA256 mismatch: {path.name}')
    home = RUNTIME / spec['java_home']
    jdk_root = RUNTIME / Path(spec['java_home']).parts[0]
    staging = RUNTIME / '.jdk-extracting'
    marker = jdk_root / '.imagej-complete.json'
    completion = {'archive_sha256': spec['sha256'], 'java_home': spec['java_home']}
    require(not staging.exists(), 'interrupted JDK extraction detected; inspect task-local .jdk-extracting')
    if jdk_root.exists():
        recorded_completion = None
        if marker.is_file():
            try:
                recorded_completion = json.loads(marker.read_text())
            except ValueError:
                pass
        require(not jdk_root.is_symlink() and recorded_completion == completion,
                'incomplete task-local JDK: missing/invalid completion marker')
    else:
        staging.mkdir()
        # Failure deliberately preserves staging for diagnosis; only a complete tree is published.
        with tarfile.open(RUNTIME / 'jdk.tar.gz') as archive:
            archive.extractall(staging, filter='data')
        staged_home = staging / spec['java_home']
        require(all((staged_home / n).is_file() for n in ('bin/java', 'bin/javac', 'release', 'lib/modules')),
                'incomplete extracted task-local JDK')
        staged_root = staging / jdk_root.name
        dump(staged_root / marker.name, completion)
        staged_root.rename(jdk_root)  # Atomic rename within this task's runtime filesystem.
        staging.rmdir()
    require(all((home / n).is_file() for n in ('bin/java', 'bin/javac', 'release', 'lib/modules')),
            'incomplete task-local JDK')
    return home


def prepare():
    home = install()
    build = RUNTIME / 'classes'
    stamp = RUNTIME / 'build.json'
    expected = {'source': sha(ROOT / 'ImageJMeasure.java'), 'jar': sha(RUNTIME / 'ij-1.54p.jar')}
    if not stamp.exists() or json.loads(stamp.read_text()) != expected or not (build / 'ImageJMeasure.class').exists():
        build.mkdir(exist_ok=True)
        run([home / 'bin/javac', '-cp', RUNTIME / 'ij-1.54p.jar', '-d', build,
             ROOT / 'ImageJMeasure.java'], RUNTIME / 'compile.log', env=clean_java_env())
        dump(stamp, expected)
    return home


def provenance(home, log):
    commit, status, dirty = None, None, None
    origin = 'copied_package_no_git_metadata'
    git_env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    try:
        # An untracked copy inside an unrelated repository is still a copied package.
        tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', '--', *SOURCES], cwd=ROOT,
                                 env=git_env, capture_output=True, text=True, timeout=10)
        if tracked.returncode == 0:
            commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, env=git_env,
                                             stderr=subprocess.DEVNULL, text=True, timeout=10).strip()
            status = subprocess.check_output(['git', 'status', '--porcelain', '--', '.'], cwd=ROOT,
                                             env=git_env, text=True, timeout=10)
            dirty = bool(status.strip())
            origin = 'git_checkout'
    except (FileNotFoundError, subprocess.SubprocessError):
        commit, status, dirty = None, None, None
    return {'tested_commit': commit, 'package_git_status': status, 'package_dirty': dirty,
            'package_origin': origin, 'source_sha256': {n: sha(ROOT / n) for n in SOURCES},
            'platform': platform.system() + '-' + platform.machine(), 'python': platform.python_version(),
            'java': run([home / 'bin/java', '--version'], log, env=clean_java_env()).strip(),
            'java_binary_sha256': sha(home / 'bin/java'), 'class_sha256': sha(RUNTIME / 'classes/ImageJMeasure.class'),
            'artifacts': LOCK, 'headless': True}


def png(path, shapes, width=32, height=24, foreground=255):
    # Original raster fixture generator. Rectangles (x,y,w,h), optional removed rectangle makes an L.
    pixels = bytearray(width * height)
    for shape in shapes:
        x, y, w, h = shape[:4]
        for j in range(y, y + h):
            for i in range(x, x + w):
                pixels[j * width + i] = foreground
        if len(shape) == 8:
            rx, ry, rw, rh = shape[4:]
            for j in range(ry, ry + rh):
                for i in range(rx, rx + rw):
                    pixels[j * width + i] = 0
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    raw = b''.join(b'\0' + pixels[y * width:(y + 1) * width] for y in range(height))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 0, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def seal(path):
    path = input_directory(path)
    files = {n: h for n, h in tree(path).items() if n != 'manifest.json'}
    dump(path / 'manifest.json', {'schema_version': 1, 'sha256': files})


def fixtures(path):
    path = Path(path).resolve()
    require(not path.exists(), 'fixture destination exists')
    path.mkdir(parents=True)
    (path / 'masks').mkdir()
    fields, fibers, rows = [], [], []
    # Fixed truth below is specified arithmetically, not derived by reading pixels or measuring masks.
    groups = [('A1', 'TA', .5, .8, [[2, 1], [1, 4]]),
              ('A1', 'GA', 1., 1., [[1, 0], [2, 2]]),
              ('A2', 'TA', .25, 2., [[2, 1], [1, 0]])]
    for animal, muscle, pw, ph, counts in groups:
        for s in range(2):
            for field, endpoint in [('HF', 'fiber'), ('GF1', 'gfp'), ('GF2', 'gfp')]:
                ids = dict(zip(IDS, ['SYN', animal, muscle, 'S' + str(s + 1), field]))
                fields.append({**ids, 'endpoint': endpoint, 'width': 32, 'height': 24,
                               'pixel_width_um': pw, 'pixel_height_um': ph})
                shapes = ([(2, 2, 4, 3), (12, 2, 3, 3, 13, 3, 2, 2), (22, 2, 2, 5)] if s == 0 else
                          [(2, 2, 4, 4), (12, 2, 3, 2), (22, 2, 6, 5)])
                if endpoint == 'fiber':
                    for i, shape in enumerate(shapes):
                        fiber = 'R' + str(i + 1)
                        fibers.append({**ids, 'fiber': fiber})
                        name = '-'.join(ids.values()) + '-' + fiber + '.png'
                        png(path / 'masks' / name, [shape])
                        # Sample includes R1,R3 in S1; R1,R2 in S2. L and large control are unsampled.
                        sampled = (s == 0 and i in (0, 2)) or (s == 1 and i in (0, 1))
                        rows.append({**ids, 'fiber': fiber, 'endpoint': endpoint, 'mask': 'masks/' + name,
                                     'reviewed': 'true', 'regeneration_sample': str(sampled).lower()})
                else:
                    count = counts[s][int(field[-1]) - 1]
                    name = '-'.join(ids.values()) + '.png'
                    png(path / 'masks' / name, [(2 + i * 6, 14, 2, 2) for i in range(count)])
                    rows.append({**ids, 'fiber': '', 'endpoint': endpoint, 'mask': 'masks/' + name,
                                 'reviewed': 'true', 'regeneration_sample': 'false'})
    dump(path / 'design.json', {'schema_version': 1, 'review': 'synthetic annotations; no human review validated',
                               'fields': fields, 'fibers': fibers})
    write_csv(path / 'regions.csv', COLUMNS, rows)
    dump(path / 'truth.json', {
        'fiber_pixels_by_section': [[12, 5, 10], [16, 6, 30]],
        'sample_pixels_by_section': [[12, 10], [16, 6]],
        'groups': {'A1/TA': {'all_n': 6, 'sample_n': 4, 'sample_mean_um2': 4.4, 'all_mean_um2': 79 / 6 * .4,
                             'section_counts': [3, 5], 'maximum': 5},
                   'A1/GA': {'all_n': 6, 'sample_n': 4, 'sample_mean_um2': 11., 'all_mean_um2': 79 / 6,
                             'section_counts': [1, 4], 'maximum': 4},
                   'A2/TA': {'all_n': 6, 'sample_n': 4, 'sample_mean_um2': 5.5, 'all_mean_um2': 79 / 6 * .5,
                             'section_counts': [3, 1], 'maximum': 3}},
        'scale_um2': {'A1/TA': .4, 'A1/GA': 1., 'A2/TA': .5},
        'gfp_field_counts': {'A1/TA': [[2, 1], [1, 4]], 'A1/GA': [[1, 0], [2, 2]], 'A2/TA': [[2, 1], [1, 0]]}})
    seal(path)
    return path


def identity(row, columns=IDS):
    return tuple(row.get(n) for n in columns)


def valid_id(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', value) is not None


def validate(inp):
    inp = input_directory(inp)
    manifest = json.loads((inp / 'manifest.json').read_text())
    require(manifest.get('schema_version') == 1, 'unsupported manifest schema')
    actual = {n: h for n, h in tree(inp).items() if n != 'manifest.json'}
    require(actual == manifest.get('sha256'), 'input hash/inventory mismatch')
    require({'design.json', 'regions.csv'} <= actual.keys(), 'missing design or regions')
    design = json.loads((inp / 'design.json').read_text())
    require(design.get('schema_version') == 1, 'unsupported design schema')
    fields, fibers = {}, set()
    for f in design['fields']:
        require(all(valid_id(f.get(k)) for k in IDS), 'invalid field identifier')
        key = identity(f)
        require(key not in fields, 'duplicate field identifier')
        require(f.get('endpoint') in ('fiber', 'gfp'), 'invalid endpoint')
        for k in ('pixel_width_um', 'pixel_height_um'):
            v = f.get(k)
            require(type(v) in (int, float) and math.isfinite(v) and v > 0, 'missing/invalid calibration: ' + k)
        area_scale = f['pixel_width_um'] * f['pixel_height_um']
        require(math.isfinite(area_scale) and area_scale > 0, 'invalid calibration product')
        require(all(type(f.get(k)) is int and 0 < f[k] <= 4096 for k in ('width', 'height')), 'invalid dimensions')
        fields[key] = f
    require(fields, 'empty design')
    for f in design['fibers']:
        require(all(valid_id(f.get(k)) for k in IDS + ['fiber']), 'invalid fiber identifier')
        require(identity(f) in fields and fields[identity(f)]['endpoint'] == 'fiber', 'fiber outside registered field')
        key = identity(f, IDS + ['fiber'])
        require(key not in fibers, 'duplicate fiber identifier')
        fibers.add(key)
    with (inp / 'regions.csv').open(newline='') as f:
        reader = csv.DictReader(f)
        require(reader.fieldnames == COLUMNS, 'invalid CSV columns')
        rows = list(reader)
    seen_fibers, seen_gfp, masks, used_fields = set(), set(), set(), set()
    for row in rows:
        require(set(row) == set(COLUMNS) and all(v is not None for v in row.values()), 'invalid CSV row')
        require(all(valid_id(row[k]) for k in IDS), 'invalid region identifier')
        key = identity(row)
        require(key in fields, 'changed/unregistered field identifier')
        field = fields[key]
        require(row['endpoint'] == field['endpoint'], 'changed endpoint')
        require(row['reviewed'] == 'true', 'reviewed annotation required')
        require(row['regeneration_sample'] in ('true', 'false'), 'invalid sampling flag')
        require(re.fullmatch(r'masks/[A-Za-z0-9_-]+\.png', row['mask']) is not None, 'invalid mask path')
        require(row['mask'] in actual and row['mask'] not in masks, 'missing/reused mask')
        masks.add(row['mask']); used_fields.add(key)
        if row['endpoint'] == 'fiber':
            require(valid_id(row['fiber']), 'invalid fiber identifier')
            fid = identity(row, IDS + ['fiber'])
            require(fid in fibers and fid not in seen_fibers, 'changed/duplicate fiber identifier')
            seen_fibers.add(fid)
        else:
            require(row['fiber'] == '' and row['regeneration_sample'] == 'false', 'GFP is a distinct endpoint')
            require(key not in seen_gfp, 'duplicate GFP field')
            seen_gfp.add(key)
    require(seen_fibers == fibers and used_fields == set(fields), 'incomplete field/fiber inventory')
    require(masks == {n for n in actual if n.startswith('masks/')}, 'unreferenced mask')
    groups = {}
    for key, f in fields.items():
        if f['endpoint'] == 'gfp':
            groups.setdefault(key[:3], set()).add(key[3])
    require(groups and all(len(s) >= 2 for s in groups.values()), 'GFP requires at least two registered sections per muscle')
    fiber_groups = {identity(r)[:3] for r in rows if r['endpoint'] == 'fiber'}
    require(fiber_groups and all(any(identity(r)[:3] == g and r['endpoint'] == 'fiber'
                                   and r['regeneration_sample'] == 'true' for r in rows) for g in fiber_groups),
            'each fiber muscle needs a declared regeneration sample')
    return rows, fields


def measure(inp, output):
    inp, out = new_output(inp, output)
    started = time.monotonic()
    report = {'status': 'fail', 'endpoint_limits': 'reviewed-region mechanics only'}
    before = tree(inp)
    dump(out / 'input-manifest.json', before)
    try:
        rows, fields = validate(inp)
        home = prepare()
        report['provenance'] = provenance(home, out / 'runtime.log')
        objects, fibers, gfp = [], [], []
        for i, row in enumerate(rows):
            f = fields[identity(row)]
            text = run([home / 'bin/java', '-Djava.awt.headless=true', '-cp',
                        str(RUNTIME / 'classes') + os.pathsep + str(RUNTIME / 'ij-1.54p.jar'),
                        'ImageJMeasure', inp / row['mask'], f['width'], f['height'],
                        f['pixel_width_um'], f['pixel_height_um']], out / 'imagej.log',
                       env=clean_java_env(), timeout=30)
            records = list(csv.DictReader(io.StringIO(text)))
            require(all(set(r) == {'object_index', 'area_um2'} for r in records), 'invalid runner output')
            for n, r in enumerate(records, 1):
                area = float(r['area_um2'])
                require(r['object_index'] == str(n) and math.isfinite(area) and area > 0, 'invalid measurement')
                objects.append({**row, 'object_index': n, 'area_um2': area})
            if row['endpoint'] == 'fiber':
                require(len(records) == 1, 'each reviewed fiber mask must contain exactly one connected object')
                fibers.append({**row, 'area_um2': float(records[0]['area_um2'])})
            else:
                gfp.append({**{k: row[k] for k in IDS}, 'reviewed_positive_count': len(records)})
        write_csv(out / 'imagej-objects.csv', COLUMNS + ['object_index', 'area_um2'], objects)
        write_csv(out / 'fiber-areas.csv', COLUMNS + ['area_um2'], fibers)
        summaries = []
        for group in sorted({identity(r)[:3] for r in fibers}):
            all_rows = [r for r in fibers if identity(r)[:3] == group]
            for scope in ('all_reviewed', 'sampled_regenerating'):
                selected = all_rows if scope == 'all_reviewed' else [r for r in all_rows if r['regeneration_sample'] == 'true']
                mean = math.fsum(r['area_um2'] for r in selected) / len(selected)
                require(math.isfinite(mean), 'nonfinite summary')
                summaries.append({**dict(zip(IDS[:3], group)), 'scope': scope, 'n': len(selected), 'mean_area_um2': mean})
        write_csv(out / 'fiber-muscle-summary.csv', IDS[:3] + ['scope', 'n', 'mean_area_um2'], summaries)
        write_csv(out / 'gfp-fields.csv', IDS + ['reviewed_positive_count'], gfp)
        section_counts = {}
        for r in gfp:
            key = identity(r)[:4]
            section_counts[key] = section_counts.get(key, 0) + r['reviewed_positive_count']
        sections = [{**dict(zip(IDS[:4], k)), 'reviewed_positive_count': v} for k, v in sorted(section_counts.items())]
        write_csv(out / 'gfp-sections.csv', IDS[:4] + ['reviewed_positive_count'], sections)
        maxima = []
        for group in sorted({k[:3] for k in section_counts}):
            counts = {k[3]: v for k, v in section_counts.items() if k[:3] == group}
            maximum = max(counts.values())
            maxima.append({**dict(zip(IDS[:3], group)), 'section_n': len(counts), 'max_reviewed_positive_count': maximum,
                           'max_sections': '|'.join(k for k, v in sorted(counts.items()) if v == maximum)})
        write_csv(out / 'gfp-muscle-max.csv', IDS[:3] + ['section_n', 'max_reviewed_positive_count', 'max_sections'], maxima)
        require(tree(inp) == before, 'inputs changed during measurement')
        report['status'] = 'pass'
        report['measured_fibers'] = len(fibers)
        report['measured_gfp_fields'] = len(gfp)
    except Exception as e:
        report['error'] = str(e)
        raise
    finally:
        report['inputs_unchanged'] = tree(inp) == before
        report['elapsed_seconds'] = time.monotonic() - started
        dump(out / 'run-report.json', report)
        dump(out / 'output-manifest.json', tree(out))
    return out


def check_truth(inp, out):
    truth = json.loads((inp / 'truth.json').read_text())
    fibers = read_csv(out / 'fiber-areas.csv')
    require(len(fibers) == 18, 'fiber inventory truth')
    for r in fibers:
        group = r['animal'] + '/' + r['muscle']
        pixels = truth['fiber_pixels_by_section'][int(r['section'][1:]) - 1][int(r['fiber'][1:]) - 1]
        require(math.isclose(float(r['area_um2']), pixels * truth['scale_um2'][group], abs_tol=1e-9), 'independent area truth')
    summary = read_csv(out / 'fiber-muscle-summary.csv')
    require(len(summary) == 6, 'separate summary truth')
    for r in summary:
        expected = truth['groups'][r['animal'] + '/' + r['muscle']]
        prefix = 'sample' if r['scope'] == 'sampled_regenerating' else 'all'
        require(int(r['n']) == expected[prefix + '_n'] and
                math.isclose(float(r['mean_area_um2']), expected[prefix + '_mean_um2'], abs_tol=1e-9), 'sampled mean truth')
    for r in read_csv(out / 'gfp-fields.csv'):
        expected = truth['gfp_field_counts'][r['animal'] + '/' + r['muscle']][int(r['section'][1:]) - 1][int(r['field'][-1]) - 1]
        require(int(r['reviewed_positive_count']) == expected, 'field count truth')
    sections = read_csv(out / 'gfp-sections.csv')
    require(len(sections) == 6, 'section inventory truth')
    for r in sections:
        expected = truth['groups'][r['animal'] + '/' + r['muscle']]['section_counts'][int(r['section'][1:]) - 1]
        require(int(r['reviewed_positive_count']) == expected, 'section count truth')
    maxima = read_csv(out / 'gfp-muscle-max.csv')
    require(len(maxima) == 3, 'muscle inventory truth')
    for r in maxima:
        expected = truth['groups'][r['animal'] + '/' + r['muscle']]
        require(int(r['section_n']) == 2 and int(r['max_reviewed_positive_count']) == expected['maximum'], 'maximum truth')
        require(expected['maximum'] != sum(expected['section_counts']), 'fixture must distinguish max from pooled sum')


def directory_symlink_fixture(original, destination):
    # Omit only the root mask tree; never copy/delete it merely to plant a link.
    shutil.copytree(original, destination,
                    ignore=lambda directory, names: ['masks'] if Path(directory) == original else [])
    (destination / 'masks').symlink_to(original / 'masks', target_is_directory=True)


def suite(output):
    out = Path(output).resolve()
    require(not out.exists(), 'suite output reuse rejected')
    out.mkdir(parents=True)
    started = time.monotonic()
    report = {'status': 'fail', 'cases': []}
    def case(name, action=None, rejection=None, *, package=ROOT, command='measure', runner_error=None):
        begin = time.monotonic()
        args = [sys.executable, package / 'tutorial.py', command]
        if command == 'measure':
            args += ['--input', action[0], '--out', action[1]]
        result = subprocess.run([str(x) for x in args], capture_output=True, text=True, timeout=240)
        (out / (name + '.log')).write_text(result.stdout + result.stderr)
        ok = result.returncode == 0 if rejection is None else result.returncode != 0 and rejection in result.stderr
        if runner_error is not None:
            imagej_log = Path(action[1]) / 'imagej.log'
            ok = ok and imagej_log.is_file() and runner_error in imagej_log.read_text()
        report['cases'].append({'case': name, 'pass': ok, 'exit_code': result.returncode,
                                'expected_imagej_error': runner_error,
                                'expected_rejection': rejection, 'log': name + '.log', 'elapsed_seconds': time.monotonic() - begin})
        require(ok, 'suite case failed: ' + name)
    try:
        home = prepare()
        report['provenance'] = provenance(home, out / 'runtime.log')
        original = fixtures(out / 'original')
        before = tree(original)
        dump(out / 'original-input-hashes.json', before)
        case('control', (original, out / 'control'))
        check_truth(original, out / 'control')
        report['cases'].append({'case': 'independent_synthetic_truth', 'pass': True})
        # Reseal intentionally modified copies so schema checks, not checksum checks, reject them.
        for name, mutation, message in [
            ('missing_calibration', lambda d, r: d['fields'][0].pop('pixel_width_um'), 'missing/invalid calibration'),
            ('nonfinite_calibration', lambda d, r: d['fields'][0].update(pixel_width_um=float('nan')), 'missing/invalid calibration'),
            ('infinite_calibration', lambda d, r: d['fields'][0].update(pixel_height_um=float('inf')), 'missing/invalid calibration'),
            ('zero_calibration', lambda d, r: d['fields'][0].update(pixel_width_um=0), 'missing/invalid calibration'),
            ('negative_calibration', lambda d, r: d['fields'][0].update(pixel_height_um=-1), 'missing/invalid calibration'),
            ('overflow_calibration', lambda d, r: d['fields'][0].update(pixel_width_um=1e308, pixel_height_um=1e308), 'invalid calibration product'),
            ('invalid_identifier', lambda d, r: r[0].update(fiber='bad/id'), 'invalid fiber identifier'),
            ('changed_identifier', lambda d, r: r[0].update(fiber='R99'), 'changed/duplicate fiber identifier'),
            ('duplicate_field_id', lambda d, r: d['fields'].append(dict(d['fields'][0])), 'duplicate field identifier'),
            ('duplicate_fiber_id', lambda d, r: d['fibers'].append(dict(d['fibers'][0])), 'duplicate fiber identifier'),
            ('changed_hierarchy', lambda d, r: r[0].update(animal='A99'), 'changed/unregistered field identifier'),
            ('unreviewed', lambda d, r: r[0].update(reviewed='false'), 'reviewed annotation required'),
            ('invalid_dimensions', lambda d, r: d['fields'][0].update(width=-1), 'invalid dimensions'),
            ('invalid_sample', lambda d, r: r[0].update(regeneration_sample='maybe'), 'invalid sampling flag')]:
            bad = out / ('input-' + name)
            shutil.copytree(original, bad)
            design, rows = json.loads((bad / 'design.json').read_text()), read_csv(bad / 'regions.csv')
            mutation(design, rows)
            # Invalid NaN/Infinity JSON deliberately exercises strict numeric validation.
            (bad / 'design.json').write_text(json.dumps(design) + '\n')
            write_csv(bad / 'regions.csv', COLUMNS, rows)
            seal(bad)
            hashes = tree(bad)
            case(name, (bad, out / ('rejected-' + name)), message)
            require(tree(bad) == hashes, 'rejection changed inputs')
        for name, shapes, foreground, message, specific in [
            ('nonbinary_mask', [(2, 2, 2, 2)], 127, 'command failed', 'Mask must contain only 0 and 255'),
            ('ring_hole', [(2, 2, 5, 5, 3, 3, 3, 3)], 255, 'command failed', 'Mask contains enclosed holes; supply filled reviewed regions'),
            ('disconnected_fiber', [(2, 2, 2, 2), (10, 2, 2, 2)], 255, 'exactly one connected object', None),
            ('empty_fiber', [], 255, 'exactly one connected object', None)]:
            bad = out / ('input-' + name)
            shutil.copytree(original, bad)
            first = read_csv(bad / 'regions.csv')[0]
            png(bad / first['mask'], shapes, foreground=foreground)
            seal(bad)
            hashes = tree(bad)
            case(name, (bad, out / ('rejected-' + name)), message, runner_error=specific)
            require(tree(bad) == hashes, 'invalid mask rejection changed inputs')
            if name == 'ring_hole':
                report['cases'][-1]['fixture_truth'] = {'outer_pixels': 25, 'enclosed_background_pixels': 9,
                                                       'foreground_pixels': 16, 'expected': 'reject'}
        # Independent topology truth: edge rectangle 3*2=6 pixels; corner-touching
        # 2*2 squares occupy 8 pixels but form ONE 8-connected object, not two cells.
        for name, shapes, pixels in [
            ('edge_touching', [(0, 0, 3, 2)], 6),
            ('diagonal_touching', [(2, 2, 2, 2), (4, 4, 2, 2)], 8)]:
            topology = out / ('input-' + name)
            shutil.copytree(original, topology)
            rows = read_csv(topology / 'regions.csv')
            selected = [rows[0], next(r for r in rows if r['endpoint'] == 'gfp')]
            for row in selected:
                png(topology / row['mask'], shapes)
            dump(topology / 'truth.json', {'scope': 'planted masks only; original geometry elsewhere unchanged',
                                         'masks': [r['mask'] for r in selected], 'objects_per_mask': 1,
                                         'pixels_per_mask': pixels, 'pixel_width_um': .5, 'pixel_height_um': .8,
                                         'area_um2_per_mask': pixels * .4})
            seal(topology)
            expected_hashes = tree(topology)
            measured = out / name
            case(name, (topology, measured))
            objects = read_csv(measured / 'imagej-objects.csv')
            for row in selected:
                actual = [r for r in objects if r['mask'] == row['mask']]
                require(len(actual) == 1 and math.isclose(float(actual[0]['area_um2']), pixels * .4, abs_tol=1e-9),
                        name + ': independent count/area truth')
            field = next(r for r in read_csv(measured / 'gfp-fields.csv') if identity(r) == identity(selected[1]))
            require(field['reviewed_positive_count'] == '1', name + ': GFP connectivity truth')
            require(tree(topology) == expected_hashes, name + ': inputs changed')
            report['cases'].append({'case': name + '_independent_truth', 'pass': True,
                                    'expected_objects_per_mask': 1, 'expected_pixels_per_mask': pixels,
                                    'expected_area_um2': pixels * .4})
        # A dangling file link proves refusal precedes even opening/hash-reading the target.
        for name, kind in [('symlink_file', 'file'), ('symlink_directory', 'directory'), ('symlink_root', 'root')]:
            bad = out / ('input-' + name)
            if kind == 'root':
                bad.symlink_to(original, target_is_directory=True)
            elif kind == 'directory':
                directory_symlink_fixture(original, bad)
            else:
                shutil.copytree(original, bad)
                target = bad / 'design.json'
                target.unlink()
                target.symlink_to('does-not-exist.json')
            case(name, (bad, out / ('rejected-' + name)), 'input symlinks rejected before hashing')
            require(not (out / ('rejected-' + name)).exists(), 'symlink refusal must precede output writes')
        bad = out / 'input-tampered'
        shutil.copytree(original, bad)
        with (bad / 'regions.csv').open('a') as f:
            f.write('\n')
        case('changed_hash', (bad, out / 'rejected-hash'), 'input hash/inventory mismatch')
        case('output_reuse', (original, out / 'control'), 'output reuse rejected')
        case('input_overlap', (original, original / 'forbidden'), 'output/input overlap rejected')
        case('input_ancestor_overlap', (original, out), 'output/input overlap rejected')
        corrected = out / 'corrected-input'
        shutil.copytree(out / 'input-missing_calibration', corrected)
        design = json.loads((corrected / 'design.json').read_text())
        design['fields'][0]['pixel_width_um'] = .5
        dump(corrected / 'design.json', design)
        # Restore canonical formatting and exact original bytes; retry with a fresh destination.
        shutil.copyfile(original / 'design.json', corrected / 'design.json')
        seal(corrected)
        require(tree(corrected) == before, 'correction must restore original fixture hashes')
        case('corrected_retry', (corrected, out / 'corrected-retry'))
        check_truth(corrected, out / 'corrected-retry')
        # Run the installed/copy workflow outside any checkout; cached archives are copied,
        # never symlinked, and extraction/runtime stay inside this disposable package.
        with tempfile.TemporaryDirectory(prefix='imagej-copied-') as temporary:
            copied = Path(temporary).resolve() / 'package'
            copied.mkdir()
            require(not any((p / '.git').exists() for p in copied.parents),
                    'copied-package test requires a temporary directory outside any checkout')
            for name in SOURCES + ['VERIFICATION.json']:
                shutil.copyfile(ROOT / name, copied / name)
            runtime = copied / '.runtime'
            runtime.mkdir()
            for name in ('ij-1.54p.jar', 'jdk.tar.gz'):
                shutil.copyfile(RUNTIME / name, runtime / name)
            spec = LOCK['jdk'][platform.system() + '-' + platform.machine()]
            jdk_root = runtime / Path(spec['java_home']).parts[0]
            fake_home = runtime / spec['java_home']
            (fake_home / 'bin').mkdir(parents=True)
            for name in ('java', 'javac'):
                (fake_home / 'bin' / name).write_text('incomplete extraction sentinel\n')
            fake_before = tree(jdk_root)
            case('incomplete_jdk_refusal', package=copied, command='install',
                 rejection='incomplete task-local JDK: missing/invalid completion marker')
            require(tree(jdk_root) == fake_before, 'incomplete JDK was changed or executed')
            shutil.rmtree(jdk_root)  # Only this planted, disposable test tree.
            staging = runtime / '.jdk-extracting'
            staging.mkdir()
            (staging / 'sentinel').write_text('interrupted extraction\n')
            case('interrupted_extraction_refusal', package=copied, command='install',
                 rejection='interrupted JDK extraction detected')
            require((staging / 'sentinel').read_text() == 'interrupted extraction\n' and not jdk_root.exists(),
                    'interrupted extraction was silently reused')
            shutil.rmtree(staging)  # Correct the planted interruption before the fresh real install.
            copied_input, copied_output = copied / 'input', copied / 'output'
            shutil.copytree(original, copied_input)
            case('copied_package_measure_retry', (copied_input, copied_output), package=copied)
            check_truth(copied_input, copied_output)
            require(tree(copied_input) == before, 'copied inputs changed')
            copied_provenance = json.loads((copied_output / 'run-report.json').read_text())['provenance']
            require(copied_provenance['tested_commit'] is None and copied_provenance['package_git_status'] is None
                    and copied_provenance['package_dirty'] is None
                    and copied_provenance['package_origin'] == 'copied_package_no_git_metadata'
                    and copied_provenance['source_sha256'] == report['provenance']['source_sha256'],
                    'copied-package provenance must be honest and preserve source hashes')
            require((jdk_root / '.imagej-complete.json').is_file(), 'atomic extraction completion marker missing')
            shutil.copytree(copied_output, out / 'copied-package-measurement')
            report['cases'].append({'case': 'copied_package_truth_and_null_git_provenance', 'pass': True,
                                    'source_sha256': copied_provenance['source_sha256'],
                                    'tested_commit': None, 'package_git_status': None, 'package_dirty': None,
                                    'outside_checkout': True, 'completion_marker': json.loads(
                                        (jdk_root / '.imagej-complete.json').read_text())})
        require(tree(original) == before, 'original inputs changed')
        report['original_inputs_unchanged'] = True
        report['status'] = 'pass'
    except Exception as e:
        report['error'] = str(e)
        raise
    finally:
        report['elapsed_seconds'] = time.monotonic() - started
        dump(out / 'suite-report.json', report)
        dump(out / 'suite-output-manifest.json', tree(out))
    print(json.dumps({'status': report['status'], 'cases': len(report['cases']), 'report': str(out / 'suite-report.json')}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('install')
    se = sub.add_parser('seal'); se.add_argument('--input', required=True)
    f = sub.add_parser('fixtures'); f.add_argument('--out', required=True)
    m = sub.add_parser('measure'); m.add_argument('--input', required=True); m.add_argument('--out', required=True)
    s = sub.add_parser('suite'); s.add_argument('--out', required=True)
    a = p.parse_args()
    if a.command == 'install':
        print(prepare())
    elif a.command == 'seal':
        inp = input_directory(a.input)
        require(inp.is_dir() and not (inp / 'manifest.json').exists(), 'seal requires a new input directory without a manifest')
        seal(inp)
        print(inp / 'manifest.json')
    elif a.command == 'fixtures':
        print(fixtures(a.out))
    elif a.command == 'measure':
        print(measure(a.input, a.out))
    else:
        suite(a.out)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
