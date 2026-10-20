#!/usr/bin/env python3
"""Safe file/metadata adapter around pinned, unmodified upstream Myotally.

No segmentation is implemented here. Upstream runs only on private copies in a
fresh run directory. Optional positivity remains a human review responsibility.
"""
import sys

# Shared software must stay byte-for-byte unchanged, including import caches.
sys.dont_write_bytecode = True

import argparse
import csv
import datetime as dt
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import traceback
import urllib.request
import zipfile

VERSION = "0.2.1-env001"
SOURCE_URL = "https://github.com/pieterboth/Myotally/releases/download/Myotally_V1.0.2/Myotally.V1.0.2.Source.Code.zip"
SOURCE_SHA256 = "5ce9156babd235994e1769c82f40542e2cd4eaeac256ae31373ce02c26a8ab6d"
SOURCE_FILES = {
    "Myotally_V1.py": "115eb7d38edd68735c45808d5273b2df260c261fc164fd9d55a9db70bd736b5a",
    "call_Myotally.py": "3de88960ab1f00e46dcf07eea80cae5919d924f485c9f8966ffd9f3f3a498773",
    "cvt_to.py": "24662d5d23aa4a0e819968aa0fe3abf920ab0ad9ad8be9a0ee687b31d6ce6c51",
    "draw_contour_outlines.py": "674cb77f25e0f0bceb784e2513f924b66a5d3dd2aa3526ed050568168ca2f5b2",
    "fill_contours.py": "c152c5e765ad0b57759e8f4f2199ab738b2ae7037f021bd80d34e230502f0f7c",
    "filter_contours.py": "632e1bb99038e70c203c548a3982cd1602d253a1a14638b27e420e706845c12f",
    "get_contours.py": "fe82bedd7627c12a5a0537bf598e3c1b26ccdb967f4003a48f328f1f69cdec92",
    "mfis.py": "b95dc0ab3b724d4d3f9b5b92f528ef09a84568ec308ff97951c1fad9fcab93f3",
}
MANIFEST_COLUMNS = ["study_id", "animal_id", "muscle_id", "section_id", "field_id",
                    "laminin_path", "dapi_path", "pixel_size_x_um", "pixel_size_y_um",
                    "calibration_source", "sampling_rule", "condition_blinded", "timepoint"]
IDS = ["study_id", "animal_id", "muscle_id", "section_id", "field_id"]
FIBER_COLUMNS = ["run_id"] + IDS + ["original_fiber_number", "csa_um2", "cnf"]
REVIEW_COLUMNS = FIBER_COLUMNS + ["decision", "reviewed_csa_um2", "reviewed_cnf",
    "dystrophin_positive", "gfp_positive", "threshold_rule_id", "reviewer_id", "review_date", "reason"]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def write_csv(path, columns, rows):
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def positive(value, name):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name}: expected a finite positive number") from None
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name}: expected a finite positive number")
    return number


def finite_decimal(value, name):
    """Exact numeric comparison permits spreadsheet formatting, never drift."""
    try:
        number = Decimal(value.strip())
    except (InvalidOperation, AttributeError, ValueError):
        raise ValueError(f"{name}: expected a finite numeric value") from None
    if not number.is_finite():
        raise ValueError(f"{name}: expected a finite numeric value")
    return number


def fetch_source(destination):
    destination = Path(destination).absolute()
    if destination.exists():
        raise ValueError(f"Source destination already exists: {destination}")
    with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:
        data = response.read(200001)
    if len(data) > 200000 or hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError("Upstream source archive SHA256 mismatch; nothing extracted")
    # Exact digest and member allowlist: never use extractall on remote archives.
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        contents = {name: archive.read("Myotally V102/" + name) for name in SOURCE_FILES}
    for name, content in contents.items():
        if hashlib.sha256(content).hexdigest() != SOURCE_FILES[name]:
            raise ValueError(f"Unexpected upstream source member: {name}")
    (destination / "source").mkdir(parents=True)
    for name, content in contents.items():
        (destination / "source" / name).write_bytes(content)
    write_json(destination / "source-provenance.json", {
        "url": SOURCE_URL, "archive_sha256": SOURCE_SHA256,
        "source_files": SOURCE_FILES, "retrieved_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "license": "No LICENSE in archive; no redistribution permission inferred",
    })
    return destination / "source"


