# CellProfiler validation record

Status: **Linux synthetic mechanics PASS**, manager-verified on 2026-10-19. FASRC job 53886969 completed with exit 0 at exact tested commit `7d2d6747d3e8e6218c4db13c4461cccd77526b85`. All 12 suite cases passed, with three real CellProfiler/core 4.2.8 invocations (baseline, corrected retry and zero-control variant). [observed-linux.json](observed-linux.json) records sanitized runtime/results and hashes of retained evidence. Independent final documentation/evidence review remains manager-owned. Shared-module deployment, real-data first use and biological validation remain pending.

The actual baseline measured 12 fields and 6 wells: counts 5/5/10 for E01/D01 and 4/4/2 for E02/D02; treated normalization was 2.0 and 0.5. The valid blank field measured zero. Corrected-retry measurements equaled baseline. Zero control denominators were rejected after real measurement. Original input and sentinel hashes were unchanged across all cases.

**Runtime limitation retained:** all three invocations emitted `WARNING: Overriding HOME environment variable with SINGULARITYENV_HOME is not permitted`. Singularity ignored the requested HOME override; actual measurements passed, but HOME redirection is not established. No executable fix or warning suppression has been applied.

Historical initial checks below ran on 2026-10-19 on Darwin arm64, Python 3.14.7, zlib 1.2.12, based on repository commit `7c50974c73193ae663e63934d4d745ba10d09145`. The initial candidate was left unstaged for independent review; the manager subsequently ran the reviewed source at `7d2d6747d3e8e6218c4db13c4461cccd77526b85`. These historical checks have not been rerun for this documentation-only update.

## Historical observed local checks

- `python3 -m unittest discover -s onboarding/tutorials/cellprofiler -p test_tutorial.py -v`: **12 tests passed** (latest run 0.082 s). These test host-only generator pixels/independent declared truth, blank valid images, metadata errors, missing/corrupt PNGs, corrected validation retry, sentinel/original immutability, output overlap/existence, well arithmetic, zero/missing controls, SIF receipt validation and refusal without runtime. No package result was mocked or accepted.
- `python3 -m py_compile` on the three Python files: passed (syntax only).
- README Slurm shell block extracted to a temporary file and checked with `bash -n`: passed; never submitted.
- New-file `git diff --no-index --check` checks: no whitespace diagnostics. No files staged.
- Actual `runner.py suite` CLI on this Mac: exit 1, no destination created, stderr `REFUSED/FAILED: actual package execution requires Linux amd64; not run`.
- Generated fixture has 12 fields, 6 wells, 2 experiment/donor identities, exactly 1 blank valid field. Pixel-area construction checks found 81 bright pixels per declared disk. Host arithmetic gives E01 controls 5/5, treated 10, normalized 2; E02 controls 4/4, treated 2, normalized 0.5. These are host arithmetic evidence, not measured package counts.

## Tested payload SHA256 at 7d2d674

These are the exact seven source hashes from the actual Linux suite report at commit `7d2d6747d3e8e6218c4db13c4461cccd77526b85`. README.md and VALIDATION.md are historical tested bytes, now superseded by this documentation-only update. The three Python files remain byte-for-byte identical to the tested source.

```json
{
  ".gitignore": "3e782aec83661b3537393e8f42b401b72f1265d22f51d8c46d5a6b84e1022e13",
  "AGENT_TASK.md": "8d0cf3d5dc65987a6f4481a955ee24471426d8eadf43c38056b5e9a189e86302",
  "README.md": "e6e0f39bc505bb33d955cfb830a1146fb74f5b3c3938509ae325899f287aee48",
  "VALIDATION.md": "c8a52834ca6f78b7efe0b8bdc3bd9bee56f5fd2702b238d060e733a97e5e2e61",
  "cp_measure.py": "ce792df162ce98b01c1d7148e30011331fcfc558f6ed660be3bb4b1d3473bb71",
  "runner.py": "94ce2dde079f60a52886124b4e58f535f43f10d9387c3aba2781d29ced9f30e6",
  "test_tutorial.py": "36e63ed5930d3aefffb3c6adb747108bb9456574bb6e16f0c382eb31c77a4b94"
}
```

## Deterministic local fixture evidence

Temporary originals were hashed before/after validation and unchanged; images are not committed. PNG compressed-byte hashes describe the observed local zlib version, not a promise across compression-library versions.

```json
{
  "metadata.csv": "958d1f8f04af72322eb3158f5bb2d783a6e443b8b3e42f511c09bf0c4c9989cc",
  "truth.csv": "b6f9753163c73d429b1ead49b2e87fecc3558cdb244fdb22eec9ce4504a0ea19",
  "blank_image": "3fd73dcca8b4bd3b7e2343bc350c019bf939543cc2a7d29eee9dc16daa2d6de4",
  "originals_sentinel": "0ed817a08abd4ef2a016508d0ac9d00c6669378f24e8296cc99a8bc078ffd6ad",
  "canonical_originals_hash_map_sha256": "13af570bcac0253487cb86227e31bebf1a5c72ecd4b14cd14a1a3be2abbf9ae0"
}
```

## Upstream static evidence

Public source files were read into a temporary directory outside the worktree, not vendored. CellProfiler release v4.2.8 resolved to commit `2df090ff281cff80943fe679a1c3192fbda9cd6d`. Its IdentifyPrimaryObjects source SHA256 was `b7389cae9e9fa63d2a0b3b1de6210b210298e2c965360a6622b249b7bcbfea7f`; its test source SHA256 was `900275b89ccd645f7cbba4447cff8e0f95f5219373c3b2f194813233e01707b3`. The core v4.2.8 ImageSegmentation source SHA256 was `b2b8016eed1b337c156f5d5ca5e93955c9266e8d5c6183ed84f7aa5366972077`.

Static checks matched the official workspace lifecycle, `ImageSet.add`, `Measurements` Count export, advanced/manual threshold settings and serialized setting API. Docker Hub tag metadata confirmed the specified digest/Linux amd64/1,656,719,742-byte image. The registry manifest SHA256 was independently recomputed as `fec440caa2b44edf80f9bd440a3d8c6b214d72437332ad2586a32d79e2eae2a4`; its config digest is `sha256:e62676bea3c021a2c50aa05217a1a9c9e9870e2a73e5da651e74d08fe887a9af`, virtual environment `/opt/venv`. During the initial Mac implementation only metadata/config/source text were fetched; the manager later pulled and executed the pinned container on Linux as recorded above.

The Linux synthetic package gate is now observed passing. Remaining manager work is independent final delta/evidence review; shared deployment, real-data first use and biology remain outside this pass. The sanitized record identifies the retained manager verification, suite/case reports and measured CSVs by SHA256; private paths, account names, usernames, runtime binaries, images and logs are not bundled. This update only reads retained evidence and edits documentation/evidence: no executable changes, test reruns, SSH or cluster actions.

The initial implementation worker performed no SSH, cluster actions, Docker daemon changes, external messages, shared-file edits, upstream vendoring or existing environment changes. The later Linux execution was manager-owned.
