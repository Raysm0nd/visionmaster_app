"""Shared fixtures for engine tests (no Qt involved)."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

import visionpower.nodes  # noqa: F401  (registers built-in nodes)
from visionpower.core import Graph, create_node


@pytest.fixture
def sample_image_path(tmp_path):
    """Write a 100x100 black image with one white square; return its path."""

    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (40, 40), (60, 60), (255, 255, 255), thickness=-1)
    path = tmp_path / "sample.png"
    cv2.imwrite(str(path), img)
    return str(path)


@pytest.fixture
def defect_graph(sample_image_path):
    """LoadImage -> Grayscale -> GaussianBlur -> Threshold -> FindContours -> Viewer."""

    g = Graph()
    g.add_node(create_node("sources/LoadImage", "load", {"path": sample_image_path}))
    g.add_node(create_node("filters/Grayscale", "gray"))
    g.add_node(create_node("filters/GaussianBlur", "blur", {"ksize": 3}))
    g.add_node(create_node("filters/Threshold", "thresh", {"thresh": 127}))
    g.add_node(create_node("analysis/FindContours", "contours", {"min_area": 50}))
    g.add_node(create_node("sinks/Viewer", "viewer"))

    g.connect("load", "image", "gray", "image")
    g.connect("gray", "image", "blur", "image")
    g.connect("blur", "image", "thresh", "image")
    g.connect("thresh", "image", "contours", "image")
    g.connect("load", "image", "viewer", "image")
    g.connect("contours", "detections", "viewer", "detections")
    g.connect("contours", "verdict", "viewer", "verdict")
    return g
