# Wagers workflows: start here

Five implemented tutorials help Amy and her agent practice analysis and review
mechanics. [Current verification](docs/current-verification.md) separates inspected
software results from deployment, access and real-study validation. Synthetic
passes establish neither tissue accuracy nor biological performance. These tools
use different methods; they are not all AI-based.

| Your question | Start with |
| --- | --- |
| Lin-type laminin/DAPI segmentation and a separately human-scored dystrophin fraction per muscle | [Myotally tutorial](docs/tutorials.md#myotally-scenarios) and [specialist skill](skills/wagers-myotally/SKILL.md) |
| Oh/Sinha H&E sampled fiber areas, or Sinha GFP maximum per-section total within a muscle | [ImageJ reviewed-mask tutorial](tutorials/imagej/README.md); calibration, masks, marker scoring and sampling need human review |
| Buchanan-inspired donor/well culture counts and matched-control normalization | [CellProfiler tutorial](tutorials/cellprofiler/README.md); counts do not establish stem-cell function |
| Preserve donor/sample/perturbation identity through QC and raw-count pseudobulk | [Scanpy tutorial](tutorials/scanpy/README.md); synthetic fixture-schema JSON only, no real CSV/transcriptome or differential-expression claim |
| Practice propose → fictional outcome → import → update | [Adaptive simulation](tutorials/adaptive-screen/README.md); fictional targets, no gene recommendations or lab control |

For all five commands and agent prompts, use the [tutorial entry points](docs/tutorials.md).
The repo-local [Wagers workflows skill](skills/wagers-workflows/SKILL.md) routes to
existing task files and the Myotally specialist. Point your agent at that file;
a local file and its UI metadata do not establish automatic skill discovery.

## Before running

For the short user/maintainer split and copyable agent instruction, read the
[root handoff](../HANDOFF.md). Historical combined module passes exist; the
existing owner-hosted cluster module is the immediate demo route. The separate
maintainer [fresh installer](deploy/install/README.md) cold run is pending; see
[current verification](docs/current-verification.md).

Use the owner's separately supplied private command card for the exact module
root. The module file is currently owner-readable only; Amy's access is not
verified. Check access for the intended session. Public source can be cloned
without GitHub signup; rebuild only if needed, following the maintainer route.
In an allocated CPU session, replace the example root below:

```sh
module use "/absolute/root/from-private-command-card"
module load wagers-tools/2026.10-env001
wagers-doctor --json
```

Repeat `module use` in each new shell/job. Loading exposes commands; it does not
allocate compute or grant access. Doctor checks inventory/hashes, not package
execution or biology. A preloaded Python module can be replaced; unload does not
restore it, so explicitly reload your previous Python module if needed. If access
or a launcher fails, retain the diagnostic and ask the maintainer to resolve it.
See [FASRC prerequisites](docs/fasrc-runbook.md) and the
[installed CLI contract](deploy/umbrella/README.md#lab-user-after-manager-application).
Installation and runtime licensing are maintainer responsibilities.

Choose new private output directories outside shared software, all runtimes,
originals and metadata; quote paths containing spaces. Keep immutable originals
and acquisition/calibration evidence. Myotally gives upstream disposable
channel-only copies because upstream cleans its input directory. All real-study
work needs approved human review, sampling and assay-specific acceptance.
Preserve study → animal → muscle → section → field → fiber identity; fields and
fibers are not animal replicates. [Review/export guidance](docs/review-and-export.md)
and [actual Myotally commands](docs/cli.md) explain that contract.

Keep data, runtimes, manuscripts and private records outside this shareable tree.
Check staged files before sharing; ignore rules are not a privacy audit. Source
retrieval/testing grants no inferred redistribution license. Local commits are
not a verified remote backup. See the [contribution guide](docs/bootloops-contribution.md)
for the local instruction pack and remaining handoff gates.
