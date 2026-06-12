"""Typed input/output ports and connection compatibility rules.

Port types let the graph validate connections statically (you cannot wire an
image output into a verdict input). ``ANY`` is an escape hatch for generic
sinks. The same type info feeds the UI and the future LLM layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PortType(str, Enum):
    IMAGE = "image"
    REGION = "region"
    MEASUREMENT = "measurement"
    DETECTION = "detection"
    VERDICT = "verdict"
    ANY = "any"


@dataclass(frozen=True)
class Port:
    """A named, typed port on a node.

    ``optional`` inputs may be left unconnected (their value is ``None`` at
    runtime) — used e.g. by a viewer that can overlay detections if present.
    """

    name: str
    type: PortType
    optional: bool = False
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type.value,
            "optional": self.optional,
            "description": self.description,
        }


def ports_compatible(source_type: PortType, target_type: PortType) -> bool:
    """True if an output of ``source_type`` may feed an input of ``target_type``."""

    return (
        source_type == target_type
        or source_type == PortType.ANY
        or target_type == PortType.ANY
    )
