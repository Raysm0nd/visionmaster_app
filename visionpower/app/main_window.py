"""Frameless main window shell for VisionPower (AXON redesign).

Layout rows: title bar (46) · toolbar (54) · body (dock 56 | canvas | right 542)
· status bar (30). This phase establishes the shell + window controls; the
canvas, left dock, and right panels are filled in by later phases, and engine
wiring (run / preview / save-load) is connected last.
"""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from visionpower.app import constants, theme
from visionpower.app.graph_bridge import GraphBridge
from visionpower.app.title_bar import TitleBar
from visionpower.app.toolbar import Toolbar


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

    # -- body (placeholders filled by later phases) ------------------------
    def _build_body(self) -> QtWidgets.QWidget:
        body = QtWidgets.QWidget()
        grid = QtWidgets.QHBoxLayout(body)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        self.dock_holder = self._placeholder(constants.DOCK_W, theme.BG_DOCK)
        self.canvas_holder = self._placeholder(0, theme.BG_CANVAS)
        self.right_holder = self._placeholder(constants.RIGHT_W, theme.BG_PANEL)

        grid.addWidget(self.dock_holder)
        grid.addWidget(self.canvas_holder, stretch=1)
        grid.addWidget(self.right_holder)
        return body

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
