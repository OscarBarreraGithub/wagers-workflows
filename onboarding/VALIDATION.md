> Current status: [verification and remaining gates](docs/current-verification.md). Execution notes below retain their historical checkpoint scope.

# Validation record — executable prototype

Date: **2026-10-19 UTC**. Wrapper/environment recipe: **0.2.1-env001**.
Historical preparation approval was at `eacf0cf0a945e8560f008f82947dd88f0b40a690`;
the core/skill baseline was subsequently reviewed at `7c50974`. Tutorial reviews
`8ce5e142` and `5d558e22` approved exact revision
`78a65ac8cfec017253cd00d3ae0bbc8b97b6c37a`. The later bounded hardening delta
awaits independent review. None of these approvals establishes Linux,
first-user or biological acceptance.

## Actual local source execution: PASS for synthetic runtime mechanics

A task-contained **macOS ARM64** environment was created with micromamba 2.9.0,
using conda-forge packages and a private root/cache under `.runtime/`. No system
Python/install, VM/daemon or shell-startup changes were made. The final local
versions were Python 3.10.14, NumPy 1.24.4, SciPy 1.10.1, OpenCV 4.8.1 and
Pillow 10.0.1. The first solve using Pillow 9.5.0 failed a libtiff constraint with
OpenCV; changing the candidate Pillow pin to 10.0.1 resolved it. Linux resolution
and the FASRC Mamba/module/launcher path are not established by this local solve.

Exact commands from the task worktree (runtime files are excluded from Git):

```bash
python3 onboarding/wagers.py fetch-source --destination onboarding/.runtime/upstream
onboarding/.runtime/tools/bin/micromamba --no-rc create --root-prefix onboarding/.runtime/mamba-root --prefix onboarding/.runtime/env --override-channels -c conda-forge --strict-channel-priority --yes python=3.10.14 numpy=1.24.4 scipy=1.10.1 pillow=10.0.1 opencv=4.8.1 tk=8.6
WAGERS_MYOTALLY_SOURCE="$PWD/onboarding/.runtime/upstream/source" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 onboarding/.runtime/env/bin/python -I onboarding/wagers.py validate-one --evidence-dir onboarding/.runtime/local-control-revision1
onboarding/.runtime/env/bin/python -I -m unittest discover -s onboarding/tests -v
```

The small archive and all eight files matched the recorded pins. The wrapper
invoked unmodified `call_Myotally.main` in child processes, not a replacement
segmentation implementation. The deterministic synthetic fixture has separate
originals and metadata; only copied TIFFs entered upstream cleanup.

Observed results:

- First real upstream run: one field, **61 exported fiber rows** and actual
  summary/per-fiber/numbered-image outputs. Retry: one field and **61 rows**.
  This observed count is not a golden count, shape-detection accuracy score or
  biological result. No Linux or future-version equality is assumed.
- Missing laminin manifest: exit **2** with `Missing channel laminin_path`,
  **no bad-run directory created**, then valid-input retry succeeded.
- Original channel files, input manifest and the separate nonchannel sentinel
  existed with matching SHA256s after first/retry execution.
- Mechanical synthetic review export produced one fictional study/animal/muscle summary.
  Dystrophin count/fraction stayed blank because no positivity was scored;
  biological validation stayed pending. Real-image reviews are never auto-filled.
- The expected SciPy mode deprecation warning was retained in logs. No source
  patch or hidden substitution was used to suppress/avoid the old API contract.

Sanitized evidence and actual small synthetic CSV exports are under
[examples/synthetic-control](examples/synthetic-control/README.md). Full private
local logs and runtime outputs are `.runtime/local-control-revision1/validation.json`,
`first-run/`, `retry-run/`, `original-files-check.json` and sibling console logs.
Those files include machine paths and are not part of the shareable repository.
The raw TIFFs and installed upstream source remain private runtime files.

## Focused checks

**PASS: nine safety/contract tests after the revision-1 fixes.** They cover original/metadata output overlap,
visible missing-channel recovery, invalid/NaN calibration and duplicate field IDs,
same-file/stack inputs, zero-output rejection, identity-preserving review and
unscored positivity, separate two-muscle summaries, BOM/exact numeric equivalence,
reserved field IDs and deployment path text rejection. An initial path-alias test failed because the location helper
assumed a resolved caller path; it now normalizes internally and the focused
suite passed. No mock segmentation or biological accuracy test was added.

Initial package inspection passed: **27 shareable files, 45 relative links/anchors**,
matching CSV contracts, observed-export hashes, S1/S2/S3 wording, safety placement,
unfilled deployment-config rejection, privacy/runtime boundary and whitespace.

Python compilation and shell syntax are checked for the affected scripts. Package
inspection covers relative links/anchors, manifest headers, fixture provenance,
whitespace and exclusion of runtime/upstream/private material. No parent-app
suite, cluster SSH, remote write/install, scheduler command or credential access
was performed by this implementer. `deploy/validate.slurm` is an unsubmitted
1-CPU/4-GB/20-minute/no-GPU template requiring exact manager policy review.

## Revision 1: code identity and contract corrections

