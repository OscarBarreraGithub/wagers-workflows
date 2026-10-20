"""Bounded actual CLI and sklearn checks. No benchmark-win pass condition."""
import contextlib
import importlib.metadata
import inspect
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

from contract import (COLUMNS, IDENTITY, OUTCOMES, Refusal, csv_bytes, digest,
                      encoded, ensure_output, load_state, read_csv, verify_bundle)

HERE = Path(__file__).resolve().parent
SOURCES = ['.gitignore', 'requirements.txt', 'contract.py', 'proposer.py',
           'simulator.py', 'tutorial.py', 'suite.py', 'README.md', 'AGENT_PROMPT.md']
PINS = {'pip': '25.0.1', 'numpy': '2.2.6', 'scipy': '1.15.3', 'scikit-learn': '1.6.1',
        'joblib': '1.4.2', 'threadpoolctl': '3.6.0'}


def file_hashes(root):
    return {str(p.relative_to(root)): digest(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}


def provenance():
    import sklearn
    from sklearn.gaussian_process import GaussianProcessRegressor
    # Git is supporting provenance only: copied folders still record exact source bytes.
    git = {'origin': 'copied_or_unavailable', 'commit': None, 'status': None}
    try:
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        def run(*args):
            return subprocess.check_output(['git', '-C', str(HERE), *args], env=env, text=True, stderr=subprocess.DEVNULL, timeout=10).strip()
        for source in SOURCES:
            run('ls-files', '--error-unmatch', source)
        git = {'origin': 'git_checkout', 'commit': run('rev-parse', 'HEAD'),
               'status': run('status', '--porcelain', '--', '.')}
    except (OSError, subprocess.SubprocessError):
        pass
    freeze = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze', '--all'], text=True, timeout=30)
    artifacts = {}
    for name in PINS:
        dist = importlib.metadata.distribution(name)
        hashes = {str(f): digest(Path(dist.locate_file(f)).read_bytes()) for f in dist.files
                  if not str(f).endswith('.pyc') and Path(dist.locate_file(f)).is_file()}
        artifacts[name] = {'file_count': len(hashes), 'files_sha256': digest(encoded(hashes))}
    env = {'installed_artifact_hashes': artifacts, 'python': platform.python_version(), 'implementation': platform.python_implementation(),
           'platform': platform.platform(), 'machine': platform.machine(),
           'packages': {name: importlib.metadata.version(name) for name in PINS},
           'pip_freeze': freeze, 'pip_freeze_sha256': digest(freeze.encode()),
           'python_executable_sha256': digest(Path(sys.executable).read_bytes()),
           'sklearn_gpr_source_sha256': digest(Path(inspect.getfile(GaussianProcessRegressor)).read_bytes()),
           'sklearn_version': sklearn.__version__}
    return {'git': git, 'environment_sha256': digest(encoded(env)), 'sources': {name: digest((HERE / name).read_bytes()) for name in SOURCES}, 'environment': env}


def linux_status(execution_platform, final_status):
    """Classify this run only; a non-Linux run cannot validate Linux."""
    if execution_platform != 'Linux':
        return 'NOT_RUN'
    return 'PASS' if final_status == 'PASS' else 'FAIL'


def run(out):
    # Never create suite output in/around sources or overwrite an earlier run.
    out = ensure_output(out, (HERE / source for source in SOURCES))
    out.mkdir(parents=True)
    started = time.monotonic()
    checks, commands = [], []
    report = {'status': 'FAIL', 'fictional': True, 'seed': 17, 'checks': checks,
              'commands': commands, 'execution_platform': platform.system(),
              'superiority_required': False}

    def check(name, condition, detail=None):
        checks.append({'name': name, 'status': 'PASS' if condition else 'FAIL', 'detail': detail})
        if not condition:
            raise AssertionError(name)

    def cli(label, args, ok=True):
        command = [sys.executable, str(HERE / 'tutorial.py'), *map(str, args)]
        result = subprocess.run(command, text=True, capture_output=True, timeout=60,
                                env={**os.environ, 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'})
        log = {'label': label, 'argv': command, 'returncode': result.returncode,
               'stdout': result.stdout, 'stderr': result.stderr}
        commands.append(log)
        with (out / 'commands.jsonl').open('a') as f:
            f.write(json.dumps(log) + '\n')
        try:
            status = json.loads(result.stdout)['status']
        except (ValueError, KeyError):
            status = None
        check(label, (result.returncode == 0 and status == 'PASS') if ok else
              (result.returncode == 2 and status == 'FAIL'), {'returncode': result.returncode})

    def write_csv(name, fields, rows):
        path = out / name
        path.write_bytes(csv_bytes(fields, rows))
        return path

    try:
        report['provenance'] = provenance()
        (out/'environment.json').write_bytes(encoded(report['provenance']['environment']))
        check('exact_runtime_pins', report['provenance']['environment']['packages'] == PINS and
              platform.python_version() == '3.12.12')
        from proposer import ALPHA, BETA, model, predictions
        import numpy as np
        # Independent scalar calculation, no sklearn kernels/linear algebra in expected values.
        # One observation x=(0,0), y=2, covariance=1, alpha=.01.
        # At x*=(.45,0): cross covariance exp(-1/2), prior variance 1.
        gp = model().fit([[0., 0.]], [2.])
        mean, std = gp.predict([[.45, 0.]], return_std=True)
        k = math.exp(-.5)
        expected_mean, expected_std = 2*k/(1+ALPHA), math.sqrt(1-k*k/(1+ALPHA))
        check('independent_fixed_gp_mean_std_score', abs(mean[0]-expected_mean) < 1e-12 and
              abs(std[0]-expected_std) < 1e-12 and
              abs((mean[0]+BETA*std[0])-(expected_mean+1.5*expected_std)) < 1e-12,
              {'mean': float(mean[0]), 'std': float(std[0]), 'score': float(mean[0]+BETA*std[0]),
               'expected_mean': expected_mean, 'expected_std': expected_std})
        check('fixed_model_no_optimizer', gp.optimizer is None and gp.normalize_y is False and
              gp.kernel_.length_scale == .45 and gp.kernel_.n_dims == 0 and gp.alpha == .01)
        check('selection_has_no_simulator_import', 'simulator' not in sys.modules)
        sim, initial = out / 'simulator-only', out / 'v000'
        cli('generate', ['generate', '--out', sim])
        sim_before = file_hashes(sim)
        cli('init', ['init', '--candidates', sim/'candidates.csv', '--outcomes', sim/'initial-outcomes.csv', '--out', initial])
        check('candidate_and_initial_bounds', len(load_state(initial)['candidates']) == 200 and len(load_state(initial)['observed']) == 6)
        p1 = out / 'adaptive-p1'
        cli('first_proposal', ['propose', '--state', initial, '--out', p1])
        scores = read_csv(p1/'scores.csv', ['target_id', 'mean', 'std', 'score'])
        ranked = sorted(scores, key=lambda r: (-float(r['score']), r['target_id']))
        pending = load_state(p1)['pending']
        check('transparent_score_and_top_batch', all(abs(float(r['score'])-(float(r['mean'])+1.5*float(r['std']))) < 1e-12 for r in scores) and
              [r['target_id'] for r in pending] == [r['target_id'] for r in ranked[:4]])
        measured = {r['target_id'] for r in load_state(initial)['observed']}
        check('selection_filters_measured_excluded_invalid', not measured.intersection(r['target_id'] for r in scores) and
              not {'FABLE-0000', 'FABLE-0001'}.intersection(r['target_id'] for r in scores) and len({r['target_id'] for r in pending}) == 4)
        # Change every hidden value, leave initial observations intact, then propose again.
        from simulator import TRUTH
        hidden = read_csv(sim/'truth.csv', TRUTH)
        changed = [{**r, 'latent_value': -999., 'measured_value': 888.} for r in hidden]
        changed_truth = write_csv('changed-truth.csv', TRUTH, changed)
        # Place changed truth at the original evaluator location temporarily in a separate copy;
        # no input state/path argument to propose can carry it.
        import shutil
        changed_sim = out / 'changed-evaluator'
        shutil.copytree(sim, changed_sim)
        (changed_sim/'truth.csv').write_bytes(changed_truth.read_bytes())
        changed_manifest = json.loads((changed_sim/'manifest.json').read_text())
        changed_manifest['files']['truth.csv'] = digest(changed_truth.read_bytes())
        (changed_sim/'manifest.json').write_bytes(encoded(changed_manifest))
        p1_again = out / 'changed-truth-proposal'
        # Run from changed evaluator cwd; proposer still receives only the original observed state.
        old_cwd = Path.cwd()
        os.chdir(changed_sim)
        try:
            cli('proposal_after_hidden_truth_change', ['propose', '--state', initial, '--out', p1_again])
        finally:
            os.chdir(old_cwd)
        check('no_truth_leakage_byte_identical_proposal', file_hashes(p1) == file_hashes(p1_again))
        # Success CSV comes from separate simulator, not selection.
        m1 = out / 'adaptive-m1'
        cli('simulate_first_batch', ['simulate', '--state', p1, '--truth', sim/'truth.csv', '--out', m1])
        correct = read_csv(m1/'outcomes.csv', OUTCOMES)
        original_state = file_hashes(initial), file_hashes(p1)
        bad_cases = {}
        bad_cases['missing_target'] = correct[:-1]
        bad_cases['duplicate_target'] = [*correct, correct[0]]
        bad_cases['unknown_target'] = [{**correct[0], 'target_id': 'FABLE-9999'}, *correct[1:]]
        bad_cases['already_measured'] = [{**correct[0], 'target_id': next(iter(measured))}, *correct[1:]]
        for status, tid in [('excluded', 'FABLE-0000'), ('invalid', 'FABLE-0001')]:
            bad_cases[status] = [{**correct[0], 'target_id': tid}, *correct[1:]]
        for key, value in [('sample_id', 'wrong-sample'), ('round_id', 'r002'), ('outcome_id', 'wrong-outcome'),
                           ('value', 'nan'), ('value', 'inf'), ('value', '-inf'), ('value', ''), ('value', 'broken')]:
            bad_cases[f'bad_{key}_{value or "missing"}'] = [{**correct[0], key: value}, *correct[1:]]
        bad_cases['contradictory_duplicate_outcome'] = [*correct, {**correct[0], 'value': float(correct[0]['value'])+10}]
        bad_cases['duplicate_sample'] = [correct[0], {**correct[1], 'sample_id': correct[0]['sample_id']}, *correct[2:]]
        bad_cases['duplicate_outcome'] = [correct[0], {**correct[1], 'outcome_id': correct[0]['outcome_id']}, *correct[2:]]
        for name, rows in bad_cases.items():
            bad_csv = write_csv(f'{name}.csv', OUTCOMES, rows)
            rejected = out / f'refused-{name}'
            cli(f'import_reject_{name}', ['import', '--state', p1, '--outcomes', bad_csv, '--out', rejected], False)
            check(f'{name}_state_unchanged_no_output', original_state == (file_hashes(initial), file_hashes(p1)) and not rejected.exists())
        for label, args, output in [
            ('pending_batch', ['propose', '--state', p1, '--out', out/'pending-refused'], out/'pending-refused'),
            ('nested_output', ['propose', '--state', initial, '--out', initial/'nested'], initial/'nested'),
            ('ancestor_output', ['propose', '--state', initial, '--out', out], None),
            ('existing_output', ['propose', '--state', initial, '--out', p1], None),
            ('oversized_batch', ['propose', '--state', initial, '--batch', 5, '--out', out/'large-refused'], out/'large-refused'),
            ('zero_batch', ['propose', '--state', initial, '--batch', 0, '--out', out/'zero-refused'], out/'zero-refused')]:
            cli(f'reject_{label}', args, False)
            check(f'{label}_preserves_states', original_state == (file_hashes(initial), file_hashes(p1)) and (output is None or not output.exists()))
        # A symlink output cannot bypass overlap or overwrite controls.
        link = out / 'linked-output'
        link.symlink_to(initial, target_is_directory=True)
        cli('reject_symlink_output', ['propose', '--state', initial, '--out', link/'nested'], False)
        check('symlink_refusal_preserves_state', original_state == (file_hashes(initial), file_hashes(p1)))
        link.unlink()
        # Tampering is detected even if the edited child's own manifest is refreshed:
        # validated transition refuses a changed prior observation relative to its parent.
        tampered = out / 'tampered-state'
        shutil.copytree(p1, tampered)
        raw = json.loads((tampered/'state.json').read_text())
        raw['observed'][0]['value'] += 1
        (tampered/'state.json').write_bytes(encoded(raw))
        refused = out / 'tamper-refused'
        cli('reject_tampered_hash', ['import', '--state', tampered, '--outcomes', m1/'outcomes.csv', '--out', refused], False)
        manifest = json.loads((tampered/'manifest.json').read_text())
        manifest['files']['state.json'] = digest((tampered/'state.json').read_bytes())
        (tampered/'manifest.json').write_bytes(encoded(manifest))
        cli('reject_altered_prior_record_with_refreshed_child_hash', ['import', '--state', tampered, '--outcomes', m1/'outcomes.csv', '--out', refused], False)
        check('tamper_refusal_no_output', not refused.exists())
        # Invalid initial catalog/outcomes and extra truth columns are refused before output.
        candidates = read_csv(sim/'candidates.csv', COLUMNS)
        invalid_catalogs = [('duplicate_candidate', COLUMNS, [candidates[0], candidates[0], *candidates[2:]]),
                            ('nonfinite_feature', COLUMNS, [{**candidates[0], 'f1': 'nan'}, *candidates[1:]]),
                            ('truth_column', COLUMNS+['truth'], [{**r, 'truth': 1} for r in candidates])]
        for label, fields, rows in invalid_catalogs:
            bad = write_csv(f'{label}.csv', fields, rows)
            cli(f'reject_{label}', ['init', '--candidates', bad, '--outcomes', sim/'initial-outcomes.csv', '--out', out/f'bad-{label}'], False)
            check(f'{label}_no_output', not (out/f'bad-{label}').exists())
        # Corrected retry uses the same desired output after every earlier refusal.
        a1 = out / 'refused-missing_target'
        before_scores = {r['target_id']: r['mean'] for r in scores}
        cli('corrected_retry_import', ['import', '--state', p1, '--outcomes', m1/'outcomes.csv', '--out', a1])
        check('import_preserves_identities_and_values', load_state(a1)['observed'][-4:] ==
              [{**r, 'value': float(r['value'])} for r in correct])
        after_scores = predictions(load_state(a1))
        delta = max(abs(r['mean']-float(before_scores[r['target_id']])) for r in after_scores)
        check('imported_observations_change_next_actual_fit', delta > 1e-6, {'max_mean_change': delta})
        cli('reject_repeated_import', ['import', '--state', a1, '--outcomes', m1/'outcomes.csv', '--out', out/'repeated-refused'], False)
        # Complete adaptive and seeded-random branches: identical initial state, 6+3*4 budget.
        finals = {}
        for strategy in ('adaptive', 'random'):
            current = a1 if strategy == 'adaptive' else initial
            for r in range(2 if strategy == 'adaptive' else 1, 4):
                proposal, measurement, imported = [out/f'{strategy}-{kind}{r}' for kind in ('p', 'm', 'v')]
                cli(f'{strategy}_propose_{r}', ['propose', '--state', current, '--strategy', strategy, '--out', proposal])
                cli(f'{strategy}_simulate_{r}', ['simulate', '--state', proposal, '--truth', sim/'truth.csv', '--out', measurement])
                cli(f'{strategy}_import_{r}', ['import', '--state', proposal, '--outcomes', measurement/'outcomes.csv', '--out', imported])
                current = imported
            finals[strategy] = current
        cli('budget_exhausted', ['propose', '--state', finals['adaptive'], '--out', out/'budget-refused'], False)
        cli('unequal_budget_comparison_refused', ['evaluate', '--adaptive', finals['adaptive'], '--random', initial,
                                               '--truth', sim/'truth.csv', '--out', out/'unequal-refused'], False)
        cli('evaluate_equal_budget', ['evaluate', '--adaptive', finals['adaptive'], '--random', finals['random'],
                                     '--truth', sim/'truth.csv', '--out', out/'evaluation'])
        report['comparison'] = json.loads((out/'evaluation'/'comparison.json').read_text())
        check('equal_initial_seed_and_18_outcomes', report['comparison']['seed'] == 17 and report['comparison']['equal_budget'] == 18 and
              all(len(load_state(p)['observed']) == 18 for p in finals.values()))
        check('all_original_inputs_unchanged', sim_before == file_hashes(sim) and original_state == (file_hashes(initial), file_hashes(p1)))
        check('source_bytes_unchanged', report['provenance']['sources'] == {name: digest((HERE/name).read_bytes()) for name in SOURCES})
        # Verify every regular generated bundle that has not deliberately been tampered with.
        for directory in out.iterdir():
            if directory.is_dir() and (directory/'manifest.json').exists() and directory != tampered:
                verify_bundle(directory)
        check('generated_bundle_hashes_verified', True)
        report['status'] = 'PASS'
    except Exception as exc:
        report['status'] = 'FAIL'
        report['error'] = f'{type(exc).__name__}: {exc}'
        (out/'failure.txt').write_text(traceback.format_exc())
    report['linux'] = linux_status(report['execution_platform'], report['status'])
    report['elapsed_seconds'] = round(time.monotonic()-started, 3)
    report['passed'] = sum(r['status'] == 'PASS' for r in checks)
    report['failed'] = sum(r['status'] == 'FAIL' for r in checks)
    (out/'suite-report.json').write_bytes(encoded(report))
    (out/'evidence-hashes.json').write_bytes(encoded(file_hashes(out)))
    print(json.dumps({'status': report['status'], 'passed': report['passed'], 'failed': report['failed'],
                      'report': str(out/'suite-report.json')}))
    return 0 if report['status'] == 'PASS' else 1
