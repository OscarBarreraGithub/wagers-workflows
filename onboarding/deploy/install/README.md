# Rebuild the five-workflow installation

This maintainer entry point builds a **new Linux x86_64 installation at its final
paths**, then calls the reviewed [module assembler](../umbrella/README.md).
It needs no previous workflow installation, private helper script, owner account
or credentials. It does need an authorized writable destination, a lab-controlled
copy of this repository, public upstream access and the configured site tools.
Local installer tests use subprocess doubles; a real cold Linux install, all five
synthetic suites, fresh-shell Lmod checks and ordinary lab-user access remain
manager verification gates. Installation/import success is not biological validation.

## First install

1. Have the lab/site maintainer authorize the final software and module parents,
   ownership, group and backup custodian. This code grants no storage permission
   and changes no ACLs. The installation starts private (`0700`); Scanpy also
   creates a private venv. Verify every ancestor and runtime's authorized access
   before Amy uses it. Same-account success does not establish her access.
2. Retain the complete reviewed Git commit, including this installer, in a
   lab-controlled repository/backup. Obtain the full commit with
   `git rev-parse HEAD`. Run the installer and `check_runtime.py` from exactly that
   commit. The exporter reads **all tracked `onboarding/` files from Git objects**,
   not selected loose files or a dirty working tree. It refuses links/submodules
   and tracked runtime/cache trees. Keep private configuration, data, credentials,
   manuscripts and upstream downloads out of that source commit.
3. Copy [config.example.json](config.example.json) to an absolute private path
   **outside all source repositories**; fill every field. No credentials belong
   in it. Select nonexistent, disjoint `install_root` and `module_root` for each
   attempt. The roots may have missing parents, but cannot overlap each other,
   source, config, site software, or an existing Python/Conda runtime. Use resolved
   physical paths: no symlink directories, `..`, placeholder text or shell
   expansions. Printable ASCII spaces and punctuation are supported literally;
   `< > $ { } ~` are refused. Do not relocate a built installation or its venv base.
4. Select exact site Python (3.12+ with SSL, venv and tarfile), Mamba,
   Singularity/Apptainer, Git and curl capabilities. Each needs its canonical
   prefix, absolute executable, executable SHA256 and complete trimmed
   `--version` output (curl is multiline). Use `sha256sum` on the resolved file;
   a final executable symlink may resolve within its declared prefix. Mamba must
   be named `mamba`. `python_module` is the exact site Python **name/version** for
   the selected host executable; no unversioned default is loaded. Select actual
   canonical system utility directories in `system_path`; `/usr/bin` is only an
   example. Keep the site runtime and Mamba available for the release lifetime.
5. In a manager-authorized CPU allocation on Linux x86_64, using the selected
   host Python, run the one entry point (substitute the concrete private paths):

   ```sh
   "/absolute/site/python" -I -B onboarding/deploy/install/install.py --config "/absolute/private/install config.json"
   ```

The installer neither allocates compute nor submits Slurm, uses SSH, invokes
sudo, alters startup files, nor installs globally. A manager reviews and submits
the site's allocation separately. Its tool probes must succeed with the declared
PATH, a sanitized environment and no account home/configuration. Runtime builds
use a new private home, temporary directory and caches under `install_root/work`;
they do not inherit Python/Conda settings, container bind variables, tokens or
credential helpers. Mamba uses `MAMBA_NO_RC=true` without `CONDARC`; a read-only
`mamba config list` probe checks configuration before either destination is
created, because `--version` alone does not load it. This route does not support a
site tool that needs undeclared private startup scripts or credentials. Site tools and their system libraries
remain explicit infrastructure prerequisites, not bundled backup artifacts.

The source snapshot is `install_root/source/onboarding`. Every source file is
copied byte-for-byte, hashed, made read-only and rechecked before assembly and
after inventory. Source directories become read-only after preparation; only
ImageJ's reviewed `.runtime/` is excluded from the source manifest. Complete
package files, including Java, locks, fixtures, docs and helper scripts, stay
together. The original repository is not a runtime dependency.
After assembly, an explicit path audit checks every selected/inventoried source,
runtime, executable and protected prefix against the fresh tree and declared site
prerequisites (plus the separate module root). It rejects checkout references and
requires Scanpy's actual venv `home` and Python to use the new base inside the
fresh tree. `provenance/installed-path-audit.json` retains the checked paths and
inventory/config hashes; it does not claim dynamic-library dependency closure.

