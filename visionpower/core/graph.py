"""The workflow graph: nodes + typed connections, with validation.

Connections are validated on creation (ports exist, types compatible, one
source per input port). Cycle detection lives in :meth:`topo_order`.
"""

from __future__ import annotations

from dataclasses import dataclass

from visionpower.core.node import Node
from visionpower.core.ports import ports_compatible


@dataclass(frozen=True)
class Connection:
    from_node: str
    from_port: str
    to_node: str
    to_port: str


class Graph:
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.connections: list[Connection] = []

    # -- mutation ----------------------------------------------------------
    def add_node(self, node: Node) -> Node:
        if node.id in self.nodes:
            raise ValueError(f"duplicate node id: {node.id!r}")
        self.nodes[node.id] = node
        return node

    def remove_node(self, node_id: str) -> None:
        self.nodes.pop(node_id, None)
        self.connections = [
            c
            for c in self.connections
            if c.from_node != node_id and c.to_node != node_id
        ]

    def connect(
        self, from_node: str, from_port: str, to_node: str, to_port: str
    ) -> Connection:
        src = self._require_node(from_node)
        dst = self._require_node(to_node)
        out_port = src.output_port(from_port)
        in_port = dst.input_port(to_port)
        if out_port is None:
            raise ValueError(f"{src.NODE_TYPE} has no output port {from_port!r}")
        if in_port is None:
            raise ValueError(f"{dst.NODE_TYPE} has no input port {to_port!r}")
        if not ports_compatible(out_port.type, in_port.type):
            raise TypeError(
                f"incompatible connection: {from_node}.{from_port}"
                f" ({out_port.type.value}) -> {to_node}.{to_port}"
                f" ({in_port.type.value})"
            )
        # one source per input port: replace any existing connection
        self.connections = [
            c
            for c in self.connections
            if not (c.to_node == to_node and c.to_port == to_port)
        ]
        conn = Connection(from_node, from_port, to_node, to_port)
        self.connections.append(conn)
        return conn

    def disconnect(self, to_node: str, to_port: str) -> None:
        self.connections = [
            c
            for c in self.connections
            if not (c.to_node == to_node and c.to_port == to_port)
        ]

    # -- queries -----------------------------------------------------------
    def inputs_of(self, node_id: str) -> dict[str, tuple[str, str]]:
        """Map each connected input port name -> (source_node_id, source_port)."""

        return {
            c.to_port: (c.from_node, c.from_port)
            for c in self.connections
            if c.to_node == node_id
        }

    def topo_order(self) -> list[str]:
        """Return node ids in dependency order. Raises on a cycle."""

        indeg = {nid: 0 for nid in self.nodes}
        adj: dict[str, list[str]] = {nid: [] for nid in self.nodes}
        for c in self.connections:
            adj[c.from_node].append(c.to_node)
            indeg[c.to_node] += 1
        queue = [nid for nid, d in indeg.items() if d == 0]
        order: list[str] = []
        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for nxt in adj[nid]:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    queue.append(nxt)
        if len(order) != len(self.nodes):
            raise ValueError("graph has a cycle")
        return order

    def validate(self) -> list[str]:
        """Return a list of human-readable problems (empty == valid)."""

        errors: list[str] = []
        try:
            self.topo_order()
        except ValueError as exc:
            errors.append(str(exc))
        for node in self.nodes.values():
            connected = self.inputs_of(node.id)
            for port in node.INPUTS:
                if not port.optional and port.name not in connected:
                    errors.append(
                        f"{node.id} ({node.NODE_TYPE}): required input"
                        f" {port.name!r} is not connected"
                    )
        return errors

    def _require_node(self, node_id: str) -> Node:
        if node_id not in self.nodes:
            raise KeyError(f"no such node: {node_id!r}")
        return self.nodes[node_id]
