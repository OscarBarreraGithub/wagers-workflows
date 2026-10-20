# Agent task: preserve identity while verifying a readout

Use this Scanpy tutorial package as read-only software. Use its separate Python
3.12 runtime (default `.runtime` or explicit `--runtime-prefix`) and exact lock;
never modify Myotally, other package environments or global Python.
Do not use SSH, Slurm, app suites, external messages or publication.

Question: Can you carry a small raw-count readout from cells to matched donor/sample
pseudobulk without losing perturbation identity or silently summing log expression?

Read README.md and fixture.json. Before executing, identify the four sample mappings,
the eight cells expected to survive and the four hand-calculated count sums. Name
why eight cells do not create eight donor replicates. The genes and assignments
are fictional.

The installer creates a fresh runtime once with `setup_runtime.py --prefix` if
needed; users reuse it without changing it. From any working directory, run one
command with a fresh private output (substitute actual absolute paths):

```sh
"/path/to/shared environment/bin/python" -B /path/to/scanpy/tutorial.py \
  --runtime-prefix "/path/to/shared environment" \
  --output "$HOME/scanpy results/agent-trial"
```

Inspect suite-report.json and the ambiguous-assignment FAIL report: validation
must fail, all later stages must be NOT_RUN, no H5AD may exist for that attempt.
The corrected retry uses a new directory; verify its actual PASS report, QC values,
integer count layer, log-normalized X, sample/donor/perturbation sums and H5AD round
trip against truth.json. Inspect the refusal logs for reuse, input overlap and
symlinks, source/runtime destinations and nested results; preserve all evidence
and original input hashes. The runtime prefix must match `sys.prefix`, all 53
pins and its install receipt. Keep caches private under the new output and
bytecode disabled. Never chmod, install into or otherwise modify a shared runtime
or source. Direct fixture use requires external output with no input overlap.
Never label a skipped stage or failed command passed. Stop on an unexpected failure; report its exact
case/stage and retained evidence instead of rerunning unrelated suites.

Deliver: tested commit (or unknown outside Git), code/input hashes, actual package
versions, observed checks and output names, plus unresolved gates. Keep detailed
logs/runtime/H5ADs private and ignored; share only a small sanitized observed summary.
`VERIFICATION.json` retains the historical 4494133 run; do not attribute its 28
checks to changed code. A successful run supports synthetic software mechanics only.
Do not infer DE, causality or stem-cell function. Independent review and installed Linux execution
belong to the manager after this local run.
