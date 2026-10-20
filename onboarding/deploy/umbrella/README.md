# Five tutorial routes, one new module

The assembly-only implementation was independently approved at `84665fb` and
integrated at `b0735262`. See [current verification](../../docs/current-verification.md)
for per-tool Linux evidence and remaining gates. Actual installed umbrella
execution, Lmod load/unload, ordinary-user access and fresh-agent checks remain
pending; no Excel/image acceptance or biological validation is claimed. The
selected Scanpy CLI `b58c2d3` was independently approved in review `54859e6b`;
adaptive-screen is `aefea1a`. Source approval does not certify an installed release.

## Maintainer

Use an absolute private config path **outside Git**, starting from
`config.example.json`. The tracked example intentionally contains no real private
paths. Do not put credentials in config. Select only already installed, reviewed,
fixed prefixes. Source paths are installed package directories, not copies to be
made by this assembler. Keep selected sources/runtimes stable for the release's
lifetime. A site Python 3.12+ runs the dispatcher, ImageJ and CellProfiler host
orchestration; Scanpy uses its own Python 3.12 venv and adaptive-screen its own
Python 3.12.12 venv or Mamba/Conda prefix. Their final `bin/python` symlink may
refer to an existing base interpreter; symlink directories are rejected. Each venv
must declare one absolute `home` naming an existing base `bin` directory with an
executable `python3.12`; ambiguous or invalid metadata is refused. The full base
prefix is protected from outputs for copied and symlinked venvs, and its interpreter
and `pyvenv.cfg` are hashed for reinspection. Config paths support the documented restricted ASCII form:
concrete absolute printable ASCII, without parent-traversal (`..`) components,
symlink directories, placeholder
text (`REQUIRED`, `PLACEHOLDER`, `CHANGE_ME`, case-insensitive), or any of
`< > $ { } ~`. Spaces and otherwise permitted punctuation are quoted literally.
User argv retains literal spaces and punctuation; it is not subject to the config
path character restriction, but package input/output path rules still apply.

Use canonical resolved paths for the config's software/runtime/module locations
and for the module root supplied to `module use`. Scanpy and adaptive-screen
refuse symlink ancestors; a convenient symlink alias is not a supported route.
Choose canonical paths for private inputs and outputs too.

Set an exact site module name/version. The manager's current tested Linux choice
is `python/3.14.7-fasrc01`; the portable example deliberately requires a choice.
This never asks Lmod to resolve the unversioned `python` default. Choose a new
`module_name`, a nonexistent `release_prefix`, and a nonexistent `module_root` for
each attempt. Each module root contains just this release's modulefile; use that
root explicitly. Destinations must be disjoint from each other, the repository,
the config file, source directories, fixed runtimes and executable locations.
Source/runtime nesting already present in an installed package is permitted.

Retain the private build default: Scanpy creates its runtime prefix with mode
`0700`. The assembler does not change existing permissions or infer group/ACL
policy. Before ordinary lab use, the maintainer must verify the authorized lab
group and its traversal of **every ancestor**, read access to software and runtime
assets, and execute access to launchers/interpreters. This includes the umbrella
release, module tree, each package/runtime and any base Python reached by a venv
symlink. Access preparation must follow the site's authorized group policy;
do not apply blanket `go+rX`. Raw data, results and per-run caches remain private.
Same-account build or `wagers-doctor` success cannot prove Amy's access. Verify
the intended user's actual route separately before making an access claim.

The existing Myotally launcher must explicitly use `python -I -B`, and its
`app/wagers.py`, `scripts/tutorial_suite.py` and `scripts/validate_one.py` must
include `-B` in every isolated child argv list (`'-I', '-B'` is accepted directly).
Historical bootstrap `4b0182c`
did **not** meet this prerequisite: its `-I` ignores the bytecode environment
variable, including in child interpreters. Assembly deliberately refuses that
older installed tree. The exact missing contract in that historical revision was:

- `scripts/bootstrap.py:86` emits `python -I` without `-B` in the installed launcher.
- `wagers.py:278,483,489`, `scripts/tutorial_suite.py:212` and
  `scripts/validate_one.py:65` construct isolated child argv without `-B`.
- `scripts/tutorial_suite.py:16-19` and `scripts/validate_one.py:11-14` import
  shared helpers without first setting `sys.dont_write_bytecode = True`.

Atomic task `881ff521` supplied the explicit child/launcher `-B` and early helper
suppression fix, independently approved at `01d3598` and integrated at `c63f8449`.
Its bounded Mac control/inventory checks passed. The new installed Linux check
remains pending in current verification; the manager must deploy and verify the
corrected bytes before assembly. Older installed Myotally trees can still be
refused. The assembler retains its compatibility guard and does not patch core
sources, the bootstrap, installed launchers or runtimes. The static gate detects
the known pattern; it is not proof of arbitrary shell/Python behavior.

ImageJ must already contain its pinned JAR and JDK archive, complete extracted JDK
(java/javac, release, modules, matching completion marker), compiled class and
matching source/JAR build stamp. Every invocation checks these before reaching
the package's implicit `prepare()` path; an incomplete runtime is refused, never
repaired. ImageJ's original suite may create its own disposable runtime under the
user's private output using those local archives, as specified by that package.
No umbrella command exposes `install`. CellProfiler requires the pinned SIF and
adjacent `.json` receipt plus an explicit executable Singularity/Apptainer path.
Its `generate` gets no runtime flags; `run`/`suite` get fixed `--sif`/`--runtime`.
Scanpy needs its install report, requirements lock and installed distribution
metadata. Adaptive needs its requirements, installed distribution metadata and an
existing JSON runtime-evidence receipt (hash recorded, contents not certified).

