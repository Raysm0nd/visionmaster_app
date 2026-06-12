"""Sink nodes: visualize / collect results at the end of a flow."""

from __future__ import annotations

from visionpower.core.node import Node, NodeContext
from visionpower.core.params import ParamSpec
from visionpower.core.ports import Port, PortType
from visionpower.core.registry import register_node
from visionpower.core.types import Detection, Image, PixelFormat, Verdict
from visionpower.render import draw_overlay, to_display_bgr


@register_node
class ViewerNode(Node):
    NODE_TYPE = "sinks/Viewer"
    CATEGORY = "sinks"
    LABEL = "Viewer"
    INPUTS = [
        Port("image", PortType.IMAGE),
        Port("detections", PortType.DETECTION, optional=True),
        Port("verdict", PortType.VERDICT, optional=True),
    ]
    OUTPUTS = [Port("image", PortType.IMAGE, description="Image with overlays baked in")]
    PARAMS: list[ParamSpec] = []

    def run(self, ctx: NodeContext, inputs: dict) -> dict:
        image: Image = inputs["image"]
        detections: Detection | None = inputs.get("detections")
        verdict: Verdict | None = inputs.get("verdict")
        bgr = to_display_bgr(image)
        overlaid = draw_overlay(bgr, detections, verdict)
        meta = dict(image.meta)
        if verdict is not None:
            meta["verdict_ok"] = verdict.ok
        return {"image": Image(overlaid, PixelFormat.BGR, meta)}
