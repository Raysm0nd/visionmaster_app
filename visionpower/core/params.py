"""Parameter specifications.

A ``ParamSpec`` is the single source of truth for a node parameter. It drives:
  - the auto-generated property panel (type -> widget; range -> slider/spinbox),
  - serialization round-trips (coercion of loaded values),
  - validation, and
  - the machine-readable node schema consumed by the future LLM layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ParamType(str, Enum):
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    CHOICE = "choice"
    PATH = "path"


@dataclass
class ParamSpec:
    name: str
    type: ParamType
    default: Any
    min: float | None = None
    max: float | None = None
    step: float | None = None
    choices: list[str] | None = None
    description: str = ""

    def coerce(self, value: Any) -> Any:
        """Coerce + clamp/validate ``value`` to this spec's type and range."""

        if value is None:
            return self.default
        if self.type is ParamType.INT:
            v = int(value)
            return int(self._clamp(v))
        if self.type is ParamType.FLOAT:
            v = float(value)
            return float(self._clamp(v))
        if self.type is ParamType.BOOL:
            return bool(value)
        if self.type is ParamType.CHOICE:
            v = str(value)
            if self.choices and v not in self.choices:
                raise ValueError(
                    f"param '{self.name}': {v!r} not in choices {self.choices}"
                )
            return v
        # STRING / PATH
        return str(value)

    def _clamp(self, v: float) -> float:
        if self.min is not None:
            v = max(self.min, v)
        if self.max is not None:
            v = min(self.max, v)
        return v

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type.value,
            "default": self.default,
            "min": self.min,
            "max": self.max,
            "step": self.step,
            "choices": self.choices,
            "description": self.description,
        }
