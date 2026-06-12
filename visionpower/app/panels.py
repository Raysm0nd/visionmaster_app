"""Right-side / bottom panels mirroring the VisionMaster layout:

- :class:`SourceStrip`   — 圖像源 thumbnail strip (i/n, click to switch, run-all)
- :class:`ResultsPanel`  — 模組結果 tab: detections table + verdict + measurements
- :class:`HistoryPanel`  — 歷史結果 bottom table: 執行序號 / 時間 / 模組數據
"""

from __future__ import annotations

import cv2
from PySide6 import QtCore, QtGui, QtWidgets

from visionpower.core import Node, NodeResult
from visionpower.core.types import Detection, Measurement, Verdict

_THUMB = QtCore.QSize(72, 54)


class SourceStrip(QtWidgets.QWidget):
    """Thumbnail strip bound to an ``sources/ImageSource`` core node."""

    index_selected = QtCore.Signal(int)
    run_all_requested = QtCore.Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._node: Node | None = None
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        header = QtWidgets.QHBoxLayout()
        self._title = QtWidgets.QLabel("圖像源 (0/0)")
        self._run_all = QtWidgets.QPushButton("全部執行")
        self._run_all.clicked.connect(self.run_all_requested.emit)
        header.addWidget(self._title)
        header.addStretch(1)
        header.addWidget(self._run_all)
        layout.addLayout(header)

        self._list = QtWidgets.QListWidget()
        self._list.setViewMode(QtWidgets.QListView.IconMode)
        self._list.setFlow(QtWidgets.QListView.LeftToRight)
        self._list.setWrapping(False)
        self._list.setIconSize(_THUMB)
        self._list.setFixedHeight(_THUMB.height() + 34)
        self._list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self._list.currentRowChanged.connect(self._on_row)
        layout.addWidget(self._list)

    def bind(self, node: Node | None) -> None:
        """Point the strip at an ImageSource node (or None) and refresh."""

        self._node = node
        self._list.blockSignals(True)
        self._list.clear()
        files = node.files() if node is not None else []
        for path in files:
            data = cv2.imread(path, cv2.IMREAD_COLOR)
            item = QtWidgets.QListWidgetItem(QtCore.QFileInfo(path).fileName())
            if data is not None:
                h, w = data.shape[:2]
                rgb = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)
                qimg = QtGui.QImage(rgb.data, w, h, 3 * w, QtGui.QImage.Format_RGB888)
                item.setIcon(QtGui.QIcon(QtGui.QPixmap.fromImage(qimg.copy())))
            item.setToolTip(path)
            self._list.addItem(item)
        if node is not None and files:
            self._list.setCurrentRow(min(int(node.param("index")), len(files) - 1))
        self._list.blockSignals(False)
        self._update_title()

    def _on_row(self, row: int) -> None:
        if row >= 0 and self._node is not None:
            self._node.set_param("index", row)
            self._update_title()
            self.index_selected.emit(row)

    def select_row(self, row: int) -> None:
        self._list.blockSignals(True)
        self._list.setCurrentRow(row)
        self._list.blockSignals(False)
        self._update_title()

    def count(self) -> int:
        return self._list.count()

    def _update_title(self) -> None:
        n = self._list.count()
        i = self._list.currentRow() + 1 if n else 0
        self._title.setText(f"圖像源 ({i}/{n})")


class ResultsPanel(QtWidgets.QWidget):
    """模組結果: structured outputs of the displayed node."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self._verdict = QtWidgets.QLabel("—")
        self._verdict.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self._verdict)
        self._table = QtWidgets.QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(["#", "標籤", "X", "Y", "寬x高", "面積"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)
        self._meta = QtWidgets.QLabel("")
        self._meta.setWordWrap(True)
        layout.addWidget(self._meta)

    def show_result(self, result: NodeResult | None) -> None:
        self._table.setRowCount(0)
        if result is None:
            self._verdict.setText("—")
            self._meta.setText("")
            return
        if not result.ok:
            self._verdict.setText("錯誤")
            self._verdict.setStyleSheet("color: #e05a5a; font-size: 14px; font-weight: bold;")
            self._meta.setText(result.error or "")
            return

        verdict = next((v for v in result.outputs.values() if isinstance(v, Verdict)), None)
        detection = next((v for v in result.outputs.values() if isinstance(v, Detection)), None)
        measurement = next((v for v in result.outputs.values() if isinstance(v, Measurement)), None)

        if verdict is None:
            self._verdict.setText("（無判定輸出）")
            self._verdict.setStyleSheet("color: #9a9a9a; font-size: 14px; font-weight: bold;")
        elif verdict.ok:
            self._verdict.setText("判定：OK")
            self._verdict.setStyleSheet("color: #5ad07a; font-size: 14px; font-weight: bold;")
        else:
            self._verdict.setText("判定：NG — " + "; ".join(verdict.reasons))
            self._verdict.setStyleSheet("color: #e05a5a; font-size: 14px; font-weight: bold;")

        if detection is not None:
            self._table.setRowCount(len(detection.items))
            for row, item in enumerate(detection.items):
                x, y, w, h = item.bbox
                cells = [str(row), item.label, str(x), str(y), f"{w}x{h}", f"{item.area:.0f}"]
                for col, text in enumerate(cells):
                    self._table.setItem(row, col, QtWidgets.QTableWidgetItem(text))

        bits = [f"耗時 {result.elapsed_ms:.1f} ms" + ("（快取）" if result.cached else "")]
        if measurement is not None and measurement.values:
            bits += [f"{k}={v:.3g}" for k, v in measurement.values.items()]
        self._meta.setText(" | ".join(bits))


class HistoryPanel(QtWidgets.QTableWidget):
    """歷史結果: one row per execution (執行序號 / 時間 / 模組數據)."""

    def __init__(self, parent=None) -> None:
        super().__init__(0, 3, parent)
        self.setHorizontalHeaderLabels(["執行序號", "時間", "模組數據"])
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setColumnWidth(0, 80)
        self.setColumnWidth(1, 170)
        self._counter = 0

    def append(self, summary: str) -> None:
        self._counter += 1
        row = 0  # newest first, like the reference
        self.insertRow(row)
        now = QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss.zzz")
        for col, text in enumerate([str(self._counter), now, summary]):
            self.setItem(row, col, QtWidgets.QTableWidgetItem(text))
