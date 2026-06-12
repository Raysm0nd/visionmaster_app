"""Right inspection panel — 源圖 / 輸出結果 / 屬性 tabs.

源圖 and 輸出結果 mirror the design; 屬性 is added so node parameters stay
editable (the design folded the property panel away, but functional parity
requires it). A sub-toolbar carries view controls; the result tab renders the
selected node's structured output as a key-value list.
"""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from visionpower.app import icons, theme
from visionpower.app.preview_view import PreviewView
from visionpower.app.property_panel import PropertyPanel
from visionpower.core import NodeResult
from visionpower.core.types import Detection, Image, Measurement, Verdict

_SUBBAR = ["split", "grid", "search", "zoomout", "onetoone", "fullscreen"]


class RightPanel(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("rightPanel")
        self.setStyleSheet(
            f"#rightPanel{{background:{theme.BG_PANEL};"
            f"border-left:1px solid rgba(255,255,255,0.06);}}"
        )
        self._tab = "image"
        self._tab_buttons: dict[str, QtWidgets.QPushButton] = {}

        col = QtWidgets.QVBoxLayout(self)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)

        col.addWidget(self._build_tabs())
        col.addWidget(self._build_subbar())

        self.preview = PreviewView()
        self.property_panel = PropertyPanel()
        self._result_view = self._build_result_view()

        self._stack = QtWidgets.QStackedWidget()
        self._stack.addWidget(self.preview)        # 0 image
        self._stack.addWidget(self._result_view)   # 1 result
        self._stack.addWidget(self.property_panel)  # 2 property
        col.addWidget(self._stack, stretch=1)

        self._restyle_tabs()

    # -- tab state ---------------------------------------------------------
    def current_tab(self) -> str:
        return self._tab

    def show_image_tab(self) -> None:
        self._set_tab("image", 0)

    def show_result_tab(self) -> None:
        self._set_tab("result", 1)

    def show_property_tab(self) -> None:
        self._set_tab("property", 2)

    def _set_tab(self, name: str, index: int) -> None:
        self._tab = name
        self._stack.setCurrentIndex(index)
        self._restyle_tabs()

    # -- results -----------------------------------------------------------
    def show_result(self, node_label: str, result: NodeResult | None) -> None:
        self._result_title.setText(f"{node_label} · 輸出")
        self._result_table.setRowCount(0)
        for key, value in _result_rows(result):
            row = self._result_table.rowCount()
            self._result_table.insertRow(row)
            self._result_table.setItem(row, 0, QtWidgets.QTableWidgetItem(key))
            self._result_table.setItem(row, 1, QtWidgets.QTableWidgetItem(value))

    def result_row_count(self) -> int:
        return self._result_table.rowCount()

    # -- construction ------------------------------------------------------
    def _build_tabs(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        bar.setFixedHeight(44)
        row = QtWidgets.QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        for name, label in [("image", "源圖"), ("result", "輸出結果"), ("property", "屬性")]:
            btn = QtWidgets.QPushButton(label)
            btn.setCursor(QtCore.Qt.PointingHandCursor)
            btn.setFixedHeight(44)
            btn.clicked.connect(lambda _=False, n=name: self._tab_clicked(n))
            self._tab_buttons[name] = btn
            row.addWidget(btn)
        row.addStretch(1)
        bar.setStyleSheet("border-bottom:1px solid rgba(255,255,255,0.06);")
        return bar

    def _tab_clicked(self, name: str) -> None:
        {"image": self.show_image_tab, "result": self.show_result_tab,
         "property": self.show_property_tab}[name]()

    def _restyle_tabs(self) -> None:
        for name, btn in self._tab_buttons.items():
            active = name == self._tab
            color = theme.TEXT if active else theme.TEXT_DIM
            border = theme.ACCENT if active else "transparent"
            bg = "rgba(47,128,216,0.06)" if active else "transparent"
            btn.setStyleSheet(
                f"QPushButton{{background:{bg};color:{color};border:none;"
                f"border-bottom:2px solid {border};font-size:14px;font-weight:600;"
                f"padding:0 22px;}}"
            )

    def _build_subbar(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(bar)
        row.setContentsMargins(12, 9, 12, 9)
        row.setSpacing(1)
        row.addStretch(1)
        for name in _SUBBAR:
            btn = QtWidgets.QPushButton()
            btn.setIcon(icons.make_icon(name, "#7E8AA0", 16))
            btn.setIconSize(QtCore.QSize(16, 16))
            btn.setCursor(QtCore.Qt.PointingHandCursor)
            btn.setFixedSize(27, 27)
            btn.setStyleSheet(
                "QPushButton{background:transparent;border:none;border-radius:6px;}"
                "QPushButton:hover{background:rgba(255,255,255,0.07);}"
            )
            row.addWidget(btn)
        bar.setStyleSheet("border-bottom:1px solid rgba(255,255,255,0.05);")
        return bar

    def _build_result_view(self) -> QtWidgets.QWidget:
        host = QtWidgets.QWidget()
        col = QtWidgets.QVBoxLayout(host)
        col.setContentsMargins(16, 16, 16, 16)
        self._result_title = QtWidgets.QLabel("輸出")
        self._result_title.setStyleSheet(
            f"color:{theme.TEXT_FAINT};font-size:11px;font-weight:600;"
            f"letter-spacing:2px;"
        )
        col.addWidget(self._result_title)
        self._result_table = QtWidgets.QTableWidget(0, 2)
        self._result_table.horizontalHeader().setVisible(False)
        self._result_table.verticalHeader().setVisible(False)
        self._result_table.setShowGrid(False)
        self._result_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._result_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeToContents
        )
        self._result_table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.Stretch
        )
        col.addWidget(self._result_table, stretch=1)
        return host


def _result_rows(result: NodeResult | None) -> list[tuple[str, str]]:
    """Flatten a NodeResult's structured outputs into key-value display rows."""

    if result is None:
        return []
    if not result.ok:
        return [("狀態", "錯誤"), ("訊息", result.error or "")]

    rows: list[tuple[str, str]] = []
    for value in result.outputs.values():
        if isinstance(value, Image):
            rows += [("影像寬度", str(value.width)), ("影像高度", str(value.height)),
                     ("通道數", str(value.channels))]
        elif isinstance(value, Detection):
            rows.append(("偵測數量", str(len(value))))
            for i, item in enumerate(value.items[:8]):
                x, y, w, h = item.bbox
                rows.append((f"#{i} {item.label or '物件'}", f"{x},{y} {w}×{h} 面積{item.area:.0f}"))
        elif isinstance(value, Measurement):
            rows += [(k, f"{v:.4g}") for k, v in value.values.items()]
        elif isinstance(value, Verdict):
            rows.append(("判定", "OK" if value.ok else "NG"))
            if value.reasons:
                rows.append(("原因", "; ".join(value.reasons)))
    rows.append(("耗時", f"{result.elapsed_ms:.2f} ms" + ("（快取）" if result.cached else "")))
    return rows
