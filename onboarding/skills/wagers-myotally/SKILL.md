---
name: wagers-myotally
description: Run the installed Wagers Myotally CLI for calibrated laminin/DAPI manifests, synthetic tutorial acceptance, runtime controls, and human-reviewed animal/muscle exports. Use for this repo's fluorescence workflow; H&E and GFP engraftment endpoints require separate workflows.
---

# Wagers Myotally

## What it does and when to use it

Use the existing `wagers-myotally` command to run pinned upstream Myotally on
laminin/DAPI fields, preserve provenance, and export reviewed sampled-fiber
summaries by study/animal/muscle. This is a repo-local instruction pack; it introduces no
segmentation algorithm or BootLoops API. Read the [CLI contract](../../docs/cli.md)
and [current verification](../../docs/current-verification.md) before execution.
The [validation record](../../VALIDATION.md) retains historical evidence. Installation and
contribution status are in the [contribution guide](../../docs/bootloops-contribution.md).

Current documentation baseline: `b0735262`, wrapper `0.2.1-env001`;
the single-tool module/environment name remains `1.0.2-env001`. Historical Linux
Myotally tests passed five scenarios. The independently approved bytecode fix is
integrated, with fresh installed Linux validation still pending; see current
verification for exact scope. The five-tool umbrella still needs actual deployment,
ordinary-user access and fresh-agent checks. This local skill is not proof of
installed discovery. For H&E/GFP endpoints, culture counts, synthetic Scanpy or
fictional adaptive practice, use the [workflow router](../wagers-workflows/SKILL.md).

## Run with explicit inputs

