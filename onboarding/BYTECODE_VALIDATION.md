# Explicit bytecode suppression: bounded validation

**PASS, implementer-executed, macOS ARM64, 2026-10-19 UTC.** Tested clean code
commit `a5db1e789345fe699b0a0151ff335df0b52e11cb`, committed before runtime execution.
Production changes were committed at `03e589d3f10a66b495c620edd6cc37fa25296d53`;
the second commit only resolves the regression's Mac temporary-directory alias.
The initial regression had three passes and that path-expectation failure;
it ran no upstream control. Its private evidence remains preserved.

The generated installed launcher and all five isolated Python child arrays now
use explicit `-B -I`. The bootstrap shell uses `python -B`, retaining its site
Python contract. Early `sys.dont_write_bytecode = True` follows the required `sys` import
and precedes subsequent local/dependency imports in the wrapper entry scripts,
including both fixture helpers. This describes wrapper imports, not suppression
before every import in upstream code. Upstream's
existing suppression remains. Dependency pins, upstream source, algorithms,
CLI arguments, output contracts and path guards are unchanged; wrapper version
remains `0.2.1-env001`, with exact revision/file hashes identifying this correction.

Four focused tests in [tests/test_bytecode.py](tests/test_bytecode.py) passed
at 11:12:01–11:12:02 UTC. They exercise real writable-scratch imports showing that
`PYTHONDONTWRITEBYTECODE=1` with `-I` still writes a cache, whereas explicit
`-B -I` prevents it; script startup and explicit-`-B` helper imports leave no
source caches. Python can cache an imported entry module before executing its
body, so an ordinary importing caller also needs `-B`; the early setter protects
subsequent imports. Child-array/dispatch assertions cover flags and paths with
spaces. Installation operations are stubbed **only for the launcher argv test**;
that test inspects the generated launcher and makes no real environment install
or upstream/doctor pass claim. Tutorial dispatch uses an argv stub; the broad
five-scenario suite and unrelated safety tests were not rerun.

One actual real-upstream `validate_one.py` synthetic first/missing-channel/retry
control passed at 11:12:02–11:12:14 UTC, through an unchanged copied onboarding
tree under `corrected source with spaces/onboarding`. Output was separate under
`actual synthetic control with spaces`. The existing pinned Mac Python 3.10.14
environment and its eight-file upstream source were consumed in place. No
runtime copy, install, chmod, source patch, SSH/Slurm or global setting change
was performed. Entry commands below use sanitized directory aliases; the private
record retains the **exact absolute argv**, working directory and environment.

```bash
"$PYTHON" -B -I -m unittest discover -s onboarding/tests -p test_bytecode.py -v
"$PYTHON" -B -I "$EVIDENCE/observe_fixture.py"
```

`PYTHON` denotes the existing `env/bin/python3.10`; `EVIDENCE` denotes the private
`881ff521 bytecode correction/a5db1e7` directory. The observation entry sets
`sys.argv` to the copied `scripts/validate_one.py --evidence-dir "$CONTROL"` and
executes it as `__main__` with `runpy.run_path`. An audit hook only snapshots the
generated fixture before the first doctor subprocess. It does not replace or
mock a subprocess or upstream call. `WAGERS_MYOTALLY_SOURCE` selected the pinned
source; OMP/OpenBLAS/MKL thread counts were 1. The environment bytecode variable
was also 1, but explicit interpreter flags provide the required protection.
The outer `wagers.py validate-one` dispatcher was checked by the focused argv
contract; this actual control entered its helper directly through `runpy`.

First and retry runs each processed one field and exported **61 observed fibers**.
The existing independent `tutorial_suite.check_run` oracle checked real raw
summary counts, fiber IDs, CSA, CNF, numbered outputs, settings and unfilled
review templates against exports. First/retry numerical records matched after
excluding only `run_id`. The mechanical synthetic review summary matched the
61 rows: mean CSA `2270.065573770492` µm², CNF count 61. These are observed fixture
results, with no golden-count or biological accuracy assertion. Positivity
count/fraction remained blank and biology remained pending. The missing-channel
case exited 2 visibly, created no `bad-run`, and the valid retry succeeded.

Before/after inventories include every entry, SHA256 for every regular file,
symlink targets, modes, ownership, size, mtime and ctime; atime is excluded.
All matched exactly: existing environment **21,769 entries / 18,710 files**,
pinned source **9 / 8**, original onboarding tree **81 / 63**, corrected copy
**81 / 63**, and generated fixture **8 entries**. No new source cache appeared.
The original tree includes the prior tracked evidence; it was not refreshed.

Private evidence is retained outside Git at
`data/private-evidence/881ff521 bytecode correction/a5db1e7/`, including logs,
full commands, code/source hashes, raw outputs and before/after manifests.
SHA256 evidence identities:

- `execution-record.json`: `66caa9dcb2ef2fa09212d4f7ea5f24038f1ada0011d3aef24657f9c6b2c59b4a`
- Both protected manifests: `b683462b5098707c53d89980c70a911f179b01910334bb4bf12fddf01904e680`
- Both fixture manifests: `28449b5e76e59b8fd8b4103cbc193971cc10bb90ede30ad709d30fcbbc9ea850`
- Observation entry: `6cd04237d8d309c5270622283a037827662c40bec8771c758f45ab3752d3971c`
- Orchestration script: `5d9e37353ee42a0f2b2437e6f7312a0a192c08ebe11be18c8c642c0c1f794572`
- Existing Python executable: `7c5e769457ce77b0dd476302bf4e80b87d5e148740af1512f00fe69ee31b5a78`

Tested executable/test SHA256s (unchanged after execution):

| File relative to onboarding | SHA256 |
| --- | --- |
| `scripts/bootstrap.py` | `696cf041e5c011da321eb9e8bf53757910897708e5a1567b45ebfea3020adda8` |
| `scripts/bootstrap.sh` | `126b45fb207ba474f346ab38f9ad4b397d40bc66441ba3a73eaff673d627af31` |
| `scripts/make_control.py` | `ab24922978e155dfca60b431a539bcb84e0c594f51d1770dafd2d8ccda7313d9` |
| `scripts/make_tutorial.py` | `e4b7be6d42abd71ee84f10b046f0a7259a15efe21a50e01677b869869a4a1e3e` |
| `scripts/tutorial_suite.py` | `b8b650ed002e44aa7ac8c5c6fa7e2475f8d081a1d07047bb41c27908aab50056` |
| `scripts/validate_one.py` | `f190abc365202470eb1e60515ac8fcc082ff2e5613f56ede334e2e8b4cb7e168` |
| `tests/test_bytecode.py` | `20d8333793ae647c27b7d068eafad6bb01a5b607efa0a02608645378fb39d557` |
| `wagers.py` | `c14407eaef48db3e1cee774160c1f5d0f9bd533fc567d38508732dd719f5631f` |

This establishes the bounded Mac source/helper correction only. Independent
review and manager-run **new installed/module Linux validation** remain required.
Earlier Linux runs remain historical for their older launcher bytes. The shared
assembler may reject older bytecode-unsafe installed trees until redeployment.
This pass establishes no installed launcher execution, Lmod/lab-user access or
biological validation. No further runtime run was performed after this pass.
