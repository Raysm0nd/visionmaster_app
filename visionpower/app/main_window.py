"""Main window — layout modeled on Hikrobot VisionMaster:

left 節點工具 palette · center vertical flow canvas · right tabs 圖像/模組結果
(preview + info readout + 圖像源 thumbnail strip) · right 屬性 panel · bottom
歷史結果 table · toolbar 執行/全部執行.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
import numpy as np
from PySide6 import QtCore, QtWidgets
from NodeGraphQt import NodeGraph
from NodeGraphQt.constants import LayoutDirectionEnum

import visionpower.nodes  # noqa: F401  (populate the node registry)
from visionpower.core import NodeContext, Scheduler, load_graph, save_graph
from visionpower.core.types import Detection, Image, Verdict
from visionpower.render import to_display_bgr
from visionpower.app.graph_bridge import GraphBridge
from visionpower.app.panels import HistoryPanel, ResultsPanel, SourceStrip
from visionpower.app.preview_view import PreviewView
from visionpower.app.property_panel import PropertyPanel

_DEMO = [
    ("sources/ImageSource", "source"),
    ("filters/Grayscale", "gray"),
    ("filters/GaussianBlur", "blur"),
    ("filters/Threshold", "thresh"),
    ("analysis/FindContours", "contours"),
    ("sinks/Viewer", "viewer"),
]


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VisionPower 視覺檢測平台")
        self.resize(1500, 900)

        self.graph = NodeGraph()
        self.graph.set_layout_direction(LayoutDirectionEnum.VERTICAL.value)
        self.bridge = GraphBridge(self.graph)
        self.scheduler = Scheduler()
        self.results: dict = {}
        self._display_id: str | None = None  # ng node id shown in preview

        self.setCentralWidget(self.graph.widget)
        self._build_palette()
        self._build_right_panels()
        self._build_history()
        self._build_toolbar()

        self.graph.node_selection_changed.connect(lambda *_: self._on_selection())
        self.statusBar().showMessage("就緒")

    # ------------------------------------------------------------------ UI
    def _build_palette(self) -> None:
        dock = QtWidgets.QDockWidget("節點工具", self)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable)
        self.palette = QtWidgets.QListWidget()
        for vp_type, label in self.bridge.vp_types():
            item = QtWidgets.QListWidgetItem(f"{label}\n{vp_type}")
            item.setData(QtCore.Qt.UserRole, vp_type)
            self.palette.addItem(item)
        self.palette.itemDoubleClicked.connect(
            lambda it: self.bridge.add_node(it.data(QtCore.Qt.UserRole))
        )
        dock.setWidget(self.palette)
        dock.setMaximumWidth(230)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)

    def _build_right_panels(self) -> None:
        # --- 圖像 tab: display selector + preview + readout + source strip
        image_tab = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(image_tab)
        v.setContentsMargins(4, 4, 4, 4)

        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("顯示來源"))
        self.display_combo = QtWidgets.QComboBox()
        self.display_combo.setMinimumWidth(180)
        self.display_combo.currentIndexChanged.connect(self._on_display_changed)
        top.addWidget(self.display_combo)
        top.addStretch(1)
        v.addLayout(top)

        self.preview = PreviewView()
        v.addWidget(self.preview, stretch=1)

        info = QtWidgets.QHBoxLayout()
        self.info_file = QtWidgets.QLabel("—")
        self.info_cursor = QtWidgets.QLabel("X,---- Y,----  R:--- G:--- B:---")
        info.addWidget(self.info_file)
        info.addStretch(1)
        info.addWidget(self.info_cursor)
        v.addLayout(info)
        self.preview.cursor_info.connect(
            lambda x, y, r, g, b: self.info_cursor.setText(
                f"X,{x:04d} Y,{y:04d}  R:{r:03d} G:{g:03d} B:{b:03d}"
            )
        )

        self.source_strip = SourceStrip()
        self.source_strip.index_selected.connect(lambda _i: self.run_flow())
        self.source_strip.run_all_requested.connect(self.run_all)
        v.addWidget(self.source_strip)

        # --- 模組結果 tab
        self.results_panel = ResultsPanel()

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(image_tab, "圖像")
        tabs.addTab(self.results_panel, "模組結果")
        self._tabs = tabs

        preview_dock = QtWidgets.QDockWidget("檢視", self)
        preview_dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable)
        preview_dock.setWidget(tabs)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, preview_dock)

        self.property_panel = PropertyPanel()
        self.property_panel.param_changed.connect(self._on_param_changed)
        prop_dock = QtWidgets.QDockWidget("屬性", self)
        prop_dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable)
        prop_dock.setWidget(self.property_panel)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, prop_dock)
        self.splitDockWidget(preview_dock, prop_dock, QtCore.Qt.Vertical)
        self.resizeDocks([preview_dock, prop_dock], [620, 240], QtCore.Qt.Vertical)

    def _build_history(self) -> None:
        dock = QtWidgets.QDockWidget("歷史結果", self)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable)
        self.history = HistoryPanel()
        dock.setWidget(self.history)
        dock.setMaximumHeight(220)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)

    def _build_toolbar(self) -> None:
        tb = self.addToolBar("主工具列")
        tb.setMovable(False)
        tb.addAction("▶ 執行", self.run_flow)
        tb.addAction("⏩ 全部執行", self.run_all)
        tb.addSeparator()
        tb.addAction("示範流程", lambda: self.build_demo_flow())
        tb.addSeparator()
        tb.addAction("儲存", self._save)
        tb.addAction("載入", self._load)

    # ------------------------------------------------------ demo workflow
    def build_demo_flow(self, source_path: str = "") -> None:
        """Build the sample pipeline. ``source_path``: folder → ImageSource,
        file → LoadImage, empty → generate 4 synthetic samples (like the ref UI).
        """

        steps = list(_DEMO)
        if source_path and Path(source_path).is_file():
            steps[0] = ("sources/LoadImage", "source")
        elif not source_path:
            source_path = self._make_demo_images()

        self.graph.clear_session()
        self.bridge.core_nodes.clear()
        created = {}
        for i, (vp_type, key) in enumerate(steps):
            created[key] = self.bridge.add_node(vp_type, pos=(0, i * 160))
        created["viewer"].set_pos(260, (len(steps) - 1) * 160)

        src_core = self.bridge.core_node_for(created["source"])
        if steps[0][0] == "sources/ImageSource":
            src_core.set_param("folder", source_path)
        else:
            src_core.set_param("path", source_path)

        def link(a, ao, b, bo):
            created[a].get_output(ao).connect_to(created[b].get_input(bo))

        link("source", "image", "gray", "image")
        link("gray", "image", "blur", "image")
        link("blur", "image", "thresh", "image")
        link("thresh", "image", "contours", "image")
        link("source", "image", "viewer", "image")
        link("contours", "detections", "viewer", "detections")
        link("contours", "verdict", "viewer", "verdict")

        # fit the whole flow in view
        self.graph.select_all()
        self.graph.fit_to_selection()
        self.graph.clear_selection()
        self.run_flow()

    @staticmethod
    def _make_demo_images() -> str:
        """Generate 4 sample images (some OK, some with defects) in a temp dir."""

        folder = tempfile.mkdtemp(prefix="visionpower_demo_")
        rng = np.random.default_rng(7)
        for i, n_defects in enumerate([0, 1, 2, 3]):
            img = np.full((240, 320, 3), 24, np.uint8)
            noise = rng.integers(0, 18, (240, 320, 1), dtype=np.uint8)
            img = cv2.add(img, np.repeat(noise, 3, axis=2))
            for _ in range(n_defects):
                x, y = int(rng.integers(30, 280)), int(rng.integers(30, 200))
                r = int(rng.integers(8, 22))
                cv2.circle(img, (x, y), r, (235, 235, 235), -1)
            cv2.imwrite(str(Path(folder) / f"sample-{i + 1}.png"), img)
        return folder

    # ----------------------------------------------------------- execution
    def run_flow(self, log_history: bool = True) -> None:
        graph = self.bridge.to_core_graph()
        ctx = NodeContext(log=lambda m: self.statusBar().showMessage(m))
        self.results = self.scheduler.run(graph)
        self._color_nodes()
        self._refresh_display_combo()
        self._refresh_source_strip()
        self._update_preview()
        self._refresh_results_panel()
        if log_history:
            self.history.append(self._summary())
        self.statusBar().showMessage(self._summary())

    def run_all(self) -> None:
        """Batch: iterate every image of the bound ImageSource (全部執行)."""

        node = self._find_image_source()
        if node is None:
            self.statusBar().showMessage("沒有 Image Source 節點可批次執行")
            return
        n = len(node.files())
        if n == 0:
            self.statusBar().showMessage("圖像源資料夾沒有符合的影像")
            return
        ok = ng = 0
        for i in range(n):
            node.set_param("index", i)
            self.source_strip.select_row(i)
            self.run_flow()
            verdicts = [
                v for r in self.results.values()
                for v in r.outputs.values() if isinstance(v, Verdict)
            ]
            if verdicts and not all(v.ok for v in verdicts):
                ng += 1
            else:
                ok += 1
            QtWidgets.QApplication.processEvents()
        self.statusBar().showMessage(f"全部執行完成：{n} 張 — OK {ok} / NG {ng}")

    def _summary(self) -> str:
        total = sum(r.elapsed_ms for r in self.results.values())
        errors = [r for r in self.results.values() if not r.ok]
        verdicts = [
            v for r in self.results.values()
            for v in r.outputs.values() if isinstance(v, Verdict)
        ]
        defects = sum(
            len(r.outputs["detections"])
            for r in self.results.values() if "detections" in r.outputs
        )
        source = next(
            (r.outputs["image"].meta.get("source", "") for r in self.results.values()
             if "image" in r.outputs and isinstance(r.outputs["image"], Image)
             and "source" in r.outputs["image"].meta),
            "",
        )
        bits = []
        if source:
            bits.append(QtCore.QFileInfo(source).fileName())
        if errors:
            bits.append(f"錯誤:{len(errors)}")
        bits.append(f"缺陷:{defects}")
        if verdicts:
            bits.append("NG" if any(not v.ok for v in verdicts) else "OK")
        bits.append(f"{total:.1f}ms")
        return " | ".join(bits)

    def _color_nodes(self) -> None:
        for ng_node in self.graph.all_nodes():
            res = self.results.get(ng_node.id)
            if res is None:
                continue
            verdict = next(
                (v for v in res.outputs.values() if isinstance(v, Verdict)), None
            ) if res.ok else None
            if not res.ok:
                ng_node.set_color(140, 40, 40)  # error → red
            elif verdict is not None and not verdict.ok:
                ng_node.set_color(150, 100, 30)  # NG → amber
            else:
                ng_node.set_color(45, 90, 55)  # ok → green

    # --------------------------------------------------- display / preview
    def _refresh_display_combo(self) -> None:
        """List nodes whose results contain an image output (like 顯示來源)."""

        current = self._display_id
        self.display_combo.blockSignals(True)
        self.display_combo.clear()
        for ng_node in self.graph.all_nodes():
            res = self.results.get(ng_node.id)
            if res and any(isinstance(v, Image) for v in res.outputs.values()):
                self.display_combo.addItem(f"{ng_node.name()}.圖像", ng_node.id)
        # prefer: previous choice → last Viewer → last entry
        idx = self.display_combo.findData(current)
        if idx < 0:
            for i in range(self.display_combo.count()):
                nid = self.display_combo.itemData(i)
                core = self.bridge.core_nodes.get(nid)
                if core is not None and core.NODE_TYPE == "sinks/Viewer":
                    idx = i
        if idx < 0:
            idx = self.display_combo.count() - 1
        if idx >= 0:
            self.display_combo.setCurrentIndex(idx)
            self._display_id = self.display_combo.itemData(idx)
        self.display_combo.blockSignals(False)

    def _on_display_changed(self, index: int) -> None:
        self._display_id = self.display_combo.itemData(index)
        self._update_preview()
        self._refresh_results_panel()

    def _update_preview(self) -> None:
        res = self.results.get(self._display_id) if self._display_id else None
        if res is None:
            self.preview.clear("執行流程後顯示")
            self.info_file.setText("—")
            return
        if not res.ok:
            self.preview.clear(res.error or "節點錯誤")
            self.info_file.setText("—")
            return
        image = next((v for v in res.outputs.values() if isinstance(v, Image)), None)
        if image is None:
            self.preview.clear("（此節點無圖像輸出）")
            self.info_file.setText("—")
            return
        self.preview.show_bgr(to_display_bgr(image))
        name = QtCore.QFileInfo(image.meta.get("source", "")).fileName() or "(記憶體影像)"
        self.info_file.setText(f"{name}   {image.width} × {image.height}")

    def _refresh_results_panel(self) -> None:
        """Show the displayed node's structured result; if it has none (e.g. a
        Viewer), fall back to the last node that produced detections/verdict."""

        res = self.results.get(self._display_id) if self._display_id else None
        if res is not None and res.ok and not any(
            isinstance(v, (Detection, Verdict)) for v in res.outputs.values()
        ):
            res = next(
                (r for r in reversed(list(self.results.values()))
                 if r.ok and any(
                     isinstance(v, (Detection, Verdict)) for v in r.outputs.values()
                 )),
                res,
            )
        self.results_panel.show_result(res)

    def _refresh_source_strip(self) -> None:
        self.source_strip.bind(self._find_image_source())

    def _find_image_source(self):
        for core in self.bridge.core_nodes.values():
            if core.NODE_TYPE == "sources/ImageSource":
                return core
        return None

    # ------------------------------------------------- selection / params
    def _on_selection(self) -> None:
        selected = self.graph.selected_nodes()
        ng_node = selected[-1] if selected else None
        core = self.bridge.core_node_for(ng_node) if ng_node else None
        self.property_panel.show_node(core)
        if ng_node is not None:
            idx = self.display_combo.findData(ng_node.id)
            if idx >= 0:
                self.display_combo.setCurrentIndex(idx)  # triggers preview update

    def _on_param_changed(self) -> None:
        # Live tuning: incremental cache recomputes only the changed subtree.
        self.run_flow(log_history=False)

    # --------------------------------------------------------- persistence
    def _save(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "儲存流程", "", "VisionPower 流程 (*.json)"
        )
        if path:
            save_graph(self.bridge.to_core_graph(), path)
            self.statusBar().showMessage(f"已儲存 {path}")

    def _load(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "載入流程", "", "VisionPower 流程 (*.json)"
        )
        if path:
            self.bridge.load_core_graph(load_graph(path))
            self.run_flow()
            self.statusBar().showMessage(f"已載入 {path}")
