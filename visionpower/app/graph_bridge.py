"""Pure-Python bridge between the UI and the executable ``core.Graph``.

The bridge owns the source of truth for the desktop UI: an *ordered* list of
``core.Node`` instances (holding parameters) plus their connections. The custom
canvas renders this order top-to-bottom; a fresh ``core.Graph`` is rebuilt on
demand right before each run. No Qt and no NodeGraphQt — this keeps the bridge
unit-testable headlessly and decoupled from any particular canvas widget.
"""

from __future__ import annotations

from visionpower.core import Graph, Node, create_node, node_schema

_Conn = tuple[str, str, str, str]  # from_id, from_port, to_id, to_port


class GraphBridge:
    def __init__(self) -> None:
        self._nodes: list[Node] = []
        self._conns: list[_Conn] = []
        self._counters: dict[str, int] = {}

    # -- queries -----------------------------------------------------------
    @property
    def nodes(self) -> list[Node]:
        """Core nodes in display order (top → bottom)."""

        return list(self._nodes)

    @staticmethod
    def vp_types() -> list[tuple[str, str]]:
        """(vp_type, label) pairs for building a palette / dock."""

        return [(e["type"], e["label"]) for e in node_schema()]

    def core_node(self, node_id: str) -> Node | None:
        return next((n for n in self._nodes if n.id == node_id), None)

    def index_of(self, node_id: str) -> int:
        return next(i for i, n in enumerate(self._nodes) if n.id == node_id)

    # -- mutation ----------------------------------------------------------
    def add_node(
        self,
        vp_type: str,
        node_id: str | None = None,
        params: dict | None = None,
    ) -> Node:
        node = create_node(vp_type, node_id or self._unique_id(vp_type), params=params)
        self._nodes.append(node)
        return node

    def connect(self, from_id: str, from_port: str, to_id: str, to_port: str) -> None:
        self._conns.append((from_id, from_port, to_id, to_port))

    def clear(self) -> None:
        self._nodes.clear()
        self._conns.clear()
        self._counters.clear()

    # -- build / load executable graph ------------------------------------
    def to_core_graph(self) -> Graph:
        """Rebuild a fresh, runnable ``core.Graph`` from the current state."""

        graph = Graph()
        for node in self._nodes:
            graph.add_node(node)
        for conn in self._conns:
            graph.connect(*conn)
        return graph

    def load_core_graph(self, core_graph: Graph) -> None:
        """Replace current state from a loaded ``core.Graph`` (order preserved)."""

        self.clear()
        self._nodes = list(core_graph.nodes.values())  # dicts keep insertion order
        self._conns = [
            (c.from_node, c.from_port, c.to_node, c.to_port)
            for c in core_graph.connections
        ]

    # -- helpers -----------------------------------------------------------
    def _unique_id(self, vp_type: str) -> str:
        stem = vp_type.split("/")[-1].lower()
        self._counters[stem] = self._counters.get(stem, 0) + 1
        return f"{stem}_{self._counters[stem]}"
