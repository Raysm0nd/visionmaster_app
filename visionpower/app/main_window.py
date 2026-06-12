"""Frameless main window shell for VisionPower (AXON redesign).

Layout rows: title bar (46) · toolbar (54) · body (dock 56 | canvas | right 542)
· status bar (30). This phase establishes the shell + window controls; the
canvas, left dock, and right panels are filled in by later phases, and engine
wiring (run / preview / save-load) is connected last.
"""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

import visionpower.nodes  # noqa: F401  (populate the node registry)
from visionpower.app import constants, theme
from visionpower.app.canvas import NodeCanvas, NodeView
from visionpower.app.demo_flow import build_demo_flow
from visionpower.app.dock import Dock
from visionpower.app.graph_bridge import GraphBridge
from visionpower.app.panels import RightPanel
from visionpower.app.title_bar import TitleBar
from visionpower.app.toolbar import Toolbar

# Core category → card glyph for the canvas.
_GLYPH_BY_CATEGORY = {
    "sources": "image",
    "filters": "bucket",
    "analysis": "blob",
    "sinks": "send",
}


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VisionPower")
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.resize(1440, 902)

        self.bridge = GraphBridge()
        self._maximized = False

        central = QtWidgets.QWidget()
        central.setStyleSheet(f"background:{theme.BG};")
        col = QtWidgets.QVBoxLayout(central)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)

        self.title_bar = TitleBar()
        self.toolbar = Toolbar()
        col.addWidget(self.title_bar)
        col.addWidget(self.toolbar)
        col.addWidget(self._build_body(), stretch=1)
        col.addWidget(self._build_status_bar())

        self.setCentralWidget(central)

        # window controls
        self.title_bar.minimizeClicked.connect(self.showMinimized)
        self.title_bar.maximizeClicked.connect(self.toggle_max)
        self.title_bar.closeClicked.connect(self.close)

        # seed with the demo pipeline so the canvas has content (engine wiring
        # — selection / run / preview — is connected in Phase 6).
        build_demo_flow(self.bridge)
        self._refresh_canvas_nodes()

    # -- body (canvas placeholder filled in Phase 5) -----------------------
    def _build_body(self) -> QtWidgets.QWidget:
        body = QtWidgets.QWidget()
        grid = QtWidgets.QHBoxLayout(body)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        self.dock = Dock()
        self.canvas = NodeCanvas()
        self.right_panel = RightPanel()
        self.right_panel.setFixedWidth(constants.RIGHT_W)

        grid.addWidget(self.dock)
        grid.addWidget(self.canvas, stretch=1)
        grid.addWidget(self.right_panel)
        return body

    def _refresh_canvas_nodes(self) -> None:
        """Build canvas NodeViews from the bridge's ordered core nodes."""

        views = []
        for i, node in enumerate(self.bridge.nodes):
            color = theme.NODE_COLORS[i % len(theme.NODE_COLORS)]
            glyph = _GLYPH_BY_CATEGORY.get(node.CATEGORY, "image")
            views.append(NodeView(
                id=node.id, index=i + 1,
                name=node.LABEL or node.NODE_TYPE, color=color, glyph=glyph,
            ))
        self.canvas.set_nodes(views)

    @staticmethod
    def _placeholder(width: int, bg: str) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        if width:
            w.setFixedWidth(width)
        w.setStyleSheet(f"background:{bg};")
        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        return w

    def _build_status_bar(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(constants.STATUS_H)
        bar.setStyleSheet(
            f"background:{theme.BG_PANEL};"
            f"border-top:1px solid rgba(255,255,255,0.06);"
        )
        lay = QtWidgets.QHBoxLayout(bar)
        lay.setContentsMargins(14, 0, 14, 0)
        self.status_label = QtWidgets.QLabel("就緒")
        self.status_label.setStyleSheet(f"color:{theme.TEXT_DIM};font-size:11px;")
        lay.addWidget(self.status_label)
        lay.addStretch(1)
        return bar

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

    # -- window controls ---------------------------------------------------
    def toggle_max(self) -> bool:
        self._maximized = not self._maximized
        if self._maximized:
            self.showMaximized()
        else:
            self.showNormal()
        return self._maximized
