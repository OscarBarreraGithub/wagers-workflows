> Current status: [verification and remaining gates](../../docs/current-verification.md). Execution notes below retain their historical checkpoint scope.

# Fictional adaptive-screen loop

Teach an agent to propose a finite batch, obtain a fictional measurement CSV,
validate/import it, then refit. This is a small software simulation with real
scikit-learn computation. It offers no real gene recommendations, biological
hits, wet-lab instructions, experiment control, robot integration or publication.
Model standard deviation is not validated biological uncertainty or confidence.

Scope: this folder only. Existing packages, shared environments and private
papers are untouched. Local Mac execution is recorded separately after testing;
Linux remains **NOT_RUN** at this source checkpoint, pending manager validation.
Each suite report records `execution_platform` from the actual host and sets
`linux` to that run's final PASS/FAIL on Linux, or NOT_RUN on other platforms. Independent review
and integration are manager-owned; implementation alone is not review approval.

## Isolated runtime and one suite command

Use CPython **3.12.12** (tested Homebrew interpreter), outside any existing package
environment. All direct/transitive dependencies, including pip, are exact pins
in `requirements.txt`: numpy 2.2.6, scipy 1.15.3, scikit-learn 1.6.1,
joblib 1.4.2, threadpoolctl 3.6.0 and pip 25.0.1. No optimizer framework.
The ignored `.runtime/` and `runs/` stay local and are never committed.

From this folder:

```sh
/opt/homebrew/bin/python3.12 -m venv .runtime
.runtime/bin/python -m pip install --disable-pip-version-check -r requirements.txt
.runtime/bin/python -m pip check
.runtime/bin/python tutorial.py suite --out runs/local-01
```

The suite refuses an existing output directory; use a new name only when a new
run is justified. It calls the actual CLI in subprocesses and the installed
`GaussianProcessRegressor`; there is no fake backend. `suite-report.json` gives
PASS/FAIL and every check, `commands.jsonl` captures exact argv, return codes and
stdout/stderr, `environment.json` records versions and artifact hashes, and
`evidence-hashes.json` hashes all retained evidence except itself. The report
records exact Git commit (or honestly reports copied/unavailable), package Git
status, nine source hashes, Python executable/GPR source hashes, a pip-freeze
hash and installed-distribution artifact fingerprints. Source hashes describe
tested bytes; a later evidence-only commit does not mean code was retested.

A suite PASS requires runtime pins, independently computed GP arithmetic,
observed-data-only proposals, changed-truth invariance, changed fits after
import, correct identity checks, failure/retry, overlap/overwrite refusals,
input preservation and an equal-budget comparison. **Adaptive superiority is
never a pass condition.** Seed 17 and all model settings are declared before
execution; do not search seeds or tune to make adaptive win. The suite uses
200 candidates, six initial observations and three batches of four: 18 total
outcomes per strategy. It is intentionally a tiny teaching example.

The Mac warning diagnosis is recorded in independent review
`51c34bf6-5925-4f10-b24a-19337c52d670`: pure-Python Cholesky recomputation of
1,320 saved proposal-score rows matched mean/std/score within 1.2e-14. The
reviewer also reproduced the matmul warnings in NumPy alone with Apple
Accelerate; finite results matched `einsum` within 1.8e-15. This supports spurious
floating-point status flags for these recorded predictions. Original warning
logs and run hashes remain intact; warnings are not suppressed. This diagnosis
does not establish that other warnings are harmless or replace the pending
manager-owned Linux full-suite execution.

## Shared software, separate user outputs

Every state/input/output path is explicit and may be absolute. No command
requires its current directory or outputs to be beneath the package. With shared
read-only software, use the installed Python and script paths and put each
user's snapshots/evidence in that user's own writable directory. For example:

```sh
/shared/adaptive-runtime/bin/python -B /shared/adaptive-screen/tutorial.py generate --out "$HOME/adaptive-tutorial/demo/sim"
/shared/adaptive-runtime/bin/python -B /shared/adaptive-screen/tutorial.py init --candidates "$HOME/adaptive-tutorial/demo/sim/candidates.csv" --outcomes "$HOME/adaptive-tutorial/demo/sim/initial-outcomes.csv" --out "$HOME/adaptive-tutorial/demo/v000"
/shared/adaptive-runtime/bin/python -B /shared/adaptive-screen/tutorial.py suite --out "$HOME/adaptive-tutorial/suite-01"
```