def verify_source(source):
    source = Path(source).resolve(strict=True)
    if {p.name for p in source.iterdir()} != set(SOURCE_FILES):
        raise ValueError("Upstream source must contain exactly the eight pinned Python files")
    for name, expected in SOURCE_FILES.items():
        p = source / name
        if p.is_symlink() or sha256(p) != expected:
            raise ValueError(f"Upstream source integrity failure: {name}")
    return source


def load_manifest(path, inspect_images=False):
    path = Path(path).resolve(strict=True)
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != MANIFEST_COLUMNS:
            raise ValueError("Manifest header must exactly match templates/image-manifest.csv")
        rows = list(reader)
    if not rows:
        raise ValueError("Manifest contains zero fields")
    seen = set()
    files = {str(path): sha256(path)}
    for row in rows:
        if None in row or any(v is None or not v.strip() for v in row.values()):
            raise ValueError("Manifest has missing/empty values or extra columns")
        for key in IDS:
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", row[key]) or row[key] == "Results":
                raise ValueError(f"Invalid {key}; use a short alphanumeric ID, underscores/dashes/dots")
        field_name = row["field_id"].lower()
        if field_name == "all" or field_name.startswith("all_results"):
            raise ValueError("Reserved field_id: all and all_results-prefixed IDs conflict with upstream summaries")
        if row["field_id"] in seen:
            raise ValueError("field_id must be unique across the manifest")
        seen.add(row["field_id"])
        sx = positive(row["pixel_size_x_um"], "pixel_size_x_um")
        sy = positive(row["pixel_size_y_um"], "pixel_size_y_um")
        if not math.isclose(sx, sy, rel_tol=1e-9):
            raise ValueError("This CLI requires square pixels; validate any resampling separately")
        paths = []
        for key in ("laminin_path", "dapi_path"):
            original = Path(row[key])
            if not original.is_absolute():
                original = path.parent / original
            if original.is_symlink():
                raise ValueError(f"Channel must be a regular original file, not a symlink: {original}")
            try:
                original = original.resolve(strict=True)
            except FileNotFoundError:
                raise ValueError(f"Missing channel {key}: {original}") from None
            if not original.is_file() or original.suffix.lower() not in (".tif", ".tiff"):
                raise ValueError(f"Expected a TIFF file for {key}: {original}")
            row[key] = str(original)
            files[str(original)] = sha256(original)
            paths.append(original)
        if paths[0] == paths[1]:
            raise ValueError("DAPI and laminin must be distinct files with verified channel identities")
        if inspect_images:
            from PIL import Image
            import numpy as np
            arrays = []
            for original in paths:
                with Image.open(original) as image:
                    if getattr(image, "n_frames", 1) != 1:
                        raise ValueError("Split image stacks into single-channel, single-plane TIFFs")
                    array = np.array(image)
                if array.ndim != 2 or array.dtype not in (np.dtype("uint8"), np.dtype("uint16")):
                    raise ValueError("Channels must be 2D uint8/uint16 grayscale TIFFs")
                if min(array.shape) < 64 or float(np.percentile(array, 99.99)) <= 0:
                    raise ValueError("Channel is too small or lacks positive signal")
                arrays.append(array)
            if arrays[0].shape != arrays[1].shape or arrays[0].dtype != arrays[1].dtype:
                raise ValueError("DAPI/laminin dimensions and bit depths must match")
    return rows, files


def unchanged(files):
    failures = [name for name, digest in files.items()
                if not Path(name).is_file() or sha256(name) != digest]
    return {"all_unchanged": not failures, "changed_or_missing": failures,
            "sha256_before": files}


def check_run_location(run, rows, manifest):
    # Reject both overlap directions. Upstream never sees originals/metadata.
    run = Path(run).absolute().resolve()
    protected = {Path(manifest).resolve().parent}
    protected.update(Path(r[k]).parent for r in rows for k in ("laminin_path", "dapi_path"))
    for p in protected:
        if run == p or run in p.parents or p in run.parents:
            raise ValueError(f"Run directory overlaps protected originals/metadata directory: {p}")
    if run.exists() or run.is_symlink():
        raise ValueError("Run directory must be new; failed runs are preserved, never overwritten")


