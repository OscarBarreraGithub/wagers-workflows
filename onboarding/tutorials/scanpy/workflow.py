"""Tiny synthetic readout mechanics. No differential expression or biological inference."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
PACKAGE = Path(__file__).resolve().parent
KEYS = ['experiment_id', 'donor_id', 'sample_id', 'perturbation']
STAGES = ['validate', 'qc', 'filter', 'normalize_log', 'aggregate', 'roundtrip']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def no_symlinks(path):
    # Inspect lexical ancestors before resolve: resolving first hides symlinks.
    path = Path(os.path.abspath(path))
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError('symlink paths are forbidden')
    return path


def selected_runtime(prefix=None):
    try:
        return no_symlinks(PACKAGE / '.runtime' if prefix is None else prefix)
    except ValueError as exc:
        raise ValueError(f'runtime prefix: {exc}') from exc


def protected_destination(out, runtime_prefix=None):
    """Protect software, environments and completed evidence before any mkdir."""
    package = no_symlinks(PACKAGE)
    runs = package / 'runs'
    if (package.is_relative_to(out)
            or (out.is_relative_to(package) and not (out != runs and out.is_relative_to(runs)))):
        raise ValueError('output under source is forbidden except fresh descendants of package runs/')
    for prefix in {selected_runtime(runtime_prefix), Path(sys.prefix).resolve(),
                   Path(sys.base_prefix).resolve()}:
        if out.is_relative_to(prefix) or prefix.is_relative_to(out):
            raise ValueError('output/runtime overlap is forbidden (selected, active or base runtime)')
    for parent in out.parents:
        if (parent / 'pyvenv.cfg').exists() or (parent / 'conda-meta').is_dir():
            raise ValueError('output/runtime overlap is forbidden (existing environment ancestor)')
        if any((parent / name).exists() for name in
               ('report.json', 'suite-report.json', 'readout.h5ad', 'pseudobulk.h5ad')):
            raise ValueError('output inside existing results/snapshot is forbidden')


def reserve_output(output, source=None, runtime_prefix=None):
    out = no_symlinks(output)
    protected_destination(out, runtime_prefix)
    if source is not None:
        src = no_symlinks(source)
        if not stat.S_ISREG(src.stat().st_mode):
            raise ValueError('input must be a regular file')
        if out.is_relative_to(src.parent) or src.parent.is_relative_to(out):
            raise ValueError('input/output overlap is forbidden')
    if out.exists():
        raise ValueError('output reuse is forbidden')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir(mode=0o700)  # Exclusive reservation; no overwrite/cleanup on failure.
    return out


def private_caches(out):
    cache = out / '.cache'
    cache.mkdir(mode=0o700)
    os.environ.update(MPLCONFIGDIR=str(cache / 'matplotlib'),
                      NUMBA_CACHE_DIR=str(cache / 'numba'), PYTHONDONTWRITEBYTECODE='1')
    sys.dont_write_bytecode = True


def code_identity():
    names = sorted(p.name for p in PACKAGE.iterdir()
                   if p.is_file() and p.name != 'VERIFICATION.json'
                   and (p.suffix in {'.py', '.json', '.md', '.lock'} or p.name == '.gitignore'))
    result = {'code_sha256': {n: digest(PACKAGE / n) for n in names},
              'tested_commit': None, 'package_git_status': None}
    try:
        subprocess.run(['git', 'ls-files', '--error-unmatch', 'workflow.py'], cwd=PACKAGE,
                       check=True, capture_output=True)
        result['tested_commit'] = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=PACKAGE, text=True).strip()
        result['package_git_status'] = subprocess.check_output(
            ['git', 'status', '--porcelain', '--', '.'], cwd=PACKAGE, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        pass  # Copied package: hashes remain authoritative; Git identity is unknown.
    return result


def runtime_identity(runtime_prefix=None):
    prefix = selected_runtime(runtime_prefix)
    if Path(sys.prefix).resolve() != prefix.resolve():
        raise ValueError(f'runtime mismatch: interpreter sys.prefix={sys.prefix}; selected={prefix}')
    if sys.version_info[:2] != (3, 12):
        raise ValueError('runtime requires Python 3.12')
    receipt = prefix / 'install-report.json'
    no_symlinks(receipt)
    try:
        installed = json.loads(receipt.read_text())
        canonical = lambda n: re.sub(r'[-_.]+', '-', n).lower()
        recorded = {canonical(item['metadata']['name']): item['metadata']['version']
                    for item in installed['install']}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError(f'runtime install receipt is missing or invalid: {receipt}') from exc
    pins = {}
    for line in (PACKAGE / 'requirements.lock').read_text().splitlines():
        if line and not line.startswith('#'):
            name, version = line.split('==')
            try:
                actual = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError as exc:
                raise ValueError(f'runtime missing pinned distribution: {name}') from exc
            if actual != version:
                raise ValueError(f'runtime version mismatch for {name}: {actual} != {version}')
            if recorded.get(canonical(name)) != version:
                raise ValueError(f'runtime install receipt disagrees with pin for {name}')
            pins[name] = actual
    return {'prefix': str(prefix), 'sys_prefix': sys.prefix, 'base_prefix': sys.base_prefix,
            'python': sys.version, 'installer_pip': importlib.metadata.version('pip'), 'versions': pins,
            'install_report_sha256': digest(receipt)}


def verify_runtime_unchanged(report, runtime_prefix=None):
    if report.get('runtime') is None:
        return  # No successful initial runtime check; do not invent an identity.
    try:
        report['runtime_after'] = runtime_identity(runtime_prefix)
        report['runtime_unchanged'] = report['runtime'] == report['runtime_after']
    except Exception as exc:
        report['runtime_unchanged'] = False
        report['runtime_after_error'] = f'{type(exc).__name__}: {exc}'
    if not report['runtime_unchanged']:
        report['status'] = 'FAIL'
        report['runtime_check'] = 'FAIL'


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*', value):
        raise ValueError('missing or ambiguous ID/perturbation; use one alphanumeric/hyphen token')
    return value


def validate(data):
    if data.get('schema') != 1:
        raise ValueError('schema must be 1')
    genes = data['genes']
    if not isinstance(genes, list) or not genes:
        raise ValueError('genes must be a nonempty list')
    for gene in genes:
        identifier(gene)
    if len(set(genes)) != len(genes):
        raise ValueError('duplicate gene ID')
    if genes.count('QcToy') != 1:
        raise ValueError('fixture requires the fictional QcToy sentinel')
    samples = {}
    for sample in data['samples']:
        for key in KEYS:
            identifier(sample.get(key))
        sid = sample['sample_id']
        if sid in samples:
            raise ValueError('duplicate sample ID')
        if sample['perturbation'] not in {'control', 'pulseQ'}:
            raise ValueError('ambiguous perturbation assignment')
        samples[sid] = {k: sample[k] for k in KEYS}
    if not samples:
        raise ValueError('samples must be nonempty')
    seen, sizes, matched = set(), {s: 0 for s in samples}, {}
    cells = data['cells']
    if not isinstance(cells, list) or not cells:
        raise ValueError('cells must be nonempty')
    for cell in cells:
        cid = identifier(cell.get('cell_id'))
        if cid in seen:
            raise ValueError('duplicate cell ID')
        seen.add(cid)
        for key in KEYS:
            identifier(cell.get(key))
        sid = cell['sample_id']
        if sid not in samples or {k: cell[k] for k in KEYS} != samples[sid]:
            raise ValueError('contradictory sample mapping')
        sizes[sid] += 1
    for sample in samples.values():
        matched.setdefault((sample['experiment_id'], sample['donor_id']), set()).add(sample['perturbation'])
    if len({d for _, d in matched}) < 2 or any(v != {'control', 'pulseQ'} for v in matched.values()):
        raise ValueError('require at least two donors with matched control/pulseQ samples')
    if any(n < 2 for n in sizes.values()):
        raise ValueError('require multiple cells per sample')
    counts = data['counts']
    if not isinstance(counts, list) or len(counts) != len(cells):
        raise ValueError('count matrix shape mismatch')
    for row in counts:
        if not isinstance(row, list) or len(row) != len(genes):
            raise ValueError('count matrix shape mismatch')
        for value in row:
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) or value < 0 or value != int(value)
                    or value > 2**31 - 1):
                raise ValueError('raw counts must be finite nonnegative integers <= 2^31-1')
    return data


def run(source, output, runtime_prefix=None):
    # Unsafe paths/reuse fail on stderr before writing anything at that destination.
    out = reserve_output(output, source, runtime_prefix)
    report = {'schema': 1, 'status': 'FAIL', 'stages': {s: 'NOT_RUN' for s in STAGES},
              'source_sha256_before': digest(source), 'identity': code_identity(),
              'runtime_check': 'NOT_RUN'}
    stage = 'validate'
    try:
        # Imports and API work happen only after validating the original JSON.
        data = validate(json.loads(Path(source).read_text()))
        report['stages'][stage] = 'PASS'
        stage = 'runtime'
        report['runtime'] = runtime_identity(runtime_prefix)
        report['runtime_check'] = 'PASS'
        private_caches(out)
        stage = 'qc'
        import anndata as ad
        import numpy as np
        import pandas as pd
        import scanpy as sc
        sc.settings.n_jobs = 1
        obs = pd.DataFrame(data['cells']).set_index('cell_id')
        var = pd.DataFrame(index=pd.Index(data['genes'], name='gene_id'))
        a = ad.AnnData(np.asarray(data['counts'], dtype=np.int64), obs=obs, var=var)
        a.layers['counts'] = a.X.copy()
        a.var['toy_qc'] = a.var_names == 'QcToy'
        stage = 'qc'
        sc.pp.calculate_qc_metrics(a, qc_vars=['toy_qc'], layer='counts',
                                  percent_top=None, log1p=False, inplace=True)
        # Scanpy gives NaN percentage for zero-total cells; encode as null in JSON.
        qc = []
        for cid, row in a.obs.iterrows():
            pct = float(row['pct_counts_toy_qc'])
            qc.append({'cell_id': cid, 'total': int(row['total_counts']),
                       'detected': int(row['n_genes_by_counts']),
                       'qc_total': int(row['total_counts_toy_qc']),
                       'qc_percent': pct if math.isfinite(pct) else None})
        write_json(out / 'qc.json', qc)
        report['stages'][stage] = 'PASS'
        stage = 'filter'
        keep = ((a.obs.total_counts >= 8) & (a.obs.n_genes_by_counts >= 2)
                & (a.obs.pct_counts_toy_qc <= 25))
        a = a[keep].copy()
        if not a.n_obs:
            raise ValueError('no cells pass the fixture-specific filter')
        # Keep donor/sample identity; require multiple surviving cells in every sample.
        sizes = a.obs.groupby('sample_id', observed=True).size().to_dict()
        if set(sizes) != {s['sample_id'] for s in data['samples']} or min(sizes.values()) < 2:
            raise ValueError('filter loses sample coverage or multiple-cell requirement')
        report['retained_cell_ids'] = a.obs_names.tolist()
        report['stages'][stage] = 'PASS'
        stage = 'normalize_log'
        a.X = a.X.astype(np.float64)
        sc.pp.normalize_total(a, target_sum=100, exclude_highly_expressed=False)
        sc.pp.log1p(a)
        a.uns['tutorial'] = {'target_sum': 100, 'filter': 'total>=8; detected>=2; QcToy%<=25',
                             'interpretation': 'synthetic mechanics only'}
        report['stages'][stage] = 'PASS'
        stage = 'aggregate'
        pb = sc.get.aggregate(a, by=KEYS, func='sum', layer='counts')
        rows = []
        for i, (_, row) in enumerate(pb.obs.iterrows()):
            sums = np.asarray(pb.layers['sum'])[i]
            if not np.all(np.isfinite(sums) & (sums == np.floor(sums))):
                raise ValueError('aggregate lost integer-valued counts')
            rows.append({**{k: str(row[k]) for k in KEYS},
                         'n_cells': int(row['n_obs_aggregated']), 'counts': sums.astype(np.int64).tolist()})
        write_json(out / 'pseudobulk.json', rows)
        pb.write_h5ad(out / 'pseudobulk.h5ad')
        report['stages'][stage] = 'PASS'
        stage = 'roundtrip'
        a.write_h5ad(out / 'readout.h5ad')
        loaded = ad.read_h5ad(out / 'readout.h5ad')
        if (loaded.obs_names.tolist() != a.obs_names.tolist()
                or loaded.var_names.tolist() != a.var_names.tolist()
                or not loaded.obs[KEYS].astype(str).equals(a.obs[KEYS].astype(str))
                or not np.issubdtype(loaded.layers['counts'].dtype, np.integer)
                or not np.array_equal(loaded.layers['counts'], a.layers['counts'])
                or not np.array_equal(loaded.X, a.X)):
            raise ValueError('AnnData round trip mismatch')
        report['stages'][stage] = 'PASS'
        report['status'] = 'PASS'
    except Exception as exc:
        if stage == 'runtime':
            report['runtime_check'] = 'FAIL'
        else:
            report['stages'][stage] = 'FAIL'
        report['failed_stage'] = stage
        report['error'] = f'{type(exc).__name__}: {exc}'
        (out / 'error.log').write_text(traceback.format_exc())
    finally:
        verify_runtime_unchanged(report, runtime_prefix)
        report['source_sha256_after'] = digest(source)
        report['input_unchanged'] = report['source_sha256_before'] == report['source_sha256_after']
        report['code_unchanged'] = report['identity'] == code_identity()
        if not report['input_unchanged'] or not report['code_unchanged']:
            report['status'] = 'FAIL'
        report['artifacts_sha256'] = {p.name: digest(p) for p in sorted(out.iterdir()) if p.is_file()}
        write_json(out / 'report.json', report)
    print(json.dumps({'status': report['status'], 'output': str(out)}))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--runtime-prefix', type=Path, default=PACKAGE / '.runtime')
    args = parser.parse_args()
    try:
        sys.exit(run(args.input, args.output, args.runtime_prefix))
    except (ValueError, OSError) as exc:
        print(f'REFUSED: {exc}', file=sys.stderr)
        sys.exit(2)
