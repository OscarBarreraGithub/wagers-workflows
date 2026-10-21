# Current verification

Status as of **2026-10-20 UTC**. This is the current summary of manager-inspected
retained evidence, not a new runtime execution by the documentation task.
Historical README/JSON records retain their original revisions and pending
statements. Full logs and deployment paths remain private.

## Observed software mechanics

- All five individual Linux routes have passed at their recorded revisions.
  Latest inspected Myotally job `53891553` and Scanpy job `53890009` passed.
- Combined module checks passed across two jobs: Myotally's five scenarios
  passed in `53902250` (**partial PASS; overall FAIL** after ImageJ fixture
  preparation failed).
  Corrected follow-up `53905648` passed ImageJ 36, CellProfiler 12, Scanpy 30 and
  adaptive 96 checks. These establish synthetic mechanics for that installed
  release, not the new cold installer or a future deployment.
- Earlier shell checks observed replacement of a preloaded Python module.
  Unload does not restore it: explicitly reload the prior Python if needed.
- The new all-five installer source, internal candidate `f82a904`, has **12 focused
  tests passed** and independent approval `74ab81a2`. Those tests use doubles;
  they alone do not establish a real cold installation or five runtime-suite passes.

## Fresh cold installation: PASS

Earlier cold job `54094966` **failed immediately** because of conflicting Mamba
configuration. The source correction adds no-rc handling and a configuration
preflight. Fresh Linux x86_64 job **`54148277` completed with a manager-inspected
PASS**: all 20 build stages passed, followed by all five synthetic suites through
the new installed module: Myotally 5 scenarios, ImageJ 36 cases, CellProfiler 12
cases, Scanpy 30 cases and adaptive 96 checks.

The original checkout was moved aside before the suites. Installed paths were
confined to the new installation/module roots and site dependencies. All seven
before/after tree inventories (source, retired checkout, runtimes, umbrella,
provenance, internal modules and modulefiles) were unchanged, including file
hashes, symlink targets, modes and mtimes. Fresh-shell Lmod load/unload restored
PATH and module state. Loading replaced an older preloaded Python module;
unloading did not restore it. Explicit reload of that prior Python was checked
and restored it.

The tested source was `f82a904`. Only four Markdown files (`README.md`,
`HANDOFF.md`, `onboarding/README.md` and `onboarding/docs/current-verification.md`)
differ from reviewed main `9900d8be`; executable bytes are unchanged. The run used
the owner's authorized FASRC account/storage and online package sources. This
PASS covers the fresh build, installed module and synthetic software mechanics;
intended-user access, lab/science acceptance and offline restore remain unverified.

For initial code handoff, required installer runtime probes, module loading and
basic executable/runtime checks are sufficient. Full tutorials, ordinary-user
acceptance and real-data/biology may be scheduled later. Follow the
[installer contract](../deploy/install/README.md) for build, receipts and full
release acceptance requirements.

Use `git rev-parse HEAD` in the complete reviewed published checkout to record
its source identity; internal candidate hashes need not exist on the remote.
The [public repository](https://github.com/OscarBarreraGithub/wagers-workflows)
is public per owner/maintenance-manager confirmation. Public availability does
not establish backup/restore verification.

## Access and scientific gates

The existing owner-hosted cluster module is the immediate synthetic demo route;
a new cold installation, GitHub signup and future lab transfer are not its
prerequisites. The owner supplies the exact module path in a separate private
command card. A current presence check found the module and launchers, but the
module file is owner-readable only (`0400`); presence does not establish Amy's
access. Her ordinary-user access, a fresh-agent walkthrough, a real Excel round
trip and real biological validation remain unverified. Use
`wagers-tools/2026.10-env001` via that card and check the intended session's access
before running. Module loading does not allocate compute. Historical same-account
passes do not establish lab-user permissions. See the [handoff](../../HANDOFF.md)
and [site runbook](fasrc-runbook.md).

Synthetic demos can proceed once software and access are verified; biological
acceptance is separate. Myotally segments laminin/DAPI and needs separate human
marker positivity scoring per muscle. ImageJ measures supplied reviewed masks;
GFP totals require nonoverlapping section coverage and maxima across sections
within each muscle. CellProfiler counts do not establish stem-cell function.
Scanpy accepts synthetic fixture-schema JSON only, not real CSV/transcriptomes
or differential expression. Adaptive targets are fictional, with no gene
recommendations or lab control. Preserve animal/muscle and donor/sample/well
identity; fields and fibers are not animal replicates.

Real studies still require calibration, sampling, thresholds, human review and
manual-reference acceptance. Scripted CSV checks are not Microsoft Excel tests.
No installed BootLoops integration or automatic skill discovery is established.
Use the [tutorial commands and agent guides](tutorials.md) for the scoped demos.
