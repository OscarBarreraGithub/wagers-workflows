"""Host-only tests. No mocks of CellProfiler, runtime launch or package success."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

import runner as t


class TutorialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.originals = t.generate(self.root / "originals")
        self.before = t.snapshot(self.originals)

    def tearDown(self):
        # Tests that deliberately corrupt cloned fixtures never mutate originals.
        self.assertEqual(t.snapshot(self.originals), self.before)

    def clone(self):
        import shutil
        dest = self.root / "mutant"
        shutil.copytree(self.originals, dest)
        return dest

    def test_generator_truth_pixels_and_blank(self):
        rows, truth = t.validate(self.originals)
        self.assertEqual(len(rows), 12)
        self.assertEqual(len({r["donor_id"] for r in rows}), 2)
        self.assertEqual(len({r["experiment_id"] for r in rows}), 2)
        self.assertEqual(sorted(truth.values()), [0, 1, 2, 2, 2, 2, 2, 3, 3, 3, 4, 6])
        # Independently check constructed pixel area, rather than segmenting objects.
        for row in rows:
            raw = t.validate_png(self.originals / row["image"])
            pixels = b"".join(raw[y * 97 + 1:(y + 1) * 97] for y in range(96))
            self.assertEqual(set(pixels) - {8, 230}, set())
            self.assertEqual(pixels.count(230), 81 * truth[t.key(row)])
            self.assertEqual(len(pixels), 96 * 96)
        self.assertEqual(sum(v == 0 for v in truth.values()), 1)

    def test_generator_is_deterministic_and_refuses_overwrite(self):
        other = t.generate(self.root / "same")
        self.assertEqual(t.snapshot(other), self.before)
        with self.assertRaisesRegex(t.Refusal, "already exists"):
            t.generate(self.originals)

    def test_sum_fields_to_wells_then_control_normalization(self):
        rows, truth = t.validate(self.originals)
        wells, controls = t.summarize(rows, truth)
        observed = {(w["experiment_id"], w["well_id"]): (w["well_count"], w["normalized_count"]) for w in wells}
        self.assertEqual(observed, {("E01", "A01"): (5, 1), ("E01", "A02"): (5, 1),
                                    ("E01", "B01"): (10, 2), ("E02", "A01"): (4, 1),
                                    ("E02", "A02"): (4, 1), ("E02", "B01"): (2, .5)})
        self.assertTrue(all(w["fields"] == 2 for w in wells))
        self.assertEqual([c["control_wells"] for c in controls], [2, 2])
        self.assertEqual([c["mean_control_well_count"] for c in controls], [5, 4])

    def test_mean_of_well_sums_not_mean_of_field_counts(self):
        rows, truth = t.validate(self.originals)
        rows = [r for r in rows if not (r["experiment_id"] == "E01" and r["well_id"] == "A02" and r["field_id"] == "F02")]
        counts = {t.key(r): truth[t.key(r)] for r in rows}
        wells, controls = t.summarize(rows, counts)
        self.assertEqual(controls[0]["mean_control_well_count"], 4)  # (5 + 3) / 2
        self.assertEqual(next(w for w in wells if w["experiment_id"] == "E01" and w["well_id"] == "B01")["normalized_count"], 2.5)

    def test_zero_and_missing_controls_refused(self):
        zero = t.generate(self.root / "zero", zero_controls=True)
        rows, truth = t.validate(zero)
        with self.assertRaisesRegex(t.Refusal, "zero control denominator"):
            t.summarize(rows, truth)
        rows = [r for r in rows if r["condition"] != "control"]
        with self.assertRaisesRegex(t.Refusal, "no control wells"):
            t.summarize(rows, {t.key(r): truth[t.key(r)] for r in rows})

    def test_measurement_identity_and_value_errors(self):
        rows, counts = t.validate(self.originals)
        missing = dict(counts)
        missing.pop(next(iter(missing)))
        with self.assertRaisesRegex(t.Refusal, "identities differ"):
            t.summarize(rows, missing)
        for invalid in (-1, 2.5, True):
            bad = dict(counts)
            bad[next(iter(bad))] = invalid
            with self.assertRaisesRegex(t.Refusal, "invalid measured count"):
                t.summarize(rows, bad)

    def test_metadata_failures_and_corrected_retry(self):
        fixture = self.clone()
        rows = t.read_csv(fixture / "metadata.csv", t.COLUMNS)
        cases = []
        duplicate = [dict(r) for r in rows] + [dict(rows[0])]
        cases.append((duplicate, "duplicate field identity"))
        for column, value, error in [("donor_id", "", "invalid/missing donor_id"),
                                     ("experiment_id", "has space", "invalid/missing experiment_id"),
                                     ("well_id", "A99", "invalid/missing well_id"),
                                     ("field_id", "", "invalid/missing field_id"),
                                     ("condition", "unknown", "invalid/missing condition"),
                                     ("image", "../escape.png", "invalid image path"),
                                     ("image", rows[1]["image"], "duplicate image path")]:
            mutated = [dict(r) for r in rows]
            # Duplicate image check triggers on second row, after the first image decode.
            mutated[0][column] = value
            cases.append((mutated, error))
        cases.append((rows[:-1], "metadata missing image identity"))
        for mutated, error in cases:
            with self.subTest(error=error):
                t.write_csv(fixture / "metadata.csv", t.COLUMNS, mutated)
                before = t.snapshot(fixture)
                output = self.root / "retry-output"
                with self.assertRaisesRegex(t.Refusal, error):
                    t.run(fixture, output, self.root / "absent.sif")
                self.assertFalse(output.exists())
                self.assertEqual(t.snapshot(fixture), before)
        t.write_csv(fixture / "metadata.csv", t.COLUMNS, rows)
        self.assertEqual(len(t.validate(fixture)[0]), 12)
        # Actual corrected package retry belongs to `suite`, not this local test.
        self.assertFalse((self.root / "retry-output").exists())

    def test_missing_corrupt_and_checksum_files_fail(self):
        fixture = self.clone()
        rows = t.read_csv(fixture / "metadata.csv", t.COLUMNS)
        image = fixture / rows[0]["image"]
        original = image.read_bytes()
        image.unlink()
        with self.assertRaisesRegex(t.Refusal, "missing image"):
            t.validate(fixture)
        image.write_bytes(b"broken")
        with self.assertRaisesRegex(t.Refusal, "corrupt PNG"):
            t.validate(fixture)
        corrupted = bytearray(original)
        corrupted[45] ^= 1
        image.write_bytes(corrupted)
        with self.assertRaisesRegex(t.Refusal, "checksum mismatch"):
            t.validate(fixture)
        image.write_bytes(original[:-4])
        with self.assertRaisesRegex(t.Refusal, "truncated PNG"):
            t.validate(fixture)
        image.write_bytes(original)
        t.validate(fixture)

    def test_existing_overlapping_symlink_output_refused(self):
        existing = self.root / "exists"
        existing.mkdir()
        (existing / "KEEP").write_text("unchanged")
        before = t.snapshot(existing)
        for out, error in [(existing, "already exists"), (self.originals, "overlaps"),
                           (self.originals / "out", "overlaps"), (self.root, "overlaps")]:
            with self.subTest(output=str(out)):
                with self.assertRaisesRegex(t.Refusal, error):
                    t.run(self.originals, out, self.root / "absent.sif")
        self.assertEqual(t.snapshot(existing), before)
        alias = self.root / "alias"
        alias.symlink_to(self.originals, target_is_directory=True)
        with self.assertRaisesRegex(t.Refusal, "overlaps"):
            t.safe_output(self.originals, alias / "out")
        dangling = self.root / "dangling"
        dangling.symlink_to(self.root / "missing")
        with self.assertRaisesRegex(t.Refusal, "already exists"):
            t.safe_output(self.originals, dangling)

    def test_input_symlinks_refused(self):
        fixture = self.clone()
        (fixture / "alias").symlink_to(self.originals / "metadata.csv")
        with self.assertRaisesRegex(t.Refusal, "symlinks"):
            t.validate(fixture)

    def test_container_receipt_hash_and_digest(self):
        # Plain bytes test receipt validation ONLY, never a package/runtime pass.
        sif = self.root / "receipt-test.sif"
        sif.write_bytes(b"not a runtime image")
        with self.assertRaisesRegex(t.Refusal, "receipt missing"):
            t.container_identity(sif)
        data = {"source": t.IMAGE, "digest": t.DIGEST, "platform": "linux/amd64", "sif_sha256": t.sha(sif)}
        receipt = Path(str(sif) + ".json")
        t.write_json(receipt, data)
        self.assertEqual(t.container_identity(sif), data)
        sif.write_bytes(b"changed")
        with self.assertRaisesRegex(t.Refusal, "hash mismatch"):
            t.container_identity(sif)
        data["digest"] = "wrong"
        t.write_json(receipt, data)
        with self.assertRaisesRegex(t.Refusal, "digest mismatch"):
            t.container_identity(sif)

    def test_local_missing_runtime_cannot_pass_package_gate(self):
        # This condition holds on the assigned Mac and on Linux with this nonexistent runtime.
        with self.assertRaisesRegex(t.Refusal, "not run"):
            t.suite(self.root / "never-created", self.root / "absent.sif", "no-such-runtime-cp-tutorial")
        self.assertFalse((self.root / "never-created").exists())


if __name__ == "__main__":
    unittest.main()
