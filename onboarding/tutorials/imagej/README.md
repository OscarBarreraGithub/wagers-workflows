> Current status: [verification and remaining gates](../../docs/current-verification.md). Execution notes below retain their historical checkpoint scope.

# Reviewed-region ImageJ tutorials

This package teaches two distinct endpoints using original synthetic binary masks and **actual headless ImageJ 1.54p**. Python only generates fixtures, validates metadata, launches Java, and aggregates ImageJ results. `ImageJMeasure.java` calls `ByteProcessor`, `Calibration`, `ResultsTable`, and `ParticleAnalyzer` from the pinned `net.imagej:ij` artifact.

These examples validate reviewed-region measurement mechanics. They do not validate automated H&E segmentation, image detection, marker classification, central-nucleus identification, Fiji GUI behavior, human review, or biological agreement. The synthetic `reviewed=true` and regeneration-sample flags are supplied annotations, not demonstrated human judgments. A mask alone cannot establish regeneration, marker positivity, or central nuclei.

## Run the focused suite

Prerequisites: Python **3.12+**, `curl`, and internet for the first download. Git is optional and supplies checkout provenance when available. No pip dependencies, Maven, Fiji, system Java, or shared analysis environment are used. Run from this directory:

```sh
python3 tutorial.py suite --out runs/first-check
```

The destination must be new. This single command verifies/downloads the pinned artifacts, extracts a task-local JDK into ignored `.runtime/`, compiles the real ImageJ runner, generates fixtures, runs measurements and negative cases, and retries corrected input in a fresh destination. Nonzero exit means failure; inspect `suite-report.json` and the named case logs. The suite stops at the first unexpected failure. It never runs app tests. Runtime artifacts, original/generated masks, manifests, and logs stay ignored; no binaries are vendored.

Supported installation pins are macOS arm64 and Linux x86_64. The Linux recipe is **untested** until a manager runs this same command there. Other platforms fail explicitly. `python3 tutorial.py install` installs/compiles without running the tutorial. All Java commands use the extracted JDK's absolute path and `-Djava.awt.headless=true`; no system Java changes or shell activation are needed. Java option injection environment variables are removed for child Java processes. The JDK is a reproducibility pin for this isolated tutorial, not a recommendation for a production runtime.

`runtime-lock.json` records exact official artifact URLs, versions, licenses, and SHA256 values. ImageJ's POM declares public domain; its JAR SHA256 was computed from the official Maven Central artifact. The Temurin 21.0.8+9 archive SHA256 pins come from the official release asset digests. The installer checks both archives before use and uses Python's data extraction filter. Extracted JDK license files remain inside `.runtime/`. A partial or mismatching download fails rather than silently changing versions. JDK extraction uses `.runtime/.jdk-extracting/`, writes an archive-specific `.imagej-complete.json` marker only after extraction and required-file checks, and publishes the JDK directory with an atomic rename. An existing staging directory or JDK without a valid completion marker is refused. Preserve and inspect an interrupted tree; move it aside within this task's `.runtime/` before retrying. Prior tutorial installations without the marker also need to be moved aside, allowing re-extraction from the verified cached archive. No global installation or automatic deletion is performed.

## Example 1: reviewed fiber area and a declared sample

The hierarchy is **study > animal > muscle > section > field > fiber**. Each fiber has its own binary grayscale PNG mask and a registered identity. ImageJ measures its single 8-connected region with supplied horizontal and vertical micrometres per pixel. All foreground is exactly 255; background is 0. Masks must represent **filled reviewed regions**, not outlines. A zero-valued enclosed hole is an error. Before measuring, the runner applies ImageJ's `Binary` Fill Holes operation to a disposable copy and rejects the mask if any pixel would change; it never fills the measurement input or infers nucleus boundaries. This uses ImageJ's 4-connected background semantics: a hole is background without a 4-connected path to an image edge. Edge objects are retained; no area cutoff is applied. Empty or disconnected fiber masks are rejected. Touching objects can merge under 8-connectivity, so identity and separation must already have been reviewed.

Each animal/muscle has two sections, three fibers per section, and a supplied four-fiber regeneration sample. The first section's regions contain 12, **5** (an L: 3×3 minus 2×2), and 10 pixels. The second contains 16, 6, and 30 pixels. The sampled subset contains 12+10+16+6 = **44 pixels**, versus **79 pixels** among all six reviewed fibers. These fixed geometric facts specify truth independently of ImageJ and the PNG reader.