The `/shared/` paths are illustrative, not an installed/deployed location.
`-B` prevents bytecode-cache writes. Each `--out` directory must be new; missing
writable user parent directories are created. State `--state`, measurement
`--outcomes`, proposal and evaluation paths can all remain in the user's tree.
Do not reuse another user's current state: pending/observed ledgers are local to
their branch. Keep referenced parent snapshots accessible at their recorded
relative locations. The source tree and active/base Python runtime are protected
from nested outputs. The only allowed package-local output subtree is ignored
`runs/`, for development on a writable checkout. Existing snapshots are protected
from nested outputs even when they are not an explicit input to that command.
No shared install or shared writable results directory is required by this CLI.

Output paths with symlinked ancestors are refused, including macOS `/tmp` or
`/var` aliases and potentially symlinked home/lab directories. Pass the resolved
physical path instead. For a new destination, the installed Python can print it
without creating it (substitute the actual installed interpreter):

```sh
/shared/adaptive-runtime/bin/python -B -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).expanduser().resolve())' "$HOME/adaptive-tutorial/fresh-run"
```

Use that printed path as `--out`; keep the destination new and writable. This
resolves existing ancestors while retaining the new final path components.

## Manual propose, simulate, import and update

From this folder, use fresh paths. All CSVs here are fictional.

```sh
.runtime/bin/python tutorial.py generate --seed 17 --count 200 --out runs/demo/sim
.runtime/bin/python tutorial.py init --candidates runs/demo/sim/candidates.csv --outcomes runs/demo/sim/initial-outcomes.csv --seed 17 --out runs/demo/v000
.runtime/bin/python tutorial.py propose --state runs/demo/v000 --batch 4 --out runs/demo/v001
.runtime/bin/python tutorial.py simulate --state runs/demo/v001 --truth runs/demo/sim/truth.csv --out runs/demo/measure1
.runtime/bin/python tutorial.py import --state runs/demo/v001 --outcomes runs/demo/measure1/outcomes.csv --out runs/demo/v002
.runtime/bin/python tutorial.py propose --state runs/demo/v002 --batch 4 --out runs/demo/v003
```

`simulate` is the separate fictional measurer. It reads hidden truth and the
pending identities and emits an outcome CSV; `propose` never imports that module
or accepts a truth path. For an import exercise, copy the outcome CSV outside its
bundle, edit one `sample_id` or leave a value blank, and import to a **fresh**
output path. The command returns JSON FAIL/exit 2, creates no state output and
leaves prior state bytes unchanged. Fix that CSV and retry at the same output
path. A complete matching batch succeeds. An already imported state rejects
repeated import. New observed outcomes enter the next GP fit; pending proposals
do not count as observations. The suite executes these cases.

For the baseline, branch from the **same** `v000`, use `propose --strategy random`
each round and the same batch sizes, then simulate and import each batch into new
snapshots. After three batches, compare completed branches:

```sh
.runtime/bin/python tutorial.py evaluate --adaptive runs/demo/adaptive-final --random runs/demo/random-final --truth runs/demo/sim/truth.csv --out runs/demo/comparison
```

Those final paths are placeholders for your actual completed snapshot paths.
The suite builds both branches automatically. Evaluation checks shared catalog,
seed, initial observations, batch budgets, declared branch strategies and oracle
measurements. It reports observed-best trajectories plus hidden latent-best and
simple regret (eligible hidden optimum minus best latent value among measured
targets). No hidden value goes back to proposal. No confidence bound, statistical
significance, optimizer guarantee or biological interpretation is claimed.

## Model and synthetic design

Each original `FABLE-0000`.. ID denotes an invented candidate, unrelated to genes.
Two numeric descriptors `f1,f2` are uniformly generated in [-1,1]. They have no
biological meaning. Status `excluded` and `invalid` demonstrate eligibility gates;
all stored feature numbers must still be finite. Generation supports 100..1000
candidates; normal teaching settings are 200, six initial valid targets and at
most three batches of 1..4. Initialization permits 4..12 round-zero observations.
Targets have one fictional sample and one outcome each; replicates are **not**
modeled by this contract.

The evaluator's arbitrary surface is
`1.2*exp(-((f1-.3)^2+(f2+.2)^2)/.22) + .25*sin(3*f1)*cos(2*f2)`.
It adds fixed per-target seeded Gaussian noise with std 0.1. Truth contains both
latent and measured values. Both strategies therefore see the same potential
measurement for any target, with no order-dependent noise advantage. The initial
six IDs are drawn with `random.Random(17)` independent of objective values.

