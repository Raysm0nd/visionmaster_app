"""Image preview widget: zoom/pan QGraphicsView fed by a BGR ndarray.

Tracks the cursor and emits ``cursor_info(x, y, r, g, b)`` over image pixels —
shown in the info bar like VisionMaster's ``X,.. Y,.. R:.. G:.. B:..`` readout.
"""

from __future__ import annotations

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets


class PreviewView(QtWidgets.QGraphicsView):
    cursor_info = QtCore.Signal(int, int, int, int, int)  # x, y, r, g, b

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self._scene)
        self._item = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._item)
        self._bgr: np.ndarray | None = None
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setRenderHints(QtGui.QPainter.SmoothPixmapTransform)
        self.setBackgroundBrush(QtGui.QColor(26, 26, 26))
        self.setMouseTracking(True)
        self._placeholder("尚無預覽 — 執行流程後顯示")

    def show_bgr(self, bgr: np.ndarray) -> None:
        """Display a BGR (H,W,3) or grayscale (H,W) uint8 array."""

        if bgr.ndim == 2:
            bgr = np.stack([bgr] * 3, axis=-1)
        self._bgr = bgr
        rgb = np.ascontiguousarray(bgr[:, :, ::-1])
        h, w = rgb.shape[:2]
        image = QtGui.QImage(rgb.data, w, h, 3 * w, QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(image.copy())
        self._item.setPixmap(pix)
        self._scene.setSceneRect(QtCore.QRectF(pix.rect()))
        self.fitInView(self._item, QtCore.Qt.KeepAspectRatio)

    def clear(self, message: str = "尚無預覽") -> None:
        self._bgr = None
        self._placeholder(message)

    def _placeholder(self, message: str) -> None:
        pix = QtGui.QPixmap(480, 320)
        pix.fill(QtGui.QColor(26, 26, 26))
        painter = QtGui.QPainter(pix)
        painter.setPen(QtGui.QColor(150, 150, 150))
        painter.drawText(pix.rect(), QtCore.Qt.AlignCenter, message)
        painter.end()
        self._item.setPixmap(pix)
        self._scene.setSceneRect(QtCore.QRectF(pix.rect()))
        self.fitInView(self._item, QtCore.Qt.KeepAspectRatio)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(factor, factor)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        super().mouseMoveEvent(event)
        if self._bgr is None:
            return
        pt = self.mapToScene(event.position().toPoint())
        x, y = int(pt.x()), int(pt.y())
        h, w = self._bgr.shape[:2]
        if 0 <= x < w and 0 <= y < h:
            b, g, r = (int(v) for v in self._bgr[y, x])
            self.cursor_info.emit(x, y, r, g, b)
