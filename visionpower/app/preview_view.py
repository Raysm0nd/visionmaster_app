"""Image preview — checkerboard backdrop, real OpenCV frame, scan overlay.

Shows the selected node's actual image output (via :meth:`show_bgr`). Prev/next
chevrons emit signals so the host can step an ImageSource. While the flow runs,
a scanning band animates over the frame (set via :meth:`set_running`).
"""

from __future__ import annotations

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from visionpower.app import icons, theme


class PreviewView(QtWidgets.QWidget):
    prevImage = QtCore.Signal()
    nextImage = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QtGui.QPixmap | None = None
        self._message = "執行流程後顯示"
        self._running = False
        self._scan_y = 0.0
        self._filename = ""
        self._dims = ""

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)

        self.prev_btn = self._chevron("chevleft")
        self.next_btn = self._chevron("chevright")
        self.prev_btn.clicked.connect(self.prevImage)
        self.next_btn.clicked.connect(self.nextImage)

        self._footer = QtWidgets.QLabel("")
        self._footer.setStyleSheet(
            f"color:{theme.TEXT_DIM};font-family:'{theme.FONT_MONO}',monospace;"
            f"font-size:10px;background:transparent;"
        )

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_stage(), stretch=1)
        footer_bar = QtWidgets.QWidget()
        fb = QtWidgets.QHBoxLayout(footer_bar)
        fb.setContentsMargins(14, 8, 14, 8)
        fb.addWidget(self._footer)
        fb.addStretch(1)
        footer_bar.setStyleSheet("border-top:1px solid rgba(255,255,255,0.05);")
        outer.addWidget(footer_bar)

    # -- public API --------------------------------------------------------
    def show_bgr(self, bgr: np.ndarray, filename: str = "") -> None:
        if bgr.ndim == 2:
            bgr = np.stack([bgr] * 3, axis=-1)
        rgb = np.ascontiguousarray(bgr[:, :, ::-1])
        h, w = rgb.shape[:2]
        image = QtGui.QImage(rgb.data, w, h, 3 * w, QtGui.QImage.Format_RGB888)
        self._pixmap = QtGui.QPixmap.fromImage(image.copy())
        self._filename = filename
        self._dims = f"{w} × {h}"
        self._footer.setText(f"{filename}    {self._dims}" if filename else self._dims)
        self._stage.update()

    def clear(self, message: str = "尚無預覽") -> None:
        self._pixmap = None
        self._message = message
        self._footer.setText("")
        self._stage.update()

    def set_running(self, running: bool) -> None:
        self._running = running
        if running:
            self._scan_y = 0.0
            self._timer.start(33)
        else:
            self._timer.stop()
        self._stage.update()

    # -- internals ---------------------------------------------------------
    def _tick(self) -> None:
        self._scan_y = (self._scan_y + 0.02) % 1.0
        self._stage.update()

    def _build_stage(self) -> QtWidgets.QWidget:
        stage = _Stage(self)
        self._stage = stage
        lay = QtWidgets.QHBoxLayout(stage)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.addWidget(self.prev_btn, alignment=QtCore.Qt.AlignVCenter)
        lay.addStretch(1)
        lay.addWidget(self.next_btn, alignment=QtCore.Qt.AlignVCenter)
        return stage

    def _chevron(self, name: str) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton()
        btn.setIcon(icons.make_icon(name, "#FFFFFF", 18))
        btn.setIconSize(QtCore.QSize(18, 18))
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setFixedSize(32, 32)
        btn.setStyleSheet(
            "QPushButton{background:rgba(0,0,0,0.45);border:none;border-radius:16px;}"
            "QPushButton:hover{background:rgba(0,0,0,0.7);}"
        )
        return btn


class _Stage(QtWidgets.QWidget):
    """Paints the checkerboard, the centred frame, and the scan overlay."""

    def __init__(self, view: PreviewView) -> None:
        super().__init__(view)
        self._view = view

    def paintEvent(self, _event: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        self._paint_checker(p)
        view = self._view
        if view._pixmap is not None:
            pm = view._pixmap.scaled(
                self.size() * 0.82,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
            x = (self.width() - pm.width()) // 2
            y = (self.height() - pm.height()) // 2
            p.drawPixmap(x, y, pm)
            if view._running:
                self._paint_scan(p)
        else:
            p.setPen(QtGui.QColor(theme.TEXT_DIM))
            p.drawText(self.rect(), QtCore.Qt.AlignCenter, view._message)
        p.end()

    def _paint_checker(self, p: QtGui.QPainter) -> None:
        p.fillRect(self.rect(), QtGui.QColor("#181B22"))
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QColor("#13151B"))
        tile = 22
        for yy in range(0, self.height(), tile):
            for xx in range(0, self.width(), tile):
                if ((xx // tile) + (yy // tile)) % 2 == 0:
                    p.drawRect(xx, yy, tile, tile)

    def _paint_scan(self, p: QtGui.QPainter) -> None:
        band_h = 60
        y = int(self._view._scan_y * (self.height() + band_h)) - band_h
        grad = QtGui.QLinearGradient(0, y, 0, y + band_h)
        grad.setColorAt(0.0, QtGui.QColor(47, 128, 216, 0))
        grad.setColorAt(0.5, QtGui.QColor(47, 128, 216, 90))
        grad.setColorAt(1.0, QtGui.QColor(47, 128, 216, 0))
        p.fillRect(0, y, self.width(), band_h, grad)