def parse_outputs(parent, field):
    summaries = list((parent / "Results").glob("all_results_*.txt"))
    tables = list((parent / "Results").glob(field + "_*.txt"))
    if len(summaries) != 1 or len(tables) != 1 or not (parent / field / "final.tif").is_file():
        raise ValueError(f"Missing real upstream outputs for {field}; zero processed is a failure")
    lines = [line.strip() for line in tables[0].read_text().splitlines() if line.strip()]
    records = list(csv.DictReader(lines, delimiter="\t", skipinitialspace=True))
    if not records:
        raise ValueError(f"Zero fibers exported for {field}; do not accept an empty run")
    fibers = []
    seen = set()
    for row in records:
        row = {k.strip(): v.strip() for k, v in row.items()}
        number = int(row["Fiber Number"])
        area = positive(row["CSA"], "upstream CSA")
        cnf = int(row["CNF (y/n = 1/0)"])
        if number < 0 or number in seen or cnf not in (0, 1):
            raise ValueError("Invalid/duplicate upstream fiber ID or central-nucleus flag")
        seen.add(number)
        fibers.append({"original_fiber_number": str(number), "csa_um2": area, "cnf": cnf})
    summary_lines = [x for x in summaries[0].read_text().splitlines() if "\t" in x]
    summary = [{k.strip(): v.strip() for k, v in row.items()}
               for row in csv.DictReader(summary_lines, delimiter="\t")]
    if len(summary) != 1 or summary[0]["Image"] != field or int(summary[0]["Number of Fibers"]) != len(fibers):
        raise ValueError("Upstream summary/field/fiber count does not agree with actual exports")
    return fibers


