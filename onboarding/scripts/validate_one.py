#!/usr/bin/env python3
"""One real pinned-tool run, visible missing-channel failure, retry, originals check."""
import sys

# Shared software must stay byte-for-byte unchanged, including import caches.
sys.dont_write_bytecode = True

import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import traceback
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import wagers
from make_control import make_control


def code_identity():
    root = Path(wagers.__file__).resolve().parent
    names = ["wagers.py", "environment.yml", "scripts/bootstrap.py", "scripts/bootstrap.sh",
             "scripts/make_control.py", "scripts/validate_one.py", "tests/test_safety.py"]
    identity = {"wrapper_version": wagers.VERSION,
                "sha256": {name: wagers.sha256(root / name) for name in names if (root / name).is_file()},
                "git_revision": None, "git_code_dirty": None}
    try:
        # Installed releases need not contain Git metadata; their file hashes
        # remain authoritative. Never attach an unrelated enclosing Git repo.
        subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", "--", "wagers.py"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        identity["git_revision"] = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
        identity["git_code_dirty"] = bool(subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain", "--", *names], text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        pass
    return identity


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evidence-dir", required=True, type=Path)
    p.add_argument("--manifest", type=Path)
    p.add_argument("--min-area", type=float, default=200)
    p.add_argument("--max-area", type=float, default=3000)
    p.add_argument("--quality", choices=("high", "low"), default="high")
    args = p.parse_args()
    root = args.evidence_dir.absolute().resolve()
    if root.exists():
        raise ValueError("Validation evidence directory must be new")
    # Validate caller manifest before creating any outputs near protected data.
    if args.manifest:
        rows, _ = wagers.load_manifest(args.manifest)
        if len(rows) != 1:
            raise ValueError("This bounded validation accepts exactly one field")
        wagers.check_run_location(root, rows, args.manifest)
    root.mkdir(parents=True)
    state = {"status": "running", "synthetic": args.manifest is None,
             "biological_validation": "pending", "commands": [], "code_identity": code_identity()}
    try:
        manifest = args.manifest.resolve() if args.manifest else make_control(root / "fixture")
        rows, originals = wagers.load_manifest(manifest)
        # Include every file in the control's originals directory, including the
        # nonchannel sentinel, to prove it never entered upstream cleanup.
        if args.manifest is None:
            originals.update({str(p): wagers.sha256(p) for p in (root / "fixture" / "originals").iterdir()})
        cli = [sys.executable, "-B", "-I", str(Path(wagers.__file__).resolve())]
        base = ["--quality", args.quality, "--min-area", str(args.min_area), "--max-area", str(args.max_area)]

        def call(arguments, log_name, expected=0):
            command = cli + arguments
            state["commands"].append(command)
            with (root / log_name).open("w") as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
            if (result.returncode == 0) != (expected == 0):
                raise ValueError(f"Unexpected exit {result.returncode}; inspect {root / log_name}")
            return result

        call(["doctor"], "doctor.log")
        call(["analyze", "--manifest", str(manifest), "--run-dir", str(root / "first-run")] + base, "first-run.log")
        row = {**rows[0], "laminin_path": str(root / "deliberately-absent-Laminin.tif")}
        bad_manifest = root / "bad-metadata" / "image-manifest.csv"
        bad_manifest.parent.mkdir()
        wagers.write_csv(bad_manifest, wagers.MANIFEST_COLUMNS, [row])
        call(["analyze", "--manifest", str(bad_manifest), "--run-dir", str(root / "bad-run")] + base,
             "missing-channel.log", expected=2)
        if (root / "bad-run").exists() or "Missing channel" not in (root / "missing-channel.log").read_text():
            raise ValueError("Missing-channel path was not rejected visibly before creating a run")
        call(["analyze", "--manifest", str(manifest), "--run-dir", str(root / "retry-run")] + base, "retry-run.log")
        checks = wagers.unchanged(originals)
        wagers.write_json(root / "original-files-check.json", checks)
        if not checks["all_unchanged"]:
            raise ValueError("Originals changed during validation")
        for name in ("first-run", "retry-run"):
            provenance = json.loads((root / name / "provenance.json").read_text())
            if provenance["status"] != "succeeded-review-pending" or provenance["processed_fields"] != 1:
                raise ValueError("Real upstream run did not produce one accepted field export")
        # A synthetic review exercises CSV/aggregation mechanics only. Never
        # silently approve real user images or fill their positivity scores.
        if args.manifest is None:
            template = root / "retry-run" / "exports" / "review-template.csv"
            with template.open(newline="") as f:
                reviews = list(csv.DictReader(f))
            for r in reviews:
                r.update(decision="accept", reviewer_id="SYNTHETIC-EXPORT-CONTROL",
                         review_date="2026-10-19", reason="Mechanical export check, not biological review")
            completed = root / "synthetic-review.csv"
            wagers.write_csv(completed, wagers.REVIEW_COLUMNS, reviews)
            call(["export-review", "--run-dir", str(root / "retry-run"), "--review", str(completed),
                  "--output", str(root / "synthetic-review-export")], "review-export.log")
        state.update(status="passed-runtime-control-only" if args.manifest is None else "passed-runtime-review-pending",
                     original_files_unchanged=True, missing_channel_rejected=True,
                     review_export="synthetic mechanics only" if args.manifest is None else "human review pending")
    except Exception as exc:
        state.update(status="failed", error=str(exc))
        raise
    finally:
        wagers.write_json(root / "validation.json", state)
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(2)
