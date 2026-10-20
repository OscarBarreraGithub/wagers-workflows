"""Focused failure/safety checks; no mock segmentation or accuracy assertions."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import wagers
from make_control import make_control
from bootstrap import absolute


class SafetyChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = make_control(self.root / "fixture")
        self.rows, self.hashes = wagers.load_manifest(self.manifest, inspect_images=True)

    def test_originals_are_never_a_run_directory(self):
        original_dir = Path(self.rows[0]["laminin_path"]).parent
        for path in [original_dir, original_dir / "run", original_dir.parent,
                     self.manifest.parent / "run"]:
            with self.assertRaises(ValueError):
                wagers.check_run_location(path, self.rows, self.manifest)
        self.assertTrue(wagers.unchanged(self.hashes)["all_unchanged"])
        self.assertTrue((original_dir / "must-survive.txt").is_file())

    def test_missing_channel_is_visible_and_writes_no_run(self):
        self.rows[0]["laminin_path"] = str(self.root / "missing.tif")
        bad = self.manifest.parent / "bad.csv"
        wagers.write_csv(bad, wagers.MANIFEST_COLUMNS, self.rows)
        result = subprocess.run([sys.executable, str(Path(wagers.__file__)), "validate-manifest",
                                 "--manifest", str(bad), "--inspect-images"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing channel", result.stderr)
        # Restore input and validate the same contract successfully.
        good = subprocess.run([sys.executable, str(Path(wagers.__file__)), "validate-manifest",
                               "--manifest", str(self.manifest), "--inspect-images"], capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stderr)

    def test_invalid_calibration_and_duplicate_fields(self):
        for value in ("0", "nan", "inf", "not-a-number"):
            row = {**self.rows[0], "pixel_size_x_um": value}
            bad = self.manifest.parent / "bad.csv"
            wagers.write_csv(bad, wagers.MANIFEST_COLUMNS, [row])
            with self.assertRaises(ValueError):
                wagers.load_manifest(bad)
        wagers.write_csv(bad, wagers.MANIFEST_COLUMNS, self.rows * 2)
        with self.assertRaisesRegex(ValueError, "unique"):
            wagers.load_manifest(bad)

    def test_reserved_field_names_and_deployment_path_text(self):
        bad = self.manifest.parent / "reserved.csv"
        for field in ("all", "all_results", "all_results-copy", "ALL_RESULTS_01"):
            wagers.write_csv(bad, wagers.MANIFEST_COLUMNS, [{**self.rows[0], "field_id": field}])
            with self.assertRaisesRegex(ValueError, "Reserved field_id"):
                wagers.load_manifest(bad)
        self.assertEqual(absolute(str(self.root / "space allowed")), (self.root / "space allowed").resolve())
        for name in ("unicodé", "line\nbreak", "tab\tpath", "delete\x7f"):
            with self.assertRaisesRegex(ValueError, "printable ASCII"):
                absolute(str(self.root / name))

    def test_same_file_or_stack_channels_are_rejected(self):
        row = {**self.rows[0], "dapi_path": self.rows[0]["laminin_path"]}
        bad = self.manifest.parent / "bad.csv"
        wagers.write_csv(bad, wagers.MANIFEST_COLUMNS, [row])
        with self.assertRaisesRegex(ValueError, "distinct"):
            wagers.load_manifest(bad)
        from PIL import Image
        stack = self.root / "stack.tif"
        Image.new("L", (512, 512), 10).save(stack, save_all=True, append_images=[Image.new("L", (512, 512), 20)])
        row["dapi_path"] = str(stack)
        wagers.write_csv(bad, wagers.MANIFEST_COLUMNS, [row])
        with self.assertRaisesRegex(ValueError, "stacks"):
            wagers.load_manifest(bad, inspect_images=True)

    def test_finished_without_real_outputs_is_a_failure(self):
        empty = self.root / "empty-results"
        (empty / "Results").mkdir(parents=True)
        (empty / "Results" / "all_results_time.txt").write_text("Image\tNumber of Fibers\n")
        with self.assertRaisesRegex(ValueError, "zero processed"):
            wagers.parse_outputs(empty, "field-001")

    def test_review_cannot_invent_positivity_or_change_identity(self):
        run = self.root / "run"
        (run / "exports").mkdir(parents=True)
        wagers.write_json(run / "provenance.json", {"status": "succeeded-review-pending",
            "fields": self.rows, "manifest": str(self.manifest)})
        fiber = dict(zip(wagers.FIBER_COLUMNS, ["run", "study", "animal", "muscle", "section", "field", "0", "500.0", "1"]))
        wagers.write_csv(run / "exports" / "fibers.csv", wagers.FIBER_COLUMNS, [fiber])
        review = {**{k: "" for k in wagers.REVIEW_COLUMNS}, **fiber,
                  "decision": "accept", "reviewer_id": "human", "review_date": "2026-10-19"}
        path = self.root / "review.csv"
        wagers.write_csv(path, wagers.REVIEW_COLUMNS, [review])
        args = argparse.Namespace(run_dir=run, review=path, output=self.root / "review-output")
        wagers.export_review(args)
        with (args.output / "animal-summary.csv").open() as f:
            row = next(csv.DictReader(f))
        self.assertEqual(row["dystrophin_fraction"], "")
        self.assertEqual(row["dystrophin_scoring_complete"], "false")
        review["dystrophin_positive"] = "1"
        wagers.write_csv(path, wagers.REVIEW_COLUMNS, [review])
        args.output = self.root / "invalid-output"
        with self.assertRaisesRegex(ValueError, "threshold"):
            wagers.export_review(args)
        self.assertFalse(args.output.exists())
        review["threshold_rule_id"] = "approved-manual-rule"
        review["animal_id"] = "changed"
        wagers.write_csv(path, wagers.REVIEW_COLUMNS, [review])
        with self.assertRaisesRegex(ValueError, "exactly one row"):
            wagers.export_review(args)

    def prepare_review(self, fibers):
        run = self.root / "run"
        (run / "exports").mkdir(parents=True)
        wagers.write_json(run / "provenance.json", {"status": "succeeded-review-pending",
            "fields": self.rows, "manifest": str(self.manifest)})
        wagers.write_csv(run / "exports" / "fibers.csv", wagers.FIBER_COLUMNS, fibers)
        reviews = [{**{k: "" for k in wagers.REVIEW_COLUMNS}, **fiber, "decision": "accept",
                    "reviewer_id": "human", "review_date": "2026-10-19"} for fiber in fibers]
        path = self.root / "review.csv"
        wagers.write_csv(path, wagers.REVIEW_COLUMNS, reviews)
        return argparse.Namespace(run_dir=run, review=path, output=self.root / "review-output"), reviews

    def test_two_muscles_remain_distinct_for_one_animal(self):
        first = dict(zip(wagers.FIBER_COLUMNS, ["run", "study", "animal", "TA-left", "section", "field-1", "0", "500.0", "1"]))
        second = {**first, "muscle_id": "DIA", "field_id": "field-2", "csa_um2": "1500.0", "cnf": "0"}
        args, reviews = self.prepare_review([first, second])
        for i, review in enumerate(reviews):
            review.update(dystrophin_positive=str(i), threshold_rule_id="approved-rule")
        wagers.write_csv(args.review, wagers.REVIEW_COLUMNS, reviews)
        wagers.export_review(args)
        with (args.output / "animal-summary.csv").open() as f:
            summary = {r["muscle_id"]: r for r in csv.DictReader(f)}
        self.assertEqual(set(summary), {"TA-left", "DIA"})
        self.assertEqual(float(summary["TA-left"]["mean_csa_um2"]), 500)
        self.assertEqual(float(summary["DIA"]["mean_csa_um2"]), 1500)
        self.assertEqual(float(summary["TA-left"]["dystrophin_fraction"]), 0)
        self.assertEqual(float(summary["DIA"]["dystrophin_fraction"]), 1)

    def test_bom_numeric_equivalence_keeps_exact_identity_and_values(self):
        fiber = dict(zip(wagers.FIBER_COLUMNS, ["run", "study", "animal", "muscle", "section", "field", "0", "2460.0", "1"]))
        args, reviews = self.prepare_review([fiber])
        original_review = reviews[0].copy()
        for i, (area, cnf) in enumerate((("2460", "1.0"), ("2.460e3", "1E+0"))):
            review = {**original_review, "csa_um2": area, "cnf": cnf, "animal_id": " animal "}
            with args.review.open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=wagers.REVIEW_COLUMNS)
                writer.writeheader()
                writer.writerow(review)
            args.output = self.root / f"equivalent-{i}"
            wagers.export_review(args)
            with (args.output / "animal-summary.csv").open() as f:
                self.assertEqual(next(csv.DictReader(f))["animal_id"], "animal")
        args.output = self.root / "rejected"
        for column, value in (("csa_um2", "2460.0001"), ("cnf", "0"),
                              ("csa_um2", "NaN"), ("csa_um2", "Infinity"),
                              ("cnf", "NaN"), ("cnf", "-Infinity"),
                              ("animal_id", "other-animal"), ("muscle_id", "other-muscle"),
                              ("section_id", "other-section"), ("original_fiber_number", "0.0")):
            review = {**original_review, column: value}
            with args.review.open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=wagers.REVIEW_COLUMNS)
                writer.writeheader()
                writer.writerow(review)
            with self.assertRaises(ValueError):
                wagers.export_review(args)
            self.assertFalse(args.output.exists())


if __name__ == "__main__":
    unittest.main()