Review `b7dca66f-cbeb-4e28-8933-e54a23c916ee` identified B1 muscle pooling and
B2 spreadsheet round-trip rejection. Both were corrected before the final run:

- `animal-summary.csv` retains its filename but now groups by
  `study_id, animal_id, muscle_id`, with a `muscle_id` column. Stdout reports
  distinct `animals` and adds `animal_muscle_groups` (summary-row count).
- Review accepts UTF-8 BOM and exact finite Decimal-equivalent CSA/CNF formatting.
  IDs remain stripped-exact; changed values, changed IDs, NaN and infinity fail.
- The walkthrough uses the generated `exports/review-template.csv`; the separate
  manual ledger is not CLI input. Shared marker-rule/GFP-summary limits are clear.
- Reserved upstream field-name collisions and unsupported deployment path text
  are rejected. The Mamba-run launcher design is unchanged.

**Tested executable checkpoint:** `94c6647afa426070090a10c2c845fa860f354bc2`.
It was committed before the nine tests and actual first/failure/retry control.
The refreshed [sanitized evidence](examples/synthetic-control/observed-mac.json)
records that Git revision, clean executable state, UTC execution windows and
SHA256s of the executable scripts, recipe and test file. Before/after hashes
matched. Later documentation/export refreshes do not change those executable
bytes. Full private records: `.runtime/revision1-test-evidence.json`,
`.runtime/revision1-focused-tests.log`, `.runtime/revision1-actual-upstream-control.log`
and `.runtime/local-control-revision1/validation.json`.

The revision-1 package check passed with 27 files and 47 relative links/anchors;
current executable/test hashes match the tested commit, refreshed output hashes
match the shared CSVs, and privacy/whitespace checks passed.

The pass is implementer-executed. The independent reviewer was read-only and did
not run these checks; manager execution/reviewer re-read remain separate evidence.
No reviewer permissions were changed or bypassed. At that historical checkpoint,
no code changed after its recorded execution; no unrelated suites or remote
commands were run. Later tutorial/hardening work has separate revision identity.

## Still open

1. Independent review/application of the bounded hardening delta after approved
   `78a65ac`. The earlier core/skill review is separate from this new delta.
2. Manager-run Linux final-prefix bootstrap and exact reviewed compute job:
   real pinned-tool control, missing-channel retry, unchanged originals and
   observed review/export mechanics; save resolved Linux builds and logs.
3. An appropriate real image, human review/export and demonstrated lab-member
   access through the shared environment. Group/fair-share visibility does not
   establish individual permissions; the Wagers write path is not assumed.
4. Representative lab-image biological validation, sampling rules, calibration,
   manual positivity thresholds and approved assay-specific H&E/GFP workflows.
5. Maintainer-controlled read-only shared release, persistent study/backup policy,
   user sign-off and any later BootLoops adapter or agent instructions.

The initial preparation host had no Linux runtime (Docker client could not reach
a daemon). Linux is **untested by this worker**, not demonstrated incompatible.
Packaged Mac/Windows binaries, the upstream GUI, Lmod activation and FASRC bootstrap
were not executed locally. Overall onboarding/deployment is not complete on the
basis of synthetic or Mac tests. No upstream code/image redistribution license
is inferred from authorized retrieval/testing; no such material is vendored.

## Problem-based tutorial suite: actual Mac source execution

**PASS, implementer-executed, 2026-10-19 09:40:34–09:41:01 UTC.** Tested clean
commit `46cddda9153010c6c6aab4ce9c852babf43fe8f8` using the existing isolated
macOS ARM64 environment and the actual pinned upstream from the earlier task.
No environment, bootstrap, deploy or upstream source bytes were changed. The
[sanitized observed summary](examples/tutorial-suite/observed-mac.json) records
code/source SHA256s, scenario results, observed counts and fictional summaries;
code identity matched before/after that execution. The summary is retained
unchanged at exact `46cddda`; it does not claim the later hardening code was run
through the positive Mac suite.

The new command is `wagers-myotally tutorial-suite --evidence-dir NEW_ABSOLUTE_PATH`;
see [tutorial prompts, contracts and exact scenario commands](docs/tutorials.md).
Actual local entry command used the existing private environment Python with
`-B -I onboarding/wagers.py tutorial-suite --evidence-dir NEW_ABSOLUTE_PATH`,
`WAGERS_MYOTALLY_SOURCE` set to its pinned source, and OMP/OpenBLAS/MKL thread
counts set to 1. The private execution record retains the absolute argv and paths.

All five scenarios passed on the first suite invocation, with 16 direct-Python
CLI subprocess commands (six successful operations and ten expected visible
refusals). These inner commands bypass the launcher; an installed launcher would
be exercised only by the outer entry, requiring separate retained evidence:

- Actual four-field upstream run: 244 observed normalized rows, 61 per field;
  raw count/CSA/CNF agreement and numbered outputs checked independently. An
  existing-run write was refused with earlier output hashes preserved.
