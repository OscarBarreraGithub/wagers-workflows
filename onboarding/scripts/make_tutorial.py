#!/usr/bin/env python3
"""Author deterministic fictional study metadata around original control shapes."""
import sys

# Shared software must stay byte-for-byte unchanged, including import caches.
sys.dont_write_bytecode = True

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import wagers
from make_control import make_control

# Two animals, three animal/muscle groups, four fields. Repeated identical
# pixels deliberately test metadata routing, not independent biological samples.
DESIGN = [("001", "TA-left", "field-001"), ("001", "TA-left", "field-002"),
          ("001", "DIA", "field-003"), ("002", "TA-left", "field-004")]


def make_tutorial(destination):
    destination = Path(destination).resolve()
    manifest = make_control(destination)
    base = wagers.load_manifest(manifest)[0][0]
    base.update(laminin_path="../originals/Laminin.tif", dapi_path="../originals/DAPI.tif")
    rows = [{**base, "study_id": "FICTIONAL-SOFTWARE-CONTRACT", "animal_id": animal,
             "muscle_id": muscle, "field_id": field,
             "sampling_rule": "fictional-repeated-pixels-not-biological-replicates"}
            for animal, muscle, field in DESIGN]
    wagers.write_csv(manifest, wagers.MANIFEST_COLUMNS, rows)
    metadata = manifest.parent
    missing = metadata / "missing-channel.csv"
    wagers.write_csv(missing, wagers.MANIFEST_COLUMNS,
                     [{**rows[0], "laminin_path": str(destination / "absent.tif")}])
    invalid = metadata / "invalid-calibration.csv"
    wagers.write_csv(invalid, wagers.MANIFEST_COLUMNS,
                     [{**rows[0], "pixel_size_x_um": "0"}])
    retry = metadata / "corrected-half-scale.csv"
    wagers.write_csv(retry, wagers.MANIFEST_COLUMNS,
                     [{**rows[0], "pixel_size_x_um": "0.5", "pixel_size_y_um": "0.5",
                       "calibration_source": "fictional-scale-contract-not-acquisition"}])
    wagers.write_json(destination / "TUTORIAL-PROVENANCE.json", {
        "origin": "Original deterministic make_control shapes, seed 102; no third-party data",
        "purpose": "Fictional software-contract study; not biological truth or automated real-image positivity",
        "design": DESIGN, "identical_pixels_reused": True,
        "segmentation_golden_count": None,
        "calibration_comparison": "1 to 0.5 um/pixel; bounds 200/3000 to 50/750 um2, same pixel bounds and quality",
        "generator_sha256": wagers.sha256(Path(__file__)),
        "marker_labels": "Assigned only to generated synthetic review rows; no marker image or assay inference"})
    return {"manifest": manifest, "missing": missing, "invalid": invalid, "retry": retry}
