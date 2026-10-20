#!/usr/bin/env python
"""Container-only real CellProfiler 4.2.8 IdentifyPrimaryObjects API pipeline.

The workspace/module lifecycle follows CellProfiler v4.2.8's own
 tests/modules/test_identifyprimaryobjects.py (test_test_zero_objects).
This program never reads truth.csv or computes substitute component counts.
"""
import csv
import hashlib
import importlib.metadata
import inspect
import json
import platform
import sys
from pathlib import Path


def main():
    import cellprofiler
    import cellprofiler_core.preferences as preferences
    # Set before module imports; no GUI, JVM or display is started for this pipeline.
    preferences.set_headless()
    preferences.set_default_image_directory("/input")
    preferences.set_default_output_directory("/output")
    import numpy as np
    from PIL import Image as PILImage
    from cellprofiler.modules import identifyprimaryobjects as ipo
    from cellprofiler.modules import threshold
    from cellprofiler_core.image import Image, ImageSetList
    from cellprofiler_core.measurement import Measurements
    from cellprofiler_core.object import ObjectSet
    from cellprofiler_core.pipeline import Pipeline
    from cellprofiler_core.workspace import Workspace

    versions = {name: importlib.metadata.version(name) for name in
                ("CellProfiler", "cellprofiler-core", "numpy", "scipy", "scikit-image", "Pillow", "centrosome")}
    if cellprofiler.__version__ != "4.2.8" or versions["CellProfiler"] != "4.2.8" or versions["cellprofiler-core"] != "4.2.8":
        raise RuntimeError("exact CellProfiler AND core 4.2.8 required: " + repr(versions))
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "amd64"):
        raise RuntimeError("Linux amd64 required")
    print("Verified exact CellProfiler 4.2.8 and core 4.2.8", flush=True)

    module = ipo.IdentifyPrimaryObjects()
    module.set_module_num(1)
    module.show_window = False
    module.x_name.value = "Fluorescence"
    module.y_name.value = "FluorescentObjects"
    module.use_advanced.value = True
    module.size_range.value = (8, 14)
    module.exclude_size.value = True
    module.exclude_border_objects.value = True
    module.unclump_method.value = ipo.UN_NONE
    module.watershed_method.value = ipo.WA_NONE
    module.fill_holes.value = ipo.FH_NEVER
    module.threshold.threshold_scope.value = threshold.TS_GLOBAL
    module.threshold.global_operation.value = threshold.TM_MANUAL
    module.threshold.manual_threshold.value = 0.5
    module.threshold.threshold_smoothing_scale.value = 0
    pipeline = Pipeline()
    pipeline.add_module(module)
    settings = [{"text": s.text, "value": s.value_text} for s in module.settings()]
    Path("/output/module-settings.json").write_text(json.dumps(settings, indent=2) + "\n")
    source = Path(inspect.getfile(ipo))
    provenance = {
        "cellprofiler": versions["CellProfiler"], "cellprofiler_core": versions["cellprofiler-core"],
        "python": sys.version, "platform": platform.platform(), "dependencies": versions,
        "module": module.module_name, "module_revision": module.variable_revision_number,
        "module_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "measurement": "Image/Count_FluorescentObjects",
        "method": "real module.run(Workspace), manual global threshold 0.5, no declumping",
    }
    Path("/output/package.json").write_text(json.dumps(provenance, indent=2) + "\n")
    masks = Path("/output/labels")
    masks.mkdir()
    with Path("/input/metadata.csv").open(newline="") as f:
        metadata = list(csv.DictReader(f))
    columns = list(metadata[0])
    with Path("/output/measured-fields.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns + ["count"])
        writer.writeheader()
        for row in metadata:
            # PIL must decode fully; missing/corrupt images propagate exceptions, never become zero.
            with PILImage.open(Path("/input") / row["image"]) as image:
                image.load()
                if image.mode != "L" or image.size != (96, 96):
                    raise RuntimeError("unsupported tutorial image format")
                data = np.asarray(image, dtype=np.float64) / 255.0
            image_sets = ImageSetList()
            image_set = image_sets.get_image_set(0)
            image_set.add("Fluorescence", Image(data, dimensions=2))
            objects = ObjectSet()
            measurements = Measurements()
            try:
                workspace = Workspace(pipeline, module, image_set, objects, measurements, image_sets)
                module.run(workspace)
                measured = np.asarray(measurements.get_current_measurement("Image", "Count_FluorescentObjects"))
                if measured.size != 1 or not np.isfinite(measured.item()) or measured.item() < 0 or measured.item() != int(measured.item()):
                    raise RuntimeError("invalid CellProfiler count measurement")
                count = int(measured.item())
                labels = objects.get_objects("FluorescentObjects").segmented
                # Export package segmentation for visual review; it is never used to infer counts here.
                PILImage.fromarray(labels.astype(np.uint16)).save(masks / (Path(row["image"]).stem + ".png"))
                writer.writerow(dict(row, count=count))
                f.flush()
                print(row["image"] + ": CellProfiler Count_FluorescentObjects=" + str(count), flush=True)
            finally:
                measurements.close()
    print("Real CellProfiler API pipeline completed all %d fields" % len(metadata), flush=True)


if __name__ == "__main__":
    main()
