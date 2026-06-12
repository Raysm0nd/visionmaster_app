"""Phase 2 (Red): demo-flow builder fills a GraphBridge with a runnable pipeline.

It builds with the *real* registered node types (LoadImage → Grayscale →
GaussianBlur → Threshold → FindContours → Viewer) so the new UI stays wired to
the real engine.
"""

from __future__ import annotations

import visionpower.nodes  # noqa: F401  (register built-in node types)
from visionpower.app.demo_flow import build_demo_flow
from visionpower.app.graph_bridge import GraphBridge
from visionpower.core import Scheduler


def test_build_demo_flow_creates_six_ordered_nodes(sample_image_path):
    b = GraphBridge()
    build_demo_flow(b, sample_image_path)
    assert len(b.nodes) == 6
    # first is a source, last is the viewer sink
    assert b.nodes[0].NODE_TYPE.startswith("sources/")
    assert b.nodes[-1].NODE_TYPE == "sinks/Viewer"


def test_build_demo_flow_is_runnable(sample_image_path):
    b = GraphBridge()
    build_demo_flow(b, sample_image_path)
    results = Scheduler().run(b.to_core_graph())
    assert all(r.ok for r in results.values()), {
        k: r.error for k, r in results.items() if not r.ok
    }


def test_build_demo_flow_without_path_generates_samples():
    b = GraphBridge()
    build_demo_flow(b)  # empty path → synthetic ImageSource folder
    results = Scheduler().run(b.to_core_graph())
    assert all(r.ok for r in results.values())


def test_build_demo_flow_clears_previous_state(sample_image_path):
    b = GraphBridge()
    b.add_node("filters/Grayscale", "stale")
    build_demo_flow(b, sample_image_path)
    assert "stale" not in [n.id for n in b.nodes]