The actual GP is zero-mean, `normalize_y=False`, unit-variance
`RBF(length_scale=0.45, length_scale_bounds="fixed")`, `alpha=0.01`,
`optimizer=None`. Alpha adds assumed observation variance to the training-kernel
diagonal; no WhiteKernel and no hyperparameter/noise fitting. `predict(...,
return_std=True)` supplies latent predictive mean/std. Rank valid, unmeasured,
nonpending candidates by **mean + 1.5*std**, descending, breaking ties by ID.
A batch takes the top scores from one fit: no fantasy outcomes, no within-batch
diversity adjustment. Correlated picks are possible. The random strategy shuffles
sorted eligible IDs with Python `random.Random(seed + round_number)` and takes
the same number of targets; it does not rank by outcome or GP score. Scores are
saved for audit for both strategies.

An independent scalar check uses one training point `(0,0)` with observed value
2. At `(0.45,0)`, cross covariance is `k=exp(-1/2)`, so expected mean is
`2*k/1.01`, std is `sqrt(1-k*k/1.01)` and score is `mean+1.5*std`.
The suite computes these with scalar `math`, independently of sklearn kernels or
matrix solvers, and compares all three to the installed estimator at 1e-12.

Primary scikit-learn docs inspected 2026-10-19:
[Gaussian Processes](https://scikit-learn.org/stable/modules/gaussian_process.html)
and [GaussianProcessRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.gaussian_process.GaussianProcessRegressor.html).
They document fixed `optimizer=None`, the role of `alpha` and `return_std`.
The stable URLs resolved to 1.9.1 docs at inspection; the pinned teaching runtime
is **1.6.1**, whose installed API and actual numeric behavior are checked by the
suite. These common options do not require the latest version.

## File contract and integrity limits

UTF-8 CSV, exact ordered headers, no missing/extra columns or blank cells:

| File | Header |
| --- | --- |
| candidates | `target_id,f1,f2,status` |
| proposal | `target_id,sample_id,round_id,outcome_id` |
| outcomes | `target_id,sample_id,round_id,outcome_id,value` |
| evaluator truth only | `target_id,latent_value,measured_value` |

`target_id` must be original fictional `FABLE-` plus four digits. Each sample and
outcome ID is a nonempty 1..80 character ASCII alphanumeric/underscore/hyphen
identifier. Round IDs are `r000` through `r003`. An outcome CSV must exactly
cover the pending batch once, retaining all four identities; row order may vary.
Unknown, missing, duplicate, nonfinite, excluded, invalid, already measured or
contradictory identities/outcomes fail. Prior ledger rows cannot be resubmitted
or edited. Corrections to a *previously accepted* outcome require human review
and a new tutorial branch from a trustworthy earlier snapshot; no in-place
correction command exists. Different finite values for a never-observed pending
outcome are measurements the importer cannot externally verify.

Every generated output is a new directory with `manifest.json` and SHA256 of its
files. State snapshots contain `state.json`: catalog/features/status, seed,
version, event, round, observed ledger, pending ledger and a relative reference
plus hash of the prior state. A proposal also contains `proposal.csv`, all
eligible `scores.csv` and `fit.json`. Imported snapshots include `imported.csv`.
Validation recursively verifies parent files/hashes and legal transitions;
prior observations must match the parent exactly. Initialization starts version
zero; each propose or import increments version once. No state is overwritten.
Outputs that exist, overlap inputs (including prior state snapshots), or use a
symlinked output path are refused. Invalid imports validate before publishing;
corrected retry can reuse the previously refused destination.

Keep all referenced snapshots together and preserve relative paths when moving
a complete run. A branch has its own pending ledger: do not reuse an older state
to issue a second operational batch. Branching is allowed here solely for the
controlled adaptive/random comparison. This is a single-user local teaching
contract, not a scheduler, locking service, global experiment registry or secure
append-only database. Hashes detect accidental/partial edits and chain changes;
an actor who rewrites an entire chain and all hashes can forge it. There is no
cryptographic authentication. Outputs publish after validation via an exclusive
directory claim; a process crash during publication may leave an incomplete
output that subsequent reads refuse. Preserve it for diagnosis and choose a new
path; do not silently overwrite it. Imports never edit input files.
