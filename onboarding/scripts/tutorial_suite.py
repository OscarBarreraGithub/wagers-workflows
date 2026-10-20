#!/usr/bin/env python3
"""Actual pinned-upstream tutorial acceptance; synthetic software contracts only."""
import sys

# Shared software must stay byte-for-byte unchanged, including import caches.
sys.dont_write_bytecode = True

import argparse
import csv
import datetime as dt
from decimal import Decimal
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import wagers
from make_tutorial import make_tutorial

PACKAGE = Path(wagers.__file__).resolve().parent
SCENARIOS = ["upstream-and-preservation", "animal-muscle-review", "spreadsheet-contract",
             "failure-retry-calibration", "unsafe-output-and-hashes"]
BOUNDARIES = ["H&E regeneration/CSA", "maximum GFP engraftment per muscle", "slow/fast fiber typing",
              "culture counts/function", "transcriptomics"]
IDENTITY_FILES = ["wagers.py", "scripts/tutorial_suite.py", "scripts/make_tutorial.py",
                  "scripts/make_control.py", "tests/test_tutorial_suite.py",
                  "docs/tutorials.md", "skills/wagers-myotally/SKILL.md"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def snapshot(root):
    return {str(p.resolve()): wagers.sha256(p) for p in sorted(Path(root).rglob("*")) if p.is_file()}


def verify_snapshot(before):
    check = wagers.unchanged(before)
    require(check["all_unchanged"], f"Protected files changed/missing: {check['changed_or_missing']}")
    return check


def overlap(a, b):
    return a == b or a in b.parents or b in a.parents


def evidence_location(value, source):
    value = Path(value).expanduser()
    require(value.is_absolute(), "Evidence directory must be an absolute path")
    root = value.resolve()
    require(not value.is_symlink() and not root.exists(), "Evidence directory must be new, not a symlink")
    # The standalone shareable package is onboarding; in a checkout also protect
    # its enclosing tracked tree, including paths reached through symlink parents.
    environment = Path(sys.prefix).resolve()
    protected = [PACKAGE, Path(source).resolve(), environment]
    # bootstrap's supported installed layout is <release>/{app,env}. Protect
    # writable siblings such as provenance/ too. A source checkout in onboarding/
    # does not acquire a release boundary merely by using an external env/.
    if (PACKAGE.name == "app" and environment.name == "env" and
            PACKAGE.parent == environment.parent and PACKAGE.is_dir() and environment.is_dir()):
        protected.append(PACKAGE.parent)
    try:
        protected.append(Path(subprocess.check_output(
            ["git", "-C", str(PACKAGE), "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL).strip()))
    except (OSError, subprocess.CalledProcessError):
        pass
    require(not any(overlap(root, p) for p in protected),
            "Evidence must be outside repository, installed release prefix, pinned source and Python environment")
    return root


def identity():
    record = {"wrapper_version": wagers.VERSION,
              "sha256": {n: wagers.sha256(PACKAGE / n) for n in IDENTITY_FILES if (PACKAGE / n).is_file()},
              "identity_files_absent": [n for n in IDENTITY_FILES if not (PACKAGE / n).is_file()],
              "git_revision": None, "git_dirty": None}
    try:
        subprocess.run(["git", "-C", str(PACKAGE), "ls-files", "--error-unmatch", "--", "wagers.py"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        record["git_revision"] = subprocess.check_output(
            ["git", "-C", str(PACKAGE), "rev-parse", "HEAD"], text=True).strip()
        record["git_dirty"] = bool(subprocess.check_output(
            ["git", "-C", str(PACKAGE), "status", "--porcelain"], text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        pass
    return record


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_review(path, rows, bom=False):
    with Path(path).open("w", newline="", encoding="utf-8-sig" if bom else "utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=wagers.REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def check_run(run, expected_fields, expected_settings):
    """Inspect saved upstream tables directly, without calling the adapter parser."""
    state = json.loads((run / "provenance.json").read_text())
    require(state["status"] == "succeeded-review-pending", "Run is not successful/review-pending")
    require(state["processed_fields"] == len(expected_fields), "Wrong processed field count")
    require(state["source_files"] == wagers.SOURCE_FILES, "Unpinned source in run provenance")
    require(state["biological_validation"] == "pending", "Biology must remain pending")
    require(json.loads((run / "original-files-check.json").read_text())["all_unchanged"], "Run changed originals")
    require(all(state["settings"][k] == v for k, v in expected_settings.items()), "Settings drift")
    fibers = read_csv(run / "exports" / "fibers.csv")
    require(len(fibers) == state["fiber_count"] and len(fibers) > 0, "Missing normalized fibers")
    require({r["field_id"] for r in fibers} == {r["field_id"] for r in expected_fields}, "Missing/extra fields")
    counts = {}
    for field in expected_fields:
        name = field["field_id"]
        selected = [r for r in fibers if r["field_id"] == name]
        require(all(all(r[k] == field[k] for k in wagers.IDS) for r in selected), "Metadata routing changed")
        dest = run / "exports" / "upstream" / name
        require((dest / "final.tif").stat().st_size > 0, "Missing numbered upstream image")
        summaries = list((dest / "Results").glob("all_results_*.txt"))
        tables = list((dest / "Results").glob(name + "_*.txt"))
        require(len(summaries) == len(tables) == 1, "Missing/ambiguous upstream tables")
        def upstream_rows(path):
            lines = [s for s in path.read_text().splitlines() if "\t" in s]
            return [{k.strip(): v.strip() for k, v in r.items()} for r in csv.DictReader(lines, delimiter="\t")]
        summary, raw = upstream_rows(summaries[0]), upstream_rows(tables[0])
        require(len(summary) == 1 and summary[0]["Image"] == name, "Wrong upstream summary field")
        require(int(summary[0]["Number of Fibers"]) == len(selected) == len(raw) > 0, "Count disagreement")
        require(len({r["original_fiber_number"] for r in selected}) == len(selected), "Duplicate fiber IDs")
        by_id = {r["original_fiber_number"]: r for r in selected}
        require(set(by_id) == {r["Fiber Number"] for r in raw}, "Upstream/normalized ID mismatch")
        for row in raw:
            norm = by_id[row["Fiber Number"]]
            area = Decimal(row["CSA"])
            require(area.is_finite() and area > 0 and area == Decimal(norm["csa_um2"]), "CSA disagreement")
            require(row["CNF (y/n = 1/0)"] in ("0", "1") and
                    Decimal(row["CNF (y/n = 1/0)"]) == Decimal(norm["cnf"]), "CNF disagreement")
        counts[name] = len(raw)
    template = read_csv(run / "exports" / "review-template.csv")
    require(len(template) == len(fibers) and all(not r[k] for r in template
            for k in wagers.REVIEW_COLUMNS if k not in wagers.FIBER_COLUMNS), "Review template was auto-filled")
    return {"fields": counts, "fiber_rows": len(fibers), "biology": "pending"}


def fictional_review(template):
    rows = read_csv(template)
    # Fixed, hand-auditable accepted subsets from actual exports. No synthetic
    # segmentation counts are assumed; a too-small runtime output fails visibly.
    chosen = {"field-001": [1, 0, 1], "field-002": [0, 1],
              "field-003": [1, 0, 0, 1], "field-004": [1, 0, None]}
    for field, scores in chosen.items():
        selected = sorted([r for r in rows if r["field_id"] == field], key=lambda r: int(r["original_fiber_number"]))
        require(len(selected) >= len(scores), f"Too few observed fibers for fictional review exercise: {field}")
        for i, row in enumerate(selected):
            row.update(decision="exclude", reviewer_id="FICTIONAL-SOFTWARE-CONTROL", review_date="2026-10-19",
                       reason="Fictional subset for arithmetic contract, not image review")
            if i < len(scores):
                row.update(decision="accept", reviewed_csa_um2=str(400 + 100 * i), reviewed_cnf=str(i % 2),
                           dystrophin_positive="" if scores[i] is None else str(scores[i]),
                           threshold_rule_id="" if scores[i] is None else "FICTIONAL-RULE-A")
    return rows


# Declared expectations, independently hand-calculated from the fictional review
# plan: 3+2 accepted TA fields, 4 DIA, and 3 partially scored second-animal TA.
EXPECTED = {("001", "TA-left"): (2, 5, 480, 2, "true", "3", 3 / 5),
            ("001", "DIA"): (1, 4, 550, 2, "true", "2", 1 / 2),
            ("002", "TA-left"): (1, 3, 500, 1, "false", "", None)}


def check_summary(path):
    rows = read_csv(path)
    require(len(rows) == 3 and {(r["animal_id"], r["muscle_id"]) for r in rows} == set(EXPECTED),
            "Expected two animals / three separate animal-muscle groups")
    for r in rows:
        fields, n, area, cnf, complete, positives, fraction = EXPECTED[(r["animal_id"], r["muscle_id"])]
        require(r["study_id"] == "FICTIONAL-SOFTWARE-CONTRACT" and r["biological_validation"] == "pending", "Scope lost")
        require((int(r["sampled_fields"]), int(r["accepted_fibers"]), float(r["mean_csa_um2"]), int(r["cnf_count"])) ==
                (fields, n, area, cnf), "Fictional accepted-subset arithmetic mismatch")
        require(r["dystrophin_scoring_complete"] == complete and r["dystrophin_positive_count"] == positives,
                "Partial scoring was treated as negative or complete")
        require((r["dystrophin_fraction"] == "" if fraction is None else
                 math.isclose(float(r["dystrophin_fraction"]), fraction, abs_tol=1e-12)), "Fraction mismatch")
        require(r["threshold_rule_id"] == "FICTIONAL-RULE-A", "Rule provenance lost")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--source", type=Path, default=os.environ.get("WAGERS_MYOTALLY_SOURCE"))
    args = parser.parse_args()
    require(args.source is not None, "Provide --source or WAGERS_MYOTALLY_SOURCE")
    root = evidence_location(args.evidence_dir, args.source)
    root.mkdir(parents=True)
    (root / "logs").mkdir()
    state = {"schema_version": 1, "status": "RUNNING", "scope": "synthetic-software-contracts-only",
             "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "execution": "real CLI subprocess / pinned upstream",
             "platform": sys.platform, "python": sys.version, "code_identity_before": identity(),
             "scenarios": {s: {"status": "NOT_RUN"} for s in SCENARIOS}, "commands": [],
             "unsupported": [{"task": s, "status": "UNSUPPORTED", "instruction": "Use a dedicated validated route"} for s in BOUNDARIES],
             "biological_validation": "pending", "installed_launcher_validation": "inner commands bypass launcher; outer launcher entry is not established by this report"}
    wagers.write_json(root / "report.json", state)
    source_before = snapshot(args.source)
    protected = {}
    first_before = {}
    active = SCENARIOS[0]
    cli = [sys.executable, "-B", "-I", str(PACKAGE / "wagers.py")]
    def save():
        wagers.write_json(root / "report.json", state)
    def call(name, arguments, expected=0, visible=None, absent=None):
        command = cli + arguments
        entry = {"argv": command, "shell": shlex.join(command), "log": f"logs/{name}.log",
                 "expected_exit": expected, "started_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
        state["commands"].append(entry)
        save()
        with (root / entry["log"]).open("w") as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        entry.update(exit_code=result.returncode, finished_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        save()
        require(result.returncode == expected, f"{name}: expected exit {expected}, got {result.returncode}; inspect {entry['log']}")
        if visible:
            require(visible in (root / entry["log"]).read_text(), f"{name}: rejection reason was not visible")
        if absent:
            require(not absent.exists(), f"{name}: refused output was created")
    def analysis(manifest, run, scale=False):
        return ["analyze", "--source", str(args.source), "--manifest", str(manifest), "--run-dir", str(run),
                "--quality", "high", "--min-area", "50" if scale else "200", "--max-area", "750" if scale else "3000"]
    def export(review, output):
        return ["export-review", "--run-dir", str(first), "--review", str(review), "--output", str(output)]
    try:
        wagers.verify_source(args.source)
        state["pinned_source_sha256"] = {name: wagers.sha256(Path(args.source) / name) for name in wagers.SOURCE_FILES}
        call("doctor", ["doctor", "--source", str(args.source)])
        fixture = make_tutorial(root / "fixture")
        protected = snapshot(root / "fixture")
        wagers.write_json(root / "protected-before.json", {"source": source_before, "fixture": protected})
        fields = wagers.load_manifest(fixture["manifest"])[0]
        call("manifest", ["validate-manifest", "--manifest", str(fixture["manifest"]), "--inspect-images"])
        first = root / "study-run"
        call("study", analysis(fixture["manifest"], first))
        observed = check_run(first, fields, {"quality": "high", "min_area_um2": 200, "max_area_um2": 3000})
        first_before = snapshot(first)
        call("existing-run", analysis(fixture["manifest"], first), 2, "Run directory must be new")
        verify_snapshot(first_before)
        state["scenarios"][active] = {"status": "PASS", "observed": observed, "existing_outputs_unchanged": True}
        save()

        active = SCENARIOS[1]
        reviews = fictional_review(first / "exports" / "review-template.csv")
        review = root / "fictional-review.csv"
        write_review(review, reviews)
        call("review", export(review, root / "review-export"))
        summary = check_summary(root / "review-export" / "animal-summary.csv")
        mixed = [dict(r) for r in reviews]
        next(r for r in mixed if r["field_id"] == "field-002" and r["decision"] == "accept")["threshold_rule_id"] = "FICTIONAL-RULE-B"
        mixed_path = root / "mixed-rule-review.csv"
        write_review(mixed_path, mixed)
        refused = root / "mixed-rule-output"
        call("mixed-rule", export(mixed_path, refused), 2, "Mixed dystrophin positivity rules", refused)
        state["scenarios"][active] = {"status": "PASS", "fictional_summary": summary,
                                    "mixed_rules_rejected": True, "inference_unit": "animal; muscle rows remain separate, fields/fibers are not replicates"}
        save()

        active = SCENARIOS[2]
        spreadsheet = [dict(r) for r in reviews]
        for r in spreadsheet:
            r["csa_um2"] = str(Decimal(r["csa_um2"]).normalize())
            r["cnf"] = r["cnf"] + ".00"
        excel = root / "excel-style-bom.csv"
        write_review(excel, spreadsheet, bom=True)
        call("bom-equivalent", export(excel, root / "bom-export"))
        check_summary(root / "bom-export" / "animal-summary.csv")
        require((root / "bom-export" / "animal-summary.csv").read_bytes() ==
                (root / "review-export" / "animal-summary.csv").read_bytes(), "Formatting changed summary")
        for name, column, value, message in [
            ("changed-id", "animal_id", "1", "exactly one row"),
            ("changed-csa", "csa_um2", str(Decimal(spreadsheet[0]["csa_um2"]) + Decimal("0.01")), "Original fiber columns"),
            ("changed-cnf", "cnf", str(1 - int(Decimal(spreadsheet[0]["cnf"]))), "Original fiber columns")]:
            changed = [dict(r) for r in spreadsheet]
            changed[0][column] = value
            path, refused = root / (name + ".csv"), root / (name + "-output")
            write_review(path, changed, bom=True)
            call(name, export(path, refused), 2, message, refused)
        state["scenarios"][active] = {"status": "PASS", "bom_numeric_equivalence": True,
                                    "changed_ids_csa_cnf_rejected": True, "excel_gui": "not exercised"}
        save()

        active = SCENARIOS[3]
        for name, manifest, message in [("missing-channel", fixture["missing"], "Missing channel"),
                                        ("invalid-calibration", fixture["invalid"], "finite positive")]:
            bad_run = root / (name + "-run")
            call(name, analysis(manifest, bad_run), 2, message, bad_run)
        retry = root / "corrected-retry"
        call("corrected-retry", analysis(fixture["retry"], retry, scale=True))
        retry_fields = wagers.load_manifest(fixture["retry"])[0]
        retry_observed = check_run(retry, retry_fields, {"quality": "high", "min_area_um2": 50, "max_area_um2": 750})
        old = {r["original_fiber_number"]: r for r in read_csv(first / "exports" / "fibers.csv") if r["field_id"] == "field-001"}
        new = {r["original_fiber_number"]: r for r in read_csv(retry / "exports" / "fibers.csv")}
        require(set(old) == set(new), "Scale comparison changed segmentation IDs/counts")
        for number, row in old.items():
            require(row["cnf"] == new[number]["cnf"], "Scale comparison changed CNF")
            # Fixture-specific: 1-um/pixel baseline contour CSAs are exact half-
            # integers at 0.1-um2 output precision, so only retry rounding adds
            # error (<=0.05). If both outputs were rounded, the general bound
            # for this 1/4 comparison would instead be 0.05 + 0.05/4 = 0.0625.
            require(abs(Decimal(row["csa_um2"]) / 4 - Decimal(new[number]["csa_um2"])) <= Decimal("0.05"),
                    "Half pixel size did not quarter CSA within 0.1-um2 reporting precision")
        state["scenarios"][active] = {"status": "PASS", "retry": retry_observed,
                                    "no_failed_run_created": True, "scale_csa_ratio": 0.25,
                                    "same_quality_and_pixel_area_bounds": True, "csa_reporting_tolerance_um2": 0.05}
        save()

        active = SCENARIOS[4]
        for name, target in [("original-overlap", root / "fixture" / "originals" / "unsafe"),
                             ("metadata-overlap", fixture["manifest"].parent / "unsafe")]:
            call(name, analysis(fixture["manifest"], target), 2, "overlaps protected", target)
        target = root / "fixture" / "originals" / "unsafe-review"
        call("review-overlap", export(review, target), 2, "overlaps protected", target)
        verify_snapshot(first_before)
        verify_snapshot(protected)
        verify_snapshot(source_before)
        state["scenarios"][active] = {"status": "PASS", "source_images_metadata_sentinel_unchanged": True,
                                    "unsafe_analysis_and_review_rejected": True}
    except Exception as exc:
        state["scenarios"][active] = {"status": "FAIL", "error": str(exc)}
        state["error"] = str(exc)
        (root / "logs" / "suite-error.log").write_text(traceback.format_exc())
    finally:
        state["preservation"] = {"source": wagers.unchanged(source_before), "fixture": wagers.unchanged(protected),
                                 "existing_run": wagers.unchanged(first_before)}
        state["preservation"]["source_tree_same"] = snapshot(args.source) == source_before
        state["code_identity_after"] = identity()
        state["code_unchanged"] = state["code_identity_before"] == state["code_identity_after"]
        passed = all(s["status"] == "PASS" for s in state["scenarios"].values())
        safe = all(state["preservation"][k]["all_unchanged"] for k in ("source", "fixture", "existing_run"))
        state["status"] = "PASS" if passed and safe and state["preservation"]["source_tree_same"] and state["code_unchanged"] else "FAIL"
        state["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        save()
        (root / "commands.sh").write_text("# Recorded commands; do not replay into these existing output paths.\n" +
                                         "\n".join(c["shell"] for c in state["commands"]) + "\n")
    print(json.dumps({"status": state["status"], "scope": state["scope"], "report": str(root / "report.json")}))
    return 0 if state["status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"TUTORIAL SUITE FAILED: {exc}", file=sys.stderr)
        sys.exit(2)
