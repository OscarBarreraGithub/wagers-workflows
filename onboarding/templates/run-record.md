# Run record — copy outside the repository for each attempt

No blank field means approval; use `not applicable` with a reason where needed.
Do not store credentials, personal access tokens or private study data in this
shareable repository. Use deidentified animal and blinded condition IDs.

## Identity and environment

- Study / run ID:
- Operator / reviewer IDs and date:
- Execution route (local Mac/Windows or FASRC OOD Remote Desktop):
- OS / architecture; session/job ID if applicable:
- Application release; source or binary asset filename and SHA256:
- Environment / launcher version and location; resolved dependency record:
- Input provenance / reuse terms; image or acquisition SHA256 record:
- Immutable raw location; disposable input-work absolute path:
- Original-file manifest before copying; before/after SHA256 comparison after
  first run and retry (all files present and identical, with evidence):
- Metadata outside processed folders preserved:
- Persistent results location; temporary work cleanup policy:
- Metadata table and approved sampling-plan location:

## Image and settings

- Animal / muscle / section / field IDs (table is authoritative):
- Channel names, identities, registration and conversion/resampling history:
- Pixel size X and Y (µm/pixel), calibration source and verification:
- Entered pixels-per-µm² ratio; calculation `1/(sx*sy)`:
- DAPI / laminin filenames and optional MFI filenames:
- Image quality choice; minimum/maximum area (µm²); default checkbox state:
- Injury/treatment time point and inclusion/exclusion plan:
- Biological endpoint, positivity threshold rule and blinded review plan:

## Execution and review

- Expected field count / actually processed field count:
- Start/end time and observed resource usage (leave unmeasured if unknown):
- Log location; warnings, traceback or missing-field symptoms:
- Actual output inventory and copy/checksum verification:
- Calibration/known-area comparison result:
- Missed/merged/split/edge/artifact objects and corrections ledger:
- Original vs reviewed exports / annotations locations:
- Reviewed denominator, positive count, and sampling unit if reporting a fraction:
- Animal-level aggregation method; distribution/export units:
- First-run result: NOT RUN / BLOCKED / PASS / FAIL, with evidence:
- Missing-channel retry: NOT RUN / BLOCKED / PASS / FAIL, with actual behavior:
- Biological validation: PENDING / approved, with reference and scope:
- Reviewer sign-off and remaining limitations:
