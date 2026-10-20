> Current status: [verification and remaining gates](../../docs/current-verification.md). Execution notes below retain their historical checkpoint scope.

# Scanpy perturbation readout with planted truth

This original toy dataset teaches an agent to keep experiment, donor, sample and
perturbation identities while checking a transcriptomic readout. It runs real
Scanpy/AnnData; it needs no network during the suite, real lab data or other package.
Source files can be installed read-only. Each user supplies fresh private output
directories and may select a separately installed, read-only Python environment.

From this folder, using an available **Python 3.12** (tested: 3.12.12):

```sh
python3.12 -B setup_runtime.py
.runtime/bin/python -B tutorial.py --output runs/my-first-run
```

The second command runs the entire focused suite, creates actual H5AD/JSON outputs,
logs and provenance, and exits 0 only on PASS. Choose a fresh output name for each
intentional run. No cleanup or overwrite occurs. Setup also refuses an existing
`--prefix` (default `.runtime`); a failed setup leaves its logs for diagnosis.
Do not install into Myotally, base Python or another package. Keep private `runs/` and `.runtime/` ignored.

`requirements.lock` pins all 53 resolved distributions. On 2026-10-19, official
[Scanpy 1.12.4 metadata](https://pypi.org/pypi/scanpy/1.12.4/json) and
[AnnData 0.13.4 metadata](https://pypi.org/pypi/anndata/0.13.4/json) both require
Python >=3.12. `artifacts.json` records the selected macOS arm64 wheel URLs,
SHA256s and interpreter markers from the actual pip resolution. It is provenance,
not a portable wheel bundle. Setup uses only binary distributions from official
PyPI with exact version pins, recording each new platform's selected artifact in
`<prefix>/install-report.json`; a missing compatible wheel is a setup failure.
Python 3.12 on Linux is a manager-owned execution gate after review. No Linux run,
installation in a shared environment or biological validation is implied here.

## Input and output contract

`fixture.json` schema 1 has ordered `genes`, a `samples` registry, ordered `cells`,
and a dense integer `counts` matrix (cells × genes). Each cell has `cell_id` and
`experiment_id`, `donor_id`, `sample_id`, `perturbation`; each registry sample has
the latter four fields. Sample IDs are globally unique; experiment/donor/perturbation
IDs repeat across their cells. All IDs are single alphanumeric/hyphen tokens,
starting with a letter. This restricted grammar also avoids ambiguous combined
Scanpy group labels. Cells and genes have unique IDs. Each sample maps to exactly
one experiment, donor and perturbation. Lists, composite perturbation labels,
missing/duplicate IDs, unknown mappings, nonfinite/negative/fractional counts,
boolean counts and malformed shapes fail. Integer-valued numbers up to 2^31−1
are supported. The toy contract requires `QcToy`, `control`/`pulseQ`, at least two
donors, both assignments per experiment/donor and multiple cells in each sample.

For a shared installation, an installer creates a **fresh** external environment
once (never an existing environment or system Python):

```sh
python3.12 -B /path/to/scanpy/setup_runtime.py --prefix "/path/to/new shared environment"
```

Setup records primary metadata, the platform's selected wheel URLs/hashes in
`install-report.json`, and `install.log` inside that new prefix. It refuses any
existing prefix, symlink, source/output overlap or active/base or recognizable existing environment subtree.
A setup failure preserves its incomplete prefix; choose a fresh one for another
attempt. Setup is an installer action, not part of a user's tutorial run.

Users run the installed package from any working directory, with paths quoted:

```sh
"/path/to/shared environment/bin/python" -B /path/to/scanpy/tutorial.py \
  --runtime-prefix "/path/to/shared environment" \
  --output "$HOME/scanpy results/my-first-run"
```

To run only the workflow, the checked-in fixture can be read directly when its
parent does not overlap the chosen external output:

```sh
"/path/to/shared environment/bin/python" -B /path/to/scanpy/workflow.py \
  --runtime-prefix "/path/to/shared environment" \
  --input /path/to/scanpy/fixture.json \
  --output "$HOME/scanpy results/readout-only"
```

`--runtime-prefix` defaults to this package's `.runtime`. It selects the required
prefix, not an interpreter to launch: use that prefix's `bin/python`. The actual
`sys.prefix` must match, Python must be 3.12, all 53 installed versions must match
the unchanged lock, and the prefix must contain a matching pip install receipt.
The suite passes this selection and `-B` to every child workflow. Reports record
both selected/actual prefix and before/after runtime identity. No activation or
current working directory assumption is needed.

Output must be a fresh private directory. External outputs are allowed; within the
source package only fresh descendants of `runs/` are allowed for development.
Outputs cannot overlap selected, active or base runtimes (or recognizable environment ancestors), the input's parent tree,
or be nested in existing results/snapshots (identified by workflow/suite reports
or H5AD results). The input parent also cannot be below output. Thus direct use of
`fixture.json` with a package-local `runs/` output is still refused: use external
output, or copy the fixture into a fresh sibling input directory under `runs/`.
Symlinks in input, output or any ancestor and existing output files/directories
are refused before writing. A parent containing unrelated inputs, such as a home
directory, may overlap an output beneath it; choose separate input/output trees.
These are ordinary local filesystem guards, not a hostile concurrent filesystem
security boundary.

Matplotlib and Numba caches live in the new output's private `.cache/`; bytecode
writes are disabled, including in suite subprocesses. Package and runtime are
read-only inputs. No package/runtime cache directory is created or changed.

A successful workflow produces `qc.json` (all original cells), `readout.h5ad`
(retained cells: log-normalized `X`, integer `layers['counts']`, all identities),
`pseudobulk.json`, `pseudobulk.h5ad` (Scanpy `layers['sum']`), and `report.json`.
The report records each stage as PASS, FAIL or NOT_RUN, versions, code/input hashes
and artifact hashes. Unsafe destinations exit 2 with a refusal on stderr and no
report there; validly reserved destinations with bad data exit 1 with a FAIL
report and downstream NOT_RUN. Runtime errors identify the runtime check separately
from input validation, leaving downstream analysis stages NOT_RUN.
Failed directories cannot be reused for retry.
Partial outputs from a later-stage failure remain marked FAIL for inspection.

The suite adds 20 real invalid-input subprocesses, one corrected retry, nine
filesystem refusal cases, logs and `suite-report.json`. It checks the known QC,
retained IDs, every scalar normalization value, raw integer counts, sample sums,
cell counts and identities in both H5AD artifacts. Each new input's before/after
hash is recorded. An unexpected error leaves the active check FAIL and unvisited
checks NOT_RUN. Git commit/status are null for a copied package outside Git;
code SHA256s still identify the executed bytes. No suite fixture is fetched from
upstream. `VERIFICATION.json` is historical evidence for commit `4494133`
(28 cases); it does not certify this runtime/output change. Its original fields and pins remain
unchanged. `INSTALLED_VERIFICATION.json` records the separate bounded local
read-only installation check and its limits; detailed logs, install reports, input variants and H5ADs remain private under ignored paths.

## Expected arithmetic

All genes and perturbations are fictional. `QcToy` is a numerical QC sentinel,
not a mitochondrial annotation or a biological marker. Cells c01–c03 are S1C,
c04–c06 S1Q, c07–c09 S2C, and c10–c12 S2Q. `truth.json` contains literal expected
per-cell totals, detected genes, sentinel totals/percentages and retained IDs.
The 0/0 sentinel percentage for c09 is undefined (Scanpy NaN, JSON null).

Fixture-specific filter: total counts >=8, detected genes >=2 and QcToy counts
<=25% of total. Retain c01,c02,c04,c05,c07,c08,c10,c11. Reject c03,c12 (75%
sentinel), c06 (one count), c09 (zero counts). These are teaching thresholds.

| Donor | Sample / assignment | FableA | FableB | FableC | QcToy | Retained cells |
|---|---|---:|---:|---:|---:|---:|
| D1 | S1C / control | 6 | 6 | 4 | 0 | 2 |
| D1 | S1Q / pulseQ | 14 | 4 | 2 | 0 | 2 |
| D2 | S2C / control | 8 | 4 | 8 | 0 | 2 |
| D2 | S2Q / pulseQ | 16 | 2 | 4 | 0 | 2 |

For example, S1C FableA = 2+4=6. Cell c01 has 8 total counts, 3 detected genes
and 0% sentinel; normalization to 100 gives [25,50,25,0] before natural log1p.
The independent suite uses literal truth and Python scalar arithmetic, with
1e-12 relative/absolute tolerance on floating transforms. Raw counts and planted
sums use exact equality.

## Actual API sequence and scientific limits

1. `scanpy.pp.calculate_qc_metrics` uses `layers['counts']`, `qc_vars=['toy_qc']`,
   `percent_top=None` (four genes cannot support default top-50 metrics),
   `log1p=False`. Subset by the declared QC mask and preserve all identity columns.
2. `scanpy.pp.normalize_total(target_sum=100, exclude_highly_expressed=False)`
   and `scanpy.pp.log1p` change floating `X`; the integer count layer stays intact.
3. `scanpy.get.aggregate(by=[experiment_id, donor_id, sample_id, perturbation],
   func='sum', layer='counts')` creates one row per retained sample. AnnData writes
   and reads the results, checked against original metadata and integer counts.

See official [QC](https://scanpy.readthedocs.io/en/stable/generated/scanpy.pp.calculate_qc_metrics.html),
[normalization](https://scanpy.readthedocs.io/en/stable/generated/scanpy.pp.normalize_total.html)
and [aggregation](https://scanpy.readthedocs.io/en/stable/generated/scanpy.get.aggregate.html)
documentation. The installed pinned signatures/source were also inspected.

There are two donor units with matched assignments, **not eight independent donor
replicates**. This deterministic construction only tests data handling. The planted
count differences establish no differential expression, causal effect, statistical
power, stem-cell function or biological validity. No embeddings, clustering, DE
models or p-values are produced. Actual experiments need defensible sample design,
assignment review, batch/technical-QC handling, appropriate donor-level analysis and
functional evidence chosen by the investigators. Tutorial mechanics passing is
separate from independent code review, Linux execution and any real-data gate.
