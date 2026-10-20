# Wagers instruction packs: local contribution candidate

Current documentation baseline: `b0735262`. Use [current verification](current-verification.md)
for reviewed integration and runtime gates and the [front door](../README.md)
for all five scientific routes. The [workflow router](../skills/wagers-workflows/SKILL.md)
links existing agent tasks and preserves the [Myotally specialist](../skills/wagers-myotally/SKILL.md).
These repo-local skills are not installed discovery or BootLoops acceptance.
Independent review of this refresh and the manager's actual installed-module /
fresh-agent workflow remain required. No external submission is authorized here.

## Historical Myotally pack provenance

The original pack was refreshed 2026-10-19 UTC against reviewed core revision
`af513bdda8fe985893f361b4096b8d749d9c10d0` (wrapper `0.2.1-env001`;
module/environment name remains `1.0.2-env001`).
This pack makes the existing safe CLI usable by an agent without duplicating
the implementation. It is locally prepared for review and a later discussion
with Matt. No upstream acceptance, public PR, publication, installed BootLoops
integration or completed deployment is claimed. Contribution-ready handoff
requires independent forward-testing with the reviewed core.

Core review `b3179fa5` approved code/staging after round-1 fixes. Its then-current CLI
commands were unchanged. `animal-summary.csv` now groups by study + animal +
muscle and includes `muscle_id`; review import accepts UTF-8 BOM and exact
finite decimal-equivalent numeric formatting while preserving identity/value
checks. The skill uses the generated `exports/review-template.csv` and incorporates
static reviewer `462a395f` suggestions S1–S4. The manager's two-field
development-route scenario passed. Its historical pending gates were subsequently
advanced by the per-tool Linux runs in current verification. Direct-Python
execution alone does not prove installed skill first use or Lmod behavior.

## Purpose and extension convention

