"""Source nodes: bring images into the workflow."""

from __future__ import annotations

from pathlib import Path

import cv2

from visionpower.core.node import Node, NodeContext
from visionpower.core.params import ParamSpec, ParamType
from visionpower.core.ports import Port, PortType
from visionpower.core.registry import register_node
from visionpower.core.types import Image, PixelFormat


@register_node
class LoadImageNode(Node):
    NODE_TYPE = "sources/LoadImage"
    CATEGORY = "sources"
    LABEL = "Load Image"
    INPUTS: list[Port] = []
    OUTPUTS = [Port("image", PortType.IMAGE)]
    PARAMS = [
        ParamSpec("path", ParamType.PATH, "", description="Image file to load"),
    ]

    def run(self, ctx: NodeContext, inputs: dict) -> dict:
        path = self.param("path")
        if not path:
            raise ValueError("LoadImage: 'path' is empty")
        data = cv2.imread(path, cv2.IMREAD_COLOR)
        if data is None:
            raise ValueError(f"LoadImage: cannot read image: {path}")
        return {"image": Image(data, PixelFormat.BGR, {"source": path})}


@register_node
class ImageSourceNode(Node):
    """Multi-image source: a folder of images navigated by index.

    Mirrors VisionMaster's 圖像源 module — the UI thumbnail strip binds to this
    node, clicking a thumbnail sets ``index``, and "run all" iterates indices.
    """

    NODE_TYPE = "sources/ImageSource"
    CATEGORY = "sources"
    LABEL = "Image Source"
    INPUTS: list[Port] = []
    OUTPUTS = [Port("image", PortType.IMAGE)]
    PARAMS = [
        ParamSpec("folder", ParamType.PATH, "", description="Folder of images"),
        ParamSpec("pattern", ParamType.STRING, "*.png;*.jpg;*.jpeg;*.bmp;*.tif",
                  description="Semicolon-separated glob patterns"),
        ParamSpec("index", ParamType.INT, 0, min=0, max=1_000_000,
                  description="Which image of the folder to emit"),
    ]

    @staticmethod
    def list_files(folder: str, pattern: str) -> list[str]:
        """Sorted file list matching the semicolon-separated glob patterns."""

        base = Path(folder)
        if not folder or not base.is_dir():
            return []
        files: set[Path] = set()
        for pat in pattern.split(";"):
            pat = pat.strip()
            if pat:
                files.update(base.glob(pat))
        return sorted(str(f) for f in files)

    def files(self) -> list[str]:
        return self.list_files(self.param("folder"), self.param("pattern"))

    def run(self, ctx: NodeContext, inputs: dict) -> dict:
        files = self.files()
        if not files:
            raise ValueError(
                f"ImageSource: no images in {self.param('folder')!r}"
                f" matching {self.param('pattern')!r}"
            )
        idx = min(int(self.param("index")), len(files) - 1)
        path = files[idx]
        data = cv2.imread(path, cv2.IMREAD_COLOR)
        if data is None:
            raise ValueError(f"ImageSource: cannot read image: {path}")
        meta = {"source": path, "index": idx, "count": len(files)}
        return {"image": Image(data, PixelFormat.BGR, meta)}
