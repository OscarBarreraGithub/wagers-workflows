# First use: one image, then review

**GUI route not executed.** The safe source-based CLI has a local synthetic
runtime pass; see [CLI commands](cli.md) and [validation](../VALIDATION.md).
The shared browser route becomes available only after the maintainer completes
the [FASRC deployment gates](fasrc-runbook.md). Linux execution and lab-image
validation remain open. The [synthetic control](../examples/synthetic-control/README.md)
is generated locally and demonstrates mechanics only.

## Before any Myotally launch

**Prepare disposable, channel-only work copies first.** Keep immutable originals,
metadata and unrelated files outside the selected input parent and its processed
child folders. In the inspected release asset, `Myotally V102/call_Myotally.py`
lines **377–381** walk the processed folder and call `os.remove` for files outside
the keep list; lines **44–52** create/write results. The exact archive identity is
recorded in [provenance](upstream-and-linux.md). This instruction applies to
both the future shared launcher and the untested Mac/Windows desktop route.

Use the [safe field layout](#prepare-one-field-safely) below. Record checksums
and filenames for the originals **before** making copies, with the manifest
outside `input-work`. After the real run, perform the
[original-files-unchanged check](#original-files-unchanged-check). The GUI-specific version of this check remains unrun. The separate source CLI
passed a local synthetic run/retry and input-hash check; Linux is still pending.

## Browser route after deployment

1. Use your own FASRC account with cluster access and the required FASRC VPN.
   The maintainer must confirm your lab membership and storage permissions.
   In Chrome or Firefox, open the institution-provided
   [Cannon OOD dashboard](https://rcood.rc.fas.harvard.edu/) or the site's assigned
   FASSE dashboard. Do not share a login or enter credentials in this repository.
2. Under **Interactive Apps → Remote Desktop**, use the maintainer's recorded
   account, partition, CPU cores, memory, and time limit. Use zero GPUs for the
   first Myotally run. The desktop is a queued compute job, so it may wait for
   resources. Connect through **My Interactive Sessions** once it is running.
3. Make the disposable image work copy described below in your writable study
   area. Store metadata alongside the run, outside the image input parent.
4. Find **Wagers Myotally 1.0.2 — CPU**, the planned version-specific launcher
   inside the desktop. If it is absent or the version differs, stop and report
   that to the maintainer. The name is a deployment specification, not an app
   claimed to exist today. Do not substitute Jupyter for this Tk GUI.
   The delivered executable launcher is the terminal command `wagers-myotally`;
   follow [the CLI path](cli.md) for manifest validation and safe channel copies.
   A desktop GUI shortcut still requires separate installation/testing.
5. Enter the parameters below, run one image, and inspect its actual outputs
   using [review and export](review-and-export.md). Save a completed run record
   before ending the session. Closing a browser tab need not end the job; save
   before the allocated time expires and terminate the session when finished.

These access/session steps follow the official
[OOD guide](https://docs.rc.fas.harvard.edu/kb/virtual-desktop/) and
[Virtual Desktop Apps guide](https://docs.rc.fas.harvard.edu/kb/vdi-apps/).
Application availability and resource options depend on your account/site.

## Mac or Windows alternative

Use this upstream-supported desktop route if the shared environment is not ready
and local use is approved. It is **not tested here**, including on Apple Silicon
or Windows; actual binary architecture/OS compatibility must be checked. The
local synthetic CLI pass does not establish packaged-binary or GUI compatibility.

- **Mac:** download [Myotally_V1_Mac.zip](https://github.com/pieterboth/Myotally/releases/download/Myotally_V1.0.2/Myotally_V1_Mac.zip)
  from the pinned release, extract it in a user-owned folder, and open the
  extracted Myotally application. The protocol describes right-click → Open for
  first launch. Follow your institution's policy if macOS blocks it; do not
  disable security controls. The protocol lists Monterey 12.4+; this is not a
  guarantee about the later release asset or your machine.
- **Windows:** download [Myotally_V1_Win.exe](https://github.com/pieterboth/Myotally/releases/download/Myotally_V1.0.2/Myotally_V1_Win.exe)
  to a user-owned folder and open it under local policy. This release asset is
  an `.exe`, not the older `.zip` mentioned in the protocol. The protocol lists
  Windows 10; this package has not checked other releases or hardware.
- On either system, record the release, actual asset checksum, OS and application
  identity in the run record. A download/launch error is a blocker to record;
  it does not justify running an unrelated executable. No Python install is
  needed for the upstream packaged route. Follow the same input/review steps.

## Prepare one field safely

Use one lawfully obtained, registered field with separate **same-size**,
single-channel TIFFs for laminin and DAPI. Confirm channel identities and image
calibration from acquisition records. If converting a multichannel acquisition,
use the lab's approved Fiji/Bio-Formats process, preserve the original, and
record the conversion. Do not infer calibration from magnification alone.

Create this structure **outside this repository**, in writable study storage:

```text
study/run-001/
  run-record.md
  study-metadata.csv
  input-work/                 ← choose this parent in Myotally
    field-001/                ← only disposable channel copies here
      DAPI.tif
      Laminin.tif
  exports/                    ← archive reviewed outputs here afterward
```

Keep immutable originals, metadata, and unrelated files outside `input-work`.
Source inspection shows Myotally writes and cleans files inside each processed
child folder. Never point it at your raw-data archive, shared software install,
or a folder containing only the TIFFs without the required child-folder level.
Make a fresh `run-002/input-work` copy for a retry or settings comparison.

## Parameters and first run

- **Folder Path:** absolute path of `input-work`, containing `field-001`.
- **DAPI image name:** `DAPI.tif`; **Laminin image name:** `Laminin.tif`. Match
  case, extension, and spelling exactly on Linux. Filenames are shared across
  all field subfolders; IDs belong in folder names and the metadata table.
- **MFI image name(s):** leave blank initially. A later extra channel requires
  matching registered input and validated interpretation of its intensity.
- **Image quality:** select high or low based on boundary contrast/noise; record
  the choice. This setting is not a quality certification.
- **Fiber size range:** record an empirically justified minimum and maximum in
  µm². The default checkbox is specific to 10X/7-day injury assumptions; do not
  automatically use it for another assay. Require minimum > 0 and maximum > minimum.
- **pixel : µm² ratio:** this source treats the value as **pixels per µm²**.
  For square pixels of side `s` µm, enter `1/(s*s)`. Example arithmetic only:
  `s = 0.5 µm/pixel` means enter `4`, not `0.5`. With unequal pixel dimensions,
  use `1/(sx*sy)` and verify the imaging workflow supports that calibration.
  The source multiplies area limits by this value and divides output pixel
  areas by it. Confirm a known-area object in Fiji before trusting real CSA.

Record all entries, then select **Run Myotally**. Keep any visible terminal
output. A **Finished** dialog is not proof that your image was processed: the
source can skip a child folder if a named channel is missing. Verify that the
summary includes `field-001`, a per-fiber table exists, and `final.tif` aligns with
the source field. Expected files, not expected numeric values, are listed in
[review and export](review-and-export.md).

## Original-files-unchanged check

After the real-tool run and again after the retry, verify that every original
file still exists and recompute its SHA256 using the same method as the initial
manifest. Require the before/after filenames and hashes to match exactly; record
the comparison in the run record. Also confirm the metadata outside the processed
tree is preserved. If anything differs or is missing, stop acceptance, retain
logs and work copies, and investigate before another run. Restore originals only
from an independently verified backup under the lab's recovery process. This
manual GUI safety check remains unrun; the source CLI control independently
passed the corresponding input-hash check locally.

## Useful retry check for the future real-tool test

On a second disposable copy only, rename `Laminin.tif` to `Laminin-missing.tif`
while leaving the GUI entry unchanged. The inspected code is expected to skip
that field rather than provide a helpful validation error. Check that no valid
per-field result is accepted even if the GUI says Finished. Restore the correct
name in a **fresh** work copy and rerun with the same settings; require that the
field appears in outputs. Save actual observed messages and output inventory.
The GUI-specific behavior has **not been run** here. The CLI instead rejects a
missing-channel manifest visibly before upstream is invoked; that contract and
retry passed the local synthetic control. The GUI destroys its window after
Finished (`Myotally_V1.py:23–24`), so a GUI retry requires relaunching and re-entering
settings. Blank/non-numeric size or ratio entries reach `float()` without a
validation dialog (`Myotally_V1.py:18–19`); retain any traceback rather than
recording such an attempt as completed analysis.

If nothing processes, check the selected parent/child layout and exact channel
names first. If there is a traceback or the GUI cannot open, save the error and
ask the maintainer to resolve that version's environment; preserve the failed
run and never repair it by overwriting originals.
