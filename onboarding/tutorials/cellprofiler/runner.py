#!/usr/bin/env python3
"""Original synthetic culture-count tutorial. Host side uses Python standard library only."""
import argparse
import csv
import hashlib
import json
import platform
import re
import shutil
import struct
import subprocess
import sys
import zlib
from collections import defaultdict
from pathlib import Path

VERSION = "4.2.8"
DIGEST = "sha256:fec440caa2b44edf80f9bd440a3d8c6b214d72437332ad2586a32d79e2eae2a4"
IMAGE = "docker://cellprofiler/cellprofiler@" + DIGEST
HERE = Path(__file__).resolve().parent
COLUMNS = ["experiment_id", "donor_id", "plate_id", "well_id", "field_id", "condition", "image"]
KEY = COLUMNS[:5]
# Planned counts are independent construction truth, never derived by segmenting pixels.
PLAN = [
    ("E01", "D01", "A01", "control", (2, 3)),
    ("E01", "D01", "A02", "control", (3, 2)),
    ("E01", "D01", "B01", "treated", (4, 6)),
    ("E02", "D02", "A01", "control", (1, 3)),
    ("E02", "D02", "A02", "control", (2, 2)),
    ("E02", "D02", "B01", "treated", (0, 2)),
]


class Refusal(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise Refusal(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_csv(path, columns, rows):
    with Path(path).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def read_csv(path, columns):
    with Path(path).open(newline="") as f:
        r = csv.DictReader(f)
        require(r.fieldnames == columns, "invalid CSV header: " + str(path))
        rows = list(r)
    require(rows and all(set(row) == set(columns) and all(v is not None for v in row.values())
                         for row in rows), "empty/malformed CSV: " + str(path))
    return rows


def key(row):
    return tuple(row[k] for k in KEY)


def snapshot(root):
    root = Path(root)
    require(root.is_dir(), "originals directory missing")
    paths = sorted(root.rglob("*"))
    require(not any(p.is_symlink() for p in paths), "symlinks in originals are forbidden")
    return {str(p.relative_to(root)): sha(p) for p in paths if p.is_file()}


def overlap(a, b):
    a, b = Path(a).resolve(), Path(b).resolve()
    return a == b or a in b.parents or b in a.parents


def safe_output(originals, output):
    output = Path(output)
    require(not overlap(originals, output), "output overlaps originals")
    require(not output.exists() and not output.is_symlink(), "output already exists")
    for p in (Path(originals).resolve(), output.resolve(), HERE):
        require(not any(c in str(p) for c in ":,\n\r"), "unsafe bind path punctuation")
    return output.resolve()


def png_bytes(count):
    """96x96 grayscale; disks radius 5, grid spacing 28, no border contacts."""
    require(0 <= count <= 9, "construction count outside grid")
    pixels = bytearray([8] * (96 * 96))
    for i in range(count):
        cx, cy = 18 + 28 * (i % 3), 18 + 28 * (i // 3)
        for y in range(cy - 5, cy + 6):
            for x in range(cx - 5, cx + 6):
                if (x - cx) ** 2 + (y - cy) ** 2 <= 25:
                    pixels[y * 96 + x] = 230
    raw = b"".join(b"\0" + pixels[y * 96:(y + 1) * 96] for y in range(96))
    def chunk(name, data):
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 96, 96, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def validate_png(path):
    """Strict tutorial format check, not segmentation; checks CRCs and full decoded size."""
    b = Path(path).read_bytes()
    require(b[:8] == b"\x89PNG\r\n\x1a\n", "corrupt PNG signature")
    pos, chunks = 8, []
    while pos < len(b):
        require(pos + 12 <= len(b), "truncated PNG")
        n = struct.unpack(">I", b[pos:pos + 4])[0]
        require(n <= len(b) - pos - 12, "truncated PNG chunk")
        name, data = b[pos + 4:pos + 8], b[pos + 8:pos + 8 + n]
        require(zlib.crc32(name + data) == struct.unpack(">I", b[pos + 8 + n:pos + 12 + n])[0],
                "PNG checksum mismatch")
        chunks.append((name, data))
        pos += n + 12
    require([n for n, _ in chunks] == [b"IHDR", b"IDAT", b"IEND"], "unsupported PNG layout")
    require(chunks[0][1] == struct.pack(">IIBBBBB", 96, 96, 8, 0, 0, 0, 0) and chunks[-1][1] == b"",
            "unsupported tutorial image dimensions/format")
    try:
        decoder = zlib.decompressobj()
        raw = decoder.decompress(chunks[1][1], 9313)
        require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,
                "invalid PNG compressed stream")
    except zlib.error as e:
        raise Refusal("corrupt PNG compressed stream") from e
    require(len(raw) == 96 * 97 and all(raw[y * 97] == 0 for y in range(96)),
            "invalid PNG scanlines")
    return raw


def generate(dest, zero_controls=False):
    dest = Path(dest).resolve()
    require(not dest.exists(), "generation destination already exists")
    (dest / "images").mkdir(parents=True)
    rows, truth = [], []
    for experiment, donor, well, condition, counts in PLAN:
        for index, planned in enumerate(counts, 1):
            count = 0 if zero_controls and condition == "control" else planned
            field = "F%02d" % index
            filename = "images/%s_%s_P01_%s_%s.png" % (experiment, donor, well, field)
            row = dict(zip(COLUMNS, [experiment, donor, "P01", well, field, condition, filename]))
            rows.append(row)
            truth.append(dict(zip(KEY + ["expected_count"], list(key(row)) + [count])))
            (dest / filename).write_bytes(png_bytes(count))
    write_csv(dest / "metadata.csv", COLUMNS, rows)
    write_csv(dest / "truth.csv", KEY + ["expected_count"], truth)
    (dest / "ORIGINALS_SENTINEL.txt").write_text("Original synthetic inputs: do not overwrite.\n")
    write_json(dest / "construction.json", {
        "creator": "original tutorial generator", "shape": [96, 96], "radius_px": 5,
        "background": 8, "foreground": 230, "grid_spacing_px": 28,
        "truth_method": "declared object construction counts, no image segmentation",
        "zero_controls": zero_controls,
    })
    return dest


def validate(originals):
    root = Path(originals).resolve()
    snapshot(root)  # reject symlinks before opening any input
    require((root / "ORIGINALS_SENTINEL.txt").is_file(), "originals sentinel missing")
    rows = read_csv(root / "metadata.csv", COLUMNS)
    seen, images, wells, donors = set(), set(), {}, {}
    for r in rows:
        for col in ("experiment_id", "donor_id", "plate_id"):
            require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,31}", r[col]), "invalid/missing " + col)
        require(re.fullmatch(r"[A-H](0[1-9]|1[0-2])", r["well_id"]), "invalid/missing well_id")
        require(re.fullmatch(r"F[0-9]{2}", r["field_id"]), "invalid/missing field_id")
        require(r["condition"] in ("control", "treated"), "invalid/missing condition")
        require(key(r) not in seen, "duplicate field identity")
        seen.add(key(r))
        well = key(r)[:4]
        require(well not in wells or wells[well] == r["condition"], "inconsistent well condition")
        wells[well] = r["condition"]
        exp = r["experiment_id"]
        require(exp not in donors or donors[exp] == r["donor_id"], "experiment donor mismatch")
        donors[exp] = r["donor_id"]
        image = Path(r["image"])
        require(image.as_posix() == r["image"] and len(image.parts) == 2 and image.parts[0] == "images"
                and image.suffix == ".png" and ".." not in image.parts, "invalid image path")
        require(r["image"] not in images, "duplicate image path")
        images.add(r["image"])
        require((root / image).is_file(), "missing image: " + r["image"])
        validate_png(root / image)
    actual = {str(p.relative_to(root)) for p in (root / "images").rglob("*") if p.is_file()}
    require(actual == images, "metadata missing image identity or unlisted image")
    truth_rows = read_csv(root / "truth.csv", KEY + ["expected_count"])
    truth = {}
    for r in truth_rows:
        require(key(r) not in truth and re.fullmatch(r"[0-9]+", r["expected_count"]), "invalid truth")
        truth[key(r)] = int(r["expected_count"])
    require(set(truth) == seen, "metadata/truth field identities differ")
    return rows, truth


def summarize(rows, counts):
    require(set(counts) == {key(r) for r in rows}, "measurement field identities differ")
    totals, conditions, fields = defaultdict(int), {}, defaultdict(int)
    for r in rows:
        count = counts[key(r)]
        require(type(count) is int and count >= 0, "invalid measured count")
        well = key(r)[:4]
        totals[well] += count
        fields[well] += 1
        conditions[well] = r["condition"]
    controls = defaultdict(list)
    for well, total in totals.items():
        if conditions[well] == "control":
            controls[well[:3]].append(total)
    summaries, control_rows = [], []
    for group in sorted({w[:3] for w in totals}):
        values = controls[group]
        require(values, "no control wells in experiment/donor/plate group")
        mean = sum(values) / len(values)
        require(mean > 0, "zero control denominator: " + repr(group))
        control_rows.append(dict(zip(KEY[:3] + ["control_wells", "mean_control_well_count"],
                                     list(group) + [len(values), mean])))
        for well in sorted(w for w in totals if w[:3] == group):
            summaries.append(dict(zip(KEY[:4] + ["condition", "fields", "well_count",
                                                  "mean_control_well_count", "normalized_count"],
                                      list(well) + [conditions[well], fields[well], totals[well], mean,
                                                    totals[well] / mean])))
    return summaries, control_rows


def linux_runtime(requested=None):
    require(platform.system() == "Linux" and platform.machine() in ("x86_64", "amd64"),
            "actual package execution requires Linux amd64; not run")
    runtime = shutil.which(requested) if requested else (shutil.which("apptainer") or shutil.which("singularity"))
    require(runtime is not None, "installed Apptainer/Singularity required; not run")
    return runtime


def runtime_run(command, log):
    with Path(log).open("w") as f:
        f.write("argv=" + json.dumps([str(x) for x in command]) + "\n")
        f.flush()
        result = subprocess.run([str(x) for x in command], stdout=f, stderr=subprocess.STDOUT)
    require(result.returncode == 0, "command failed (exit %s); see %s" % (result.returncode, log))


def install(sif, runtime=None):
    runtime = linux_runtime(runtime)
    sif = Path(sif).resolve()
    receipt = Path(str(sif) + ".json")
    require(not sif.exists() and not receipt.exists(), "SIF or receipt already exists; refusing overwrite")
    require(not overlap(HERE, sif) or HERE / ".runtime" in sif.parents,
            "install only to private external storage or ignored .runtime")
    sif.parent.mkdir(parents=True, exist_ok=True)
    # No source/binary downloaded to Git. Pull is explicit, only at install time.
    log = Path(str(sif) + ".pull.log")
    require(not log.exists(), "pull log already exists")
    runtime_run([runtime, "pull", sif, IMAGE], log)
    write_json(receipt, {"source": IMAGE, "digest": DIGEST, "sif_sha256": sha(sif),
                         "platform": "linux/amd64", "runtime": runtime,
                         "runtime_version": subprocess.check_output([runtime, "--version"], text=True).strip()})
    return receipt


def container_identity(sif):
    sif = Path(sif).resolve()
    require(sif.is_file(), "explicit existing SIF missing; run install on compute first")
    receipt = Path(str(sif) + ".json")
    require(receipt.is_file(), "SIF receipt missing; use runner install and retain SIF.json")
    data = json.loads(receipt.read_text())
    require(data.get("source") == IMAGE and data.get("digest") == DIGEST
            and data.get("platform") == "linux/amd64", "SIF receipt source/digest mismatch")
    require(data.get("sif_sha256") == sha(sif), "SIF hash mismatch")
    return data


def run(originals, output, sif, runtime=None):
    originals = Path(originals).resolve()
    output = safe_output(originals, output)
    before = snapshot(originals)
    rows, truth = validate(originals)
    runtime = linux_runtime(runtime)
    identity = container_identity(sif)
    output.mkdir(parents=True, exist_ok=False)
    report = {"status": "failed", "package_check": "not_run", "cellprofiler_expected": VERSION,
              "container": identity, "originals_before": before, "host_python": sys.version,
              "host_platform": platform.platform(), "source_sha256": {
                  p.name: sha(p) for p in HERE.iterdir() if p.is_file() and p.name != "VALIDATION.md"},
              "normalization": "well sum / arithmetic mean of control well sums within experiment/donor/plate",
              "replication": "fields and objects are subsamples, not biological replicates"}
    error = None
    try:
        runtime_run([runtime, "--version"], output / "runtime-version.log")
        (output / "runtime").mkdir()
        command = [runtime, "exec", "--cleanenv", "--containall", "--no-home", "--pwd", "/output",
                   "--bind", str(originals) + ":/input:ro", "--bind", str(output) + ":/output:rw",
                   "--bind", str(HERE) + ":/tutorial:ro", "--env",
                   "HOME=/output/runtime,MPLCONFIGDIR=/output/runtime,OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1",
                   str(Path(sif).resolve()), "/opt/venv/bin/python", "/tutorial/cp_measure.py"]
        report["command"] = command
        report["package_check"] = "failed"
        runtime_run(command, output / "cellprofiler.log")
        package = json.loads((output / "package.json").read_text())
        require(package["cellprofiler"] == VERSION and package["cellprofiler_core"] == VERSION,
                "exact package version mismatch")
        require(package["module"] == "IdentifyPrimaryObjects", "unexpected segmentation module")
        report["tool_versions"] = package
        measured = read_csv(output / "measured-fields.csv", COLUMNS + ["count"])
        counts = {}
        metadata = {key(r): r for r in rows}
        for r in measured:
            k = key(r)
            require(k in metadata and k not in counts, "duplicate/unknown measured field")
            require(all(r[c] == metadata[k][c] for c in COLUMNS), "measurement metadata changed")
            require(re.fullmatch(r"[0-9]+", r["count"]), "invalid package count")
            counts[k] = int(r["count"])
        require(counts == truth, "actual CellProfiler counts differ from construction truth")
        report["truth_match"] = True
        report["blank_valid_fields"] = sum(value == 0 for value in truth.values())
        require(report["blank_valid_fields"] > 0, "blank valid field test missing")
        report["package_check"] = "passed"
        wells, controls = summarize(rows, counts)
        write_csv(output / "measured-wells.csv", KEY[:4] + ["condition", "fields", "well_count",
                                                          "mean_control_well_count", "normalized_count"], wells)
        write_csv(output / "control-summary.csv", KEY[:3] + ["control_wells", "mean_control_well_count"], controls)
        report["status"] = "passed"
    except Exception as e:
        error = e
        report["error"] = str(e)
    finally:
        after = snapshot(originals)
        report["originals_after"] = after
        report["originals_unchanged"] = before == after
        if before != after:
            report["status"] = "failed"
            error = Refusal("originals or sentinel changed")
            report["error"] = str(error)
        write_json(output / "case-report.json", report)
    if error:
        raise error
    return report


def suite(dest, sif, runtime=None):
    """Real Linux integration gate: no mocks, no skip-to-pass behavior."""
    dest = Path(dest).resolve()
    require(not dest.exists(), "suite destination already exists")
    linux_runtime(runtime)  # Mac cannot produce a passing/not-run suite report.
    container_identity(sif)
    dest.mkdir(parents=True)
    (dest / "SUITE_SENTINEL.txt").write_text("Keep suite sentinel unchanged.\n")
    sentinel_before = sha(dest / "SUITE_SENTINEL.txt")
    cases = []
    report = {"status": "failed", "package_gate": "not_run", "container_digest": DIGEST, "cases": cases}
    def check(name, function, expected_error=None, originals=None):
        before = snapshot(originals) if originals else None
        case = {"name": name, "status": "failed"}
        try:
            function()
            require(expected_error is None, "expected refusal was not raised")
            case["status"] = "passed"
        except Exception as e:
            case["error"] = str(e)
            if expected_error is not None and isinstance(e, Refusal) and expected_error in str(e):
                case["status"] = "passed"
        if originals:
            after = snapshot(originals)
            case.update(originals_before=before, originals_after=after, originals_unchanged=before == after)
            if before != after:
                case["status"] = "failed"
        cases.append(case)
        write_json(dest / "suite-report.json", report)
        return case["status"] == "passed"
    originals = generate(dest / "originals")
    def baseline():
        run(originals, dest / "baseline", sif, runtime)
        # Independent declared arithmetic targets, read from the actual exported CSVs.
        fields = read_csv(dest / "baseline" / "measured-fields.csv", COLUMNS + ["count"])
        require(len(fields) == 12 and sum(r["count"] == "0" for r in fields) == 1,
                "actual baseline field/blank check failed")
        wells = read_csv(dest / "baseline" / "measured-wells.csv", KEY[:4] + [
            "condition", "fields", "well_count", "mean_control_well_count", "normalized_count"])
        observed = {(r["experiment_id"], r["donor_id"], r["well_id"]):
                    (int(r["well_count"]), float(r["normalized_count"])) for r in wells}
        expected = {("E01", "D01", "A01"): (5, 1), ("E01", "D01", "A02"): (5, 1),
                    ("E01", "D01", "B01"): (10, 2), ("E02", "D02", "A01"): (4, 1),
                    ("E02", "D02", "A02"): (4, 1), ("E02", "D02", "B01"): (2, .5)}
        require(len(wells) == 6 and observed == expected and all(r["fields"] == "2" for r in wells),
                "actual well/control arithmetic targets failed")
        controls = read_csv(dest / "baseline" / "control-summary.csv", KEY[:3] + [
            "control_wells", "mean_control_well_count"])
        require(len(controls) == 2 and
                [(r["experiment_id"], int(r["control_wells"]), float(r["mean_control_well_count"]))
                 for r in controls] == [("E01", 2, 5), ("E02", 2, 4)],
                "actual control summary targets failed")
    try:
        check("real_package_counts_blank_and_well_controls", baseline, originals=originals)
        for name, expected in [("duplicate_identity", "duplicate field identity"),
                               ("missing_identity", "invalid/missing donor_id"),
                               ("invalid_identity", "invalid/missing well_id"),
                               ("missing_metadata_row", "metadata missing image identity"),
                               ("missing_file", "missing image"), ("corrupt_file", "corrupt PNG")]:
            fixture = dest / name
            shutil.copytree(originals, fixture)
            rows = read_csv(fixture / "metadata.csv", COLUMNS)
            if name == "duplicate_identity":
                rows.append(rows[0].copy())
            elif name == "missing_identity":
                rows[0]["donor_id"] = ""
            elif name == "invalid_identity":
                rows[0]["well_id"] = "A99"
            elif name == "missing_metadata_row":
                rows.pop()
            elif name == "missing_file":
                (fixture / rows[0]["image"]).unlink()
            elif name == "corrupt_file":
                (fixture / rows[0]["image"]).write_bytes(b"broken")
            write_csv(fixture / "metadata.csv", COLUMNS, rows)
            check(name, lambda f=fixture: run(f, dest / (name + "-out"), sif, runtime), expected, fixture)
        existing = dest / "already-exists"
        existing.mkdir()
        (existing / "KEEP.txt").write_text("do not touch\n")
        existing_before = snapshot(existing)
        report["existing_output_before"] = existing_before
        check("existing_output", lambda: run(originals, existing, sif, runtime),
              "output already exists", originals)
        report["existing_output_after"] = snapshot(existing)
        require(report["existing_output_after"] == existing_before, "existing output sentinel changed")
        check("overlapping_child", lambda: run(originals, originals / "results", sif, runtime),
              "output overlaps originals", originals)
        check("overlapping_parent", lambda: run(originals, dest, sif, runtime),
              "output overlaps originals", originals)
        # Correct the failed duplicate metadata fixture and retry the SAME previously rejected output.
        fixture = dest / "duplicate_identity"
        shutil.copyfile(originals / "metadata.csv", fixture / "metadata.csv")
        check("corrected_retry_real_package", lambda: run(fixture, dest / "duplicate_identity-out", sif, runtime),
              originals=fixture)
        zeros = generate(dest / "zero-controls", zero_controls=True)
        check("zero_control_denominator", lambda: run(zeros, dest / "zero-controls-out", sif, runtime),
              "zero control denominator", zeros)
        zero_report_path = dest / "zero-controls-out" / "case-report.json"
        require(zero_report_path.is_file() and json.loads(zero_report_path.read_text())["package_check"] == "passed",
                "zero denominator check did not execute the real package")
        report["package_gate"] = "passed" if all(c["status"] == "passed" for c in cases) else "failed"
        report["status"] = report["package_gate"]
    except Exception as e:
        report["error"] = str(e)
    finally:
        report["suite_sentinel_before"] = sentinel_before
        report["suite_sentinel_after"] = sha(dest / "SUITE_SENTINEL.txt")
        if report["suite_sentinel_after"] != sentinel_before:
            report["status"] = "failed"
        report["source_sha256"] = {p.name: sha(p) for p in HERE.iterdir() if p.is_file()}
        write_json(dest / "suite-report.json", report)
    require(report["status"] == "passed", "real CellProfiler tutorial suite failed; see suite-report.json")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("generate")
    p.add_argument("--dest", type=Path, required=True)
    p = sub.add_parser("install")
    p.add_argument("--sif", type=Path, required=True)
    p.add_argument("--runtime", help="installed singularity/apptainer executable")
    for cmd in ("run", "suite"):
        p = sub.add_parser(cmd)
        p.add_argument("--sif", type=Path, required=True, help="existing pinned SIF with adjacent .json receipt")
        p.add_argument("--runtime")
        if cmd == "run":
            p.add_argument("--originals", type=Path, required=True)
            p.add_argument("--output", type=Path, required=True)
        else:
            p.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "generate":
            print(generate(args.dest))
        elif args.command == "install":
            print(install(args.sif, args.runtime))
        elif args.command == "run":
            run(args.originals, args.output, args.sif, args.runtime)
            print(args.output / "case-report.json")
        else:
            suite(args.dest, args.sif, args.runtime)
            print(args.dest / "suite-report.json")
    except (Refusal, OSError, ValueError, KeyError) as e:
        print("REFUSED/FAILED: " + str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
