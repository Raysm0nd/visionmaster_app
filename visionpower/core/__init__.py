"""Pure-Python workflow engine. MUST NOT import Qt or any UI framework.

This package is the foundation shared by the desktop UI, the (future) headless
service, and the (future) LLM/agent layer. Keeping it Qt-free is what enables
headless batch execution and automated testing.
"""

from visionpower.core.graph import Connection, Graph
from visionpower.core.node import Node, NodeContext, NodeResult
from visionpower.core.params import ParamSpec, ParamType
from visionpower.core.ports import Port, PortType, ports_compatible
from visionpower.core.registry import (
    create_node,
    get_node_class,
    node_schema,
    register_node,
    registered_types,
)
from visionpower.core.scheduler import Scheduler
from visionpower.core.serialize import (
    SCHEMA_VERSION,
    graph_from_dict,
    graph_to_dict,
    load_graph,
    save_graph,
)
from visionpower.core.types import (
    Detection,
    DetectionItem,
    Image,
    Measurement,
    PixelFormat,
    Region,
    Verdict,
)

__all__ = [
    "Connection",
    "Graph",
    "Node",
    "NodeContext",
    "NodeResult",
    "ParamSpec",
    "ParamType",
    "Port",
    "PortType",
    "ports_compatible",
    "create_node",
    "get_node_class",
    "node_schema",
    "register_node",
    "registered_types",
    "Scheduler",
    "SCHEMA_VERSION",
    "graph_from_dict",
    "graph_to_dict",
    "load_graph",
    "save_graph",
    "Detection",
    "DetectionItem",
    "Image",
    "Measurement",
    "PixelFormat",
    "Region",
    "Verdict",
]
