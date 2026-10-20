"""Focused new-runner checks. Real CLI execution belongs to tutorial-suite."""
import csv
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import tutorial_suite as suite
from make_tutorial import make_tutorial


class TutorialContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_evidence_path_refuses_existing_relative_and_symlink_aliases(self):
        source = self.root / "source"
        source.mkdir()
        for path in [self.root, Path("relative"), source / "new", source.parent]:
            with self.assertRaises(ValueError):
                suite.evidence_location(path, source)
        alias = self.root / "alias"
        alias.symlink_to(source, target_is_directory=True)
        with self.assertRaises(ValueError):
            suite.evidence_location(alias / "new", source)
        with self.assertRaises(ValueError):
            suite.evidence_location(suite.PACKAGE / "new", source)
        self.assertEqual(suite.evidence_location(self.root / "new", source), (self.root / "new").resolve())
        self.assertFalse((self.root / "new").exists())

    def test_installed_release_protects_writable_sibling_but_not_outside(self):
        prefix = (self.root / "release").resolve()
        app, env = prefix / "app", prefix / "env"
        source = prefix / "upstream" / "source"
        for directory in (app, env, source):
            directory.mkdir(parents=True)
        # Only the filesystem layout/interpreter location is varied; this does
        # not substitute a CLI, an installed runtime or segmentation results.
        with patch.object(suite, "PACKAGE", app), patch.object(suite.sys, "prefix", str(env)):
            with self.assertRaisesRegex(ValueError, "installed release prefix"):
                suite.evidence_location(prefix / "writable-sibling-evidence", source)
            self.assertEqual(suite.evidence_location(self.root / "outside", source), (self.root / "outside").resolve())
        self.assertFalse((prefix / "writable-sibling-evidence").exists())
        # An ordinary standalone source folder is not an installed app/. Keep
        # the pre-existing permission for siblings outside the source/env dirs.
        checkout = prefix / "onboarding"
        checkout.mkdir()
        with patch.object(suite, "PACKAGE", checkout), patch.object(suite.sys, "prefix", str(env)):
            self.assertEqual(suite.evidence_location(prefix / "source-sibling-evidence", source),
                             prefix / "source-sibling-evidence")

    def test_real_cli_invalid_source_reports_failure_without_upstream(self):
        # Optional external retention is for the task's private execution record;
        # ordinary test runs clean up with setUp's TemporaryDirectory.
        retained = os.environ.get("WAGERS_TUTORIAL_FAILURE_EVIDENCE")
        case = suite.evidence_location(Path(retained), self.root / "unused-source") if retained else self.root
        if retained:
            case.mkdir(parents=True)
        source = case / "invalid-source"
        source.mkdir()
        sentinel = source / "not-upstream.txt"
        sentinel.write_text("Deliberately invalid source; no algorithm may run.\n")
        before = suite.snapshot(source)
        evidence = case / "failed-suite"
        command = [sys.executable, "-B", "-I", str(suite.PACKAGE / "wagers.py"),
                   "tutorial-suite", "--source", str(source), "--evidence-dir", str(evidence)]
        result = subprocess.run(command, capture_output=True, text=True)
        (case / "failure-subprocess.json").write_text(json.dumps({
            "argv": command, "exit_code": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}, indent=2) + "\n")
        self.assertEqual(result.returncode, 2, result.stderr)
        report = json.loads((evidence / "report.json").read_text())
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["scenarios"][suite.SCENARIOS[0]]["status"], "FAIL")
        self.assertIn("exactly the eight pinned Python files", report["scenarios"][suite.SCENARIOS[0]]["error"])
        self.assertTrue(all(report["scenarios"][name]["status"] == "NOT_RUN" for name in suite.SCENARIOS[1:]))
        self.assertEqual(report["commands"], [])  # Refusal before doctor or analysis.
        self.assertTrue(report["code_unchanged"])
        self.assertTrue(report["preservation"]["source_tree_same"])
        self.assertEqual(suite.snapshot(source), before)
        self.assertFalse((evidence / "fixture").exists())
        self.assertFalse((evidence / "study-run").exists())
        self.assertIn("eight pinned", (evidence / "logs" / "suite-error.log").read_text())

    def test_fixture_is_deterministic_and_keeps_leading_zero_ids(self):
        first = make_tutorial(self.root / "a")
        second = make_tutorial(self.root / "b")
        self.assertEqual(first["manifest"].read_bytes(), second["manifest"].read_bytes())
        for name in ("Laminin.tif", "DAPI.tif", "must-survive.txt"):
            self.assertEqual((self.root / "a" / "originals" / name).read_bytes(),
                             (self.root / "b" / "originals" / name).read_bytes())
        rows = suite.read_csv(first["manifest"])
        self.assertEqual(len(rows), 4)
        self.assertEqual({r["animal_id"] for r in rows}, {"001", "002"})
        self.assertEqual(len({(r["animal_id"], r["muscle_id"]) for r in rows}), 3)
        with self.assertRaises(ValueError):
            make_tutorial(self.root / "a")

    def test_preservation_detects_missing_and_changed_protected_files(self):
        path = self.root / "sentinel"
        path.write_text("before")
        hashes = suite.snapshot(self.root)
        suite.verify_snapshot(hashes)
        path.write_text("changed")
        with self.assertRaisesRegex(ValueError, "changed/missing"):
            suite.verify_snapshot(hashes)
        path.unlink()
        with self.assertRaises(ValueError):
            suite.verify_snapshot(hashes)

    def test_summary_oracle_rejects_pooling_and_unscored_zero(self):
        # Hand-authored expected records test the acceptance oracle, not a fake
        # analysis run. No fabricated provenance or CLI is used.
        columns = ["study_id", "animal_id", "muscle_id", "sampled_fields", "accepted_fibers",
                   "mean_csa_um2", "cnf_count", "dystrophin_scoring_complete",
                   "dystrophin_positive_count", "dystrophin_fraction", "threshold_rule_id", "biological_validation"]
        rows = [dict(zip(columns, values)) for values in [
            ["FICTIONAL-SOFTWARE-CONTRACT", "001", "TA-left", 2, 5, 480, 2, "true", 3, .6, "FICTIONAL-RULE-A", "pending"],
            ["FICTIONAL-SOFTWARE-CONTRACT", "001", "DIA", 1, 4, 550, 2, "true", 2, .5, "FICTIONAL-RULE-A", "pending"],
            ["FICTIONAL-SOFTWARE-CONTRACT", "002", "TA-left", 1, 3, 500, 1, "false", "", "", "FICTIONAL-RULE-A", "pending"]]]
        path = self.root / "summary.csv"
        def write():
            with path.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)
        write()
        suite.check_summary(path)
        rows[-1]["dystrophin_fraction"] = "0"
        write()
        with self.assertRaisesRegex(ValueError, "Fraction"):
            suite.check_summary(path)
        rows[-1]["dystrophin_fraction"] = ""
        rows[1]["muscle_id"] = "TA-left"
        write()
        with self.assertRaisesRegex(ValueError, "separate"):
            suite.check_summary(path)


if __name__ == "__main__":
    unittest.main()
