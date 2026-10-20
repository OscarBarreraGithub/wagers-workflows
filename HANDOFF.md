# Start here

Clone the [public repository](https://github.com/OscarBarreraGithub/wagers-workflows)
and read this guide; no GitHub account is required:

```sh
git clone https://github.com/OscarBarreraGithub/wagers-workflows.git
cd wagers-workflows
```

## Copy to your setup agent

> Clone https://github.com/OscarBarreraGithub/wagers-workflows and read
> HANDOFF.md plus onboarding/deploy/install/README.md. Set this up on my
> authorized cluster so I can module load it. Inspect Linux x86_64, site
> Python/Mamba/Singularity prerequisites and authorized account/storage. Reuse an
> accessible verified existing module when appropriate; otherwise configure and
> run pinned installer into new final install/module paths in allocated compute.
> Run documented verification for the new installation and give me exact module
> use/load commands and a concise result. Ask only missing access/site/storage
> decisions; don't guess accounts/ACLs, run compute on login nodes, or
> reinstall/retest an already verified owner setup.

Follow the [installer contract](onboarding/deploy/install/README.md) for actual
site preconditions: Linux x86_64, selected site Python 3.12+, Mamba,
Singularity/Apptainer, Git and curl, exact executable/version/hash declarations,
and authorized final storage and compute allocation. These are site-specific;
source availability does not establish them. Cold job `54148277` is still
unverified/pending, so no new cold-install success is claimed. Reuse of the
existing accessible verified setup does not depend on that portability test.

Reuse the **existing owner-hosted cluster installation** for the immediate demo
when accessible.
Its historical combined module runs passed all five tutorials; see
[current verification](onboarding/docs/current-verification.md). The fresh
installer and future lab transfer are separate maintainer work; cold job
`54148277` remains pending as a portability test, not a prerequisite to the
existing demo. Rebuild only when needed. Ordinary users do not install packages or rebuild
runtimes. Biological acceptance is separate and need not block a synthetic demo.

## Lab user: existing cluster demo

The owner supplies a private command card separately with the exact module root,
release identity and allocation instructions. Module and launcher files are
present, but the module file is currently owner-readable only (`0400`). Amy's
access is not verified; use an authorized accessible session and check access
before running. In an allocated CPU session,
replace the example root with the card's path:

```sh
module use "/absolute/root/from-private-command-card"
module load wagers-tools/2026.10-env001
wagers-doctor --json
```

Repeat `module use` in each new shell/job. It adds a module search path;
`module load` exposes commands. Neither allocates compute nor grants access.
Doctor checks inventory/hashes, not five-suite execution or biology. Loading can
replace a preloaded Python module; unloading does not restore it. Explicitly
reload your previous Python module if needed.

Choose a route in the [workflow chooser](onboarding/README.md), then use the
[installed commands and five agent guides](onboarding/docs/tutorials.md).
Use new private output directories outside software, runtimes, originals and
metadata. Retain diagnostics on failure and contact the maintainer.

## Later: lab maintainer installation, rebuild or transfer

Follow the reviewed [fresh installer contract](onboarding/deploy/install/README.md),
including its private config template, site prerequisites, new final destinations,
receipts and acceptance steps. Do not use the assembly-only route as a substitute
for building missing runtimes. Myotally, Scanpy and adaptive use separate Python
environments; ImageJ has its pinned JDK; CellProfiler uses a pinned container.
The module selects these fixed runtimes for users.

Place software and module roots in authorized lab-owned storage, with a lab
custodian and second maintainer. Deployment and recovery must not depend on
any individual's account. Verify the intended user's access through
every ancestor and runtime before advertising the transferred deployment. The
existing owner-hosted installation is the immediate demo route; future lab
transfer does not gate that walkthrough. Hosting does not prove lab ownership,
backup or access.

Use the complete reviewed published checkout from the
[public repository](https://github.com/OscarBarreraGithub/wagers-workflows), and
record `git rev-parse HEAD` there. The published snapshot may have a new commit;
internal review hashes are not guaranteed remote commits. Retain source,
private configs/receipts and permitted artifact backups separately. The installer
is an online pinned rebuild, not a demonstrated offline restore. It neither
allocates compute nor submits a job. Require the fresh installation, all five
suites through its new module, shell load/unload and intended-user access evidence
before declaring that release ready. The runtime task remains open.

## Copy to your usage agent

> Read README.md, HANDOFF.md, onboarding/docs/current-verification.md and
> onboarding/skills/wagers-workflows/SKILL.md. Choose the relevant tutorial and
> its linked task guide in onboarding/docs/tutorials.md; for Myotally also read
> onboarding/skills/wagers-myotally/SKILL.md. Use the existing cluster module
> root from the owner's private command card, check access for the intended
> session, and use an allocated CPU session. Load
> wagers-tools/2026.10-env001 via that root; do not install or override runtimes.
> Run the chosen synthetic tutorial into a new private output directory outside
> protected trees. Inspect the report, exit statuses, preserved inputs and logs.
> Report exact source/runtime identity, outcomes and unresolved gates. On an
> unexpected failure retain evidence and stop; do not suppress or retry it.
> Never invent human review or biological validity. Myotally needs separate human
> positivity scoring; ImageJ uses reviewed masks; CellProfiler counts do not prove
> function; Scanpy accepts synthetic fixture JSON and makes no DE claim; adaptive
> targets are fictional and never control a lab or recommend genes.

Repo-local skills must be read explicitly; their presence does not prove automatic
agent discovery. Keep private data, accounts, paths, manuscripts and runtime
receipts out of the shareable repository.
