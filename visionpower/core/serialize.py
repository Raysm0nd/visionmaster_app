"""Workflow (de)serialization to/from a plain dict / JSON file.

The logical graph (nodes, params, connections) and the UI layout (node ``pos``)
are stored together but kept semantically separate: ``pos`` never participates
in the execution signature. ``schema_version`` is recorded so future formats
can be migrated.
"""

from __future__ import annotations

import json
from pathlib import Path

from visionpower.core import registry
from visionpower.core.graph import Graph

SCHEMA_VERSION = 1


def graph_to_dict(graph: Graph) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "nodes": [
            {
                "id": node.id,
                "type": node.NODE_TYPE,
                "params": dict(node.params),
                "pos": list(node.pos),
            }
            for node in graph.nodes.values()
        ],
        "connections": [
            {
                "from_node": c.from_node,
                "from_port": c.from_port,
                "to_node": c.to_node,
                "to_port": c.to_port,
            }
            for c in graph.connections
        ],
    }


def graph_from_dict(data: dict) -> Graph:
    version = data.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ValueError(
            f"unsupported schema_version {version!r} (expected {SCHEMA_VERSION})"
        )
    graph = Graph()
    for nd in data.get("nodes", []):
        pos = tuple(nd.get("pos", (0.0, 0.0)))
        node = registry.create_node(nd["type"], nd["id"], nd.get("params"), pos)
        graph.add_node(node)
    for c in data.get("connections", []):
        graph.connect(c["from_node"], c["from_port"], c["to_node"], c["to_port"])
    return graph


def save_graph(graph: Graph, path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(graph_to_dict(graph), indent=2), encoding="utf-8"
    )


def load_graph(path: str | Path) -> Graph:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return graph_from_dict(data)
