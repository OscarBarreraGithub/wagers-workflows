"""One focused suite: real failure, corrected retry, arithmetic, round trip and safety."""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
from workflow import (PACKAGE, KEYS, STAGES, code_identity, digest, private_caches,
                      reserve_output, runtime_identity, selected_runtime,
                      verify_runtime_unchanged, write_json)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def invoke(source, output, log, runtime_prefix=None):
    env = {**os.environ, 'MPLBACKEND': 'Agg', 'OMP_NUM_THREADS': '1',
           'OPENBLAS_NUM_THREADS': '1', 'NUMBA_NUM_THREADS': '1',
           'PYTHONDONTWRITEBYTECODE': '1'}
    with log.open('w') as stream:
        completed = subprocess.run(
            [sys.executable, '-I', '-B', str(PACKAGE / 'workflow.py'), '--input', str(source),
             '--output', str(output), '--runtime-prefix', str(selected_runtime(runtime_prefix))],
            stdout=stream, stderr=subprocess.STDOUT,
            env=env, timeout=180)
    return completed.returncode


def verify_result(source, output):
    """Oracle uses literal truth and scalar arithmetic, never Scanpy or workflow helpers."""
    import anndata as ad
    import numpy as np
    fixture = json.loads(source.read_text())
    truth = json.loads((PACKAGE / 'truth.json').read_text())
    report = json.loads((output / 'report.json').read_text())
    require(report['status'] == 'PASS', 'corrected retry did not pass')
    require(all(report['stages'][s] == 'PASS' for s in STAGES), 'missing successful API stage')
    require(report['input_unchanged'] and report['code_unchanged'], 'source/code mutation')
    require(report['runtime_check'] == 'PASS' and report['runtime_unchanged'], 'runtime mutation')
    qc = json.loads((output / 'qc.json').read_text())
    require([r['cell_id'] for r in qc] == [c['cell_id'] for c in fixture['cells']], 'QC cell order')
    for column, truth_key in [('total', 'totals'), ('detected', 'detected'),
                              ('qc_total', 'qc_totals'), ('qc_percent', 'qc_percent')]:
        require([r[column] for r in qc] == truth[truth_key], f'known QC {column}')
    require(report['retained_cell_ids'] == truth['retained'], 'known retained cells')
    a = ad.read_h5ad(output / 'readout.h5ad')
    require(a.obs_names.tolist() == truth['retained'], 'round-trip cell IDs')
    require(a.var_names.tolist() == fixture['genes'], 'round-trip gene IDs')
    original = {c['cell_id']: (c, row) for c, row in zip(fixture['cells'], fixture['counts'], strict=True)}
    for i, cid in enumerate(truth['retained']):
        metadata, counts = original[cid]
        require({k: str(a.obs.iloc[i][k]) for k in KEYS} == {k: metadata[k] for k in KEYS},
                'round-trip experiment/donor/sample/perturbation')
        require(a.layers['counts'][i].tolist() == counts, 'raw count preservation')
        require(np.issubdtype(a.layers['counts'].dtype, np.integer), 'raw counts lost integer dtype')
        expected = [math.log1p(100 * x / sum(counts)) for x in counts]
        require(all(math.isclose(float(v), e, rel_tol=1e-12, abs_tol=1e-12)
                    for v, e in zip(a.X[i], expected, strict=True)), 'scalar log normalization')
        require(math.isclose(sum(math.expm1(float(v)) for v in a.X[i]), 100,
                             rel_tol=1e-12, abs_tol=1e-12), 'normalization target invariant')
    pb = json.loads((output / 'pseudobulk.json').read_text())
    require(len(pb) == 4, 'aggregation mixed or split samples')
    samples = {s['sample_id']: s for s in fixture['samples']}
    require({r['sample_id']: r['counts'] for r in pb} == truth['pseudobulk'], 'hand-calculated sums')
    for row in pb:
        require({k: row[k] for k in KEYS} == samples[row['sample_id']], 'pseudobulk identity mapping')
        require(row['n_cells'] == 2, 'cells per sample')
    saved = ad.read_h5ad(output / 'pseudobulk.h5ad')
    require(saved.var_names.tolist() == fixture['genes'], 'pseudobulk gene round trip')
    require(saved.n_obs == 4, 'pseudobulk row round trip')
    for i, (_, row) in enumerate(saved.obs.iterrows()):
        require({k: str(row[k]) for k in KEYS} == samples[str(row['sample_id'])], 'saved group identity')
        require(saved.layers['sum'][i].tolist() == truth['pseudobulk'][str(row['sample_id'])],
                'saved pseudobulk counts')
        require(int(row['n_obs_aggregated']) == 2, 'saved cell counts')
    return {'input_cells': 12, 'retained_cells': 8, 'donors': 2, 'samples': 4,
            'qc_totals': truth['totals'], 'pseudobulk': truth['pseudobulk'],
            'normalization_target': 100, 'arithmetic_tolerance': 1e-12,
            'raw_integer_counts_and_all_identities_roundtrip': True}


