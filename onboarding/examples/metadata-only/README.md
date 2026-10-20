# A small fictional metadata exercise

This example works as a reading/editing exercise in a text editor or spreadsheet
application. It has **no image files, no Myotally run, and no measured outputs**.
It is not a substitute segmentation demo. All IDs, paths and numbers were newly
invented for this onboarding package; they refer to no animals or experiments.
There is no third-party dataset to redistribute.

1. Open [study-metadata.csv](study-metadata.csv). The two fields belong to the
   **same** fictional animal and section, so they do not represent two animals.
2. Note the declared square pixel size of 0.5 µm/pixel in both directions. The
   corresponding Myotally entry would be 4 pixels/µm². This is arithmetic
   practice, not a measured image calibration. Calibration must be confirmed
   from actual acquisition records before any real run.
3. Both fields require `DAPI.tif` and `Laminin.tif` in their own child folders.
   The `NOT_SUPPLIED` original paths/checksums deliberately prevent these rows
   from masquerading as completed image provenance.
4. Copy the empty [run record](../../templates/run-record.md) to a private scratch
   document. Record first-run and biological validation as **NOT RUN / PENDING**.
   Leave observed outputs and positive counts unknown. These rows provide no
   basis for computing a biological fraction or CSA distribution.

Expected result of this exercise: one animal with two field records, a recognized
calibration entry of 4, and an incomplete run record that correctly refuses to
claim image analysis. The empty [metadata template](../../templates/study-metadata.csv)
is the starting point for a real study. Keep its required per-field hierarchy;
`mfi_filenames` may be empty, while missing calibration/provenance/animal identity
blocks acceptance. Use `review_status=pending` until a reviewer signs off.

The separate [synthetic-control example](../synthetic-control/README.md) now
executes the real pinned upstream algorithm on original generated shapes, with
actual local exports and a missing-channel/retry record. It establishes runtime
mechanics on the tested Mac environment only. Linux execution, human lab-image
review and biological validation remain open; this exercise stays metadata-only.
