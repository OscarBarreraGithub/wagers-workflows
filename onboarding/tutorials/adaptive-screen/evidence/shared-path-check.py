"""Focused integration check; no full suite or deployment. Run from package root."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

package = Path.cwd().resolve()
root = package/'runs/shared-paths-01'
root.mkdir()
shared = root/'shared-readonly'
shared.mkdir()
source_names = ['.gitignore', 'requirements.txt', 'contract.py', 'proposer.py',
                'simulator.py', 'tutorial.py', 'suite.py', 'README.md', 'AGENT_PROMPT.md']
for name in source_names:
    shutil.copy2(package/name, shared/name)
user = root/'users/amy own work'
cwd = root/'unrelated-cwd'
cwd.mkdir()
commands = []
checks = []

def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def files(path):
    return {str(p.relative_to(path)): hash_file(p) for p in sorted(path.rglob('*')) if p.is_file()}

def check(name, value):
    checks.append({'name': name, 'status': 'PASS' if value else 'FAIL'})
    if not value:
        raise AssertionError(name)

def cli(name, args, success=True):
    argv = [sys.executable, '-B', str(shared/'tutorial.py'), *map(str, args)]
    process = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=60,
                             env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'})
    commands.append({'name': name, 'argv': argv, 'returncode': process.returncode,
                     'stdout': process.stdout, 'stderr': process.stderr})
    expected = (0, 'PASS') if success else (2, 'FAIL')
    check(name, (process.returncode, json.loads(process.stdout)['status']) == expected)

report = {'status': 'FAIL', 'checks': checks, 'commands': commands,
          'tested_commit': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
          'source_sha256': {name:hash_file(package/name) for name in source_names},
          'git_status_before': subprocess.check_output(['git','status','--porcelain'],text=True).strip(),
          'python': sys.version, 'python_executable_sha256': hash_file(Path(sys.executable)),
          'full_suite_rerun': False, 'deployment': 'NOT_RUN'}
for p in shared.iterdir():
    p.chmod(0o444)
shared.chmod(0o555)
shared_before = files(shared)
old_run_before = files(package/'runs/local-01')
try:
    cli('generate_to_new_absolute_user_dir', ['generate','--out',user/'sim'])
    cli('init_to_separate_user_state_dir', ['init','--candidates',user/'sim/candidates.csv',
           '--outcomes',user/'sim/initial-outcomes.csv','--out',user/'state/v000'])
    cli('propose_from_readonly_software', ['propose','--state',user/'state/v000','--out',user/'state/v001'])
    cli('simulate_to_separate_measurement_dir', ['simulate','--state',user/'state/v001',
           '--truth',user/'sim/truth.csv','--out',user/'measurements/round1'])
    cli('import_to_new_user_snapshot', ['import','--state',user/'state/v001',
           '--outcomes',user/'measurements/round1/outcomes.csv','--out',user/'state/v002'])
    records_before = files(user)
    for name, out in [('source', shared/'forbidden-output'),
                      ('active_runtime', Path(sys.prefix)/'adaptive-forbidden-output'),
                      ('base_runtime', Path(sys.base_prefix)/'adaptive-forbidden-output'),
                      ('prior_snapshot', user/'sim/nested-output')]:
        check(name+'_destination_initially_absent', not out.exists())
        cli('reject_output_under_'+name, ['generate','--out',out], False)
        check(name+'_refusal_has_no_output', not out.exists())
    cli('reject_repeated_import', ['import','--state',user/'state/v002',
           '--outcomes',user/'measurements/round1/outcomes.csv','--out',user/'state/refused'], False)
    check('refusals_preserve_all_user_records', records_before == files(user))
    # The suite uses the same guard with explicit source inputs; check its external
    # destination is accepted, without rerunning the full statistical suite.
    code = ('import contract; from pathlib import Path; '
            f'out=contract.ensure_output({str(user/"evidence/fresh-suite")!r}, '
            '[Path(contract.__file__)]); print(out)')
    process = subprocess.run([sys.executable,'-B','-c',code],cwd=shared,
                             capture_output=True,text=True,timeout=10)
    commands.append({'name':'external_suite_destination_guard_only','argv':[sys.executable,'-B','-c',code],
                     'returncode':process.returncode,'stdout':process.stdout,'stderr':process.stderr})
    check('external_suite_destination_guard_accepts', process.returncode == 0 and
          process.stdout.strip() == str(user/'evidence/fresh-suite'))
    accepted = json.loads((user/'state/v002/state.json').read_text())
    check('user_fit_imported_four_outcomes', len(accepted['observed']) == 10 and not accepted['pending'])
    check('readonly_source_tree_unchanged_no_bytecode', files(shared) == shared_before and not (shared/'__pycache__').exists())
    check('original_full_suite_evidence_unchanged', files(package/'runs/local-01') == old_run_before)
    check('source_bytes_unchanged', report['source_sha256'] == {name:hash_file(package/name) for name in source_names})
    report['status'] = 'PASS'
except Exception as error:
    report['error'] = f'{type(error).__name__}: {error}'
finally:
    # Restore disposable fixture permissions so it can be cleaned up by its owner.
    shared.chmod(0o755)
    for p in shared.iterdir():
        p.chmod(0o644)
    report['passed'] = sum(c['status'] == 'PASS' for c in checks)
    report['failed'] = sum(c['status'] == 'FAIL' for c in checks)
    (root/'path-check-report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':report['status'],'passed':report['passed'],'failed':report['failed']}))
sys.exit(0 if report['status'] == 'PASS' else 1)
