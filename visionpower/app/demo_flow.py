"""Build the sample inspection pipeline into a :class:`GraphBridge`.

Uses the real registered node types so the pipeline genuinely runs on the
engine. ``source_path``: a folder → ImageSource (multi-image), a file →
LoadImage, empty → generate 4 synthetic samples (like the reference UI).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
import numpy as np

from visionpower.app.graph_bridge import GraphBridge

# (vp_type, node_id) in display order — top to bottom on the canvas.
_STEPS = [
    ("sources/ImageSource", "source"),
    ("filters/Grayscale", "gray"),
    ("filters/GaussianBlur", "blur"),
    ("filters/Threshold", "thresh"),
    ("analysis/FindContours", "contours"),
    ("sinks/Viewer", "viewer"),
]


def build_demo_flow(bridge: GraphBridge, source_path: str = "") -> None:
    """Populate ``bridge`` with the demo pipeline (clears any prior state)."""

    steps = list(_STEPS)
    if source_path and Path(source_path).is_file():
        steps[0] = ("sources/LoadImage", "source")
    elif not source_path:
        source_path = _make_demo_images()

    bridge.clear()
    for vp_type, node_id in steps:
        bridge.add_node(vp_type, node_id)

    source = bridge.core_node("source")
    if steps[0][0] == "sources/ImageSource":
        source.set_param("folder", source_path)
    else:
        source.set_param("path", source_path)

    bridge.connect("source", "image", "gray", "image")
    bridge.connect("gray", "image", "blur", "image")
    bridge.connect("blur", "image", "thresh", "image")
    bridge.connect("thresh", "image", "contours", "image")
    bridge.connect("source", "image", "viewer", "image")
    bridge.connect("contours", "detections", "viewer", "detections")
    bridge.connect("contours", "verdict", "viewer", "verdict")


def _make_demo_images() -> str:
    """Generate 4 sample images (some OK, some with defects) in a temp dir."""

    folder = tempfile.mkdtemp(prefix="visionpower_demo_")
    rng = np.random.default_rng(7)
    for i, n_defects in enumerate([0, 1, 2, 3]):
        img = np.full((240, 320, 3), 24, np.uint8)
        noise = rng.integers(0, 18, (240, 320, 1), dtype=np.uint8)
        img = cv2.add(img, np.repeat(noise, 3, axis=2))
        for _ in range(n_defects):
            x, y = int(rng.integers(30, 280)), int(rng.integers(30, 200))
            r = int(rng.integers(8, 22))
            cv2.circle(img, (x, y), r, (235, 235, 235), -1)
        cv2.imwrite(str(Path(folder) / f"sample-{i + 1}.png"), img)
    return folder