The [BootLoops harness](https://bootloops.ai/harness.html) describes tool
documentation and reusable plain-Markdown protocols. Its official
[tool-stewardship skill](https://github.com/BootLoops-ai/skills/blob/main/skills/tool-stewardship/SKILL.md)
asks tool pages to explain purpose, when to use them, output meaning and the
check needed to trust the answer. Our [skill](../skills/wagers-myotally/SKILL.md)
uses those four questions for the actual Wagers CLI. These primary sources and
the [official skills repository](https://github.com/BootLoops-ai/skills) were
read on 2026-10-19; this is a local adaptation of documentation conventions,
not an assertion of a formal extension API. No BootLoops toolkit installation
is required. Numerical precision gates from mathematical tools do not establish
histological accuracy; our scientific gate is blinded, representative manual
reference validation under an approved assay plan.

The original addition consisted of `skills/wagers-myotally/SKILL.md`, its brief
`agents/openai.yaml` discovery metadata, and this guide. The existing CLI and
manuals remain authoritative. There is no second wrapper, source fork,
redistributed upstream asset, private study, runtime environment or site path.

## Load and reproduce a bounded demo

Keep the combined `onboarding/` tree intact so the skill's relative links reach
the CLI contract, templates and evidence. Point an agent at
`onboarding/skills/wagers-workflows/SKILL.md` and ask it to select the relevant
existing task; use the Myotally specialist for the bounded demo below. Repo-local
storage alone does not guarantee automatic discovery by every harness. `agents/openai.yaml` supplies optional Codex UI metadata; it
does not install a skill or register an API. No global installation is needed.

Installation belongs to the maintainer: follow the
[pinned bootstrap/launcher contract](cli.md#bootstrap-for-the-manager),
[candidate environment recipe](../environment.yml), and
[source/version/licensing inventory](upstream-and-linux.md). Use a reviewed
release in the selected environment. Historical Myotally installed Linux checks
passed; the fresh bytecode release and combined umbrella still require their own
measured checks. Follow [module prerequisites](../README.md#before-running).
If `wagers-myotally` is unavailable, report that blocker before running the demo.
Do not fetch/install a substitute through the skill.

Choose a writable absolute directory **outside this repository**, originals,
metadata and the software installation. The evidence directory must not yet
exist. In that environment run, checking each exit status:

```bash
wagers-myotally doctor
wagers-myotally validate-one --evidence-dir "$HOME/Wagers private results/control-01"
```

The [synthetic example](../examples/synthetic-control/README.md) describes the
original deterministic fixture and the actual observed Mac exports. The command
generates its TIFFs locally; no images ship with this skill. It exercises a
real upstream run, a missing-laminin failure, valid retry, input/manifest/sentinel
hash checks and a fictional review export. Inspect `validation.json`,
`missing-channel.log`, both run provenances, `original-files-check.json` and
`synthetic-review-export/`. A successful synthetic report is
`passed-runtime-control-only`; individual analysis runs remain
`succeeded-review-pending`. Synthetic auto-filled review decisions exercise
CSV mechanics only and must never be applied to real images. Bounds
200–3000 µm² and 1 µm/pixel describe the control, not study recommendations.

For a lawful calibrated real field, use the [manifest template](../templates/image-manifest.csv)
and [actual analysis/review commands](cli.md#prepare-a-study-manifest). Human
review, manual positivity and [scientific boundaries](review-and-export.md)
remain required. Preserve raw, failed, normalized and reviewed outputs with
their provenance in private run storage; share only sanitized evidence approved
for the contribution.

Report each study/animal/muscle summary row separately; do not hand-pool rows
into an animal fraction without predeclared weighting. Positivity needs human
scoring from separately acquired marker channels of the same registered field,
retained as review evidence. Laminin/DAPI views are not marker evidence. Import
Excel identifiers as Text and retain ISO `YYYY-MM-DD` review dates as text;
save CSV UTF-8 and verify neither was coerced. The [skill](../skills/wagers-myotally/SKILL.md)
states identifier/reserved-name rules and exact numeric import semantics.

## Historical core evidence (current gates are linked above)

Core evidence is recorded in [VALIDATION.md](../VALIDATION.md), with versions,
settings, execution windows and hashes in
[observed-mac.json](../examples/synthetic-control/observed-mac.json). The tested
executable checkpoint is `94c6647afa426070090a10c2c845fa860f354bc2`;
the approved package revision above retains those executable bytes. The manager
subsequently repeated the nine tests and actual upstream `validate-one` via the
Mac environment's Python: passed, with reviewer evidence re-read. That subsequent
code/staging approval resolves the older open-review entry in the core record.
Complete manager logs remain private. These are core development-route results,
not a forward-test of this pack or an installed launcher. Observed 61-row and
nine-test counts describe this revision/run, never immutable acceptance counts.

The manager also executed the integrated core above on macOS through the
pinned environment's Python: **exit 0**, two fictional muscles of one synthetic
animal, two actual upstream fields and 122 exported rows. A missing channel
exited 2 without creating a run; valid retry succeeded. An Excel-style UTF-8 BOM
review with reformatted equivalent numbers was accepted, while a changed animal
ID exited 2 without an export. The summary retained two muscle rows for one
animal. Unscored dystrophin fractions stayed blank; deliberately fictional 0/1
marker-score records produced separate muscle fractions of 0 and 1. Input and
code hashes remained unchanged and project Git was clean. These duplicated
synthetic shapes and fabricated score records test software mechanics only;
they provide no biology or human marker-review evidence. The original manager
execution record remains private for the independent review; this summary is
manager-reported evidence, not a new run by the pack implementer.

| Gate | Measured status at the referenced revision |
| --- | --- |
| Mac ARM64 direct environment Python, pinned upstream synthetic control | Passed in core validation and manager repeat: first and retry each produced one field and 61 fiber rows. Observed count only, not a golden count or accuracy score. |
| Missing channel and input safety in that Mac run | Passed: missing laminin exited 2, visibly reported the missing channel, created no bad run, then valid retry succeeded; originals, manifest and nonchannel sentinel hashes matched. |
| Mechanical synthetic review export | Passed: fictional study/animal/muscle summary; unscored dystrophin count/fraction remained blank. No real-image review. |
| Focused safety/contract tests | Nine passed in the core record and manager repeat; names below. |
| This instruction pack's packaging | Skill-creator quick validation, UI YAML, relative file/anchor links and instruction/contract checks; static checks only, not runtime or installed discovery. |
| Installed CLI/skill discovery and launcher | Historical installed Myotally passed; current bytecode release, umbrella and skill discovery remain separate gates in current verification. |
| Linux dependency solve/final-prefix bootstrap | Historical Myotally build passed; new release validation remains pending in current verification. |
| Linux module and installed launcher/control | Historical Myotally route passed; actual five-tool module and fresh-shell checks remain pending. |
| Lab-member first use/access and real-image human review/export | Pending; GUI/packaged binaries also untested here. |
| Representative biological accuracy and assay acceptance | Pending; synthetic shape segmentation does not validate tissue measurements or positivity. |
| Independent executable core review | Code/staging approved at the referenced package revision by review `b3179fa5`; deployment/scientific gates remain open. |
| Two-field development-route CLI scenario | Manager execution passed: two muscles/one animal, missing-channel retry, BOM/numeric import, identity rejection and separate unscored/fictional-score summaries. Independent instruction/original-evidence review remains pending. |
| Independent skill plus reviewed-core acceptance | Pending reviewer check of the refreshed pack and manager execution record. No installed-route or skill first-use pass claimed. |

The nine tests recorded for that core checkpoint in [test_safety.py](../tests/test_safety.py) are:

- `test_originals_are_never_a_run_directory`
- `test_missing_channel_is_visible_and_writes_no_run`
- `test_invalid_calibration_and_duplicate_fields`
- `test_reserved_field_names_and_deployment_path_text`
- `test_same_file_or_stack_channels_are_rejected`
- `test_finished_without_real_outputs_is_a_failure`
- `test_review_cannot_invent_positivity_or_change_identity`
- `test_two_muscles_remain_distinct_for_one_animal`
- `test_bom_numeric_equivalence_keeps_exact_identity_and_values`

Current developer command examples (not executed by this documentation refresh),
run from `onboarding/` in the selected environment:

```bash
python -B -I -m unittest discover -s tests -v
bash -n scripts/bootstrap.sh deploy/validate.slurm
```

Their recorded pass does not replace actual upstream execution or independent
review. This instruction-only addition does not rerun or certify the core suite.
The packaging checks use the local skill-creator's `scripts/quick_validate.py`
on `onboarding/skills/wagers-myotally`, plus UI strings, scope and relative links.
In the original isolated pack worktree containing only those three new files,
relative links were resolved using local additions first and the read-only
core revision above for dependencies. No core files were copied into this
patch. This refresh compares instructions with the reviewed contract/code by
reading only; it does not execute core tests, the installed launcher or upstream
analysis. Those checks establish packaging, not agent behavior. In the manager
repeat, raw CSV hashes differed solely because of CRLF/LF endings; parsed rows
and normalized bytes matched. Record normalization explicitly when comparing
shared LF exports with raw runtime CSVs; do not silently normalize original images.

## Independent integration gate

Have an independent reviewer use the skill to complete a realistic request such
as: “Use this skill and the installed Wagers CLI to check a synthetic field,
handle a missing channel, retry safely and explain which animal export can be
used and what is still unscored.” Give the reviewer the skill, reviewed core,
actual CLI/environment and isolated original synthetic files, with all generated
data/evidence outside the shareable tree. Keep original channels and metadata
outside disposable work. Do not substitute mocked upstream execution.

Verify that two muscles from one animal
remain separate rows in `animal-summary.csv` and that a BOM/Excel numeric
round-trip of the generated review template accepts equivalent values while
changed identities or measurements still fail. Keep positivity blank without
registered marker evidence; report muscle rows separately and confirm ID/date
preservation. Record actual results without treating observed counts as targets.

The manager's completed bounded two-field scenario used the actual core CLI
through the pinned environment's Python as a development route, with the exact
invocation retained in the original execution record. Independent review must
check that record against the refreshed instructions. The execution pass
establishes that route only; current installed umbrella/skill discovery and lab
first use remain pending.
Historical individual Linux passes and changed-release checks have the separate
scopes listed in current verification.

Record the exact combined core/skill revisions, invocation and environment,
commands/exit codes, visible missing-channel outcome and retry, output inventory,
first/retry original/manifest hashes, review/export behavior and the agent's
scientific interpretation. Retain complete logs privately. The reviewer must
check actual artifacts, not merely re-read this page. Resolve findings before
the manager declares the combined package ready; core approval alone does not
approve the skill, and a skill schema check does not approve the runtime.

Update current verification only after inspecting new execution evidence: date,
OS/architecture, resolved
builds, reviewed release identity, actual launcher/module/control commands and
observed results, including failures. Record lab first use and biological
validation separately. Do not replace pending statuses with planned outcomes.
The owner will handle any later discussion or submission; this task sends no
external messages and publishes nothing.
