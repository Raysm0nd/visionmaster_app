"""End-to-end tests for the pure-Python engine (Definition of Done, headless)."""

from __future__ import annotations

import subprocess
import sys

import pytest

import visionpower.nodes  # noqa: F401
from visionpower.core import (
    Graph,
    PortType,
    Scheduler,
    Verdict,
    create_node,
    graph_from_dict,
    graph_to_dict,
    load_graph,
    node_schema,
    save_graph,
)
from visionpower.core.types import Detection, Image


def test_core_imports_no_qt():
    """Importing the engine must not pull in any Qt binding.

    Checked in a clean subprocess so a sibling GUI test that already imported Qt
    into this pytest process cannot pollute the result.
    """

    code = (
        "import sys; import visionpower.core; import visionpower.nodes;"
        " bad = [m for m in sys.modules if m.split('.')[0] in"
        " ('PySide6', 'PyQt5', 'PyQt6', 'NodeGraphQt', 'Qt')];"
        " assert not bad, bad; print('ok')"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stderr


def test_scheduler_runs_flow(defect_graph):
    results = Scheduler().run(defect_graph)

    assert all(r.ok for r in results.values()), {
        k: r.error for k, r in results.items() if not r.ok
    }
    det = results["contours"].outputs["detections"]
    verdict = results["contours"].outputs["verdict"]
    assert isinstance(det, Detection)
    assert len(det) == 1  # the single white square
    assert isinstance(verdict, Verdict)
    assert verdict.ok is False  # 1 defect > max_allowed (0)
    assert isinstance(results["viewer"].outputs["image"], Image)


def test_incremental_cache_recomputes_only_downstream(defect_graph):
    sched = Scheduler()
    sched.run(defect_graph)  # warm the cache

    # Change a DOWNSTREAM param: only that node should recompute.
    defect_graph.nodes["contours"].set_param("max_allowed", 5)
    results = sched.run(defect_graph)

    assert results["contours"].cached is False
    for upstream in ("load", "gray", "blur", "thresh"):
        assert results[upstream].cached is True, upstream
    # verdict now passes (1 <= 5)
    assert results["contours"].outputs["verdict"].ok is True


def test_incremental_cache_invalidates_descendants(defect_graph):
    sched = Scheduler()
    sched.run(defect_graph)

    # Change an UPSTREAM param: that node + its descendants recompute.
    defect_graph.nodes["thresh"].set_param("thresh", 100)
    results = sched.run(defect_graph)

    assert results["thresh"].cached is False
    assert results["contours"].cached is False
    assert results["viewer"].cached is False
    for unaffected in ("load", "gray", "blur"):
        assert results[unaffected].cached is True, unaffected


def test_serialize_roundtrip(defect_graph, tmp_path):
    data = graph_to_dict(defect_graph)
    assert data["schema_version"] == 1

    restored = graph_from_dict(data)
    assert set(restored.nodes) == set(defect_graph.nodes)
    assert len(restored.connections) == len(defect_graph.connections)

    # File round-trip + run produces an equivalent verdict.
    path = tmp_path / "flow.json"
    save_graph(defect_graph, path)
    reloaded = load_graph(path)
    results = Scheduler().run(reloaded)
    assert len(results["contours"].outputs["detections"]) == 1


def test_connection_type_validation():
    g = Graph()
    g.add_node(create_node("analysis/FindContours", "c"))
    g.add_node(create_node("filters/Grayscale", "gray"))
    # verdict (VERDICT) -> image (IMAGE) is incompatible
    with pytest.raises(TypeError):
        g.connect("c", "verdict", "gray", "image")


def test_error_isolation_does_not_crash_run():
    g = Graph()
    g.add_node(create_node("sources/LoadImage", "load", {"path": "/nonexistent.png"}))
    g.add_node(create_node("filters/Grayscale", "gray"))
    g.connect("load", "image", "gray", "image")

    results = Scheduler().run(g)  # must not raise
    assert results["load"].ok is False
    assert results["gray"].ok is False  # skipped because upstream failed
    assert "unavailable" in results["gray"].error


def test_node_schema_describes_all_nodes():
    schema = node_schema()
    types = {entry["type"] for entry in schema}
    assert {"sources/LoadImage", "filters/Threshold", "sinks/Viewer"} <= types
    thresh = next(e for e in schema if e["type"] == "filters/Threshold")
    param_names = {p["name"] for p in thresh["params"]}
    assert {"thresh", "maxval", "type", "otsu"} == param_names
    # Threshold output is an IMAGE port
    assert thresh["outputs"][0]["type"] == PortType.IMAGE.value