- Fictional two-animal/three-muscle-group review arithmetic matched 3/5 and 2/4;
  partial scoring stayed blank and mixed rules were refused. Fields/fibers are
  not animal replicates. Marker labels and reviewed corrections are fictional
  software-contract inputs, never automated real-image judgments.
- BOM/exact-decimal-equivalent CSV accepted with identical summary; changed
  leading-zero ID, CSA and CNF rejected without accepted output. Excel GUI was
  not executed.
- Missing channel and zero calibration failed visibly before any run directory;
  a corrected single-field retry produced 61 observed rows. Halving square pixel
  size with corresponding area-bound scaling retained pixel settings, IDs and
  CNF; CSA was quarter scale within upstream's one-decimal reporting precision.
- Analysis output overlap with originals/metadata and review overlap with
  originals were refused. Original image, metadata, sentinel, source and earlier
  run file hashes matched; the source tree gained no files.

Four focused new-runner regression tests passed (evidence path safety including
symlink aliases, deterministic fixtures/IDs, checksum tamper detection, and
independent summary-oracle rejection of pooling/unscored-zero errors).
`skill-creator/scripts/quick_validate.py` passed for the updated skill, and 28
local file links in changed documentation/skill resolved. The existing nine core
tests and unrelated app suites were not repeated: no core analysis/review contract
was changed, only the new subcommand/runner was added.

Full generated fixtures, reviews, report.json, command argv/exit/timestamps,
command and field logs, protected-before hashes and console log are private at
`data/private-evidence/0ec3c881-tutorial/` outside this worktree. They are not
shareable package files. The suite directory is `suite-46cddda/`; its report
records the tested full commit and SHA256s. A private `execution-record.json`
links the suite and focused-check evidence.

**Read-only reviews `8ce5e142` / `5d558e22` approved exact `78a65ac` and executed
none of these commands. The subsequent hardening delta awaits review.**
The implementer's actual execution was separately authorized by this task; no
reviewer permissions were changed. This pass establishes synthetic software
contracts via the Mac source route, not an installed launcher, Linux/module,
lab-user access, Excel GUI or biological validation. H&E regeneration, maximum
GFP engraftment, fiber typing, culture and transcriptomics remain UNSUPPORTED
routes in the report. Manager-owned Linux bootstrap testing of the earlier
reviewed `7c50974` snapshot remains separate; bootstrap/deploy files are untouched.

## Bounded predeployment hardening delta (revision 1)

After the exact `78a65ac` approval, the manager authorized one bounded delta:
protect the entire release prefix when app/env are siblings in the supported
installed layout, and add a real invalid-source subprocess regression for the
suite's FAIL report/exit contract. Ordinary source-checkout boundaries remain.
Core analysis/export, bootstrap, environment/deploy and successful observed Mac
files/results remain unchanged. The affected focused test file was run once
on a committed revision, with its private result recorded below.

Provenance wording now makes explicit that installed Git fields can be null:
compare installed executable SHA256s to reviewed code and bootstrap's
`wrapper_sha256`, allowing absent docs/tests/skills. The inner 16 commands use
Python directly; outer-launcher evidence is separate. Scientific notation in the
scripted BOM CSV is an extra numeric-equivalence stress case, not typical Excel
output. The 0.05 µm² calibration tolerance is specific to the exact half-integer
baseline areas of this fixture; two rounded measurements would warrant the
0.0625 µm² bound for the same quarter-scale comparison. No positive upstream Mac
suite or old nine-test suite is repeated for this delta. A future manager-owned
Linux run must test the complete new candidate.

**Revision-1 checks: PASS**, implementer-executed at clean commit
`6e62cf74d9700a42e9db03c2b6bde1c40ba939d3`,
2026-10-19T09:56:08.863386+00:00–2026-10-19T09:56:09.419977+00:00.
The six tests in `test_tutorial_suite.py` passed in the existing isolated Mac
environment. The new installed-layout check refuses a writable release-prefix
sibling, allows outside-prefix evidence and retains ordinary source-folder
behavior. This is a filesystem-contract test, not an installed deployment test.

The real `wagers.py tutorial-suite` subprocess with deliberately invalid source
exited **2** and recorded report **FAIL**, active first scenario **FAIL** and
four later scenarios **NOT_RUN**. Its command list is empty: it refused source
before doctor/analysis, created no fixture or accepted run, and preserved the
invalid-source sentinel. This is the expected failure contract, not a failed
positive upstream run. Before/after code identity matched with Git dirty=false.
Skill validation passed. The affected test file was executed once; no positive
upstream run was performed for this delta.

Private evidence: `data/private-evidence/0ec3c881-tutorial/revision1-6e62cf7/`
contains `execution-record.json` with exact argv/revision/SHA256s before/after,
`focused-tests.log`, `skill-validation.log`, and
`real-failure/failed-suite/report.json` plus traceback/command artifacts and
`real-failure/failure-subprocess.json` with the outer exit/stdout/stderr.
Previous positive report/execution records and the tracked observed Mac summary
were verified unchanged. The earlier summary's execution-time review status is
historical; later approval at exact `78a65ac` is recorded above. This test pass
does not approve the new delta or establish installed/Linux/biological acceptance.