Adaptive's existing venv route still requires `pyvenv.cfg` declaring Python
3.12.12. Its Conda route requires `conda-meta/history`, executable `bin/python`
and exactly one installed Python package record declaring version `3.12.12`.
Every `conda-meta/*.json` must be a JSON object with nonempty string `name`,
`version` and `build` fields agreeing exactly with its `name-version-build.json`
filename. Duplicate JSON keys, nonfinite numbers (including exponent overflow),
malformed records, missing/multiple Python records and mixed `pyvenv.cfg` plus
`conda-meta` layouts are refused. This ambiguity policy avoids choosing one of
conflicting declarations; history alone cannot establish the Python version.
History and every package JSON record enter the hash inventory, so later metadata
edits, additions or removals invalidate the release. Both adaptive layouts retain
all six pinned distribution metadata checks. Scanpy still requires a venv.
This accepts the layout used by the verified adaptive Mamba environment without
creating `pyvenv.cfg`, rebuilding or relocating it; actual installed umbrella
execution remains a manager gate after independent source review.

Run only assembly, using an existing Python interpreter:

```sh
python3 -B onboarding/deploy/umbrella/assemble.py --config /absolute/private/config.json
```

It never executes configured runtimes or packages, installs, downloads, relocates
environments, alters startup files/ACLs, or contacts SSH/a scheduler. Full preflight
precedes writes. Construction failures retain `provenance/build.json`, the exact
config and any files already written; inspect them and retry with fresh paths.
Preflight failures create nothing and print their diagnostic; correct those
without deleting any installed tree. Successful builds retain exact config,
entrypoint/helper/receipt/runtime metadata hashes and assembler/dispatcher/module
hashes. They are labeled `assembled-not-installed-validated`. Inventory validates
filesystem shape/hashes and declared venv/Conda metadata only; it does not execute a
Python version probe, import native extensions or certify runtime pins by execution.
Existing installer receipts are evidence, not an installation performed here.

Focused local check (tiny fake executables capture argv only):

```sh
python3 -B -m unittest discover -s onboarding/deploy/umbrella -p 'test_umbrella.py' -v
```

These tests do not run any tutorial, dependency install, biological computation or
Lmod interpreter. Conda cases use synthetic package records and six distribution
pins; the venv compatibility fixture uses standard `pyvenv.cfg` syntax and a
symlink to an existing interpreter, without executing or installing that runtime.
`/bin/sh -n` checks generated wrapper syntax; inspection checks
the restricted Lua call/string syntax. Real fresh-shell Lmod syntax, load/unload,
dependency/conflict behavior, PATH restoration and five launcher routes remain
manager-owned on FASRC after final source integration and independent review.

## Lab user (after manager application)

The maintainer provides the new module root. Use `module use` with that path, then
load `wagers-tools/2026.10-env001` (or the reviewed release's name). The module's own
body adds only its `bin` to PATH and sets `WAGERS_TOOLS_PREFIX` and
`WAGERS_TOOLS_MODULE`; Lmod manages its exact Python dependency. Loading does not
run a tutorial or write outputs/caches. Loading the exact dependency can swap a
different Python version already loaded in the shell. Unloading the umbrella
removes its own module changes but does not restore that previous Python version.
The manager must test dependency pairing and load/unload in a fresh shell on the
site. No shell startup changes are needed.

Choose a **fresh private output** for every run, outside all shared software,
module and runtime trees. Existing package input/output/refusal/cache contracts
still apply. The wrappers additionally reject output overlap across all five
packages. `seal --input` is treated as a write destination too. User argv retains
literal spaces and punctuation. Runtime/source override flags, their argparse
abbreviations, fetch/install/internal worker commands are unavailable. Do not
write results into the shared package's `runs/` directory.

```sh
wagers-doctor --json
wagers-myotally tutorial-suite --evidence-dir "$HOME/wagers-runs/myotally-01"
wagers-imagej suite --out "$HOME/wagers-runs/imagej-01"
wagers-cellprofiler generate --dest "$HOME/wagers-runs/cp-input-01"
wagers-cellprofiler run --originals "$HOME/wagers-runs/cp-input-01" --output "$HOME/wagers-runs/cp-run-01"
wagers-cellprofiler suite --dest "$HOME/wagers-runs/cp-suite-01"
wagers-scanpy suite --output "$HOME/wagers-runs/scanpy-suite-01"
wagers-scanpy run --input "$HOME/private fixtures/syntheticfixture.json" --output "$HOME/wagers-runs/scanpy-run-01"
wagers-adaptive-screen suite --out "$HOME/wagers-runs/adaptive-01"
```

For the Scanpy `run` example, first place a private copy of the tutorial's
`fixture.json` at the shown input path. `run` accepts only the tutorial's synthetic
fixture-schema JSON, including its fixture contract; CSV and real counts are
unsupported. Use `wagers-scanpy run --help` to inspect the existing input/output CLI.

`wagers-doctor` is a read-only inventory/hash recheck of all selected assets. It
does not import packages or run their own doctors. Drift or missing assets fails
closed; ask the maintainer for a reviewed new release. Launchers clear Python
environment leakage, disable user site packages and bytecode, and preserve each
package's existing private cache behavior. Outputs/caches are never created by the
module or dispatcher under shared paths. User access and real data/biology remain
pending even after a synthetic software suite passes.
An optional cache-creation failure may be reported by a package as a runtime
failure; it remains fail-closed and must not be interpreted as a successful run.