1. Confirm the maintainer has verified deployment and your access; use the
   [single-module entry steps](../../README.md#before-running). The umbrella fixes
   source/runtime selection: do not pass `--source` or replace its environment. Run
   `wagers-myotally doctor` and retain its output. If the command is unavailable,
   source verification fails, or the runtime differs, report the failure and
   stop execution. Follow the linked installation contract; do not substitute
   a mock, another segmenter, or an unverified dependency upgrade. `doctor`
   checks compatibility, not image processing or biology.
2. For problem-based software acceptance and agent practice, read the
   [tutorial index and prompts](../../docs/tutorials.md), then run
   `wagers-myotally tutorial-suite --evidence-dir "$HOME/Wagers private results/myotally-01"`.
   Keep evidence outside the whole installed release prefix, repository and source.
   For installed Git-null reports, compare executable SHA256s to reviewed code;
   the inner direct-Python commands do not validate the outer launcher.
   Require exit 0, top-level `report.json` PASS and all five scenarios PASS;
   RUNNING/NOT_RUN is incomplete. Inspect commands, field logs, code/source hashes
   and preservation checks. Unsupported tasks remain UNSUPPORTED. Generated
   marker labels are fictional software-contract data, never real-image
   positivity. Report two fictional animals and three separate animal/muscle
   rows without treating fields/fibers as replicates. On unexpected failure,
   retain evidence and report it before another suite invocation. A prior
   installed release may not contain this new subcommand.
   For a smaller runtime smoke check, use
   `wagers-myotally validate-one --evidence-dir "$HOME/Wagers private results/control-01"`.
   Keep the evidence outside the shareable repository. It generates original
   synthetic shapes, runs upstream, tests missing-channel rejection and retry,
   checks hashes, and exercises synthetic review export. Its area bounds
   200–3000 µm² and declared calibration are control settings only.
3. For user images, start from [image-manifest.csv](../../templates/image-manifest.csv).
   Preserve study → animal → muscle → section → field → fiber identity, globally
   unique field IDs, sampling rule, blinded condition and time point. Channel
   paths resolve relative to the manifest, or may be absolute. All manifest
   values are required; do not invent missing metadata.
   IDs must match `[A-Za-z0-9][A-Za-z0-9_.-]{0,63}`; `Results` is forbidden
   for every manifest ID. Field IDs `all` and names beginning `all_results`
   are also reserved, case-insensitively. Preserve leading zeros as text.
4. Require registered, distinct, single-plane 2D grayscale TIFF channels with
   matching dimensions/bit depth (uint8/uint16), positive signal, and at least
   64 pixels per dimension. Verify channel identity and numeric positive X/Y
   µm/pixel from acquisition/calibration evidence, never magnification alone.
   This CLI requires square pixels. Separately validate any conversion or
   resampling; do not relabel anisotropic pixels to pass validation. The CLI
   converts calibration to pixels/µm²; area bounds are in µm².
5. Keep originals, metadata and installed software separate from writable run
   storage. Use new run/output directories outside the repository and outside
   original/metadata directories. Upstream cleans its input folders: let this
   CLI create and hash disposable channel-only copies in `work/`; never call
   its internal `_upstream` worker on originals. Record the justified quality
   choice (`high` or `low`) and finite area bounds (0 < minimum < maximum).

After setting `MANIFEST`, `RUN_DIR`, `QUALITY`, `MIN_AREA_UM2` and `MAX_AREA_UM2`
to the chosen inputs, run each command separately and check its exit status:

```bash
wagers-myotally validate-manifest --manifest "$MANIFEST" --inspect-images
wagers-myotally analyze --manifest "$MANIFEST" --run-dir "$RUN_DIR" --quality "$QUALITY" --min-area "$MIN_AREA_UM2" --max-area "$MAX_AREA_UM2"
```

A nonzero exit is a visible failure. Retain stderr/logs and any failed run's
provenance; do not suppress errors or accept partial/empty results. On a missing
channel, correct the manifest/path or approved channel preparation, then
revalidate and retry into a new run directory. Do not manufacture a channel,
alter originals, or reuse failed runs. If a retry fails, stop and report the
remaining cause. A checksum mismatch requires investigation before more runs.

## What the output means

Successful analysis is **`succeeded-review-pending`**, with nonempty per-fiber
rows, matching upstream summary counts, a numbered `final.tif` for every field,
`exports/fibers.csv`, and an unfilled `exports/review-template.csv`. Check
`provenance.json`, `original-files-check.json` (`all_unchanged` must be true),
and field logs. Preserve settings, runtime/source hashes, manifest and run ID.
Neither an upstream Finished message nor status `running` proves success.

Read [review and export](../../docs/review-and-export.md) for human review.
Compare originals and numbered views under the lab's blinded plan. Use a copy
of the **generated** `exports/review-template.csv`; the older descriptive
`fiber-review.csv` ledger is not the CLI import schema. Keep original identity
and measurement values unchanged and exactly one row per original fiber.
UTF-8 BOM CSVs and exact finite decimal-equivalent CSA/CNF formatting are
accepted (`2460`, `2460.0`, `2.460e3`); there is no rounding tolerance.
Changed identifiers or numeric values, NaN and infinity fail visibly. Import
identity columns as **Text** in Excel, including original fiber numbers, so
leading zeros and exact spelling survive; identity comparison only trims outer
whitespace. Keep `review_date` as ISO `YYYY-MM-DD` text and save CSV UTF-8.
Check the saved file for coerced IDs/dates; do not edit identities or round
measurements to force acceptance.
Obtain `accept`/`exclude`, reviewer ID and ISO date for every row, and reasons
for exclusions. Corrections belong in `reviewed_csa_um2`/`reviewed_cnf`; retain
external annotation evidence. Added/split/merged objects need an approved
separate annotation workflow. Never fill real-image decisions automatically.

After the human review is complete, set `REVIEW_CSV` and a new `REVIEW_OUTPUT`:

```bash
wagers-myotally export-review --run-dir "$RUN_DIR" --review "$REVIEW_CSV" --output "$REVIEW_OUTPUT"
```

The export contains `fiber-review.csv`, `animal-summary.csv` and
`review-provenance.json`. CSA is µm²; CNF is 0/1. Dystrophin/GFP positivity is
manual 0/1 under a documented `threshold_rule_id`, independent of segmentation;
blank means unscored, never negative or zero. This CLI scores no MFI channel.
Humans must judge positivity from separately acquired dystrophin/GFP channels
of the same registered field and retain those channels as review evidence;
laminin/DAPI numbered views alone cannot establish marker positivity. If those
marker channels or approved rules are absent, leave scores blank. The single
rule ID must document both markers if both are scored. GFP entries are retained
in the ledger only; this export produces no GFP summary.
Dystrophin count/fraction require complete scoring under one rule within each
summary group. Despite its filename, `animal-summary.csv` groups by
`study_id` + `animal_id` + `muscle_id`, with `muscle_id` in the output.
Report each row separately; do not manually pool muscle rows into an animal
fraction unless a predeclared analysis plan defines the weighting. Retain
section/field detail and the sampling plan. Muscles, fibers and fields are not
independent animal replicates. Do not infer edited-nuclei
percentages, H&E regeneration CSA, or Sinha maximum GFP count per muscle from
this export; those require separate validated assay/sampling workflows.

## What must pass before trusting it

Require visible invalid-input rejection, real nonempty upstream outputs,
first/retry original and manifest hash preservation, then human field review
and an identity-preserving export. The [synthetic control](../../examples/synthetic-control/README.md)
tests runtime mechanics, with no target biological count or accuracy claim.
Representative lab images need blinded manual-reference comparisons and
predeclared assay-specific acceptance, calibration, sampling and positivity
rules. Biological validation stays pending even after export. Report measured
evidence and unresolved limits separately; never invent counts or sign-off.
