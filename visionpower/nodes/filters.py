"""Filter nodes: per-pixel / neighbourhood image transforms (image -> image)."""

from __future__ import annotations

import cv2

from visionpower.core.node import Node, NodeContext
from visionpower.core.params import ParamSpec, ParamType
from visionpower.core.ports import Port, PortType
from visionpower.core.registry import register_node
from visionpower.core.types import Image, PixelFormat


@register_node
class GrayscaleNode(Node):
    NODE_TYPE = "filters/Grayscale"
    CATEGORY = "filters"
    LABEL = "Grayscale"
    INPUTS = [Port("image", PortType.IMAGE)]
    OUTPUTS = [Port("image", PortType.IMAGE)]
    PARAMS: list[ParamSpec] = []

    def run(self, ctx: NodeContext, inputs: dict) -> dict:
        image: Image = inputs["image"]
        if image.fmt is PixelFormat.GRAY or image.data.ndim == 2:
            return {"image": image}
        gray = cv2.cvtColor(image.data, cv2.COLOR_BGR2GRAY)
        return {"image": Image(gray, PixelFormat.GRAY, dict(image.meta))}


@register_node
class GaussianBlurNode(Node):
    NODE_TYPE = "filters/GaussianBlur"
    CATEGORY = "filters"
    LABEL = "Gaussian Blur"
    INPUTS = [Port("image", PortType.IMAGE)]
    OUTPUTS = [Port("image", PortType.IMAGE)]
    PARAMS = [
        ParamSpec("ksize", ParamType.INT, 5, min=1, max=99, step=2,
                  description="Kernel size (forced odd)"),
        ParamSpec("sigma", ParamType.FLOAT, 0.0, min=0.0, max=50.0, step=0.1,
                  description="Gaussian sigma (0 = derived from ksize)"),
    ]

    def run(self, ctx: NodeContext, inputs: dict) -> dict:
        image: Image = inputs["image"]
        k = max(1, int(self.param("ksize")))
        if k % 2 == 0:
            k += 1
        blurred = cv2.GaussianBlur(image.data, (k, k), float(self.param("sigma")))
        return {"image": Image(blurred, image.fmt, dict(image.meta))}


@register_node
class ThresholdNode(Node):
    NODE_TYPE = "filters/Threshold"
    CATEGORY = "filters"
    LABEL = "Threshold"
    INPUTS = [Port("image", PortType.IMAGE)]
    OUTPUTS = [Port("image", PortType.IMAGE)]
    PARAMS = [
        ParamSpec("thresh", ParamType.INT, 127, min=0, max=255,
                  description="Threshold value (ignored when Otsu is on)"),
        ParamSpec("maxval", ParamType.INT, 255, min=0, max=255,
                  description="Value assigned to pixels above threshold"),
        ParamSpec("type", ParamType.CHOICE, "binary",
                  choices=["binary", "binary_inv", "trunc", "tozero", "tozero_inv"],
                  description="Thresholding mode"),
        ParamSpec("otsu", ParamType.BOOL, False,
                  description="Auto-pick threshold via Otsu's method"),
    ]

    _MODES = {
        "binary": cv2.THRESH_BINARY,
        "binary_inv": cv2.THRESH_BINARY_INV,
        "trunc": cv2.THRESH_TRUNC,
        "tozero": cv2.THRESH_TOZERO,
        "tozero_inv": cv2.THRESH_TOZERO_INV,
    }

    def run(self, ctx: NodeContext, inputs: dict) -> dict:
        image: Image = inputs["image"]
        data = image.data
        if data.ndim == 3:
            data = cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)
        flag = self._MODES[self.param("type")]
        if self.param("otsu"):
            flag |= cv2.THRESH_OTSU
        _, out = cv2.threshold(
            data, int(self.param("thresh")), int(self.param("maxval")), flag
        )
        return {"image": Image(out, PixelFormat.GRAY, dict(image.meta))}
