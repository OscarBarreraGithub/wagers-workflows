# CPU CLI: bootstrap, one image, review

These commands call pinned upstream Myotally; there is no new segmentation method.
Use ordinary per-user accounts and new output paths. Keep original channels,
metadata and the software installation separate from writable run directories.

## Bootstrap for the manager

The owner authorizes the implementation/test; only the manager stages cluster
artifacts, chooses the saved account/partition, obtains exact Slurm policy review
and runs cluster commands. The implementer has made no remote changes.

1. Copy `deploy/config.example.json` to a private deployment config. Fill absolute
   **final** `release_prefix` and `module_root`; keep `module_name` versioned.
   Do not use a Wagers path unless the executing account can access it. Build at
   the final prefix; never relocate an existing environment or overwrite a release.
   Deployment paths must use printable ASCII (spaces allowed); Unicode and
   control characters are rejected before writes so generated Lua stays valid.
2. In an authorized compute allocation where the site's Lmod is initialized:

```bash
module load python
bash scripts/bootstrap.sh /absolute/deploy-config.json
```

`bootstrap.sh` uses the FASRC `python` module's Mamba. `bootstrap.py` fetches the
15 KB release archive over HTTPS, verifies its SHA256 and every allowed Python
member, and extracts only those eight files under the private release prefix.
It creates the Mamba environment from `environment.yml`, writes resolved YAML and
an explicit package list to `provenance/`, then installs the wrapper/scripts and
an absolute-path `bin/wagers-myotally` launcher. The launcher uses `mamba run` so
activation hooks run; it clears `PYTHONPATH` and disables user site packages.
Lmod is generated at `module_root/module_name.lua` after the import/compatibility
check passes. The module loads `python`, exposes the launcher, and records the
prefix. It does not allocate compute or modify shell-startup files.

Candidate package pins: Python 3.10.14, NumPy 1.24.4, SciPy 1.10.1, OpenCV 4.8.1,
Pillow 10.0.1, Tk 8.6. They resolved and ran the control on macOS ARM64, not yet
Linux. This YAML is not a platform-verified lockfile. The first local solve with
Pillow 9.5.0 failed a libtiff conflict; the delivered recipe uses 10.0.1.
The historical protocol versions differ; the unmodified source still requires
SciPy's old mode return shape. `doctor` checks that assumption and exact runtime
package versions. Record the Linux resolved builds after successful bootstrap.

A failure retains `provenance/build.json` and logs. Inspect it and use a **new**
release prefix/module version for retry; the bootstrap will not overwrite an
existing prefix or module. No automatic deletion, permission change or replacement
of a live release occurs. Confirm site quotas and network access before building.

## One bounded compute validation

`deploy/validate.slurm` requests **1 CPU, 4 GB RAM, 20 minutes, no GPU** and includes
bootstrap plus one control/failure/retry. Fill its account, partition, onboarding
path, private deploy-config path, module root and new evidence path. Submit from
an approved persistent evidence directory so the scheduler's default log persists.
The manager must review the exact filled script/command under site policy before
submission. The template is not a submission and contains no inferred site values.

Once a release exists, the validation command itself is:

```bash
module load python
module use /absolute/module-root
module load wagers-myotally/1.0.2-env001
wagers-myotally doctor
wagers-myotally validate-one --evidence-dir /absolute/new-control-evidence
```

The deterministic generator authors 512×512 TIFF shapes, metadata and a
nonchannel sentinel in a separate originals directory. `validate-one` executes
actual upstream analysis, attempts a manifest with a missing laminin file (must
exit nonzero before creating a run), retries the valid manifest, compares original
and manifest hashes, and mechanically exercises the synthetic review export.
A report under `validation.json` distinguishes runtime control from biology.
Any failure exits nonzero and preserves logs; an unfinished `running` state is
not a pass. It never accepts an upstream Finished message as proof of processing.

For one privately supplied lawful real field, add `--manifest /absolute/one-field.csv`
and explicit `--min-area`, `--max-area`, `--quality`. This still requires human
review/export afterward; the validator does not fill real-image review decisions.
Use the [same manifest format](../templates/image-manifest.csv), even for one field.

## Prepare a study manifest

Each row identifies study, animal, muscle, section and a globally unique field ID.
`laminin_path` and `dapi_path` point to distinct original TIFFs, relative to the
manifest's directory or absolute. Both images must be registered, single-plane,
2D uint8/uint16 grayscale, the same dimensions/bit depth, with positive signal.
Record numeric positive X/Y pixel sizes in µm/pixel, calibration evidence,
sampling rule, blinded condition and time point. The CLI currently requires
square pixels; validate resampling separately for anisotropic acquisitions.
Field IDs `all` and names starting with `all_results` are reserved (case-insensitive)
because they collide with upstream summary filenames. Empty, duplicate, NaN/zero calibration, missing-channel and invalid-image inputs
fail visibly. The manifest is distinct from the older descriptive study-metadata
sheet; the run provenance retains its complete row metadata.