| Animal / muscle | Pixel width × height (µm) | Sample n | Sample mean (µm²) | All reviewed mean (µm²) |
|---|---|---|---|---|
| A1 / TA | 0.5 × 0.8 | 4 | 4.4 | 5.2666666667 |
| A1 / GA | 1 × 1 | 4 | 11 | 13.1666666667 |
| A2 / TA | 0.25 × 2 | 4 | 5.5 | 6.5833333333 |

`fiber-areas.csv` holds every ImageJ fiber measurement with its sample flag. `fiber-muscle-summary.csv` reports `sampled_regenerating` and `all_reviewed` separately for each study/animal/muscle. Fibers and fields are nested observations, not independent animals. The all-reviewed output is not a reproduction of a published sampled regeneration endpoint. This example does not define or validate how fibers should be selected for a biological study.

## Example 2: reviewed GFP-positive count, maximum across sections

Each section has two already reviewed, nonoverlapping GFP fields. One binary mask per field contains only objects already designated GFP positive. ImageJ counts connected objects in these masks. It does not threshold a fluorescence image or judge positivity. Empty GFP fields count as zero and remain in the registered inventory. GFP masks must also contain filled regions without enclosed holes. **8-connectivity counts touching regions as one object**, including two regions meeting only at a diagonal pixel corner. This is a limitation, not a biological merge or a cell-splitting procedure. Reviewed GFP objects intended as distinct counts must already be separated; otherwise this runner can undercount biological objects.

| Animal / muscle | S1 field counts → section count | S2 field counts → section count | Muscle maximum |
|---|---|---|---|
| A1 / TA | 2 + 1 → 3 | 1 + 4 → 5 | 5 |
| A1 / GA | 1 + 0 → 1 | 2 + 2 → 4 | 4 |
| A2 / TA | 2 + 1 → 3 | 1 + 0 → 1 | 3 |

`gfp-fields.csv` preserves each field, `gfp-sections.csv` sums the reviewed, nonoverlapping fields **within** a section, and `gfp-muscle-max.csv` takes the **maximum section count per study/animal/muscle**. It records the number of sections and all tied maximum section IDs. It never pools sections, divides by total fibers, or combines muscles/animals. Every GFP muscle must have at least two sections. The fixture maxima differ from pooled section sums (8, 5, 4) and the A1/TA maximum differs from the largest single field (4), so wrong reductions fail. Counts describe only registered reviewed coverage; a whole-section endpoint requires complete section coverage established outside this tool.

## Separate fixture and measurement commands

```sh
python3 tutorial.py fixtures --out runs/demo-input
python3 tutorial.py measure --input runs/demo-input --out runs/demo-measurement
```

To use later pre-reviewed regions, create a **new** input directory with the same schema as the generated example:

- `design.json`: `schema_version: 1`, `fields` with the five hierarchy IDs, endpoint (`fiber` or `gfp`), integer width/height, and positive finite `pixel_width_um`/`pixel_height_um`; `fibers` registers each six-part fiber identity. Fields are keyed by the entire five-part identity, fibers by the six-part identity. Repeated short IDs under different parents are allowed.
- `regions.csv`: exactly the generated column order. A `fiber` row references one registered fiber and mask, with `reviewed=true` and an explicitly supplied `regeneration_sample=true/false`. A `gfp` row references one registered field, has a blank fiber ID, and `regeneration_sample=false`. Every registered fiber and field must appear exactly once in its applicable inventory. Both endpoints and a nonempty sample in each fiber muscle are required by this tutorial contract.
- `masks/NAME.png`: 8-bit, single-channel PNG, 0/255 only, declared field dimensions, unique relative filename per row. Supply registered, nonoverlapping, filled reviewed regions without enclosed holes. Do not supply raw fluorescence or H&E images as masks.

After separately reviewing the design, CSV, masks, calibration and coverage, create the initial manifest and run:

```sh
python3 tutorial.py seal --input runs/reviewed-input
python3 tutorial.py measure --input runs/reviewed-input --out runs/reviewed-measurement
```

Sealing records bytes, not scientific correctness or reviewer identity. It refuses an existing manifest; never reseal an unexplained mutation. Keep the original sealed inputs. Copy them into a new correction directory, deliberately correct and review the metadata, then create a new manifest and use a new output directory. A changed CSV identity must also agree with the reviewed design registry; updating both is an intentional design change, not something hashes can detect as scientifically wrong.