| Runtime | Recipe retained with source | Final location under `install_root` |
| --- | --- | --- |
| Myotally | `environment.yml`, `scripts/bootstrap.py`, `wagers.py`: Python 3.10.14, NumPy 1.24.4, SciPy 1.10.1, Pillow 10.0.1, OpenCV 4.8.1, tk 8.6; upstream 1.0.2 archive/member hashes | `runtimes/myotally/{env,upstream,app}` |
| Scanpy | Mamba creates Python **3.12.12**, pip 25.0.1 base; existing `setup_runtime.py` creates actual separate venv from `requirements.lock` (Scanpy 1.12.4, AnnData 0.13.4 and all listed pins) | `runtimes/scanpy-base`, `runtimes/scanpy-venv` |
| Adaptive | Separate Mamba Python **3.12.12**, pip 25.0.1; `requirements.txt` pins NumPy 2.2.6, SciPy 1.15.3, scikit-learn 1.6.1, joblib 1.4.2, threadpoolctl 3.6.0, pip 25.0.1 | `runtimes/adaptive` |
| ImageJ | Existing `tutorial.py install`; `runtime-lock.json` pins ImageJ 1.54p JAR and Temurin **21.0.8+9** Linux x86_64 archive by SHA256, then compiles Java helper | `source/onboarding/tutorials/imagej/.runtime` |
| CellProfiler | Existing `runner.py install`; CellProfiler/core **4.2.8**, pinned OCI digest `sha256:fec440caa2b44edf80f9bd440a3d8c6b214d72437332ad2586a32d79e2eae2a4` | `runtimes/cellprofiler/cellprofiler-4.2.8.sif` plus `.json` receipt |

The unchanged Myotally bootstrap writes an auxiliary module in
`internal-modules/`, using its legacy `python` config sentinel. That module is
never loaded or exposed by this route. The final umbrella alone uses the explicit
configured site Python module. Mamba is selected by exact PATH for that bootstrap;
all other orchestrator commands use configured absolute executable paths.

## Receipts, failure and verification

`provenance/install.json` records status, source commit, site versions, each exact
argv, stage return code and successful log hash. Its sibling files retain private
config, full source SHA256 inventory, per-stage logs, adaptive pip report, Mamba
explicit exports/resolved YAML, and generated bootstrap/assembler configs.
Package receipts also remain: Myotally source provenance/build/export records,
Scanpy install report/metadata/log, ImageJ artifact/build stamps, and SIF receipt.
These contain absolute private build paths; keep them in the lab's private backup,
not in portable source. Retain failed logs and partial trees for diagnosis.

Read-only preflight runs before creating either destination. A started stage
failure records `failed`, exits nonzero and stops: no later runtime or module
assembly and no automatic retry/deletion/reuse of the destination. Underlying
reviewed installers retain their own behavior, including ImageJ's bounded curl
transfer retry; a failed package command cannot become a successful stage.
Preserve the partial attempt and choose **two new roots** for the corrected build.
An interrupt may leave a running stage receipt if the process is killed; absence
of final `installed-runtime-probed` is never success. If inventory fails after
assembly, retain but do not advertise that module.

`installed-runtime-probed` means pinned Python/distribution version checks,
selected imports, pip checks where supplied, JDK execution/compilation and
CellProfiler/core imports succeeded, followed by source and assembler inventory
checks. It is not five-suite acceptance. The assembler separately retains its
`assembled-not-installed-validated` label; it inspects assets without installing.
The final module is assembled only after runtime probes pass. No test silently
falls back to an existing installed workflow.

After independent review, the manager must run the real installation in an empty
separate destination and execute the existing five tutorial suites through the
new module with fresh private outputs **outside** all install/module trees. Do
not delete an old release as a recovery test. Retain source and runtime receipts,
suite reports, actual Lmod load/unload results and the ordinary user's access
test. This is the recovery demonstration; a unit test or doctor alone is not.

