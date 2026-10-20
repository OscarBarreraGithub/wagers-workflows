"""Focused classification/syntax/error-report check, not a model or Linux run."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
from unittest.mock import patch

import suite

package = Path.cwd().resolve()
out = package/'runs/reporting-revision1'
out.mkdir()
checks = []
def check(name, passed):
    checks.append({'name':name,'status':'PASS' if passed else 'FAIL'})
    if not passed:
        raise AssertionError(name)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def hashes(root): return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()}
report = {'status':'FAIL', 'checks':checks,
          'tested_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
          'git_status_before':subprocess.check_output(['git','status','--porcelain'],text=True).strip(),
          'source_sha256':{name:sha(package/name) for name in suite.SOURCES},
          'actual_host':platform.system(), 'python':platform.python_version(),
          'python_executable_sha256':sha(Path(sys.executable)),
          'full_suite_executed':False, 'model_executed':False, 'actual_linux_execution':'NOT_RUN',
          'note':'Injected platform labels below are classifier/error-report fixtures, not Linux execution or numeric results.'}
historical_before = {name:hashes(package/'runs'/name) for name in ['local-01','shared-paths-01']}
try:
    for host,status,expected in [('Linux','PASS','PASS'),('Linux','FAIL','FAIL'),
                                 ('Linux','RUNNING','FAIL'),('Linux',None,'FAIL'),
                                 ('Darwin','PASS','NOT_RUN'),('Darwin','FAIL','NOT_RUN'),
                                 ('Windows','PASS','NOT_RUN'),('FreeBSD','FAIL','NOT_RUN')]:
        check(f'classifier_{host}_{status}', suite.linux_status(host,status)==expected)
    for source in package.glob('*.py'):
        compile(source.read_text(),str(source),'exec')
        check(f'syntax_{source.name}',True)
    report['error_path_fixtures'] = []
    for host,expected in [('Linux','FAIL'),('Darwin','NOT_RUN')]:
        fixture = out/f'injected-{host}-failure'
        stdout = io.StringIO()
        # Failure is injected before any sklearn import, CLI command or model fit.
        with patch.object(suite.platform,'system',return_value=host), \
             patch.object(suite,'provenance',side_effect=RuntimeError('injected reporting-only failure')), \
             contextlib.redirect_stdout(stdout):
            code = suite.run(fixture)
        saved = json.loads((fixture/'suite-report.json').read_text())
        check(f'{host}_exception_reports_fail',code==1 and saved['status']=='FAIL' and
              json.loads(stdout.getvalue())['status']=='FAIL' and saved['linux']==expected and
              saved['execution_platform']==host and saved['error']=='RuntimeError: injected reporting-only failure')
        report['error_path_fixtures'].append({'simulated_platform':host,'exitcode':code,
                  'linux_field':saved['linux'],'status':saved['status'],'stdout':json.loads(stdout.getvalue()),
                  'suite_report_sha256':sha(fixture/'suite-report.json')})
    check('no_model_simulator_or_sklearn_imported',not {'sklearn','proposer','simulator'}.intersection(sys.modules))
    check('historic_run_files_unchanged',historical_before=={name:hashes(package/'runs'/name) for name in historical_before})
    check('source_bytes_unchanged',report['source_sha256']=={name:sha(package/name) for name in suite.SOURCES})
    unchanged = ['contract.py','proposer.py','simulator.py','tutorial.py','requirements.txt','AGENT_PROMPT.md']
    check('model_selection_ledger_and_runtime_pins_unchanged', all(
        (package/name).read_bytes()==subprocess.check_output(['git','show',f'12bfa2b:onboarding/tutorials/adaptive-screen/{name}']) for name in unchanged))
    report['status']='PASS'
except Exception as exc:
    report['error']=f'{type(exc).__name__}: {exc}'
report['passed']=sum(c['status']=='PASS' for c in checks)
report['failed']=sum(c['status']=='FAIL' for c in checks)
(out/'focused-report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':report['status'],'passed':report['passed'],'failed':report['failed']}))
sys.exit(0 if report['status']=='PASS' else 1)
