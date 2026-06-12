"""Node base class and execution context/result types.

A node is a pure, stateless transformation: given its parameters and the values
on its input ports, it produces values on its output ports. Statelessness is
what makes runs reproducible and caching safe.

Subclasses declare ``INPUTS`` / ``OUTPUTS`` / ``PARAMS`` as class attributes and
implement :meth:`run`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from visionpower.core.params import ParamSpec
from visionpower.core.ports import Port


@dataclass
class NodeContext:
    """Shared, read-only-ish context passed to every node during a run."""

    log: Callable[[str], None] = lambda msg: None
    meta: dict = field(default_factory=dict)


@dataclass
class NodeResult:
    """Outcome of executing one node: outputs, timing, error, cache status."""

    node_id: str
    outputs: dict[str, Any]
    elapsed_ms: float = 0.0
    error: str | None = None
    cached: bool = False

    @property
    def ok(self) -> bool:
        return self.error is None


class Node:
    """Base class for all processing nodes.

    Class attributes (override in subclasses):
        NODE_TYPE: stable id, e.g. ``"filters/Grayscale"``. Set automatically by
            the ``@register_node`` decorator from CATEGORY/LABEL if left blank.
        CATEGORY:  palette grouping, e.g. ``"filters"``.
        LABEL:     human-readable name shown in the UI.
        INPUTS / OUTPUTS: list[Port].
        PARAMS:    list[ParamSpec].
    """

    NODE_TYPE: str = ""
    CATEGORY: str = ""
    LABEL: str = ""
    INPUTS: list[Port] = []
    OUTPUTS: list[Port] = []
    PARAMS: list[ParamSpec] = []

    def __init__(
        self,
        node_id: str,
        params: dict[str, Any] | None = None,
        pos: tuple[float, float] = (0.0, 0.0),
    ) -> None:
        self.id = node_id
        self.pos = (float(pos[0]), float(pos[1]))  # UI layout only; not in exec signature
        self.params: dict[str, Any] = {p.name: p.default for p in self.PARAMS}
        if params:
            for key, value in params.items():
                self.set_param(key, value)

    # -- parameters --------------------------------------------------------
    @classmethod
    def param_specs(cls) -> dict[str, ParamSpec]:
        return {p.name: p for p in cls.PARAMS}

    def set_param(self, name: str, value: Any) -> None:
        specs = self.param_specs()
        if name not in specs:
            raise KeyError(f"{self.NODE_TYPE}: unknown param {name!r}")
        self.params[name] = specs[name].coerce(value)

    def param(self, name: str) -> Any:
        return self.params[name]

    # -- ports -------------------------------------------------------------
    @classmethod
    def input_port(cls, name: str) -> Port | None:
        return next((p for p in cls.INPUTS if p.name == name), None)

    @classmethod
    def output_port(cls, name: str) -> Port | None:
        return next((p for p in cls.OUTPUTS if p.name == name), None)

    # -- execution ---------------------------------------------------------
    def run(self, ctx: NodeContext, inputs: dict[str, Any]) -> dict[str, Any]:
        """Transform ``inputs`` (keyed by input port name) into outputs.

        Must return a dict keyed by output port name. Override in subclasses.
        """

        raise NotImplementedError

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<{type(self).__name__} id={self.id!r} type={self.NODE_TYPE!r}>"