Input/output nesting in either direction and destination reuse are rejected before writing there. The complete input inventory and SHA256 hashes must match the manifest; extra, missing, changed, or symlinked input files are rejected. Input file, directory, root and ancestor symlinks are refused before any input hashing or output creation; use canonical directory paths. Identifiers use 1–64 ASCII letters/digits/underscores/hyphens, starting with a letter or digit. Calibration must be numeric, finite and positive, with a finite positive product. Dimensions must be integers from 1 to 4096. Invalid annotations, missing inventory, reused masks and invalid ImageJ values fail explicitly. On a measurement failure after output creation, preserve its new output directory and `run-report.json`; retry in another new directory. Symlink refusal happens before an output directory exists and is reported in the invoking case log. Partial CSVs from a failed run are not valid results.

## Evidence and limits

The suite emits originals and their hashes, deliberately modified input copies, expected rejection logs, a corrected retry restoring the exact original hashes, actual ImageJ object/area/count CSVs, per-run reports, and a machine-readable suite report. Reports record elapsed time, source SHA256 values, artifact pins, observed runtime versions, and executable/class hashes. In a tracked checkout, they also record the exact Git commit, working-tree status and a boolean dirty flag. A copied package without Git metadata reports `tested_commit`, `package_git_status` and `package_dirty` as JSON `null`, with `package_origin=copied_package_no_git_metadata`. Source hashes remain available; a null dirty flag means unknown, not clean. Running a copied package requires no Git checkout or Git executable. Each output manifest hashes all preceding outputs except itself. `VERIFICATION.json` preserves the prior 22-case local execution reviewed at source/evidence commits `4e2e9e7`/`d0d39d2`. It predates the filled-region/refusal changes and is historical evidence only. `VERIFICATION-round1.json` records the new revision's execution separately. Evidence records are later commits, so the exact tested source commit is the one named in each record. Consult source hashes and working-tree status rather than assuming an arbitrary later commit was tested.

Negative cases cover missing/nonfinite/zero/negative/overflow calibration, invalid and changed IDs/hierarchy, duplicate field/fiber IDs, invalid dimensions/sample/review flags, nonbinary/empty/disconnected masks, enclosed holes, input symlinks and tampering, output reuse, overlap, and corrected retry. Nonbinary and hole cases require their specific Java error in `imagej.log`, so an unrelated Java failure cannot pass them.

Additional planted fixtures independently specify a 5×5 ring with a 3×3 enclosed hole (16 foreground pixels, 9 enclosed background pixels, **rejected**), a 3×2 rectangle touching the top/left edges (one object, 6 pixels, **2.4 µm²** at 0.5×0.8 µm), and two 2×2 squares meeting diagonally (one 8-connected object, 8 pixels, **3.2 µm²**). The latter two run through both fiber and GFP masks. Their expected counts/areas are fixed geometric facts independent of the runner, and the diagonal case explicitly does not claim two biological GFP cells are distinguishable.

The suite also copies the package and cached official archives into a disposable directory outside the checkout, plants incomplete/interrupted JDK trees and checks refusal, then corrects that runtime and runs an actual copied-package `measure`. It asserts unchanged copied inputs, the original independent area/count/aggregation truth, a completion marker, null Git/dirty metadata, and source hashes identical to the checkout. Copied measurement reports/CSVs/logs are retained under the suite's `copied-package-measurement/` directory before the disposable installation is removed. No real-image, GUI, segmentation, human-review or biological accuracy claim follows from a passing synthetic suite.

Public references: [ImageJ introduction and calibration](https://imagej.net/ij/docs/intro.html), [pinned ParticleAnalyzer source/API](https://github.com/imagej/ImageJ/blob/v1.54p/ij/plugin/filter/ParticleAnalyzer.java), [pinned Binary fill source/API](https://github.com/imagej/ImageJ/blob/v1.54p/ij/plugin/filter/Binary.java), [pinned Calibration source/API](https://github.com/imagej/ImageJ/blob/v1.54p/ij/measure/Calibration.java), [official Maven POM and license declaration](https://repo.maven.apache.org/maven2/net/imagej/ij/1.54p/ij-1.54p.pom), [official Temurin release](https://github.com/adoptium/temurin21-binaries/releases/tag/jdk-21.0.8%2B9).
