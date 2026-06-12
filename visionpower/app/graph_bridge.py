"""Bridge between the NodeGraphQt visual scene and the pure ``core.Graph``.

Strategy: the visual scene + a per-node ``core.Node`` (holding parameters) are
the source of truth. The executable ``core.Graph`` is rebuilt on demand from the
scene right before each run. This avoids fragile incremental signal syncing.

One NodeGraphQt node class is generated per registered core node type, with
ports matching the core schema, so connection validity is visually constrained.
"""

from __future__ import annotations

from NodeGraphQt import BaseNode, NodeGraph

from visionpower.core import Graph, Node, create_node, node_schema

_IDENTIFIER = "visionpower"


def _safe(vp_type: str) -> str:
    return vp_type.replace("/", "_").replace("-", "_")


class GraphBridge:
    def __init__(self, ng_graph: NodeGraph) -> None:
        self.ng = ng_graph
        self.core_nodes: dict[str, Node] = {}  # ng node id -> core Node
        self._vp_by_ngtype: dict[str, str] = {}
        self._ngtype_by_vp: dict[str, str] = {}
        self._register_all()
        self.ng.node_created.connect(self._on_node_created)

    # -- registration ------------------------------------------------------
    def _register_all(self) -> None:
        for entry in node_schema():
            cls = self._make_class(entry)
            self.ng.register_node(cls)
            ng_type = f"{_IDENTIFIER}.{cls.__name__}"
            self._vp_by_ngtype[ng_type] = entry["type"]
            self._ngtype_by_vp[entry["type"]] = ng_type

    @staticmethod
    def _make_class(entry: dict) -> type[BaseNode]:
        inputs = entry["inputs"]
        outputs = entry["outputs"]
        label = entry["label"]

        class _VPNode(BaseNode):
            __identifier__ = _IDENTIFIER
            NODE_NAME = label

            def __init__(self) -> None:
                super().__init__()
                for port in inputs:
                    self.add_input(port["name"], multi_input=False)
                for port in outputs:
                    self.add_output(port["name"], multi_output=True)

        _VPNode.__name__ = "NG_" + _safe(entry["type"])
        _VPNode.__qualname__ = _VPNode.__name__
        return _VPNode

    def vp_types(self) -> list[tuple[str, str]]:
        """(vp_type, label) pairs for building a palette."""

        return [(e["type"], e["label"]) for e in node_schema()]

    # -- scene mutation ----------------------------------------------------
    def add_node(self, vp_type: str, pos=(0.0, 0.0)):
        ng_type = self._ngtype_by_vp[vp_type]
        return self.ng.create_node(ng_type, pos=list(pos))

    def _on_node_created(self, ng_node) -> None:
        vp_type = self._vp_by_ngtype.get(ng_node.type_)
        if vp_type is None:
            return  # e.g. a backdrop node
        self.core_nodes[ng_node.id] = create_node(
            vp_type, ng_node.id, pos=tuple(ng_node.pos())
        )

    def core_node_for(self, ng_node) -> Node | None:
        return self.core_nodes.get(ng_node.id)

    # -- build executable graph -------------------------------------------
    def to_core_graph(self) -> Graph:
        """Rebuild a fresh ``core.Graph`` from the current visual scene."""

        graph = Graph()
        for ng_node in self.ng.all_nodes():
            core = self.core_nodes.get(ng_node.id)
            if core is None:
                continue
            core.pos = tuple(ng_node.pos())
            graph.add_node(core)
        for ng_node in self.ng.all_nodes():
            if ng_node.id not in self.core_nodes:
                continue
            for in_name, in_port in ng_node.inputs().items():
                for out_port in in_port.connected_ports():
                    src = out_port.node()
                    if src.id not in self.core_nodes:
                        continue
                    graph.connect(src.id, out_port.name(), ng_node.id, in_name)
        return graph

    # -- load a saved graph into the scene --------------------------------
    def load_core_graph(self, core_graph: Graph) -> None:
        self.ng.clear_session()
        self.core_nodes.clear()

        id_map = {}  # file node id -> ng node
        for core in core_graph.nodes.values():
            ng_type = self._ngtype_by_vp[core.NODE_TYPE]
            ng_node = self.ng.create_node(ng_type, name=core.id, pos=list(core.pos))
            id_map[core.id] = ng_node

        # node_created populated core_nodes with fresh nodes; replace with loaded
        self.core_nodes.clear()
        for file_id, ng_node in id_map.items():
            loaded = core_graph.nodes[file_id]
            loaded.id = ng_node.id
            self.core_nodes[ng_node.id] = loaded

        for conn in core_graph.connections:
            src = id_map[conn.from_node]
            dst = id_map[conn.to_node]
            src.get_output(conn.from_port).connect_to(dst.get_input(conn.to_port))
