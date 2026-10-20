# Five tutorial entry points for Amy and her agent

Read [current verification](current-verification.md) before running. All five
routes are implemented; shared umbrella deployment and a fresh-agent walkthrough
remain pending. Use the [front-door module steps](../README.md#before-running)
only after the maintainer verifies deployment and your access. The umbrella fixes
runtimes/source: do not add `--source`, `--runtime-prefix`, `--sif` or `--runtime`,
install/fetch commands or runtime overrides from standalone maintainer examples.
The per-tool task files below describe their original package execution context;
under the umbrella, use these commands instead of their setup/local commands.

Choose an existing writable private parent outside software, runtimes, originals
and metadata. The example uses your home directory, with spaces deliberately
quoted. Each destination below must be new; change the suffix for a new attempt.
Run only the tutorial relevant to the question, inspect its report and stop on an
unexpected failure, retaining all evidence.

| Route | Conditional installed umbrella command | Agent instructions |
| --- | --- | --- |
| Myotally | `wagers-myotally tutorial-suite --evidence-dir "$HOME/Wagers private results/myotally-01"` | [Specialist skill](../skills/wagers-myotally/SKILL.md) and [five scenarios](#myotally-scenarios) |
| ImageJ | `wagers-imagej suite --out "$HOME/Wagers private results/imagej-01"` | [AGENT_PROMPT.md](../tutorials/imagej/AGENT_PROMPT.md) |
| CellProfiler | `wagers-cellprofiler suite --dest "$HOME/Wagers private results/cellprofiler-01"` | [AGENT_TASK.md](../tutorials/cellprofiler/AGENT_TASK.md) |
| Scanpy | `wagers-scanpy suite --output "$HOME/Wagers private results/scanpy-01"` | [AGENT_TASK.md](../tutorials/scanpy/AGENT_TASK.md) |
| Adaptive simulation | `wagers-adaptive-screen suite --out "$HOME/Wagers private results/adaptive-01"` | [AGENT_PROMPT.md](../tutorials/adaptive-screen/AGENT_PROMPT.md) |

Example prompts (after the same deployment/access prerequisites):

- **Myotally:** Use the linked specialist skill and the Myotally command above.
  Inspect all five scenarios, raw outputs, muscle-separated fictional review
  arithmetic and hashes. Explain why real dystrophin fractions need separately
  human-scored marker channels; laminin/DAPI segmentation is insufficient.
- **ImageJ:** Read the linked prompt and use the ImageJ command above with the
  fixed installed runtime. Check reviewed masks, calibration and sampled fiber
  areas for Oh/Sinha H&E questions. For Sinha GFP, check per-section totals from
  nonoverlapping fields and the maximum across sections within each muscle.
  Do not turn synthetic masks into evidence of human marker review.
- **CellProfiler:** Read the linked task and use the CellProfiler command above
  on an allocated Linux session with the maintainer's fixed container. Inspect
  donor/well identities, blank-field zero, control normalization and refusals.
  Explain why Buchanan-inspired counts do not establish stem-cell function.
- **Scanpy:** Read the linked task and use the Scanpy command above. Check the
  synthetic fixture-schema JSON, QC, raw-count pseudobulk and donor/sample/
  perturbation identities. Do not accept real CSV/transcriptomes or claim DE.
- **Adaptive simulation:** Read the linked prompt and use the adaptive command
  above. Explain fictional targets, propose/import state transitions and seeded
  random comparison. Do not recommend genes, demand superiority or control a lab.

Report exact code/runtime identity, exit status, case outcomes, preserved inputs,
output locations and unresolved gates. Synthetic fixtures are software exercises,
not independent biological samples. Keep study → animal → muscle → section →
field → fiber identity for tissue work and donor/sample/well identity for the
relevant assays. No real-image review decisions may be auto-filled.

## Myotally scenarios

This suite tests the delivered fluorescence CLI and review/export contracts using
**original deterministic synthetic shapes and fictional software-contract labels**.
It invokes pinned, unmodified upstream Myotally. It supplies no golden segmentation
count, biological accuracy target, real-image positivity or human review sign-off.
The same pixels are reused across fields to test metadata routing. They represent
no independent biological samples. No marker channel is generated or analyzed.

## One entry command

Use a new absolute directory outside the repository, entire installed release
prefix (including writable siblings of app/env), Python environment and upstream
source. The supported installed layout is sibling `<prefix>/app` and
`<prefix>/env`; their shared prefix is protected. Ordinary source checkouts keep
the repository/source/environment boundaries. Select the maintainer-provided
environment/source first; for the verified installed route:

```bash
wagers-myotally tutorial-suite --evidence-dir "$HOME/Wagers private results/myotally-01"
```

The umbrella supplies the fixed source through the installed Myotally launcher;
it refuses `--source`. Standalone source/developer routes have separate runtime
selection contracts. Older installed releases must be updated by the maintainer
before they expose this subcommand and the reviewed bytecode correction.

For source execution in the existing isolated Mac environment, the equivalent is:

```bash
WAGERS_MYOTALLY_SOURCE="/absolute/pinned source" "/absolute/selected environment/bin/python" -B -I "/absolute/source checkout/onboarding/wagers.py" tutorial-suite --evidence-dir "$HOME/Wagers private results/myotally-source-01"
```

The source route does not test the installed launcher, Lmod, Linux, lab access or
biological validity. Read [current verification](current-verification.md) for current gates and the
[observed Mac record](../examples/tutorial-suite/observed-mac.json) /
[validation record](../VALIDATION.md) for their historical execution scope. No global install,
network fetch or upstream source edit occurs in the suite.

Agent starting prompt:

> Use the Wagers Myotally skill and run the tutorial suite in the selected pinned
> environment into a new absolute evidence directory outside the checkout. Inspect
> report.json, every command exit status and field logs. Explain each scenario's
> outcome and unsupported task boundaries. Report fictional animal/muscle rows
> separately, preserving leading-zero animal IDs. Distinguish observed runtime
> behavior, review arithmetic, installed-launcher evidence and biological validation.
> If the suite fails, retain evidence and report the failing scenario and reason;
> do not change the source, suppress the error or keep retrying.

The generator is [make_tutorial.py](../scripts/make_tutorial.py), which reuses the
original seed-102 shape author in [make_control.py](../scripts/make_control.py).
Only generators, instructions and a small sanitized observed summary are tracked.
All generated TIFFs, metadata, reviews, normalized exports and detailed logs stay
in the external evidence directory. `CONTROL-PROVENANCE.json` and
`TUTORIAL-PROVENANCE.json` record authorship, seed, hashes and synthetic limits.

## Evidence contract

Exit **0** and top-level `report.json` status **PASS** mean all five software
scenarios passed. Exit **2** / **FAIL** is a failure; **RUNNING** or **NOT_RUN**
is incomplete. A refusal before safe evidence-directory creation exits nonzero
without creating a report. Never accept an upstream Finished message alone.

The report records code commit/dirty state, SHA256s before/after, runtime/platform,
pinned source hashes, exact command argument arrays, return codes, timestamps,
relative log paths, observed counts, arithmetic summaries and preservation checks.
For installed copies outside Git, `git_revision` and `git_dirty` are null; compare
`wagers.py`/`scripts/` SHA256s against the reviewed revision and bootstrap's
`wrapper_sha256` instead. `identity_files_absent` may list uncopied docs, tests or
skills and does not fail the suite; compare the files that are actually installed.
The inner 16 commands in current code use the selected Python directly
(`python -B -I app/wagers.py`), not the launcher script. An installed `wagers-myotally tutorial-suite` invocation
exercises the launcher only as the outer entry. Retain that separate entry's argv,
exit and deployment evidence; the inner-command report alone cannot establish it.
`commands.sh` is a readable record, **not a replay script**: existing output paths
must not be reused. `logs/*.log` retain stdout/stderr; `study-run/logs/` and
`corrected-retry/logs/` retain actual per-field upstream logs. `protected-before.json`
and report preservation checks cover source files, fixture TIFFs, all generated
fixture metadata/provenance and the nonchannel sentinel. Existing successful run
files are also compared after refused writes and subsequent exercises.

The runner stops at the first unexpected result, records **FAIL**, leaves later
scenarios **NOT_RUN** and retains artifacts. Expected negative commands exit 2
with the expected visible reason and create no refused output directory. The
suite itself includes one corrected retry, and does not automatically retry a
failed suite. Investigate the saved failure before an authorized new invocation.

## Scenario index and agent prompts

In the commands below, set `E` to the absolute evidence directory just produced.
Each displayed command names the installed CLI; the report records the actual equivalent Python argv used by the
suite. Commands describe what the suite runs; inspect the retained outputs rather
than replaying successful writes into existing directories.

### 1. Real count, CSA, CNF and preserved outputs

> Inspect the four-field manifest, calibration evidence and provenance. Verify
> nonempty upstream count/CSA/CNF exports and numbered images against normalized
> rows. Explain the existing-run refusal and prove earlier outputs survived.
> Describe the observed segmentation counts without treating them as accuracy.

Input: `fixture/metadata/image-manifest.csv`; four fields, animal `001` TA-left
(two fields), `001` DIA, `002` TA-left; synthetic square 1 µm/pixel calibration.
Bounds 200–3000 µm², quality high are fixture settings, not lab recommendations.

```bash
wagers-myotally doctor
wagers-myotally validate-manifest --manifest "$E/fixture/metadata/image-manifest.csv" --inspect-images
wagers-myotally analyze --manifest "$E/fixture/metadata/image-manifest.csv" --run-dir "$E/study-run" --quality high --min-area 200 --max-area 3000
```

The last command is deliberately repeated once to require an existing-directory
refusal and unchanged prior file hashes. Independent invariants: one real upstream
summary and table plus nonempty `final.tif` per field; summary counts equal actual
rows; normalized IDs/CSA/CNF agree with raw tables; CSA finite/positive, CNF 0/1;
metadata identity preserved; generated review fields blank; successful state is
`succeeded-review-pending`. No particular number of segmented objects is required.

### 2. Sampled-fiber arithmetic and animal/muscle identity

> Inspect fictional-review.csv alongside its actual generated template. Explain
> accepted/excluded subsets and the fictional reviewed corrections. Confirm the
> three separate animal/muscle rows and their denominators. Explain why neither
> fields nor fibers are animal replicates, why the incomplete fraction stays
> blank, and why mixed threshold rules prevent an accepted export.

`fictional-review.csv` is generated only for these shapes. It takes the lowest
observed fiber IDs in each field, retaining immutable original measurements and
placing fictional corrections in reviewed columns. All remaining fibers are
excluded with a reason. Scores are explicitly fictional labels, **never an
algorithm for judging positivity in a real image**.

| Animal / muscle | Accepted per field | Fictional dystrophin scores | Expected summary |
| --- | --- | --- | --- |
| 001 / TA-left | 3 + 2 | 1,0,1 / 0,1 | 5 accepted; 3/5 = 0.6; 2 fields |
| 001 / DIA | 4 | 1,0,0,1 | 4 accepted; 2/4 = 0.5; 1 field |
| 002 / TA-left | 3 | 1,0,blank | 3 accepted; count/fraction blank; incomplete |

Reviewed CSA per accepted field is 400, 500, 600, 700 µm² as applicable; reviewed
CNF is 0,1,0,1. Thus expected group mean CSA is 480, 550, 500 µm² respectively,
and CNF counts are 2, 2, 1. These are arithmetic exercise constants, not measured
truth. Groups with complete scoring use one `FICTIONAL-RULE-A`; the partially
scored group retains that rule but emits no positive count or fraction.

```bash
wagers-myotally export-review --run-dir "$E/study-run" --review "$E/fictional-review.csv" --output "$E/review-export"
wagers-myotally export-review --run-dir "$E/study-run" --review "$E/mixed-rule-review.csv" --output "$E/mixed-rule-output"
```

The second must fail visibly with mixed-rule rejection and no output. Expected
output: exactly three `animal-summary.csv` rows by study/animal/muscle, representing
two fictional animals; no cross-muscle pool, significance test or GFP endpoint.
The runner checks hand-calculated expectations independent of exporter logic.
Real use still needs human image review, marker channels, validated thresholds,
calibration evidence and a predeclared sampling/analysis plan.

### 3. Excel-style CSV formatting and identity protection

> Inspect the BOM bytes and decimal-equivalent values in excel-style-bom.csv.
> Confirm its summary matches the baseline. Explain why animal ID 001 changing
> to 1, CSA changing by 0.01, or CNF flipping must fail. Do not claim Excel GUI
> automation or spreadsheet application compatibility from this CSV exercise.

```bash
wagers-myotally export-review --run-dir "$E/study-run" --review "$E/excel-style-bom.csv" --output "$E/bom-export"
wagers-myotally export-review --run-dir "$E/study-run" --review "$E/changed-id.csv" --output "$E/changed-id-output"
wagers-myotally export-review --run-dir "$E/study-run" --review "$E/changed-csa.csv" --output "$E/changed-csa-output"
wagers-myotally export-review --run-dir "$E/study-run" --review "$E/changed-cnf.csv" --output "$E/changed-cnf-output"
```

The scripted CSV uses `Decimal.normalize()`, which can emit scientific notation
such as `2.46E+3`. That is an extra numeric-equivalence stress case, not a claim
about typical Excel CSV output. No additional application or CSV export was run.
Expected: BOM/exact decimal equivalence accepted; byte-identical summary. Each
changed identity/value rejected before output creation. Import IDs as **Text**,
preserve leading zeros, dates as ISO text, and save UTF-8 CSV without rounding.
This does not exercise Microsoft Excel itself. See [review contracts](review-and-export.md).

### 4. Visible failures, corrected retry and calibration scaling

> Identify both bad-input errors and prove neither made an accepted run. Inspect
> the corrected manifest and new retry directory. Explain why area bounds must
> change along with calibration for a useful scale comparison; report the
> resulting CSA relationship and its reporting precision, not biological accuracy.

```bash
wagers-myotally analyze --manifest "$E/fixture/metadata/missing-channel.csv" --run-dir "$E/missing-channel-run" --quality high --min-area 200 --max-area 3000
wagers-myotally analyze --manifest "$E/fixture/metadata/invalid-calibration.csv" --run-dir "$E/invalid-calibration-run" --quality high --min-area 200 --max-area 3000
wagers-myotally analyze --manifest "$E/fixture/metadata/corrected-half-scale.csv" --run-dir "$E/corrected-retry" --quality high --min-area 50 --max-area 750
```

Missing laminin and zero calibration each exit 2 with a visible reason and no
run directory. Corrected retry uses the existing original channels, valid square
0.5 µm/pixel and a new directory; it invents no missing channel. Baseline and
retry have identical high quality and pixel area bounds (200–3000 pixels²):
`200/3000 × 1` versus `50/750 × 4` pixels/µm². Therefore fiber IDs/count and CNF
must agree for the repeated pixels, and retry CSA must be baseline / 4 within
0.05 µm² for this fixture: baseline contour areas at 1 µm/pixel are exact
half-integers at upstream's one-decimal output precision, so only retry rounding
adds error. This bound is fixture-specific; if both baseline and retry were
rounded, the corresponding general bound would be 0.05 + 0.05/4 = 0.0625 µm².
This is a relational
calibration test of the pinned algorithm, not a golden count or accuracy test.

### 5. Unsafe output refusal and immutable inputs

> Inspect the analysis/review overlap errors, source and fixture hashes and the
> sentinel. Confirm no unsafe output was created and no prior successful run was
> overwritten. Explain why upstream receives disposable channel-only copies.

```bash
wagers-myotally analyze --manifest "$E/fixture/metadata/image-manifest.csv" --run-dir "$E/fixture/originals/unsafe" --quality high --min-area 200 --max-area 3000
wagers-myotally analyze --manifest "$E/fixture/metadata/image-manifest.csv" --run-dir "$E/fixture/metadata/unsafe" --quality high --min-area 200 --max-area 3000
wagers-myotally export-review --run-dir "$E/study-run" --review "$E/fictional-review.csv" --output "$E/fixture/originals/unsafe-review"
```

All three must fail visibly and leave no target directory. Original TIFFs,
metadata, fixture provenance, `must-survive.txt`, pinned source and earlier run
files must retain their SHA256s. The source-tree comparison also detects added
files. These controls establish software preservation for the named generated
inputs, not a backup policy for a real study.

## Route beyond the Myotally CLI

The Myotally suite still labels the following requests **UNSUPPORTED** by that
CLI. Those labels are not a statement that the other tutorials are unimplemented:

- H&E regeneration/CSA: use [ImageJ](../tutorials/imagej/README.md) for supplied
  reviewed masks, explicit calibration and declared sampled fibers. Automatic
  H&E segmentation and regeneration classification need separate validation.
- Maximum GFP engraftment per muscle: use ImageJ's reviewed GFP masks, summing
  nonoverlapping fields within each covered section, then taking the maximum
  across at least two sampled sections within each animal/muscle. Myotally's
  optional GFP ledger is not that endpoint.
- Culture counts: use [CellProfiler](../tutorials/cellprofiler/README.md) for the
  synthetic donor/well count and control-normalization contract. Functional
  stem-cell activity requires separate assays and cannot follow from counts.
- Transcriptomic bookkeeping: use [Scanpy](../tutorials/scanpy/README.md) for
  synthetic fixture-schema JSON/QC/pseudobulk only. It accepts neither real CSV
  nor real transcriptomes and establishes no DE or regeneration conclusion.
- Experiment-loop practice: use the [fictional simulator](../tutorials/adaptive-screen/README.md)
  for propose/import mechanics, never real gene selection or wet-lab control.
- Slow/fast fiber typing still needs appropriate channels and a separately
  validated typing workflow; no typing route is implemented here.

Retain absent marker scores as blank, require human-reviewed evidence and an
approved sampling/analysis plan, and explain missing inputs rather than fabricate
an answer. Neither fields nor fibers become animal replicates.
