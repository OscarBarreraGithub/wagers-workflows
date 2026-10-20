# Pinned upstream and Linux feasibility

Checked 2026-10-19 UTC using the upstream GitHub release API, tagged tree,
downloaded source asset, and primary documentation. Links identify upstream
resources; software and images are not redistributed here.

## Pin and downloads

- Repository: [pieterboth/Myotally](https://github.com/pieterboth/Myotally).
- Release: [Myotally_V1.0.2](https://github.com/pieterboth/Myotally/releases/tag/Myotally_V1.0.2),
  published 2024-11-21. The release note says the change reduces false-positive
  fiber counting relative to 1.0.1; that is an upstream statement, not a result
  of this package's validation.
- Tag resolved to commit `713a9c13bd44dee7ae2469ee474fef7290d70d50`.
- [Release API](https://api.github.com/repos/pieterboth/Myotally/releases/tags/Myotally_V1.0.2)
  was checked for asset names, sizes, identifiers, and dates. Release assets can
  change independently of a tag: store the actual downloaded asset's checksum.

| Use | Exact asset (direct upstream download) | API asset ID | Bytes |
| --- | --- | --- | ---: |
| Mac desktop | [Myotally_V1_Mac.zip](https://github.com/pieterboth/Myotally/releases/download/Myotally_V1.0.2/Myotally_V1_Mac.zip) | 303507523 | 80471704 |
| Windows desktop | [Myotally_V1_Win.exe](https://github.com/pieterboth/Myotally/releases/download/Myotally_V1.0.2/Myotally_V1_Win.exe) | 246472315 | 88203926 |
| Inspected source | [Myotally.V1.0.2.Source.Code.zip](https://github.com/pieterboth/Myotally/releases/download/Myotally_V1.0.2/Myotally.V1.0.2.Source.Code.zip) | 246472390 | 15485 |
| Upstream example, not downloaded | [Example_Img.zip](https://github.com/pieterboth/Myotally/releases/download/Myotally_V1.0.2/Example_Img.zip) | 208059137 | 60682091 |

The source asset was downloaded and hashed locally:

```text
5ce9156babd235994e1769c82f40542e2cd4eaeac256ae31373ce02c26a8ab6d
```

It contains eight Python files under `Myotally V102/`, including the entry point
`Myotally_V1.py`. This asset was uploaded 2025-04-15. The tagged Git tree instead
uses `Myotally_V1/Myotally_1.py`; the automatic GitHub source archive and this
separate release asset must not be treated as identical. This package's source
inspection refers to the **separate release asset with the SHA256 above**.

The Mac asset was replaced/uploaded 2025-10-12. Its API-reported SHA256 is
`3a51384b67679330050d0c2933b4d621ef3818979c23975d964da396bdc496bb`;
the binary was not downloaded or independently hashed here. No API digest was
provided for the Windows asset. Record its locally computed SHA256 before use;
a self-computed hash records identity, not independent authenticity.

The [published protocol](https://pmc.ncbi.nlm.nih.gov/articles/PMC11772141/)
points to **1.0.1**, while this package pins **1.0.2**. Record version and artifact
hash rather than combining their results as if versions were interchangeable.
The protocol's old 1.0.1 release link is not this package's download target.

## Concrete execution blocker

**Historical preparation check:** the facts below describe the initial
documentation-only revision. Owner authorization now permits task-contained
dependencies and manager-controlled compute testing. A local Mamba environment
has since run the real algorithm through the new CLI on synthetic shapes;
[VALIDATION.md](../VALIDATION.md) gives the evidence. Linux remains untested by
this implementer, and macOS success does not establish Linux compatibility.

The inspection workstation reports `Darwin arm64` and Python `3.14.7`.
`docker version` reports client `29.2.1`, context `desktop-linux`, but exits 1
because it cannot connect to the Docker daemon. `podman`, `singularity`,
`apptainer`, `conda`, `micromamba`, and `uv` were not found on PATH. No daemon,
VM, system dependency, Python environment, or model was installed or started.

At that preparation stage, Linux execution was blocked by the unavailable
host runtime. That was not evidence that Myotally cannot run on Linux. The later
local source-CLI run establishes Mac mechanics only; it does not establish Linux
compatibility. The manager's subsequent read-only FASRC access checks are separate
from actual compute execution. This worker has made no remote connection or job
submission; the Linux real-tool run remains a manager-controlled acceptance gate.

The Mac/Windows packaged desktop route in
[first use](first-use.md#mac-or-windows-alternative) is still untested here.
The executable stage provides a demonstrated local **source CLI** synthetic
control; it does not establish Linux deployment or real-image acceptance.

## Requirements established by inspection

| Source evidence | Consequence for a future Linux check |
| --- | --- |
| `Myotally_V1.py:1–3,26,108–110` imports Tkinter and immediately creates a GUI | Python with working Tcl/Tk and a graphical display; OOD Remote Desktop is appropriate, a headless notebook is not the GUI |
| Eight Python files import `PIL`, `cv2`, `numpy`, `scipy` plus standard library | Pillow, OpenCV native libraries, NumPy, SciPy, and all eight sibling files are needed |
| `get_contours.py:14–39` unpacks two return values from `cv2.findContours` | Inspect/test an OpenCV 4 environment rather than assuming any OpenCV version works |
| `call_Myotally.py:142` indexes `stats.mode(...)[0][0]` | An unmodified source candidate needs the old array-return behavior; a current SciPy may fail |
| `call_Myotally.py:44–52,77–83,377–381` changes directory, writes results, cleans image folders | Absolute input parent path, writable disposable work copies, no original images or unrelated files in processed folders |
| No CUDA/Torch/model import or model-weight file in the inspected archive | CPU first; no basis for requesting a GPU for this implementation |

[SciPy 1.8.0](https://docs.scipy.org/doc/scipy-1.8.0/reference/generated/scipy.stats.mode.html)
documents the older array return; [SciPy 1.11 release notes](https://docs.scipy.org/doc/scipy-1.11.0/release/1.11.0-notes.html#backwards-incompatible-changes)
document the changed `keepdims` default. This is a compatibility concern from
inspection, not an observed image-run traceback. No source patch is included. The delivered CLI invokes this unmodified function
with SciPy 1.10.1 and records the deprecation warning rather than changing it.

The protocol reports Python **3.9.10**, SciPy **1.8.0**, NumPy **1.22.2**,
OpenCV **4.5.5**, and PIL/Pillow **9.0.1** for unpackaged scripts. Use these as a
historical candidate specification, **not a tested Linux lockfile**. The protocol
does not specify the OpenCV package build suffix, Linux OS, Tcl/Tk version, or
native-library builds. The new [environment recipe and bootstrap](cli.md) select explicit candidate
versions and record resolved builds; those still must be checked on an
authorized Linux host before a launcher is advertised. Do not install these into
the host Python 3.14 environment or silently upgrade the source's dependencies.

## Licensing

No LICENSE file was present in the tagged recursive tree or downloaded source
archive. The upstream README describes scientific availability but does not
state a redistribution license. The protocol's article license does not by
itself establish a license for code or release image assets. The lab maintainer
must resolve permitted shared installation, modification, and image reuse before
distribution/deployment. No upstream code, binary, image, or article is vendored.
Do not assume a Zenodo record's terms cover every later GitHub asset.

Upstream requests citation of [DOI 10.5281/zenodo.14197515](https://doi.org/10.5281/zenodo.14197515).
For an image test, obtain explicit suitable provenance/terms for one upstream
example or use an original synthetic image; record its origin, checksum, channel
layout, and declared purpose. Synthetic execution would check mechanics only.
