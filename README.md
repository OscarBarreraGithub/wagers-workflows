# Wagers workflows

Clone the [public repository](https://github.com/OscarBarreraGithub/wagers-workflows)
and read [HANDOFF.md](HANDOFF.md):

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
> install pinned code with the installer into new final install/module paths in
> allocated compute. Preserve required installer runtime probes; ensure module
> loading and basic executable/runtime checks succeed for initial code handoff.
> Give me exact `module use`/`module load` commands and a concise result, reporting
> only checks actually run. The full tutorial suite, real-data/biology and ordinary
> user acceptance may be scheduled later and must not block initial code handoff.
> Ask only missing access/site/storage decisions; don't guess accounts/ACLs, run
> compute on login nodes, or reinstall/retest an already verified owner setup.

See [setup details and site prerequisites](HANDOFF.md#copy-to-your-setup-agent).
Fresh Linux installation job `54148277` completed with a manager-inspected PASS
for the build, installed module and all five synthetic suites. Site prerequisites
and intended-user access must still be established for each deployment.

Reuse the **existing owner-hosted cluster module** for the immediate synthetic
demo when accessible. In an allocated CPU session, use the exact module root
from the owner's separately supplied private command card:

```sh
module use "/absolute/root/from-private-command-card"
module load wagers-tools/2026.10-env001
wagers-doctor --json
```

Module loading does not allocate compute or grant access. Amy's access is
unverified; the module file is currently owner-readable only. GitHub signup is
not required to read or clone this public source. The separate fresh installer
is for maintainers when a rebuild is needed.

Five synthetic tutorials exercise analysis and review mechanics. Use the
[workflow chooser](onboarding/README.md), then the
[five commands and agent task guides](onboarding/docs/tutorials.md).
These exercises do not establish biological accuracy.

[Current verification](onboarding/docs/current-verification.md) records historical
Linux/module passes and the **completed fresh Linux installation PASS**.
This documentation handoff does not establish Amy's access, Excel compatibility
or real-study acceptance.
