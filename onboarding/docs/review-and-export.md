# Review, export, and scientific endpoints

**Real lab-image validation is pending.** Successful software execution would
establish file handling, not biological accuracy. Keep animal → muscle → section
→ field → fiber relationships throughout review and analysis. Multiple fields or
fibers from the same animal are not independent animal replicates.

## Expected file inventory, derived from source

These names/layouts were read from the pinned source asset's
`call_Myotally.py:44–59,330–381`. The non-MFI output subset was exercised in the
[local synthetic source run](../examples/synthetic-control/README.md); MFI outputs
remain source-derived expectations, not tested exports.
`<time>` is the upstream timestamp; `<field>` is a child-folder name.

| Relative to the selected input parent | Contents expected from source |
| --- | --- |
| `Results/all_results_<time>.txt` | Folder/time, chosen size range, then tab-separated `Image`, `Number of Fibers`, `Average CSA (µm²)`, optional channel mean FI |
| `Results/<field>_<time>.txt` | Tab-separated `Fiber Number`, `CSA`, `CNF (y/n = 1/0)`, optional channel MFI columns |
| `Results/CSA_CSVs/<field>_CSAs_<time>.txt` | Comma-separated areas, with a trailing comma; not a conventional headed CSV |
| `Results/MFI_CSVs/<field>_<channel-index> MFIs_<time>.txt` | Optional comma-separated intensity values, with a trailing comma |
| `<field>/final.tif` | Numbered final visualization; original channel files also retained |

The source numbers fibers from zero. Do not renumber the original result when
joining a review ledger. Intermediate masks/overlays are created during the run
but many are deleted by cleanup; do not promise they remain as exports.
`final.tif` and the original channel copies are the source-supported review
starting point. Verify actual output structure on the first real execution.

## Review one field before accepting a batch

1. Confirm that each expected field is present in the summary and has a nonempty
   per-fiber table and visualization. A skipped field or empty table is not an
   accepted analysis. Preserve logs, including warnings and failed attempts.
2. Open the original laminin/DAPI channels and `final.tif` side by side in the
   lab's approved viewer (for example Fiji). Check registration and field
   identity. Review missed, merged/split, edge-cut, nonmuscle and artifact objects;
   compare central nuclei to DAPI. Record accept/exclude/correct decisions under
   a blinded review plan with a second scorer where the assay requires it.
3. Myotally's inspected GUI has parameter entry, Run and Quit, not a manual
   correction editor. Make manual contour/count corrections in the approved
   external workflow and retain the annotated view/ROI records. Keep original
   results unchanged. A correction must identify the run, field, original fiber
   ID or new manual ID, reason, reviewer and date. For the CLI `export-review`
   command, copy the run's generated **`exports/review-template.csv`**, fill its
   decisions/reviewer/date and optional reviewed measurements, and follow the
   [CLI export instructions](cli.md#review-and-export). The separate
   [manual fiber-review.csv](../templates/fiber-review.csv) is an external
   annotation ledger for new/split/merged objects; its schema is not accepted by
   `export-review` and needs a separately approved aggregation workflow.
4. Check µm/pixel against acquisition metadata or a known calibration; document
   any resampling. Verify a known area in the external viewer. A numerical CSA
   is usable only after calibration is confirmed. Review the effect of size
   bounds and image quality on retained fibers; keep settings comparisons as
   distinct runs. Define positivity thresholds independently of segmentation.
5. Agree on acceptable error rates and exclusions **before** validating real
   images. Compare counts, area and classifications to blinded manual reference
   measurements across representative staining/conditions. Record the sample,
   disagreements and acceptance decision; no default accuracy threshold or
   claimed validation is supplied here.

## Export without losing provenance

Copy the unchanged `Results/` tree, each accepted field's `final.tif`, metadata,
settings/version record and log to `exports/original/` in persistent run storage.
Verify copied filenames, sizes/checksums and field completeness before removing
temporary work. Keep the raw acquisition files in their separate immutable area.

For spreadsheet import, use **tab separation** for the summary/per-fiber text
files. Check any leading metadata lines and whitespace in headings. The files in
`CSA_CSVs`/`MFI_CSVs` are comma lists with possible empty trailing cells; verify
their lengths against the fiber table and do not count a trailing blank as a
fiber. Record decimal/import settings. The [CLI](cli.md) parses and validates the
non-MFI summary/per-fiber contract and produces normalized CSVs. Direct spreadsheet
imports and optional MFI parsing remain the user's separate review step.

Export a reviewed CSV into `exports/reviewed/`, with explicit units and stable
study/animal/muscle/section/field/run/fiber identifiers. Join the metadata and
review ledger explicitly; never guess the animal from sort order. Preserve
original and corrected values and document how manually added/split/merged
objects map to IDs. Store summaries separately for each study/animal/muscle and the field sampling plan
alongside distributions, rather than pooling all fibers as independent animals.
Have the reviewer sign off the run record before results are used downstream.

## How this maps to the lab's endpoints

| Scientific aim | Usable starting point | Required adaptation and review |
| --- | --- | --- |
| Dystrophin-positive fiber fraction (Lin-type endpoint) | Laminin-defined total fibers; separately scored dystrophin-positive fibers | Fraction = reviewed dystrophin-positive fibers / all eligible reviewed laminin-defined fibers in the matched sampled tissue. Use blinded manual ImageJ scoring/validated positivity rules; reconcile IDs and exclusions. It is not percent edited nuclei, and generic segmentation/MFI does not solve positivity classification. |
| Regeneration with H&E (Oh-type endpoint) | Centrally nucleated regenerating fibers and their CSA distribution | H&E requires a validated stain-specific/manual workflow; it is not the laminin+DAPI input assumed by this Myotally route. Preserve the animal-level sampling plan (for example approximately 150 sampled fibers per animal when reproducing that design), selection rules, calibration, injury time and CSA distributions. |
| Regenerated fiber CSA and GFP engraftment (Sinha-type endpoints) | H&E regenerated-fiber CSA; separate GFP engraftment scoring | Sinha's CSA endpoint used H&E (Fig. 2D–E), outside this laminin/DAPI route. Its engraftment endpoint was the maximum GFP-positive fiber count per engrafted muscle, not a fraction. Define regenerated fibers, injury/treatment time, positivity/background and muscle sampling explicitly; an MFI column or sampled animal fiber sum does not implement that endpoint. |

These are endpoint mappings, not replicated experiments. The published
[Myotally protocol](https://pmc.ncbi.nlm.nih.gov/articles/PMC11772141/) describes
fluorescent border/DAPI analysis; extrapolation to another stain or biological
classification requires validation. No private manuscript text or unpublished
identifier is included. The study team must approve the relevant protocol,
sampling and positivity rules before data collection or comparison.
