"""Headless tests for the NodeGraphQt <-> core.Graph bridge (needs gui extra).

Run with: uv sync --extra gui --group gui-dev && QT_QPA_PLATFORM=offscreen uv run pytest
These are skipped automatically if PySide6/NodeGraphQt are not installed.
"""

from __future__ import annotations

import os

import cv2
import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")
pytest.importorskip("NodeGraphQt")

from PySide6 import QtWidgets  # noqa: E402

from visionpower.core import Scheduler  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app


@pytest.fixture
def sample_image_path(tmp_path):
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (40, 40), (60, 60), (255, 255, 255), -1)
    path = tmp_path / "sample.png"
    cv2.imwrite(str(path), img)
    return str(path)


def test_demo_flow_builds_runs_and_roundtrips(qapp, sample_image_path, tmp_path):
    from visionpower.app.main_window import MainWindow

    win = MainWindow()
    win.build_demo_flow(sample_image_path)

    # 6 nodes created and wired into a runnable core graph
    assert len(win.bridge.core_nodes) == 6
    assert all(r.ok for r in win.results.values()), {
        k: r.error for k, r in win.results.items() if not r.ok
    }
    # the FindContours node should have found the one square
    found = [
        r.outputs["detections"]
        for r in win.results.values()
        if "detections" in r.outputs
    ]
    assert found and len(found[0]) == 1

    # Save -> Load round-trip rebuilds an equivalent, runnable graph
    out = tmp_path / "flow.json"
    from visionpower.core import save_graph, load_graph

    save_graph(win.bridge.to_core_graph(), out)
    win.bridge.load_core_graph(load_graph(out))
    results = Scheduler().run(win.bridge.to_core_graph())
    assert all(r.ok for r in results.values())


def test_param_change_triggers_incremental_rerun(qapp, sample_image_path):
    from visionpower.app.main_window import MainWindow

    win = MainWindow()
    win.build_demo_flow(sample_image_path)

    # Find the threshold core node and bump its value; re-run via the same path
    thresh = next(
        n for n in win.bridge.core_nodes.values() if n.NODE_TYPE == "filters/Threshold"
    )
    thresh.set_param("thresh", 100)
    win.run_flow()
    # upstream load/gray/blur stay cached; threshold + downstream recompute
    by_type = {
        win.bridge.core_nodes[nid].NODE_TYPE: res for nid, res in win.results.items()
    }
    assert by_type["filters/GaussianBlur"].cached is True
    assert by_type["filters/Threshold"].cached is False
    assert by_type["analysis/FindContours"].cached is False
