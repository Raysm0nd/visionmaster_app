"""Phase 2 (Red): the rewritten GraphBridge is a pure-Python data bridge.

No Qt, no NodeGraphQt — it owns an *ordered* list of core nodes plus their
connections and rebuilds a runnable ``core.Graph`` on demand.
"""

from __future__ import annotations

import sys

import pytest

import visionpower.nodes  # noqa: F401  (register built-in node types)
from visionpower.app.graph_bridge import GraphBridge
from visionpower.core import Scheduler, load_graph, save_graph


def _linear_bridge(sample_image_path) -> GraphBridge:
    b = GraphBridge()
    b.add_node("sources/LoadImage", "load", {"path": sample_image_path})
    b.add_node("filters/Grayscale", "gray")
    b.add_node("filters/GaussianBlur", "blur", {"ksize": 3})
    b.add_node("filters/Threshold", "thresh", {"thresh": 127})
    b.add_node("analysis/FindContours", "contours", {"min_area": 50})
    b.add_node("sinks/Viewer", "viewer")
    b.connect("load", "image", "gray", "image")
    b.connect("gray", "image", "blur", "image")
    b.connect("blur", "image", "thresh", "image")
    b.connect("thresh", "image", "contours", "image")
    b.connect("load", "image", "viewer", "image")
    b.connect("contours", "detections", "viewer", "detections")
    b.connect("contours", "verdict", "viewer", "verdict")
    return b


def test_bridge_module_does_not_import_nodegraphqt():
    import visionpower.app.graph_bridge as gb_mod

    src = open(gb_mod.__file__, encoding="utf-8").read()
    assert "import NodeGraphQt" not in src
    assert "from NodeGraphQt" not in src
    # and it must not be present in sys.modules via this import
    assert "NodeGraphQt" not in type(gb_mod.GraphBridge()).__mro__[0].__module__


def test_add_node_keeps_insertion_order_and_returns_core_node():
    b = GraphBridge()
    n1 = b.add_node("filters/Grayscale", "gray")
    n2 = b.add_node("filters/Threshold", "thresh")
    assert n1.NODE_TYPE == "filters/Grayscale"
    assert [n.id for n in b.nodes] == ["gray", "thresh"]
    assert b.nodes[1] is n2


def test_add_node_autogenerates_unique_ids_when_omitted():
    b = GraphBridge()
    a = b.add_node("filters/Grayscale")
    c = b.add_node("filters/Grayscale")
    assert a.id != c.id


def test_clear_empties_nodes_and_connections():
    b = GraphBridge()
    b.add_node("filters/Grayscale", "gray")
    b.add_node("filters/Threshold", "thresh")
    b.connect("gray", "image", "thresh", "image")
    b.clear()
    assert b.nodes == []
    assert b.to_core_graph().connections == []


def test_index_of_and_core_node_lookup():
    b = GraphBridge()
    b.add_node("filters/Grayscale", "gray")
    b.add_node("filters/Threshold", "thresh")
    assert b.index_of("thresh") == 1
    assert b.core_node("gray").NODE_TYPE == "filters/Grayscale"
    assert b.core_node("missing") is None


def test_to_core_graph_runs_through_scheduler(sample_image_path):
    b = _linear_bridge(sample_image_path)
    results = Scheduler().run(b.to_core_graph())
    assert all(r.ok for r in results.values()), {
        k: r.error for k, r in results.items() if not r.ok
    }
    found = [r.outputs["detections"] for r in results.values() if "detections" in r.outputs]
    assert found and len(found[0]) == 1


def test_load_core_graph_roundtrips_order_and_connections(sample_image_path, tmp_path):
    b = _linear_bridge(sample_image_path)
    out = tmp_path / "flow.json"
    save_graph(b.to_core_graph(), out)

    b2 = GraphBridge()
    b2.load_core_graph(load_graph(out))
    assert [n.id for n in b2.nodes] == [n.id for n in b.nodes]
    results = Scheduler().run(b2.to_core_graph())
    assert all(r.ok for r in results.values())
