"""Node registry: discovery, construction, and machine-readable schema export.

The ``@register_node`` decorator records each node class under its NODE_TYPE.
``node_schema()`` exports every node's full description (ports + params) — one
artifact that powers the UI palette, the property panel, connection validation,
and the future LLM-assisted workflow design.
"""

from __future__ import annotations

from typing import Any

from visionpower.core.node import Node

_REGISTRY: dict[str, type[Node]] = {}


def register_node(cls: type[Node]) -> type[Node]:
    """Class decorator that registers ``cls`` under its ``NODE_TYPE``.

    If ``NODE_TYPE`` is blank it is derived as ``"{CATEGORY}/{ClassName}"``.
    """

    if not cls.NODE_TYPE:
        name = cls.__name__.removesuffix("Node")
        cls.NODE_TYPE = f"{cls.CATEGORY}/{name}" if cls.CATEGORY else name
    if cls.NODE_TYPE in _REGISTRY:
        raise ValueError(f"duplicate NODE_TYPE: {cls.NODE_TYPE!r}")
    _REGISTRY[cls.NODE_TYPE] = cls
    return cls


def get_node_class(node_type: str) -> type[Node]:
    try:
        return _REGISTRY[node_type]
    except KeyError:
        raise KeyError(f"unregistered node type: {node_type!r}") from None


def create_node(
    node_type: str,
    node_id: str,
    params: dict[str, Any] | None = None,
    pos: tuple[float, float] = (0.0, 0.0),
) -> Node:
    return get_node_class(node_type)(node_id, params=params, pos=pos)


def registered_types() -> list[str]:
    return sorted(_REGISTRY)


def node_schema() -> list[dict]:
    """Return a JSON-serializable description of every registered node type."""

    schema: list[dict] = []
    for node_type in registered_types():
        cls = _REGISTRY[node_type]
        schema.append(
            {
                "type": node_type,
                "category": cls.CATEGORY,
                "label": cls.LABEL or node_type,
                "inputs": [p.to_dict() for p in cls.INPUTS],
                "outputs": [p.to_dict() for p in cls.OUTPUTS],
                "params": [p.to_dict() for p in cls.PARAMS],
            }
        )
    return schema