def suite(output, runtime_prefix=None):
    root = reserve_output(output, runtime_prefix=runtime_prefix)
    started = time.monotonic()
    report = {'schema': 1, 'status': 'FAIL', 'identity_before': code_identity(),
              'cases': [], 'runtime': None, 'scientific_scope': 'synthetic mechanics only; no DE or causal inference'}
    names = ['runtime', 'invalid_inputs', 'failure_report', 'corrected_retry', 'independent_arithmetic',
             'path_safety', 'unchanged_inputs']
    report['checks'] = {n: 'NOT_RUN' for n in names}
    active = 'runtime'
    input_hashes = {}
    def remember(path):
        input_hashes[str(path.relative_to(root))] = digest(path)
    def case(name, operation):
        record = {'name': name, 'status': 'FAIL'}
        report['cases'].append(record)
        operation()
        record['status'] = 'PASS'
    try:
        report['runtime'] = runtime_identity(runtime_prefix)
        private_caches(root)
        report['checks'][active] = 'PASS'
        active = 'invalid_inputs'
        inputs = root / 'inputs'
        inputs.mkdir()
        logs = root / 'logs'
        logs.mkdir()
        fixture = json.loads((PACKAGE / 'fixture.json').read_text())
        # Each mutation is explicit, and every rejection is checked in a new process.
        variants = []
        def variant(name, change, message):
            data = copy.deepcopy(fixture)
            change(data)
            variants.append((name, data, message))
        variant('ambiguous-assignment', lambda d: d['cells'][0].update(perturbation='control+pulseQ'), 'ambiguous ID')
        variant('missing-cell-id', lambda d: d['cells'][0].pop('cell_id'), 'missing or ambiguous ID')
        variant('duplicate-cell-id', lambda d: d['cells'][1].update(cell_id='c01'), 'duplicate cell ID')
        variant('duplicate-gene-id', lambda d: d['genes'].__setitem__(1, 'FableA'), 'duplicate gene ID')
        variant('missing-gene-id', lambda d: d['genes'].__setitem__(0, None), 'missing or ambiguous ID')
        variant('duplicate-sample-id', lambda d: d['samples'].append(d['samples'][0].copy()), 'duplicate sample ID')
        variant('missing-donor-id', lambda d: d['samples'][0].pop('donor_id'), 'missing or ambiguous ID')
        variant('unknown-sample', lambda d: d['cells'][0].update(sample_id='Unknown'), 'contradictory sample mapping')
        variant('contradictory-donor', lambda d: d['cells'][0].update(donor_id='D2'), 'contradictory sample mapping')
        variant('contradictory-experiment', lambda d: d['cells'][0].update(experiment_id='Other'), 'contradictory sample mapping')
        variant('contradictory-perturbation', lambda d: d['cells'][0].update(perturbation='pulseQ'), 'contradictory sample mapping')
        variant('multiple-assignments', lambda d: d['cells'][0].update(perturbation=['control','pulseQ']), 'ambiguous ID')
        variant('unknown-perturbation', lambda d: d['samples'][0].update(perturbation='mystery'), 'ambiguous perturbation')
        for name, value in [('nan-count', float('nan')), ('inf-count', float('inf')),
                            ('negative-count', -1), ('fractional-count', 1.5), ('boolean-count', True)]:
            variant(name, lambda d, v=value: d['counts'][0].__setitem__(0, v), 'raw counts must be finite nonnegative integers')
        variant('ragged-counts', lambda d: d['counts'][0].pop(), 'count matrix shape mismatch')
        def unmatched(d):
            d['samples'][1]['perturbation'] = 'control'
            for cell in d['cells'][3:6]:
                cell['perturbation'] = 'control'
        variant('unmatched-donor', unmatched, 'matched control/pulseQ')
        for name, data, message in variants:
            source, out = inputs / f'{name}.json', root / name
            # NaN/Infinity intentionally exercise rejection of non-standard JSON numbers.
            source.write_text(json.dumps(data) + '\n')
            remember(source)
            def reject(source=source, out=out, name=name, message=message):
                require(invoke(source, out, logs / f'{name}.log', runtime_prefix) == 1, 'expected analysis failure exit 1')
                observed = json.loads((out / 'report.json').read_text())
                require(observed['status'] == 'FAIL', 'failed case mislabeled passed')
                require(observed['stages'] == {s: 'FAIL' if s == 'validate' else 'NOT_RUN' for s in STAGES},
                        'failed validation ran downstream stages')
                require(message in observed['error'], 'wrong rejection reason')
                require(observed['input_unchanged'], 'rejection altered input')
                require(not list(out.glob('*.h5ad')), 'rejected input produced AnnData')
            case(name, reject)
        report['checks']['invalid_inputs'] = 'PASS'
        active = 'failure_report'
        failed = json.loads((root / 'ambiguous-assignment/report.json').read_text())
        require(failed['stages']['validate'] == 'FAIL' and failed['stages']['qc'] == 'NOT_RUN', 'failure report evidence')
        report['checks'][active] = 'PASS'
        active = 'corrected_retry'
        fixed = inputs / 'corrected.json'
        shutil.copyfile(PACKAGE / 'fixture.json', fixed)
        remember(fixed)
        retry = root / 'corrected-retry'
        case('corrected-retry', lambda: require(invoke(fixed, retry, logs / 'corrected-retry.log', runtime_prefix) == 0,
                                                'corrected retry failed; inspect its report/log'))
        report['checks'][active] = 'PASS'
        active = 'independent_arithmetic'
        report['observed'] = verify_result(fixed, retry)
        report['checks'][active] = 'PASS'
        active = 'path_safety'
        def refusal(name, source, out, message):
            before = {str(p.relative_to(root)): digest(p) for p in root.rglob('*') if p.is_file() and not p.is_symlink()}
            def operation():
                log = logs / f'{name}.log'
                require(invoke(source, out, log, runtime_prefix) == 2, 'expected path refusal exit 2')
                require(message in log.read_text(), 'wrong path refusal reason')
                require(all(digest(root / p) == h for p, h in before.items()), 'refusal changed existing files')
            case(name, operation)
        refusal('no-output-reuse', fixed, retry, 'output reuse')
        refusal('failed-output-reuse', fixed, root / 'ambiguous-assignment', 'output reuse')
        overlap = inputs / 'nested-output'
        refusal('input-overlap', fixed, overlap, 'input/output overlap')
        require(not overlap.exists(), 'overlap created output')
        symin = inputs / 'linked.json'
        symin.symlink_to(fixed.name)
        refusal('input-symlink', symin, root / 'symlink-input-output', 'symlink paths')
        require(not (root / 'symlink-input-output').exists(), 'symlink input created output')
        link = root / 'linked-output'
        link.symlink_to(retry.name, target_is_directory=True)
        refusal('output-symlink', fixed, link, 'symlink paths')
        refusal('ancestor-symlink', fixed, link / 'new-child', 'symlink paths')
        require(not (retry / 'new-child').exists(), 'symlink ancestor created output')
        refusal('under-source', fixed, PACKAGE / 'forbidden-output', 'output under source')
        require(not (PACKAGE / 'forbidden-output').exists(), 'outside destination created')
        refusal('under-runtime', fixed, selected_runtime(runtime_prefix) / 'forbidden-output', 'output/runtime overlap')
        require(not (selected_runtime(runtime_prefix) / 'forbidden-output').exists(), 'runtime destination created')
        refusal('nested-results', fixed, retry / 'forbidden-output', 'existing results/snapshot')
        require(not (retry / 'forbidden-output').exists(), 'nested results destination created')
        report['checks'][active] = 'PASS'
        active = 'unchanged_inputs'
        report['input_sha256_before'] = input_hashes
        report['input_sha256_after'] = {p: digest(root / p) for p in input_hashes}
        require(report['input_sha256_before'] == report['input_sha256_after'], 'input hashes changed')
        report['identity_after'] = code_identity()
        require(report['identity_before'] == report['identity_after'], 'code changed during suite')
        report['checks'][active] = 'PASS'
        report['status'] = 'PASS'
    except Exception as exc:
        report['checks'][active] = 'FAIL'
        report['error'] = f'{type(exc).__name__}: {exc}'
        (root / 'suite-error.log').write_text(traceback.format_exc())
    finally:
        verify_runtime_unchanged(report, runtime_prefix)
        if report.get('runtime_unchanged') is False:
            report['checks']['runtime'] = 'FAIL'
        report['elapsed_seconds'] = round(time.monotonic() - started, 3)
        report['evidence_sha256'] = {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob('*'))
                                     if p.is_file() and not p.is_symlink()
                                     and not any(parent.is_symlink() for parent in p.parents)}
        write_json(root / 'suite-report.json', report)
    print(json.dumps({'status': report['status'], 'cases_passed': sum(c['status'] == 'PASS' for c in report['cases']),
                      'cases_total': len(report['cases']), 'report': str(root / 'suite-report.json')}))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runtime-prefix', type=Path, default=PACKAGE / '.runtime')
    args = parser.parse_args()
    try:
        sys.exit(suite(args.output, args.runtime_prefix))
    except (ValueError, OSError) as exc:
        print(f'REFUSED: {exc}', file=sys.stderr)
        sys.exit(2)
