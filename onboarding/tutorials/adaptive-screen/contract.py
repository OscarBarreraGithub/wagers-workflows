"""Small local file contract. Hashes detect edits, not hostile forgery/authenticity."""
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

COLUMNS = ['target_id', 'f1', 'f2', 'status']
IDENTITY = ['target_id', 'sample_id', 'round_id', 'outcome_id']
OUTCOMES = IDENTITY + ['value']
MAX_ROUND = 3
MAX_BATCH = 4


class Refusal(ValueError):
    pass


def require(test, message):
    if not test:
        raise Refusal(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(obj):
    return (json.dumps(obj, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def csv_bytes(fields, rows):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def read_csv(path, fields):
    with Path(path).open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        require(reader.fieldnames == fields, f'CSV columns must be exactly {fields}')
        rows = list(reader)
    require(rows and all(set(row) == set(fields) and all(v is not None and v != '' for v in row.values()) for row in rows), 'Empty/missing/extra CSV fields')
    return rows


def number(value):
    require(not isinstance(value, bool), 'Boolean is not numeric')
    try:
        result = float(value)
    except (ValueError, TypeError):
        raise Refusal('Invalid number') from None
    require(math.isfinite(result), 'Nonfinite number')
    return result


def catalog(rows):
    require(100 <= len(rows) <= 1000, 'Catalog must contain 100..1000 candidates')
    seen = set()
    result = []
    for row in rows:
        require(set(row) == set(COLUMNS), 'Invalid candidate fields (truth is forbidden)')
        tid = row['target_id']
        require(isinstance(tid, str) and re.fullmatch(r'FABLE-\d{4}', tid) and tid not in seen, 'Invalid/duplicate fictional target')
        require(row['status'] in ('valid', 'excluded', 'invalid'), 'Unknown candidate status')
        features = [number(row[k]) for k in ('f1', 'f2')]
        require(all(-1 <= x <= 1 for x in features), 'Features must be in [-1,1]')
        result.append(dict(zip(COLUMNS, [tid, *features, row['status']])))
        seen.add(tid)
    return result


def records(rows, candidates, pending=False):
    fields = IDENTITY if pending else OUTCOMES
    valid = {r['target_id'] for r in candidates if r['status'] == 'valid'}
    seen = {k: set() for k in ('target_id', 'sample_id', 'outcome_id')}
    result = []
    for row in rows:
        require(set(row) == set(fields), 'Invalid observation fields')
        require(row['target_id'] in valid, 'Unknown/excluded/invalid target')
        require(isinstance(row['round_id'], str) and re.fullmatch(r'r00[0-3]', row['round_id']), 'Invalid round identity')
        for key in ('sample_id', 'outcome_id'):
            require(isinstance(row[key], str) and re.fullmatch(r'[A-Za-z0-9_-]{1,80}', row[key]), 'Invalid sample/outcome identity')
        for key in seen:
            require(row[key] not in seen[key], f'Duplicate {key}')
            seen[key].add(row[key])
        item = dict(row)
        if not pending:
            item['value'] = number(row['value'])
        result.append(item)
    return result


def ensure_output(out, inputs=()):
    out = Path(out).absolute()
    require(not out.exists() and not out.is_symlink(), 'Output already exists')
    # Resolve symlinks before checking both directions of ancestry.
    resolved = out.resolve()
    package = Path(__file__).resolve().parent
    local_runs = package / 'runs'
    require(package not in resolved.parents or local_runs in resolved.parents,
            'Output is inside protected package source; use a user directory or local runs/')
    for runtime in {Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()}:
        require(resolved != runtime and runtime not in resolved.parents,
                'Output is inside protected Python runtime')
    require(not any((parent / 'manifest.json').exists() for parent in resolved.parents),
            'Output is nested inside a prior snapshot')
    protected = []
    for source in inputs:
        source = Path(source).resolve()
        protected.append(source)
        # Files inside a bundle protect that whole bundle from nested outputs.
        protected.extend(p for p in source.parents if (p / 'manifest.json').is_file())
        if source.is_dir() and (source / 'state.json').is_file():
            cursor, seen = source, set()
            while cursor not in seen:
                seen.add(cursor)
                protected.append(cursor)
                state = json.loads((cursor / 'state.json').read_text())
                if state['parent'] is None:
                    break
                cursor = (cursor / state['parent']['path']).resolve()
    for source in protected:
        require(resolved != source and resolved not in source.parents and source not in resolved.parents, 'Output overlaps input')
    # A symlinked parent would undermine the local snapshot contract.
    require(not any(p.is_symlink() for p in [out, *out.parents]), 'Symlinked output path')
    return out


def publish(out, files, inputs=()):
    """Validate first, then publish a new directory; never rewrite an input/output."""
    out = ensure_output(out, inputs)
    require(all(Path(k).name == k and k != 'manifest.json' for k in files), 'Invalid bundle filename')
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.adaptive-stage-', dir=out.parent))
    try:
        for name, data in files.items():
            (stage / name).write_bytes(data)
        manifest = {'schema': 1, 'files': {k: digest(v) for k, v in sorted(files.items())}}
        (stage / 'manifest.json').write_bytes(encoded(manifest))
        # mkdir is exclusive, including against simultaneous writers. Never rename over output.
        out.mkdir()
        try:
            for child in stage.iterdir():
                os.rename(child, out / child.name)
        except BaseException:
            shutil.rmtree(out)
            raise
    finally:
        shutil.rmtree(stage)
    return manifest


def verify_bundle(path):
    path = Path(path).resolve()
    require(path.is_dir(), 'Snapshot directory missing')
    require(not any(p.is_symlink() for p in path.iterdir()), 'Symlinked snapshot file')
    m = json.loads((path / 'manifest.json').read_text())
    require(set(m) == {'schema', 'files'} and m['schema'] == 1 and isinstance(m['files'], dict), 'Invalid manifest')
    require(set(p.name for p in path.iterdir()) == set(m['files']) | {'manifest.json'}, 'Unexpected/missing snapshot files')
    for name, expected in m['files'].items():
        require(Path(name).name == name and name != 'manifest.json', 'Invalid manifest filename')
        require(digest((path / name).read_bytes()) == expected, f'Altered snapshot file: {name}')
    return m


def load_state(path, visited=None):
    path = Path(path).resolve()
    visited = set() if visited is None else visited
    require(path not in visited and len(visited) < 10, 'State chain cycle/too long')
    visited.add(path)
    verify_bundle(path)
    state = json.loads((path / 'state.json').read_text())
    require(set(state) == {'schema', 'version', 'event', 'seed', 'round', 'candidates', 'observed', 'pending', 'parent'}, 'Invalid state fields')
    require(state['schema'] == 1 and type(state['version']) is int and type(state['seed']) is int and 0 <= state['seed'] <= 2**32-1, 'Invalid state header')
    require(type(state['round']) is int and 0 <= state['round'] <= MAX_ROUND, 'Invalid round')
    require(catalog(state['candidates']) == state['candidates'], 'Invalid catalog')
    require(records(state['observed'], state['candidates']) == state['observed'], 'Invalid observations')
    require(records(state['pending'], state['candidates'], True) == state['pending'], 'Invalid pending')
    require(4 <= len(state['observed']) <= 12 + MAX_ROUND * MAX_BATCH and len(state['pending']) <= MAX_BATCH, 'Observation budget exceeded')
    for key in ('target_id', 'sample_id', 'outcome_id'):
        require(not ({r[key] for r in state['observed']} & {r[key] for r in state['pending']}), 'Already measured identity is pending')
    require(all(r['round_id'] <= f"r{state['round']:03}" for r in state['observed']), 'Future observation')
    require(all(r['round_id'] == f"r{state['round']:03}" for r in state['pending']), 'Pending round mismatch')
    if state['parent'] is None:
        require(state['version'] == 0 and state['round'] == 0 and state['event'] == 'init' and not state['pending'], 'Invalid initial state')
        require(4 <= len(state['observed']) <= 12 and all(r['round_id'] == 'r000' for r in state['observed']), 'Invalid initial ledger')
        return state
    parent_ref = state['parent']
    require(set(parent_ref) == {'path', 'sha256'}, 'Invalid parent reference')
    parent_path = (path / parent_ref['path']).resolve()
    require(digest((parent_path / 'state.json').read_bytes()) == parent_ref['sha256'], 'Altered prior state')
    parent = load_state(parent_path, visited)
    require(state['version'] == parent['version'] + 1 and state['seed'] == parent['seed'] and state['candidates'] == parent['candidates'], 'Altered prior catalog/header')
    require(state['observed'][:len(parent['observed'])] == parent['observed'], 'Altered prior observations')
    if state['event'] == 'propose':
        require(not parent['pending'] and 1 <= len(state['pending']) <= MAX_BATCH, 'Pending batch already exists/empty')
        require(state['round'] == parent['round'] + 1 and state['observed'] == parent['observed'], 'Invalid proposal transition')
    elif state['event'] == 'import':
        require(parent['pending'] and not state['pending'] and state['round'] == parent['round'], 'Invalid import transition')
        new = state['observed'][len(parent['observed']):]
        require([{k: r[k] for k in IDENTITY} for r in new] == parent['pending'], 'Imported identities differ from pending')
    else:
        raise Refusal('Unknown state event')
    return state


def save_state(state, out, parent=None, artifacts=None, inputs=()):
    import copy
    state = copy.deepcopy(state)
    if parent is not None:
        parent = Path(parent).resolve()
        state['parent'] = {'path': os.path.relpath(parent, Path(out).resolve()), 'sha256': digest((parent / 'state.json').read_bytes())}
        state['version'] += 1
        inputs = (*inputs, parent)
    files = {'state.json': encoded(state), **(artifacts or {})}
    return publish(out, files, inputs)


def initialize(candidates_path, outcomes_path, out, seed=17):
    require(type(seed) is int and 0 <= seed <= 2**32-1, 'Invalid seed')
    candidates = catalog(read_csv(candidates_path, COLUMNS))
    observed = records(read_csv(outcomes_path, OUTCOMES), candidates)
    require(4 <= len(observed) <= 12 and all(r['round_id'] == 'r000' for r in observed), 'Need 4..12 initial r000 observations')
    state = dict(schema=1, version=0, event='init', seed=seed, round=0, candidates=candidates, observed=observed, pending=[], parent=None)
    save_state(state, out, inputs=(candidates_path, outcomes_path))


def import_outcomes(state_path, csv_path, out):
    state = load_state(state_path)
    require(state['pending'], 'No pending batch; already measured/repeated import')
    imported = records(read_csv(csv_path, OUTCOMES), state['candidates'])
    # Whole batch only; ordering in CSV may vary, identity and complete set may not.
    by_target = {r['target_id']: r for r in imported}
    require(set(by_target) == {r['target_id'] for r in state['pending']}, 'Unknown/missing/already measured target in import')
    new = []
    for expected in state['pending']:
        row = by_target[expected['target_id']]
        require({k: row[k] for k in IDENTITY} == expected, 'Contradictory sample/round/outcome identity')
        new.append(row)
    records(state['observed'] + new, state['candidates'])
    state['observed'].extend(new)
    state['pending'] = []
    state['event'] = 'import'
    save_state(state, out, state_path, {'imported.csv': csv_bytes(OUTCOMES, new)}, (csv_path,))