Focused orchestration check, without downloads, package execution or Lmod:

```sh
python3 -B -m unittest discover -s onboarding/deploy/install -p 'test_install.py' -v
```

The tests explicitly double subprocess execution and Git object reads. They
cover fresh/existing destinations, overlaps, prerequisites, canonical/space
paths, exact argv, failure retention, source mutation and post-assembly refusal of
external/checkout references or an old venv base. Assembler artifacts in these
tests are simulated too. No package runtime suite is claimed by these tests.

## Module use and updates

Once the maintainer supplies the **verified accessible** module root/name, each
new shell or allocated job uses that root explicitly:

```sh
module use "/absolute/lab/module-root-for-this-release"
module load wagers-tools/2026.10-env001
wagers-doctor --json
```

`module use` selects a module search directory. `module load` exposes the five
fixed launchers and the exact Python dependency; neither grants storage access
nor allocates compute. `wagers-doctor` rechecks inventory/hashes, not scientific
execution. Run ordinary workflows in an allocated session with new private
outputs; see the [launcher commands and restrictions](../umbrella/README.md#lab-user-after-manager-application).
No ordinary user runs the installer to load or use a module.

For updates, choose a reviewed new source commit, versioned install root,
versioned module root and module name, then repeat installation and acceptance.
Never edit sources/runtimes underneath an existing module or update its venv
in place. Keep the old release available until the lab explicitly retires it.
This entry point never removes old or failed releases.

## Backup ownership and recovery

Appoint a lab custodian and a second authorized maintainer who can retrieve the
repository, private configs/receipts and permitted artifacts without the original
maintainer's account. Record their storage/access/retention procedure outside
portable source. Confirm restoration using their ordinary account, a separately
authorized **empty** destination and the documented site capabilities. No actual
lab-owned location or ordinary account access is established by this code.

An **online pinned rebuild** re-fetches public sources using the retained recipes
and hashes. It is not a byte-identical offline reconstruction: Conda recipes pin
the reviewed direct versions but resolve some transitive/build dependencies;
Scanpy/adaptive locks pin versions rather than every Linux wheel hash. Preserve
the actual Linux Mamba exports and pip install reports/hashes from each build.
`scanpy/artifacts.json` records macOS arm64 wheels and is not a Linux artifact
backup. Upstream removal or solver/artifact changes can prevent a later rebuild.
The installer fails instead of silently substituting a newer tool.

An **offline artifact backup** needs the actual permitted artifact bytes, not
just a lockfile, URL, export or hash. The lab must arrange and test its own approved
mirror/restore route; this online entry point does **not** implement offline
artifact injection. At minimum assess and retain, where licenses permit:

- The complete reviewed portable Git source and exact commit, config templates,
  recipes, source inventory, private configs, receipts and verification records.
- Myotally's exact upstream ZIP and its recorded archive/member hashes. The
  existing fetcher retrieves/extracts it online but does not retain the ZIP.
  **No LICENSE is supplied in that archive; redistribution/mirroring permission
  remains unresolved.** Obtain permission and an approved continuity plan rather
  than bundling upstream here. Its URL and hash are retained in `wagers.py`.
- Conda package artifacts for **all** resolved packages (including both Python
  bases), channel metadata and explicit exports; approved platform-specific
  Python wheels for all Scanpy/adaptive packages and installation tooling, with
  hashes/licenses. Caches/exports alone are not a certified complete mirror.
- ImageJ JAR and Temurin archive with `runtime-lock.json`, license notices and
  extracted JDK `legal/`/`NOTICE`. The lock records public-domain ImageJ and JDK
  GPL-2.0 with Classpath Exception; the custodian must fulfill applicable terms.
- The actual CellProfiler SIF **and adjacent receipt**, pinned OCI digest and
  dependency/license notices; audit redistribution obligations for the complete
  image before sharing/mirroring. Registry availability is an external dependency.

Backing up an installed prefix may preserve a working release at its original
paths, but venvs, launchers and module inventories embed absolute paths. It does
not establish recovery at a new prefix. Preserve a site-tool continuity plan too;
hashing Mamba/Python/Singularity does not back up those tools or system libraries.
No upstream binary/source vendoring or redistribution permission is inferred here.