def analyze(args):
    source = verify_source(args.source)
    runtime = runtime_info()
    rows, originals = load_manifest(args.manifest, inspect_images=True)
    minimum = positive(args.min_area, "min_area")
    maximum = positive(args.max_area, "max_area")
    if maximum <= minimum:
        raise ValueError("max_area must be greater than min_area")
    run = args.run_dir.absolute().resolve()
    if source == run or source in run.parents:
        raise ValueError("Runs must be outside the pinned source directory")
    check_run_location(run, rows, args.manifest)
    run.mkdir(parents=True)
    (run / "logs").mkdir()
    (run / "exports").mkdir()
    record = {"status": "running", "wrapper_version": VERSION, "run_id": run.name,
        "source_archive_sha256": SOURCE_SHA256, "source_files": SOURCE_FILES,
        "source_path": str(source), "manifest": str(args.manifest.resolve()),
        "manifest_sha256": sha256(args.manifest), "fields": rows, "argv": sys.argv,
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "settings": {"quality": args.quality, "min_area_um2": minimum, "max_area_um2": maximum,
                     "mfi_channels": [], "positivity": "manual review only"},
        "runtime": runtime, "biological_validation": "pending"}
    write_json(run / "provenance.json", record)
    shutil.copyfile(args.manifest, run / "manifest.input.csv")
    all_fibers = []
    try:
        # Copy every channel before starting upstream, so no source folder is
        # ever a working folder and a later missing field cannot be silently skipped.
        for row in rows:
            field = row["field_id"]
            parent = run / "work" / field / "input"
            copied = parent / field
            copied.mkdir(parents=True)
            for key, canonical in (("laminin_path", "Laminin.tif"), ("dapi_path", "DAPI.tif")):
                shutil.copyfile(row[key], copied / canonical)
                if sha256(copied / canonical) != originals[row[key]]:
                    raise ValueError("Channel changed while copying")
            write_json(parent.parent / "worker-contract.json", {
                "work": str(parent), "field_id": field,
                "channels": {name: sha256(copied / name) for name in ("Laminin.tif", "DAPI.tif")}})
        for row in rows:
            field = row["field_id"]
            parent = run / "work" / field / "input"
            command = [sys.executable, "-B", "-I", str(Path(__file__).resolve()), "_upstream",
                "--source", str(source), "--work", str(parent), "--quality", args.quality,
                "--min-area", str(minimum), "--max-area", str(maximum),
                "--contract", str(parent.parent / "worker-contract.json"),
                "--pixels-per-um2", str(1 / (float(row["pixel_size_x_um"]) * float(row["pixel_size_y_um"])))]
            with (run / "logs" / (field + ".log")).open("w") as log:
                subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, cwd=run)
            fibers = parse_outputs(parent, field)
            dest = run / "exports" / "upstream" / field
            shutil.copytree(parent / "Results", dest / "Results")
            shutil.copyfile(parent / field / "final.tif", dest / "final.tif")
            for fiber in fibers:
                all_fibers.append({"run_id": run.name, **{k: row[k] for k in IDS}, **fiber})
        write_csv(run / "exports" / "fibers.csv", FIBER_COLUMNS, all_fibers)
        write_csv(run / "exports" / "review-template.csv", REVIEW_COLUMNS,
                  [{**f, **{k: "" for k in REVIEW_COLUMNS if k not in f}} for f in all_fibers])
        record.update(status="succeeded-review-pending", processed_fields=len(rows), fiber_count=len(all_fibers))
    except Exception as exc:
        record.update(status="failed", error=str(exc))
        raise
    finally:
        safety = unchanged(originals)
        write_json(run / "original-files-check.json", safety)
        if not safety["all_unchanged"]:
            record.update(status="failed-originals-changed", error="Original/manifest checksum mismatch")
        record["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        write_json(run / "provenance.json", record)
    if not safety["all_unchanged"]:
        raise ValueError("Original files changed; stop and investigate")
    print(json.dumps({"status": record["status"], "run_dir": str(run),
                      "processed_fields": len(rows), "fiber_count": len(all_fibers)}))


def upstream(args):
    source = verify_source(args.source)
    contract = json.loads(args.contract.read_text())
    work = args.work.resolve(strict=True)
    if args.contract.resolve() != work.parent / "worker-contract.json" or contract["work"] != str(work):
        raise ValueError("Internal worker requires the wrapper's disposable-copy contract")
    copied = work / contract["field_id"]
    if set(p.name for p in work.iterdir()) != {contract["field_id"]}:
        raise ValueError("Unexpected content in disposable input parent")
    if set(p.name for p in copied.iterdir()) != {"DAPI.tif", "Laminin.tif"}:
        raise ValueError("Only copied channels may enter the upstream worker")
    for name, digest in contract["channels"].items():
        if (copied / name).is_symlink() or sha256(copied / name) != digest:
            raise ValueError("Disposable-copy checksum mismatch")
    # No GUI import, no replacement algorithm, no source modifications.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source))
    import call_Myotally
    call_Myotally.main(str(args.work.resolve()), "DAPI.tif", "Laminin.tif", "",
                      2 if args.quality == "high" else 1, args.min_area, args.max_area, args.pixels_per_um2)


def runtime_info():
    import numpy
    import scipy
    import cv2
    import PIL
    # Verify the exact source indexing assumption, rather than claiming imports
    # demonstrate successful segmentation.
    from scipy import stats
    int(stats.mode(numpy.array([1, 1, 2]))[0][0])
    info = {
        "numpy": numpy.__version__, "scipy": scipy.__version__, "opencv": cv2.__version__,
        "pillow": PIL.__version__, "python": sys.version, "platform": sys.platform}
    expected = {"numpy": "1.24.4", "scipy": "1.10.1", "opencv": "4.8.1", "pillow": "10.0.1"}
    if any(info[k] != value for k, value in expected.items()) or sys.version_info[:3] != (3, 10, 14):
        raise ValueError(f"Runtime differs from environment.yml: {info}")
    return info


def doctor(args):
    source = verify_source(args.source)
    print(json.dumps({"wrapper_version": VERSION, "source": str(source), **runtime_info(),
        "image_execution": "not established by doctor", "biology": "not validated"}, indent=2))


def export_review(args):
    run = args.run_dir.resolve(strict=True)
    state = json.loads((run / "provenance.json").read_text())
    if state["status"] != "succeeded-review-pending":
        raise ValueError("Only successful upstream runs can be reviewed")
    with (run / "exports" / "fibers.csv").open(newline="") as f:
        originals = list(csv.DictReader(f))
    with args.review.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != REVIEW_COLUMNS:
            raise ValueError("Use the generated review-template.csv header")
        rows = list(reader)
    identity_columns = ["run_id"] + IDS + ["original_fiber_number"]
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("Review has missing values or extra columns")
        for column in identity_columns:
            row[column] = row[column].strip()
    def key(row):
        return tuple(row[k].strip() for k in identity_columns)
    baseline = {key(r): r for r in originals}
    if len(rows) != len(baseline) or len({key(r) for r in rows}) != len(rows) or {key(r) for r in rows} != set(baseline):
        raise ValueError("Review must contain exactly one row per original exported fiber")
    groups = {}
    for row in rows:
        if any(finite_decimal(row[c], c) != finite_decimal(baseline[key(row)][c], c)
               for c in ("csa_um2", "cnf")):
            raise ValueError("Original fiber columns must remain unchanged; use reviewed columns")
        if row["decision"] not in ("accept", "exclude") or not row["reviewer_id"].strip():
            raise ValueError("Every fiber requires accept/exclude and reviewer_id")
        dt.date.fromisoformat(row["review_date"])
        if row["decision"] == "exclude":
            if not row["reason"].strip():
                raise ValueError("Excluded fibers need a reason")
            continue
        area = positive(row["reviewed_csa_um2"] or row["csa_um2"], "reviewed CSA")
        cnf = finite_decimal(row["reviewed_cnf"] or row["cnf"], "reviewed_cnf")
        if cnf not in (Decimal(0), Decimal(1)):
            raise ValueError("reviewed_cnf must be 0 or 1")
        for name in ("dystrophin_positive", "gfp_positive"):
            if row[name] not in ("", "0", "1"):
                raise ValueError(f"{name} must be blank (unscored), 0 or 1")
            if row[name] and not row["threshold_rule_id"].strip():
                raise ValueError("Positivity scores require a documented threshold_rule_id")
        group = groups.setdefault((row["study_id"], row["animal_id"], row["muscle_id"]), [])
        group.append((row, area, int(cnf)))
    if not groups:
        raise ValueError("No accepted fibers; no animal export can be accepted")
    summaries = []
    for (study, animal, muscle), items in sorted(groups.items()):
        scored = all(r["dystrophin_positive"] != "" for r, _, _ in items)
        rules = {r["threshold_rule_id"] for r, _, _ in items if r["dystrophin_positive"] != ""}
        if len(rules) > 1:
            raise ValueError("Mixed dystrophin positivity rules within animal/muscle; reconcile before aggregation")
        positive_count = sum(int(r["dystrophin_positive"]) for r, _, _ in items) if scored else ""
        summaries.append({"study_id": study, "animal_id": animal, "muscle_id": muscle,
            "sampled_fields": len({r["field_id"] for r, _, _ in items}), "accepted_fibers": len(items),
            "mean_csa_um2": sum(area for _, area, _ in items) / len(items),
            "cnf_count": sum(cnf for _, _, cnf in items), "dystrophin_scoring_complete": str(scored).lower(),
            "dystrophin_positive_count": positive_count,
            "dystrophin_fraction": positive_count / len(items) if scored else "",
            "threshold_rule_id": next(iter(rules)) if rules else "",
            "biological_validation": "pending"})
    output = args.output.absolute().resolve()
    if output.exists() or output == run or output in run.parents:
        raise ValueError("Review output must be a new directory and must not contain the original run")
    if output == args.review.resolve() or output in args.review.resolve().parents:
        raise ValueError("Review output may not overlap the input review")
    check_run_location(output, state["fields"], state["manifest"])
    output.mkdir(parents=True)
    shutil.copyfile(args.review, output / "fiber-review.csv")
    write_csv(output / "animal-summary.csv", list(summaries[0]), summaries)
    write_json(output / "review-provenance.json", {"run": str(run), "review_sha256": sha256(args.review),
        "wrapper_version": VERSION, "biological_validation": "pending",
        "scope": "Sampled accepted laminin/DAPI fibers grouped by study/animal/muscle; no H&E or GFP summary"})
    print(json.dumps({"output": str(output), "animals": len({(study, animal) for study, animal, _ in groups}),
                      "animal_muscle_groups": len(summaries), "biology": "validation pending"}))


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", action="version", version=VERSION)
    commands = p.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch-source", help="Retrieve/hash upstream code outside this repository")
    fetch.add_argument("--destination", type=Path, required=True)
    fetch.set_defaults(func=lambda a: print(fetch_source(a.destination)))
    check = commands.add_parser("validate-manifest", help="Validate channels/IDs/calibration without creating a run")
    check.add_argument("--manifest", type=Path, required=True)
    check.add_argument("--inspect-images", action="store_true")
    check.set_defaults(func=lambda a: print(json.dumps({"validated_fields": len(load_manifest(a.manifest, a.inspect_images)[0])})))
    for name in ("doctor", "analyze", "_upstream"):
        q = commands.add_parser(name, help="internal child worker" if name == "_upstream" else None)
        q.add_argument("--source", type=Path, default=os.environ.get("WAGERS_MYOTALLY_SOURCE"))
        if name != "doctor":
            q.add_argument("--quality", choices=("high", "low"), required=True)
            q.add_argument("--min-area", type=float, required=True)
            q.add_argument("--max-area", type=float, required=True)
        if name == "analyze":
            q.add_argument("--manifest", type=Path, required=True)
            q.add_argument("--run-dir", type=Path, required=True)
        elif name == "_upstream":
            q.add_argument("--work", type=Path, required=True)
            q.add_argument("--contract", type=Path, required=True)
            q.add_argument("--pixels-per-um2", type=float, required=True)
        q.set_defaults(func={"doctor": doctor, "analyze": analyze, "_upstream": upstream}[name])
    review = commands.add_parser("export-review", help="Export reviewed fiber ledger and sampled animal summaries")
    review.add_argument("--run-dir", type=Path, required=True)
    review.add_argument("--review", type=Path, required=True)
    review.add_argument("--output", type=Path, required=True)
    review.set_defaults(func=export_review)
    validation = commands.add_parser("validate-one", help="Real upstream control/manifest run, missing-channel retry and checksums")
    validation.add_argument("--evidence-dir", type=Path, required=True)
    validation.add_argument("--manifest", type=Path)
    validation.add_argument("--min-area", type=float, default=200)
    validation.add_argument("--max-area", type=float, default=3000)
    validation.add_argument("--quality", choices=("high", "low"), default="high")
    validation.set_defaults(func=validate_one)
    tutorial = commands.add_parser("tutorial-suite", help="Five real-upstream synthetic tutorial contracts; no biological validation")
    tutorial.add_argument("--evidence-dir", type=Path, required=True)
    tutorial.add_argument("--source", type=Path, default=os.environ.get("WAGERS_MYOTALLY_SOURCE"))
    tutorial.set_defaults(func=tutorial_suite)
    return p


def tutorial_suite(args):
    script = Path(__file__).resolve().parent / "scripts" / "tutorial_suite.py"
    subprocess.run([sys.executable, "-B", "-I", str(script), "--evidence-dir", str(args.evidence_dir),
                    "--source", str(args.source)], check=True)


def validate_one(args):
    script = Path(__file__).resolve().parent / "scripts" / "validate_one.py"
    command = [sys.executable, "-B", "-I", str(script), "--evidence-dir", str(args.evidence_dir),
               "--min-area", str(args.min_area), "--max-area", str(args.max_area), "--quality", args.quality]
    if args.manifest:
        command += ["--manifest", str(args.manifest)]
    subprocess.run(command, check=True)


def main():
    args = parser().parse_args()
    if hasattr(args, "source") and args.source is None:
        raise ValueError("Provide --source or WAGERS_MYOTALLY_SOURCE")
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"WAGERS ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        if "_upstream" in sys.argv:
            traceback.print_exc()
        sys.exit(2)