```bash
wagers-myotally validate-manifest --manifest /absolute/metadata/image-manifest.csv --inspect-images
wagers-myotally analyze --manifest /absolute/metadata/image-manifest.csv --run-dir /absolute/results/run-001 --quality high --min-area 200 --max-area 3000
```

The bounds above are control-example settings, not a default for every study.
Use empirically justified study bounds. The CLI computes pixels/µm² from each
row's calibration. It rejects run directories that already exist or overlap the
original/metadata directories. Make a new run for retry/settings comparison.
It copies channels to `work/<field>/input/<field>/{DAPI,Laminin}.tif`, verifies
copy hashes, and invokes the upstream entry point in a separate child process
for each field. An internal worker contract guards that disposable-only layout.
Only channel copies enter upstream's cleanup path. No MFI/positivity channel is
scored by this first CLI version. There is no GUI under this command.

Success requires the expected field summary, per-fiber rows, numbered image,
nonzero fiber count and agreement between the summary and per-fiber table.
On error, logs and `provenance.json` remain; there is no accepted zero-field or
zero-fiber run. Original/manifest hashes are checked after execution, including
failures that reach the run stage. This protects the named inputs, not a snapshot
of every other study file; the control also verifies a nonchannel sentinel.

## Review and export

A successful run has `provenance.json`, `original-files-check.json`, `logs/`,
`exports/upstream/<field>/{Results/,final.tif}`, normalized `exports/fibers.csv`,
and **unfilled** `exports/review-template.csv`. Status is `succeeded-review-pending`.
All outputs remain pending biological validation. Inspect the original channels
and numbered views under the lab's blinded review plan, as described in
[review/export](review-and-export.md).

Copy the generated review template to your study review area. Keep its original
identity/measurement values unchanged; fill each decision (`accept`/`exclude`),
reviewer ID and ISO review date. Exclusions need a reason. Optional corrections
use `reviewed_csa_um2` and `reviewed_cnf`. Dystrophin/GFP scores must be manually
entered as 0/1 with a documented `threshold_rule_id`; blanks mean **unscored**.
CSV UTF-8 with a BOM is accepted. IDs are compared exactly after trimming outside
whitespace; keep them as text in spreadsheets. Immutable CSA/CNF values are
compared as exact finite decimal numbers: `2460`, `2460.0` and `2.460e3` are
equivalent, but any numerical change, NaN or infinity is rejected. There is no
rounding tolerance. Use the reviewed columns to record an intentional correction.
The single `threshold_rule_id` identifies the shared marker-scoring rule for
that row; if both markers are scored, it must document both. GFP scores/rules
are retained in the ledger only: no GFP count, fraction or engraftment summary
is supported. Do not interpret this column as two independent marker rules.

```bash
wagers-myotally export-review --run-dir /absolute/results/run-001 --review /absolute/review/completed.csv --output /absolute/results/review-001
```

The adapter requires exactly one row per original fiber, rejects identity changes,
and produces the copied ledger plus `animal-summary.csv` and review provenance.
Despite the retained filename, each summary row is a distinct
**`study_id, animal_id, muscle_id`** group and includes `muscle_id`; muscles are
never pooled. A group's dystrophin fraction is emitted only when every accepted
sampled fiber has a score under one threshold rule. Otherwise count/fraction stay blank.
The stdout JSON retains `animals` as the distinct study/animal count and adds
`animal_muscle_groups` as the number of summary rows.
These are sampled-fiber summaries, not independent fiber-level replicates or a
validated estimate of edited nuclei. No GFP engraftment endpoint is inferred.
New/split/merged manual objects need a separately approved annotation/aggregation
workflow; do not force them into an unchanged original-fiber ID. H&E CSA and
Sinha maximum-GFP-per-muscle analysis remain separate workflows.

## Focused developer checks

From this folder in the selected environment:

```bash
python -I -m unittest discover -s tests -v
python -m py_compile wagers.py scripts/bootstrap.py scripts/make_control.py scripts/validate_one.py
bash -n scripts/bootstrap.sh deploy/validate.slurm
```

The checks target input safety, calibration, missing-channel recovery, zero-output
rejection and unscored/manual-review semantics. They do not replace real upstream
execution, Linux validation, independent code review or representative lab images.

## Problem-based tutorial acceptance

```bash
wagers-myotally tutorial-suite --evidence-dir /absolute/new-tutorial-evidence
```

See the [tutorial index](tutorials.md) for scenario prompts, contracts, commands
and expected arithmetic. This new source command uses real pinned upstream on
four fictional fields and one corrected retry. It emits private report.json,
command/field logs and generated data outside the repository. PASS establishes
synthetic software contracts only; unsupported assays stay UNSUPPORTED. No
installed-launcher, Linux, lab-access or biological acceptance follows from a
local source pass. Bootstrap/deployment files are unchanged.
