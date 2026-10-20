> Current status: [verification and remaining gates](../../docs/current-verification.md). Execution notes below retain their historical checkpoint scope.

# CellProfiler: synthetic culture-image counting

**Linux synthetic mechanics PASS.** FASRC job 53886969 completed with exit 0 at tested commit `7d2d6747d3e8e6218c4db13c4461cccd77526b85`; the manager verified all 12 suite cases and three real **CellProfiler/core 4.2.8** invocations on 2026-10-19. The baseline measured 12 fields and 6 wells, including a blank field at zero and matched-control normalization. The suite also verified zero-denominator refusal after real measurement, unchanged input/sentinel hashes and an equal corrected retry. See [observed-linux.json](observed-linux.json) for sanitized results and evidence hashes and [VALIDATION.md](VALIDATION.md) for historical local checks and exact tested source hashes. Independent final delta/evidence review remains manager-owned; shared-module deployment, real-data use and biological validation remain pending.

This tutorial measures original synthetic fluorescent objects, sums fields into wells and normalizes wells to matched controls. The historical 12 host-only tests remain separate evidence from the actual Linux package run.

The container runs a one-module in-memory API pipeline: `IdentifyPrimaryObjects.run(Workspace)`. `cp_measure.py` follows the workspace lifecycle in the [official v4.2.8 module tests](https://github.com/CellProfiler/CellProfiler/blob/2df090ff281cff80943fe679a1c3192fbda9cd6d/tests/modules/test_identifyprimaryobjects.py), including the blank-image count measurement. This is real package segmentation, not an implementation of connected components in this tutorial. It does not use a `.cppipe` loader or the CellProfiler GUI. Inputs are supplied through `ImageSetList`; the module's `Image/Count_FluorescentObjects` measurement is the exported count. The Python API script is the executable pipeline. `module-settings.json` records every effective module setting for review.

The original generator makes twelve 96 × 96 grayscale PNGs: two donors, two experiments, one plate per experiment, three wells per plate, two non-overlapping fields per well. Circular objects have radius 5 pixels, background 8/255 and foreground 230/255. The module uses a global manual threshold of 0.5, smoothing 0, diameter 8–14 pixels, size/border exclusion enabled and no declumping or hole filling. One valid field contains no bright objects and must measure zero. Missing and corrupt files must refuse the run.

## Local checks and sample data

Run from the repository root with Python 3.9+ (host code has no third-party dependencies):

```sh
python3 -m unittest discover -s onboarding/tutorials/cellprofiler -p test_tutorial.py -v
python3 onboarding/tutorials/cellprofiler/runner.py generate \
  --dest onboarding/tutorials/cellprofiler/.runtime/originals
```

Only this generator's small, 2D, 8-bit grayscale PNG encoding is accepted. Validation deliberately rejects other layouts, dimensions, encodings, symlinks and malformed files. This is not a general image importer. No upstream images, source or binaries are vendored. Generated data, SIFs, caches and results belong in ignored `.runtime/` or a private scratch directory, never staged in Git. The generator refuses an existing destination.

`metadata.csv` has this exact ordered header and representative rows:

```csv
experiment_id,donor_id,plate_id,well_id,field_id,condition,image
E01,D01,P01,A01,F01,control,images/E01_D01_P01_A01_F01.png
E01,D01,P01,A01,F02,control,images/E01_D01_P01_A01_F02.png
E02,D02,P01,B01,F01,treated,images/E02_D02_P01_B01_F01.png
```

The generated manifest contains all twelve rows; the excerpt above is not a runnable complete manifest. The tuple `(experiment_id, donor_id, plate_id, well_id, field_id)` uniquely identifies a field. Experiment/donor/plate IDs start with a letter, have at most 32 letters, digits, underscores or hyphens; wells are A01–H12 and fields match `F[0-9]{2}`. Conditions are `control` or `treated` and must agree within a well. Each experiment has one donor in this tutorial. Every image path is a unique relative `images/*.png` path. The manifest must cover every image exactly once. No missing identity, duplicate identity, duplicate image, traversal, unlisted image or missing image is allowed.

`truth.csv` contains the same five identity columns plus `expected_count`. Truth is declared from the number of objects the generator draws; it is never computed by segmenting the pixels. The host compares real CellProfiler output to truth. The container pipeline reads only metadata and images, not truth. `ORIGINALS_SENTINEL.txt`, truth, metadata and every original image are hashed before and after each run. Outputs must be new directories and cannot equal, contain, or be contained by originals, including resolved symlink aliases. Failed preflight creates no output, allowing a corrected retry at the same requested destination. Once a package run creates output, preserve that evidence and retry into a new directory.

## Pinned Linux installation and execution

On an allocated **Linux amd64 compute node**, use an already installed Singularity or Apptainer. Do not install Docker, start daemons, alter existing environments, or pull/convert the image on a login node. FASRC documents [Singularity on the cluster](https://docs.rc.fas.harvard.edu/kb/singularity-on-the-cluster/); its observed executable is `/usr/bin/singularity`. Other sites may use `apptainer`; omit `--runtime` to discover Apptainer first, then Singularity.

The official [Docker Hub 4.2.8 metadata](https://hub.docker.com/v2/repositories/cellprofiler/cellprofiler/tags/4.2.8) was checked on 2026-10-19: `linux/amd64`, compressed size 1,656,719,742 bytes, last pushed 2024-09-16. The pull uses this immutable reference:

```text
docker://cellprofiler/cellprofiler@sha256:fec440caa2b44edf80f9bd440a3d8c6b214d72437332ad2586a32d79e2eae2a4
```

The registry manifest's SHA256 was independently checked against that digest; its config digest is `sha256:e62676bea3c021a2c50aa05217a1a9c9e9870e2a73e5da651e74d08fe887a9af`, architecture amd64, OS linux, and virtual environment path `/opt/venv/bin`. The runner overrides the image's CellProfiler entrypoint with `singularity exec ... /opt/venv/bin/python /tutorial/cp_measure.py`. Inside the container, both CellProfiler and core must report **exactly 4.2.8**; PyPI 4.2.8.1 is not substituted.

Installation is explicit and never overwrites an existing SIF, receipt or pull log. Replace the two private path placeholders below, then run these exact commands on compute:

```sh
CP_TUTORIAL=/ABSOLUTE/PATH/TO/REVIEWED/CHECKOUT/onboarding/tutorials/cellprofiler
CP_PRIVATE=/ABSOLUTE/PRIVATE/COMPUTE/SCRATCH/cellprofiler-tutorial
mkdir -p "$CP_PRIVATE"
export SINGULARITY_CACHEDIR="$CP_PRIVATE/singularity-cache"
export SINGULARITY_TMPDIR="$CP_PRIVATE/singularity-tmp"
export APPTAINER_CACHEDIR="$CP_PRIVATE/apptainer-cache"
export APPTAINER_TMPDIR="$CP_PRIVATE/apptainer-tmp"
mkdir -p "$SINGULARITY_CACHEDIR" "$SINGULARITY_TMPDIR" "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR"
python3 "$CP_TUTORIAL/runner.py" install \
  --runtime /usr/bin/singularity --sif "$CP_PRIVATE/cellprofiler-4.2.8.sif"
python3 "$CP_TUTORIAL/runner.py" suite \
  --runtime /usr/bin/singularity --sif "$CP_PRIVATE/cellprofiler-4.2.8.sif" \
  --dest "$CP_PRIVATE/suite-001"
```

`install` pulls only the digest-pinned reference and writes `SIF.json` with the digest, runtime version and full SIF SHA256, plus `SIF.pull.log`. `--sif` accepts an explicit existing SIF path: retain/copy its adjacent receipt, too. The runner checks the receipt's pinned source, platform and SIF hash before every package run. This is a local provenance chain from the pull command, not a signature or an independently attested assertion about an arbitrary SIF. Unreceipted or modified SIFs are rejected; don't fabricate a receipt to adopt an unrelated image. Keep the same SIF and receipt for retries. Both the SIF conversion and full SIF hash checks take time and scratch space; the 1.66 GB compressed size is not a complete disk-space estimate.

For one generated plate instead of the full suite:

```sh
python3 "$CP_TUTORIAL/runner.py" generate --dest "$CP_PRIVATE/originals-001"
python3 "$CP_TUTORIAL/runner.py" run \
  --runtime /usr/bin/singularity --sif "$CP_PRIVATE/cellprofiler-4.2.8.sif" \
  --originals "$CP_PRIVATE/originals-001" --output "$CP_PRIVATE/run-001"
```

Bindings are explicit: originals → `/input:ro`, tutorial scripts → `/tutorial:ro`, new output → `/output:rw`; the container working directory is `/output`. The runner requests `--cleanenv --containall --no-home` and sets the Matplotlib cache under output. **Observed runtime limitation:** Singularity 4.5.1 emitted `WARNING: Overriding HOME environment variable with SINGULARITYENV_HOME is not permitted` in all three actual invocations, ignoring the requested HOME override. Actual measurements and suite checks passed, but HOME redirection is not established. The tested runner and warning are preserved; no runtime fix or suppression has been applied. No source inputs are edited. Runtime logs capture argument vectors and merged stdout/stderr. A failed launch, version mismatch, missing package output, count mismatch, zero denominator or changed original cannot pass. There is no mocked or skipped package-pass mode.

## Manager-owned Slurm recipe

This reusable template requires review against the site's current policy. The observed completed manager-run job is summarized above; this block is not a transcript of that submission. Replace every angle-bracket placeholder, select a new private directory for each suite attempt, and have the manager obtain required submission review. The log parent must already exist before `sbatch` runs. Pull and conversion happen inside the allocation. To reuse an installed image, remove only the `install` command and retain the existing SIF plus receipt.

```sh
#!/bin/bash
#SBATCH --job-name=cp-culture-tutorial
#SBATCH --account=<ACCOUNT>
#SBATCH --partition=<PARTITION>
#SBATCH --time=00:45:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=<EXISTING_PRIVATE_LOG_DIRECTORY>/cp-%j.out
#SBATCH --error=<EXISTING_PRIVATE_LOG_DIRECTORY>/cp-%j.err
set -euo pipefail
CP_TUTORIAL='<ABSOLUTE_REVIEWED_CHECKOUT>/onboarding/tutorials/cellprofiler'
CP_PRIVATE='<PRIVATE_COMPUTE_SCRATCH>/cp-tutorial-001'
mkdir -p "$CP_PRIVATE"
export SINGULARITY_CACHEDIR="$CP_PRIVATE/cache"
export SINGULARITY_TMPDIR="$CP_PRIVATE/tmp"
mkdir -p "$SINGULARITY_CACHEDIR" "$SINGULARITY_TMPDIR"
python3 "$CP_TUTORIAL/runner.py" install --runtime /usr/bin/singularity \
  --sif "$CP_PRIVATE/cellprofiler-4.2.8.sif"
python3 "$CP_TUTORIAL/runner.py" suite --runtime /usr/bin/singularity \
  --sif "$CP_PRIVATE/cellprofiler-4.2.8.sif" --dest "$CP_PRIVATE/suite-001"
```

The 8 GB/45 minute request is a starting allocation estimate, not observed resource use. No GPU, SSH or privileged runtime is needed by the tutorial.

## Reports and interpretation

The Linux suite runs the real module on the baseline, a corrected duplicate-metadata retry, and the all-blank-control variant. Other cases intentionally fail during host preflight: duplicate/missing/invalid identities, missing metadata row, missing/corrupt image, existing output, and parent/child overlap. It records hash maps before/after attempted runs and checks originals and sentinels, including the existing-output sentinel. Negative-case success means the expected refusal was observed; it does not mean the package executed for that case. `suite-report.json` can pass only after the successful real-package cases and real-package zero-denominator refusal are verified. Mac/no-runtime execution exits nonzero before creating a suite.

Every started package attempt writes `case-report.json`, `runtime-version.log`, `cellprofiler.log`, `package.json`, `module-settings.json`, `measured-fields.csv`, and label PNGs where execution reached those steps. Successful normalized runs also write `measured-wells.csv` and `control-summary.csv`. Reports record container digest, SIF hash, Python/dependency versions, module source hash and tutorial source hashes. Partial/failed artifacts remain evidence, never reusable output destinations. A preflight refusal prints an error and creates no run directory; the suite records it in its own report.

Fields sum within each `(experiment, donor, plate, well)`. The denominator is the arithmetic mean of the **control well sums** within `(experiment, donor, plate)`; it must be positive. There is no pooled denominator across donors or experiments. For this synthetic plate, the actual Linux run measured these well totals:

| Experiment / donor | Control A01 | Control A02 | Treated B01 | Control mean | B01 / control mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| E01 / D01 | 5 | 5 | 10 | 5 | 2.0 |
| E02 / D02 | 4 | 4 | 2 | 4 | 0.5 |

These are synthetic mechanics checks, not biological hits, treatment effects, p-values or evidence of biological replication. Fields and cells/objects are subsamples and cannot supply biological sample size. The two donor/experiment labels demonstrate grouping only. Each well uses equal area and field count in this example; real unequal sampling requires a prespecified area/exposure design rather than blindly summing. Fluorescent-object counts are only a cultured-cell count proxy under an independently validated one-object-per-cell assay; they do not establish survival, self-renewal, fusion, regeneration or stem-cell function. Real overlapping objects, staining variability, dead cells, debris, saturation and merged nuclei require a separate validated pipeline and review. Do not apply this fixed synthetic threshold directly to research data.
