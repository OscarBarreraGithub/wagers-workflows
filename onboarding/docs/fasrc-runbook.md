# FASRC maintainer and user runbook

[Current verification](current-verification.md) records four manager-inspected
Linux tutorial passes: historical Myotally (5 scenarios), ImageJ (36 cases),
CellProfiler (12 cases) and adaptive simulation (96 checks). Scanpy's first Linux
run and the fresh Myotally bytecode release check remain pending. The independently
approved five-tool assembler is integrated, but its actual combined deployment,
fresh-shell behavior and lab-user access remain unverified. The manager owns
staging, policy review and remote execution.

**Before upstream runs:** use the safe `wagers-myotally` CLI, which gives upstream
only new disposable channel copies. Keep original images and metadata outside
processed folders. Follow the [CLI workflow](cli.md) and preserve before/after
input hashes. Direct GUI use requires the [manual copy precautions](first-use.md#before-any-myotally-launch).

In a full repository checkout, Codex discovers `wagers-myotally` and
`wagers-workflows` through the relative symlinks in `.agents/skills/`. These resolve
to the original skill directories under `onboarding/skills/`; keep the onboarding
tree intact so the skills' relative references resolve. This repository-local
discovery preserves user-wide skill settings. Actual execution still requires
the maintainer-verified module and the individual user's verified access.

## REQUIRED site settings

Reported group membership or fair-share visibility does not establish individual
login/OOD access, storage permissions or an installed tool. Verify each separately.
The manager has read-only site evidence, but this portable package deliberately
contains no owner-specific home path or inferred Wagers deployment location.

| Setting | Before shared deployment |
| --- | --- |
| Responsible maintainer and backup | **REQUIRED** |
| Authorized final release prefix and module root | **REQUIRED** in private deploy config |
| Persistent study/results root and backup/recovery policy | **REQUIRED** |
| Temporary work root, quota and cleanup/retention policy | **REQUIRED** |
| Executing Slurm account, CPU partition and session limits | **REQUIRED**; manager selects/reviews exact job |
| Lab group / ACLs and per-user study write permissions | **REQUIRED** |
| Approved OOD dashboard; individual VPN/cluster access | **REQUIRED**, tested per user |
| Authorized retrieval/testing and any redistribution decision | Owner-authorized retrieval/test; no upstream redistribution license inferred |
| Linux OS/architecture and resolved environment builds | Retain exact per-release compute evidence; see current verification |
| Successful control/retry/input preservation/review exports | Historical per-tool passes exist; verify changed releases and combined launchers |
| Independent executable review and first lab-user sign-off | **REQUIRED** |

## Build and expose a versioned release

For all five tools, follow the [assembly contract](../deploy/umbrella/README.md)
using already installed, reviewed per-tool runtimes. Assembly does not install or
execute them. The integrated bytecode fix resolves the source prerequisite
formerly described there; old installed Myotally trees can still fail its guard.
Verify the new installed bytes before selecting them. Do not mix this existing
single-tool bootstrap with the new umbrella module's user-facing setup.

Follow [bootstrap for the manager](cli.md#bootstrap-for-the-manager). The package
provides `environment.yml`, `scripts/bootstrap.sh`, `scripts/bootstrap.py`,
`deploy/config.example.json`, and `deploy/validate.slurm`. The bootstrap retrieves
and hashes upstream source without vendoring it, builds at the final environment
prefix using FASRC's `module load python` / Mamba / conda-forge route, and records
resolved YAML, explicit package URLs/builds and logs. Historical Linux Myotally
build/control evidence exists; it does not certify a new release or make this
recipe a universal cross-platform lockfile.

A generated launcher **`wagers-myotally` (CPU)** calls the environment through
`mamba run`, clears `PYTHONPATH`, and disables user-site packages. The generated
Lmod file loads the site `python` module and prepends the final launcher directory.
Use `module use` with the approved module root in each session/job, then
`module load wagers-myotally/1.0.2-env001`. This exposes commands; it does not
allocate compute, grant folder permissions or install an OOD portal app.

The bootstrap refuses to overwrite a prefix/module. A failed build retains logs;
inspect those and use a new versioned prefix for a retry. One maintainer manages
package changes and approved updates. After successful independent/runtime
review, the maintainer makes the software release read-only to ordinary lab users
and confirms that analysis writes only to each user's new study run directories.
Test the launcher with an ordinary lab account, not just the installing account.
Keep prior releases for rollback; never edit a live environment during use.
The [site VDI guide](https://docs.rc.fas.harvard.edu/kb/vdi-apps/) recommends one
person manage a shared environment.

The initial [Slurm template](../deploy/validate.slurm) requests one CPU, 4 GB RAM,
20 minutes and no GPU. It includes bootstrap and synthetic upstream validation.
All account, partition and path placeholders must be filled in the **exact**
script presented to the manager's policy review before submission. No scheduler
command has been executed by this worker. A later run against one lawful real
field uses `validate-one --manifest ...`; human review remains pending afterward.

## Lab user through existing OOD Remote Desktop

After the maintainer verifies the combined release and the user's access:

1. Connect to the required FASRC VPN and the assigned OOD dashboard using your
   own account with cluster access. Do not use a shared/service login.
2. Under **Interactive Apps → Remote Desktop**, request the approved CPU resources
   and time limit. This is a queued compute job; wait for its session to start,
   then connect via **My Interactive Sessions**.
3. In the desktop terminal, use the maintainer's verified module root/name:
   `module use` is required once in every new shell/job, then `module load` the
   single `wagers-tools` release. See [exact entry steps](../README.md#before-running).
   Run `wagers-doctor --json` for inventory/hashes, then the relevant
   [tutorial command](tutorials.md). Package execution is a separate check. For
   Myotally, also follow the [one-image CLI workflow](cli.md); review numbered
   images beside the original channels before accepting muscle exports.
4. Save logs, provenance, review and outputs to persistent study storage before
   the session's time limit. Closing a browser tab need not end the job; reconnect
   through My Interactive Sessions if still active and terminate when finished.

A future desktop shortcut labeled **Wagers Myotally 1.0.2 — CPU** could launch the
validated workflow from this desktop; no GUI shortcut or new portal app has been
installed. The current supported artifact is the terminal launcher. Jupyter can
support suitable downstream Python/R analysis, but is not the upstream Tk GUI.
See the official [OOD guide](https://docs.rc.fas.harvard.edu/kb/virtual-desktop/)
and [VDI apps](https://docs.rc.fas.harvard.edu/kb/vdi-apps/) for current access.

## Storage and maintenance

Separate read-only software, immutable acquisition files, manifests and writable
per-user results. Suggested logical layout under an approved study root:

```text
study-id/
  raw/                         immutable acquisitions, hashes, calibration
  metadata/                    animal/section/field manifest and sampling plan
  users/individual-id/run-id/   new work copies, logs, provenance, exports
  review/                      manual ledger and approved annotations
```

The CLI rejects overlapping raw/manifest and run directories, never overwrites a
run, and checks named originals/manifest after computation. The synthetic control
also verifies a nonchannel sentinel. These checks do not replace permissions or
backup of the entire dataset. Keep all study/runtime files outside this repo.

Temporary scratch is working storage, not the durable record. Confirm the site's
quota, retention and recovery policy. Copy/verify results to approved persistent
storage before a session ends; persistent does not automatically mean backed up.
The maintainer defines backup/recovery responsibilities. Consult
[FASRC storage guidance](https://docs.rc.fas.harvard.edu/kb/storage-service-center/).

CellProfiler uses its pinned Linux amd64 container and an existing
Singularity/Apptainer runtime, supplied by the maintainer. Its Linux suite has
passed; that does not establish shared-user permissions or a general image
importer. The other tools retain their separate runtimes. See
[the site container guide](https://docs.rc.fas.harvard.edu/kb/singularity-on-the-cluster/).

## Compute escalation

| Work | First route | Before scale-up |
| --- | --- | --- |
| One-image segmentation/review | CPU CLI in allocated OOD desktop; approved local source route | Linux control/retry, original hashes and observed export checks |
| Larger Myotally manifests | Same CPU CLI, per-user runs | Measure dimensions, memory, wall time and I/O; do not infer GPU support |
| Optional learned/GPU analysis | Separate selected tool/environment | Lawful model/data, endpoint validation and site-approved resources; Myotally has no inspected GPU backend |
| Real/larger transcriptomics | Separate validated pipeline; delivered Scanpy tutorial accepts synthetic fixture-schema JSON only | Assay/reference versions, donor/sample design, privacy, memory/I/O and scientific review |

Culture-count and fictional adaptive-loop tutorials are implemented; they do not
establish stem-cell function, recommend genes or control experiments. Lab-member
access and biological validation remain distinct from a synthetic runtime pass.
