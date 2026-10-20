---
name: wagers-workflows
description: Route Wagers analysis questions to the five implemented tutorials and the Myotally specialist, preserving assay boundaries and checking deployment prerequisites before execution.
---

# Wagers workflows

Read [current verification](../../docs/current-verification.md) and the
[onboarding entry](../../README.md) first. This is a repo-local routing skill;
installation, automatic discovery, the combined module and ordinary lab access
are not established by these files. If no verified launcher/runtime is available,
report that prerequisite; do not install or substitute a runtime through this skill.
Keep the onboarding tree intact for relative references.

Choose only the relevant route and read its instructions:

| Scientific question | Existing instructions | Boundary |
| --- | --- | --- |
| Lin laminin/DAPI segmentation and dystrophin fraction per muscle | [Myotally specialist](../wagers-myotally/SKILL.md) | Dystrophin needs separate human marker scoring; retain each muscle separately |
| Oh/Sinha H&E sampled areas or Sinha GFP section maximum within muscle | [ImageJ prompt](../../tutorials/imagej/AGENT_PROMPT.md) | Supplied reviewed masks, calibration and sample membership; review positivity and section coverage outside the tool |
| Buchanan-inspired culture counts | [CellProfiler task](../../tutorials/cellprofiler/AGENT_TASK.md) | Donor/well counts and matched controls, not stem-cell function |
| QC and donor/sample/perturbation pseudobulk | [Scanpy task](../../tutorials/scanpy/AGENT_TASK.md) | Synthetic fixture-schema JSON only; no real CSV/transcriptome or DE claim |
| Propose/outcome/import/update practice | [Adaptive prompt](../../tutorials/adaptive-screen/AGENT_PROMPT.md) | Fictional targets only; no gene recommendations or lab control |

Use the [five umbrella commands and example prompts](../../docs/tutorials.md)
after maintainer-verified deployment/access. The linked task files retain their
standalone package context; do not copy install/local runtime commands into an
umbrella invocation. Its runtime/source selection is fixed: no `--source`,
`--runtime-prefix`, `--sif`, `--runtime` or install/fetch override. Each output must
be a new private directory outside software, runtimes, originals and metadata;
quote paths with spaces. Do not write into the shared package's `runs/` folder.

Preserve assay identity and biological sampling units. Tissue hierarchy is
study → animal → muscle → section → field → fiber; fields/fibers are not animal
replicates. For GFP, sum nonoverlapping fields within each section, then take the
maximum across sampled sections within each muscle. Never auto-fill real marker
or mask-review decisions. Stop on unexpected failure, retain evidence and report
the actual failed/incomplete stages. Distinguish synthetic mechanics from human
review, deployment/access and real-study validation in the answer.
