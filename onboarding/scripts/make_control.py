#!/usr/bin/env python3
"""Generate original synthetic shapes for upstream runtime mechanics only."""
import sys

# Shared software must stay byte-for-byte unchanged, including import caches.
sys.dont_write_bytecode = True

import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import wagers


def make_control(destination):
    import numpy as np
    from PIL import Image, ImageDraw
    destination = Path(destination).absolute()
    if destination.exists():
        raise ValueError("Control destination must be new")
    raw = destination / "originals"
    meta = destination / "metadata"
    raw.mkdir(parents=True)
    meta.mkdir()
    rng = np.random.default_rng(102)
    background = rng.integers(4, 24, size=(512, 512), dtype=np.uint8)
    laminin = Image.fromarray(background)
    dapi = Image.fromarray(rng.integers(1, 6, size=(512, 512), dtype=np.uint8))
    boundary = ImageDraw.Draw(laminin)
    nuclei = ImageDraw.Draw(dapi)
    for i, y in enumerate(range(48, 480, 60)):
        for j, x in enumerate(range(48, 480, 60)):
            radius = 15 + (i * 3 + j * 2) % 12
            intensity = 40 + (i * 21 + j * 31) % 210
            boundary.ellipse((x-radius, y-radius, x+radius, y+radius), outline=intensity, width=3)
            nx = x if (i+j) % 3 == 0 else x + radius - 6
            nuclei.ellipse((nx-3, y-3, nx+3, y+3), fill=230)
    laminin.save(raw / "Laminin.tif")
    dapi.save(raw / "DAPI.tif")
    (raw / "must-survive.txt").write_text("Original sentinel: upstream must never see this folder.\n")
    row = dict(zip(wagers.MANIFEST_COLUMNS, [
        "SYNTHETIC-CONTROL", "SYNTHETIC-A001", "TA-left", "section-01", "field-001",
        "../originals/Laminin.tif", "../originals/DAPI.tif", "1", "1",
        "synthetic-declared-1um-per-pixel-not-acquisition", "runtime-control-only",
        "fictional-A", "fictional-day7"]))
    manifest = meta / "image-manifest.csv"
    wagers.write_csv(manifest, wagers.MANIFEST_COLUMNS, [row])
    wagers.write_json(destination / "CONTROL-PROVENANCE.json", {
        "purpose": "Synthetic shape fixture: actual upstream runtime/control only, not biological accuracy",
        "origin": "Original deterministic synthetic shapes authored for this package; no third-party image data",
        "seed": 102, "shape": [512, 512], "dtype": "uint8", "declared_um_per_pixel": 1,
        "expected_segmentation_count": "No accuracy/count target asserted",
        "generator_sha256": wagers.sha256(Path(__file__)),
        "files": {str(p.relative_to(destination)): wagers.sha256(p) for p in raw.iterdir()}})
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--destination", type=Path, required=True)
    print(make_control(p.parse_args().destination))
