"""Frameless main window for VisionPower (AXON redesign).

Layout rows: title bar (46) · toolbar (54) · body (dock 56 | canvas | right 542)
· status bar (30). The custom canvas, dock, and right panel stay wired to the
real engine: selecting a node shows its params and image, the run buttons drive
the real Scheduler (with the canvas light-up animation on top), parameter edits
re-run incrementally, and flows save/load as JSON.
"""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

import visionpower.nodes  # noqa: F401  (populate the node registry)
from visionpower.app import constants, theme
from visionpower.app.canvas import NodeCanvas, NodeView
from visionpower.app.demo_flow import build_demo_flow
from visionpower.app.dock import Dock
from visionpower.app.graph_bridge import GraphBridge
from visionpower.app.panels import RightPanel
from visionpower.app.title_bar import TitleBar
from visionpower.app.toolbar import Toolbar
from visionpower.core import Scheduler, load_graph, save_graph
from visionpower.core.types import Image, Verdict
from visionpower.render import to_display_bgr

# Core category → card glyph for the canvas.
_GLYPH_BY_CATEGORY = {
    "sources": "image",
    "filters": "bucket",
    "analysis": "blob",
    "sinks": "send",
}

_DESIGN_SIZE = (1440, 902)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VisionPower")
        # Pure frameless: extra window-button hints make Windows draw native
        # caption buttons that overlap and swallow clicks on our custom controls.
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setMinimumSize(1024, 640)
        screen = QtGui.QGuiApplication.primaryScreen()
        if screen is not None:
            self.setGeometry(self._fitted_geometry(screen.availableGeometry()))
        else:
            self.resize(*_DESIGN_SIZE)

        self.bridge = GraphBridge()
        self.scheduler = Scheduler()
        self.results: dict = {}
        self._display_id: str | None = None
        self._maximized = False
        self._restore_geom: QtCore.QRect | None = None

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

        self._wire_signals()

        # seed with the demo pipeline so the canvas has content on launch.
        build_demo_flow(self.bridge)
        self._refresh_canvas_nodes()

    # -- body --------------------------------------------------------------
    def _build_body(self) -> QtWidgets.QWidget:
        body = QtWidgets.QWidget()
        grid = QtWidgets.QHBoxLayout(body)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)

        self.dock = Dock()
        self.canvas = NodeCanvas()
        self.right_panel = RightPanel()
        # Lock the dock + right panel: fixed width, no splitter/dock to drag.
        self.right_panel.setFixedWidth(constants.RIGHT_W)
        self.right_panel.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding
        )
        self.dock.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding
        )
        self.property_panel = self.right_panel.property_panel  # convenience alias

        grid.addWidget(self.dock)
        grid.addWidget(self.canvas, stretch=1)
        grid.addWidget(self.right_panel)
        return body

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
        version = QtWidgets.QLabel("VisionPower v0.2 · AXON")
        version.setStyleSheet(
            f"color:{theme.TEXT_FAINT};font-family:'{theme.FONT_MONO}',monospace;"
            f"font-size:10px;"
        )
        lay.addWidget(version)
        # corner grip: the only way to resize the frameless window (pure Qt).
        grip = QtWidgets.QSizeGrip(bar)
        grip.setFixedSize(14, 14)
        lay.addWidget(grip, 0, QtCore.Qt.AlignBottom)
        return bar

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

    # -- signal wiring -----------------------------------------------------
    def _wire_signals(self) -> None:
        # window controls
        self.title_bar.minimizeClicked.connect(self.showMinimized)
        self.title_bar.maximizeClicked.connect(self.toggle_max)
        self.title_bar.closeClicked.connect(self.close)
        # execution
        self.toolbar.runAll.connect(self.run_all)
        self.toolbar.runPartial.connect(self.run_partial)
        self.canvas.runFinished.connect(self._on_run_finished)
        # selection / params
        self.canvas.nodeSelected.connect(self._on_node_selected)
        self.right_panel.property_panel.param_changed.connect(self._on_param_changed)
        # image stepping
        self.right_panel.preview.prevImage.connect(lambda: self._step_image(-1))
        self.right_panel.preview.nextImage.connect(lambda: self._step_image(1))
        # save / load
        self.toolbar.saveClicked.connect(self._save_dialog)
        self.toolbar.openClicked.connect(self._load_dialog)

    # -- canvas model ------------------------------------------------------
    def _refresh_canvas_nodes(self) -> None:
        views = []
        for i, node in enumerate(self.bridge.nodes):
            color = theme.NODE_COLORS[i % len(theme.NODE_COLORS)]
            glyph = _GLYPH_BY_CATEGORY.get(node.CATEGORY, "image")
            views.append(NodeView(
                id=node.id, index=i + 1,
                name=node.LABEL or node.NODE_TYPE, color=color, glyph=glyph,
            ))
        self.canvas.set_nodes(views)

    # -- execution ---------------------------------------------------------
    def run_all(self) -> None:
        self._execute(0)

    def run_partial(self) -> None:
        start = self.canvas.selected_index if self.canvas.selected_index >= 0 else 0
        self._execute(start)

    def _execute(self, from_index: int) -> None:
        self.results = self.scheduler.run(self.bridge.to_core_graph())
        total = sum(
            self.results[n.id].elapsed_ms
            for n in self.bridge.nodes[from_index:]
            if n.id in self.results
        )
        self.canvas.set_run_time(f"{total:.2f}ms")
        if self._display_id is None and self.bridge.nodes:
            self._display_id = self.bridge.nodes[-1].id
        # results are ready synchronously; the canvas animation is cosmetic.
        self._update_preview_and_result()
        self.right_panel.preview.set_running(True)
        self.canvas.start_run(from_index)
        self.set_status("流程執行中…")

    def _on_run_finished(self) -> None:
        self.right_panel.preview.set_running(False)
        if self._display_id is None and self.bridge.nodes:
            self._display_id = self.bridge.nodes[-1].id
        self._update_preview_and_result()
        self.set_status(self._summary())

    # -- selection / params ------------------------------------------------
    def _on_node_selected(self, node_id: str) -> None:
        self._display_id = node_id
        self.right_panel.property_panel.show_node(self.bridge.core_node(node_id))
        self._update_preview_and_result()

    def _on_param_changed(self) -> None:
        # live tuning: incremental cache recomputes only the changed subtree.
        self.results = self.scheduler.run(self.bridge.to_core_graph())
        self._update_preview_and_result()
        self.set_status(self._summary())

    def _step_image(self, delta: int) -> None:
        source = self._find_image_source()
        if source is None:
            return
        files = source.files()
        if not files:
            return
        idx = (int(source.param("index")) + delta) % len(files)
        source.set_param("index", idx)
        self.results = self.scheduler.run(self.bridge.to_core_graph())
        self._update_preview_and_result()

    # -- preview / result --------------------------------------------------
    def _update_preview_and_result(self) -> None:
        node = self.bridge.core_node(self._display_id) if self._display_id else None
        res = self.results.get(self._display_id) if self._display_id else None
        label = (node.LABEL or node.NODE_TYPE) if node else "—"
        self.right_panel.show_result(label, res)

        if res is None or not res.ok:
            self.right_panel.preview.clear(
                res.error if (res and not res.ok) else "執行流程後顯示"
            )
            return
        image = next((v for v in res.outputs.values() if isinstance(v, Image)), None)
        if image is None:
            self.right_panel.preview.clear("（此節點無圖像輸出）")
            return
        name = QtCore.QFileInfo(image.meta.get("source", "")).fileName() or "(記憶體影像)"
        self.right_panel.preview.show_bgr(to_display_bgr(image), name)

    def _summary(self) -> str:
        total = sum(r.elapsed_ms for r in self.results.values())
        errors = [r for r in self.results.values() if not r.ok]
        defects = sum(
            len(r.outputs["detections"])
            for r in self.results.values() if "detections" in r.outputs
        )
        verdicts = [
            v for r in self.results.values()
            for v in r.outputs.values() if isinstance(v, Verdict)
        ]
        bits = []
        if errors:
            bits.append(f"錯誤:{len(errors)}")
        bits.append(f"缺陷:{defects}")
        if verdicts:
            bits.append("NG" if any(not v.ok for v in verdicts) else "OK")
        bits.append(f"{total:.1f}ms")
        return " | ".join(bits)

    def _find_image_source(self):
        return next(
            (n for n in self.bridge.nodes if n.NODE_TYPE == "sources/ImageSource"),
            None,
        )

    # -- persistence -------------------------------------------------------
    def save_flow(self, path: str) -> None:
        save_graph(self.bridge.to_core_graph(), path)

    def load_flow(self, path: str) -> None:
        self.bridge.load_core_graph(load_graph(path))
        self._refresh_canvas_nodes()

    def _save_dialog(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "儲存流程", "", "VisionPower 流程 (*.json)"
        )
        if path:
            self.save_flow(path)
            self.set_status(f"已儲存 {path}")

    def _load_dialog(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "載入流程", "", "VisionPower 流程 (*.json)"
        )
        if path:
            self.load_flow(path)
            self.run_all()
            self.set_status(f"已載入 {path}")

    # -- window controls ---------------------------------------------------
    def toggle_max(self) -> bool:
        """Maximise to fill the screen's work area, or restore the prior size."""

        self._maximized = not self._maximized
        if self._maximized:
            self._restore_geom = self.geometry()
            screen = self.screen() or QtGui.QGuiApplication.primaryScreen()
            if screen is not None:
                self.setGeometry(screen.availableGeometry())
        elif self._restore_geom is not None:
            self.setGeometry(self._restore_geom)
        return self._maximized

    # -- sizing -----------------------------------------------------------
    @staticmethod
    def _fitted_geometry(avail: QtCore.QRect) -> QtCore.QRect:
        """Cap the window at the design size, shrink to fit, and centre it."""

        w = min(_DESIGN_SIZE[0], int(avail.width() * 0.95))
        h = min(_DESIGN_SIZE[1], int(avail.height() * 0.95))
        x = avail.x() + (avail.width() - w) // 2
        y = avail.y() + (avail.height() - h) // 2
        return QtCore.QRect(x, y, w, h)
