"""Shared rendering helpers (OpenCV/NumPy, no Qt).

Used by the Viewer node to bake overlays and by the UI preview to turn any
``Image`` into a displayable BGR buffer. Kept out of ``core`` because it pulls
in OpenCV, but it is still UI-framework agnostic.
"""

from __future__ import annotations

import cv2
import numpy as np

from visionpower.core.types import Detection, Image, PixelFormat, Verdict


def to_display_bgr(image: Image) -> np.ndarray:
    """Return a contiguous uint8 BGR array suitable for display/overlay."""

    data = image.data
    if data.dtype != np.uint8:
        data = np.clip(data, 0, 255).astype(np.uint8)
    if image.fmt is PixelFormat.GRAY or data.ndim == 2:
        return cv2.cvtColor(data, cv2.COLOR_GRAY2BGR)
    if image.fmt is PixelFormat.BGRA or (data.ndim == 3 and data.shape[2] == 4):
        return cv2.cvtColor(data, cv2.COLOR_BGRA2BGR)
    return np.ascontiguousarray(data)


def draw_overlay(
    bgr: np.ndarray,
    detection: Detection | None = None,
    verdict: Verdict | None = None,
) -> np.ndarray:
    """Draw detection boxes and a pass/fail banner onto a copy of ``bgr``."""

    out = bgr.copy()
    if detection is not None:
        for item in detection.items:
            x, y, w, h = item.bbox
            cv2.rectangle(out, (x, y), (x + w, y + h), (0, 0, 255), 2)
            if item.label:
                cv2.putText(
                    out,
                    item.label,
                    (x, max(0, y - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    1,
                    cv2.LINE_AA,
                )
    if verdict is not None:
        color = (0, 200, 0) if verdict.ok else (0, 0, 255)
        text = "OK" if verdict.ok else "NG"
        cv2.putText(
            out, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2, cv2.LINE_AA
        )
    return out
