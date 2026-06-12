"""Engine tests for the sources/ImageSource folder node (no Qt)."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

import visionpower.nodes  # noqa: F401
from visionpower.core import Graph, Scheduler, create_node


@pytest.fixture
def image_folder(tmp_path):
    for i in range(3):
        img = np.zeros((50, 60, 3), dtype=np.uint8)
        img[:, :, 0] = (i + 1) * 40  # distinguishable blue level per file
        cv2.imwrite(str(tmp_path / f"img-{i}.png"), img)
    (tmp_path / "notes.txt").write_text("ignored")
    return tmp_path


def test_image_source_lists_and_emits_by_index(image_folder):
    g = Graph()
    src = g.add_node(create_node("sources/ImageSource", "src", {
        "folder": str(image_folder), "index": 1,
    }))
    assert len(src.files()) == 3  # txt ignored by pattern

    results = Scheduler().run(g)
    assert results["src"].ok, results["src"].error
    image = results["src"].outputs["image"]
    assert image.meta["index"] == 1 and image.meta["count"] == 3
    assert image.meta["source"].endswith("img-1.png")
    assert int(image.data[0, 0, 0]) == 80  # second file's blue level

    # index switch re-runs (different signature), out-of-range clamps
    src.set_param("index", 99)
    results = Scheduler().run(g)
    assert results["src"].outputs["image"].meta["index"] == 2


def test_image_source_empty_folder_fails_cleanly(tmp_path):
    g = Graph()
    g.add_node(create_node("sources/ImageSource", "src", {"folder": str(tmp_path)}))
    results = Scheduler().run(g)
    assert results["src"].ok is False
    assert "no images" in results["src"].error
