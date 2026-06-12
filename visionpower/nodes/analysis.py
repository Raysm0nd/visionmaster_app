"""Analysis nodes: turn images into structured results + pass/fail verdicts."""

from __future__ import annotations

import cv2

from visionpower.core.node import Node, NodeContext
from visionpower.core.params import ParamSpec, ParamType
from visionpower.core.ports import Port, PortType
from visionpower.core.registry import register_node
from visionpower.core.types import Detection, DetectionItem, Image, Verdict


@register_node
class FindContoursNode(Node):
    NODE_TYPE = "analysis/FindContours"
    CATEGORY = "analysis"
    LABEL = "Find Contours"
    INPUTS = [Port("image", PortType.IMAGE, description="Binary image")]
    OUTPUTS = [
        Port("detections", PortType.DETECTION),
        Port("verdict", PortType.VERDICT),
    ]
    PARAMS = [
        ParamSpec("min_area", ParamType.FLOAT, 100.0, min=0.0, max=1_000_000.0,
                  description="Ignore contours smaller than this area (px^2)"),
        ParamSpec("max_allowed", ParamType.INT, 0, min=0, max=10_000,
                  description="Verdict is NG when defect count exceeds this"),
    ]

    def run(self, ctx: NodeContext, inputs: dict) -> dict:
        image: Image = inputs["image"]
        data = image.data
        if data.ndim == 3:
            data = cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)
        contours, _ = cv2.findContours(
            data, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        min_area = float(self.param("min_area"))
        items: list[DetectionItem] = []
        for c in contours:
            area = float(cv2.contourArea(c))
            if area < min_area:
                continue
            x, y, w, h = cv2.boundingRect(c)
            items.append(
                DetectionItem(bbox=(x, y, w, h), label="defect", area=area)
            )
        max_allowed = int(self.param("max_allowed"))
        ok = len(items) <= max_allowed
        reasons = [] if ok else [f"found {len(items)} defects (allowed {max_allowed})"]
        return {
            "detections": Detection(items=items),
            "verdict": Verdict(ok=ok, reasons=reasons),
        }
