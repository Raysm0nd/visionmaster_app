"""Core data types that flow on graph edges.

Design note: a machine-vision pipeline does not just pass a bare image between
steps — it passes an image *plus* context (ROI, results, verdict, metadata).
We model that as a small set of typed values; ``Image`` additionally carries a
free-form ``meta`` dict (source filename, etc.). Heavier per-pixel coordinate
frames can be layered on later without changing the port system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class PixelFormat(str, Enum):
    """Pixel layout of an :class:`Image`. Stored as a string for easy JSON."""

    GRAY = "gray"
    BGR = "bgr"
    BGRA = "bgra"


@dataclass
class Image:
    """An image buffer plus its pixel format and arbitrary metadata.

    ``data`` is a NumPy array shaped ``(H, W)`` for GRAY or ``(H, W, C)``.
    """

    data: np.ndarray
    fmt: PixelFormat = PixelFormat.BGR
    meta: dict = field(default_factory=dict)

    @property
    def height(self) -> int:
        return int(self.data.shape[0])

    @property
    def width(self) -> int:
        return int(self.data.shape[1])

    @property
    def channels(self) -> int:
        return 1 if self.data.ndim == 2 else int(self.data.shape[2])


@dataclass
class Region:
    """A rectangular region of interest (x, y, w, h) in pixel coordinates.

    Polygon/rotated regions can be added later as additional fields.
    """

    x: int
    y: int
    w: int
    h: int


@dataclass
class Measurement:
    """Named scalar measurement results (e.g. ``{"area": 1234.0}``)."""

    values: dict[str, float] = field(default_factory=dict)


@dataclass
class DetectionItem:
    """A single detected object: bounding box + optional label/score/area."""

    bbox: tuple[int, int, int, int]  # x, y, w, h
    label: str = ""
    score: float = 1.0
    area: float = 0.0


@dataclass
class Detection:
    """A set of detected items produced by an analysis node."""

    items: list[DetectionItem] = field(default_factory=list)

    def __len__(self) -> int:  # convenience for verdict logic / tests
        return len(self.items)


@dataclass
class Verdict:
    """Pass/fail decision with human-readable reasons for traceability."""

    ok: bool
    reasons: list[str] = field(default_factory=list)
